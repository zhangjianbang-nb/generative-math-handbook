#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补写短节：把低于预算的节补到目标比例，直到全书可见字符达到目标。
复用 gen_book 的 call/clean/merge 逻辑；每次只补 1–2 个新小节。"""
import argparse
import concurrent.futures
import json
import os
import re
import threading
import time

import gen_book as G

ROOT = G.ROOT
BOOK = G.BOOK
SEC = G.OUTDIR
PROGRESS = os.path.join(ROOT, "book", "progress_fill.jsonl")


def build_fill(t, text, need):
    heads = re.findall(r"^###\s+(.+)$", text, re.M)
    avoid = "；".join(heads[-10:]) if heads else "（无）"
    n = 1 if need < 1600 else 2
    return G.STYLE.format(
        sid=t["id"], title=t["title"], target=t["target_cjk"], minc=t["min_cjk"],
        formulas=t["formulas"], derivs=t["derivations"], tables=t["tables"], figures=t["figures"],
    ) + f"""

本次任务：为第 {t['id']} 节《{t['title']}》补写 {n} 个深化小节。
已有小标题（不要重复，也不要换词重讲）：
{avoid}

写 {n} 个新的 `###` 小节，标题必须是 `### 深入：<具体主题>` 或 `### 补论：<具体主题>`；
不要复用“问题/对象/定理/离散化/误差界/实验映射/小结与陷阱”这些已有标题。
合计约 {need} 个汉字；推进到尚未覆盖的内容：常数与阶的完整推导、具体模型的最小实验、
失效判据与反例三选一，必须与本节的数学对象直接相关。
至少含 1 个公式或 1 张表；不要导语，不要总结前文，不要重复已有段落。直接开始写正文。"""


def fill_one(t, target_vis, rounds_cap=3):
    path = os.path.join(SEC, f"{t['id']}.md")
    if not os.path.exists(path):
        return {"id": t["id"], "status": "missing"}
    txt = open(path, encoding="utf-8").read()
    if G.visible(txt) >= target_vis:
        return {"id": t["id"], "status": "skip", "visible": G.visible(txt)}
    started = time.time()
    rounds = 0
    try:
        while G.visible(txt) < target_vis and rounds < rounds_cap:
            rounds += 1
            need = max(700, int((target_vis - G.visible(txt)) / 1.6))
            frag, fin = G.call(build_fill(t, txt, need), max_tokens=8192)
            frag = G.clean(frag, t)
            frag = re.sub(r"^##\s+.*\n+", "", frag)
            txt = G.merge_duplicate_headings(txt.rstrip() + "\n\n" + frag.strip() + "\n")
        txt = G.clean(txt, t)
        open(path, "w", encoding="utf-8").write(txt)
        rec = {"id": t["id"], "status": "ok", "visible": G.visible(txt), "cjk": G.cjk(txt),
               "rounds": rounds, "elapsed": round(time.time() - started, 1), "finish": fin}
    except Exception as e:
        rec = {"id": t["id"], "status": "error", "err": repr(e)[:200],
               "elapsed": round(time.time() - started, 1)}
    with open(PROGRESS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--goal", type=int, default=8100000)
    ap.add_argument("--factor", type=float, default=1.01)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    tasks = json.load(open(BOOK, encoding="utf-8"))
    vis = {}
    for t in tasks:
        p = os.path.join(SEC, t["id"] + ".md")
        vis[t["id"]] = G.visible(open(p, encoding="utf-8").read()) if os.path.exists(p) else 0
    total = sum(vis.values())
    print(f"start total {total:,} goal {args.goal:,}")
    cand = [t for t in tasks if vis[t["id"]] < t["budget"] * args.factor]
    cand.sort(key=lambda t: vis[t["id"]] / t["budget"])
    if args.limit:
        cand = cand[: args.limit]
    print(f"candidates {len(cand)} (worst {cand[0]['id']} {vis[cand[0]['id']]}/{cand[0]['budget']})")
    lock = threading.Lock()
    stop = [False]

    def run(t):
        with lock:
            if stop[0]:
                return {"id": t["id"], "status": "stopped"}
        rec = fill_one(t, int(t["budget"] * args.factor), args.rounds)
        with lock:
            nonlocal total
            if rec.get("status") == "ok":
                total += rec["visible"] - vis[t["id"]]
            print(f"{rec['id']} {rec['status']} vis={rec.get('visible','-')} total={total:,}", flush=True)
            if total >= args.goal:
                stop[0] = True
        return rec

    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(run, cand))
    print(f"done in {(time.time()-t0)/60:.1f} min total={total:,}")


if __name__ == "__main__":
    main()
