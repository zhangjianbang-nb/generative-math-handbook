#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《生成式数学手册》正文批量生成器（断点续跑，本地 tensorfold 18891）。"""
import argparse
import concurrent.futures
import json
import os
import re
import threading
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "book", "book.json")
OUTDIR = os.path.join(ROOT, "book", "sec")
LOG = os.path.join(ROOT, "book", "gen.log")
PROGRESS = os.path.join(ROOT, "book", "progress.jsonl")
API = "http://127.0.0.1:18891/v1/chat/completions"
MODEL = "DeepSeek-V4.1-Flash-1017-TF"

STYLE = """你是《生成式数学手册》的作者。读者是做生成模型（扩散、流匹配、VAE、GAN、自回归、SSM）的中文算法工程师与研究生。本书的写作协议是七段式：**问题 → 对象 → 定理 → 离散化 → 误差界 → 实验映射 → 小结与陷阱**。写作要求：
1. 只输出 Markdown 正文；不要 HTML、不要代码围栏包整篇、不要 YAML front matter。
2. 以 `## {sid} {title}` 开头；下面用 `###` 小标题按七段组织（小标题可带编号）。
3. 目标 {target} 个汉字，不得少于 {minc} 字；信息密度高，不写套话，不重复开头。
4. 公式用 `$$...$$`（块）或 `$...$`（行内）；本节至少 {formulas} 个公式、{derivs} 处三步以上推导。
5. 至少 {tables} 张 Markdown 表（符号表 / 对比表 / 失效判据表）。
6. 至少 {figures} 个图注，写成 `![图 {sid}-k：描述](fig://{sid}-k)`，后接 2–3 句图说；不要引用外部图片路径。
7. 定理必须写全条件；至少 1 个反例说明“去掉条件会怎样”。
8. 不编造实验数字、页码、年份；只使用给定事实中的数字，没有就定性表述。禁止“大概 / 可能 / 一般来说”糊过去。
9. 结尾“小结与陷阱”不超过 3 条，至少 1 条失效判据；最后一段落在具体机制或判据上，不写空泛总结。"""


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def visible(s):
    return len(re.sub(r"\s", "", s))


def count_formulas(s):
    block = len(re.findall(r"\$\$[\s\S]*?\$\$", s))
    inline = len(re.findall(r"(?<!\$)\$[^$\n]+\$(?!\$)", s))
    return block + inline


def count_tables(s):
    return len(re.findall(r"^\s*\|[\s\-:|]+\|\s*$", s, re.M))


def count_figures(s):
    return len(re.findall(r"!\[", s))


def count_derivations(s):
    return len(re.findall(r"^#{2,4}.*(推导|证明)", s, re.M)) + len(re.findall(r"\*\*(推导|证明)\*\*", s))


def _norm_head(h):
    h = re.sub(r"^#+\s*", "", h)
    for t in ("误差界", "实验映射", "小结与陷阱"):
        if t in h:
            return "t:" + t
    m = re.match(r"^(\d+(?:\.\d+)*)", h)
    if m:
        parts = m.group(1).split(".")
        # 5 / 5.1 视为同一小节；1.3.5 / 1.3.5（续）按完整号区分
        return "n:" + (parts[0] if len(parts) <= 2 else m.group(1))
    h = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", h)
    return h[:12]


def merge_duplicate_headings(s):
    """扩写轮常把已有小节换个编号重写一遍：同义标题合并为一个，正文按出现顺序拼接。"""
    lines = s.splitlines()
    pre, blocks, cur = [], [], None
    for line in lines:
        if line.startswith("### "):
            if cur is not None:
                blocks.append(cur)
            cur = [line, []]
        elif cur is not None:
            cur[1].append(line)
        else:
            pre.append(line)
    if cur is not None:
        blocks.append(cur)
    order, groups = [], {}
    for head, body in blocks:
        key = _norm_head(head)
        if key not in groups:
            groups[key] = [head, list(body)]
            order.append(key)
        else:
            # 同一小节的重复扩写：保留正文更长的一版，避免字数翻倍
            if cjk("\n".join(body)) > cjk("\n".join(groups[key][1])):
                groups[key][1] = list(body)
    out = list(pre)
    for key in order:
        head, body = groups[key]
        out.append(head)
        out.extend(body)
    return "\n".join(out).strip() + "\n"


def clean(s, t):
    s = s.strip()
    s = re.sub(r"^```(?:markdown|md)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    s = re.sub(r"^#\s+.*\n", "", s)  # 去掉一级标题
    if not s.lstrip().startswith("## "):
        s = f"## {t['id']} {t['title']}\n\n" + s.lstrip()
    # 公式 $$ 配对：奇数个则丢弃末尾未闭合块
    if s.count("$$") % 2:
        idx = s.rfind("$$")
        s = s[:idx].rstrip() + "\n"
    return s.strip() + "\n"


def call(prompt, max_tokens=12288, temp=0.55):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temp,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    last = None
    for attempt in range(4):
        try:
            p = prompt if attempt == 0 else prompt + "\n请开始写作。" + "。" * (attempt * 5)
            body["messages"] = [{"role": "user", "content": p}]
            data = json.dumps(body).encode()
            req = urllib.request.Request(
                API, data=data, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=1800) as r:
                d = json.loads(r.read())
            ch = d["choices"][0]
            return ch["message"]["content"], ch.get("finish_reason")
        except Exception as e:
            last = e
            if attempt < 3:
                time.sleep(15 * (attempt + 1))
    raise last


def build_first(t):
    b = t["budget"]
    factor = 0.75 if b <= 16000 else (0.66 if b <= 20000 else 0.55)
    target_cjk = int(b * factor)
    min_cjk = int(b * (factor - 0.13))
    per_seg = max(450, target_cjk // 7)
    need_total = int(target_cjk * 0.9)
    return STYLE.format(
        sid=t["id"], title=t["title"], target=target_cjk, minc=min_cjk,
        formulas=t["formulas"], derivs=t["derivations"], tables=t["tables"], figures=t["figures"],
    ) + f"""

本次任务：写第 {t['id']} 节《{t['title']}》。
所属：第 {t['chapter']} 章《{t['chapter_title']}》· 第 {t['unit']} 编《{t['unit_title']}》。
核心要点（必须覆盖，可展开但不得跑题）：
{t['points']}
AI 关联（必须落到具体模型/论文/算法，不得只写“可用于深度学习”）：
{t['ai']}
来源（只可引用这些书与章；不要编页码、年份、实验数字）：
{t['source']}

篇幅分配：本节目标 {t['target_cjk']} 个汉字（不含公式）。请**一次写完整七段**：
问题 → 对象 → 定理 → 离散化 → 误差界 → 实验映射 → 小结与陷阱。
七段每段不少于 {per_seg} 个汉字，合计不少于 {need_total} 个汉字；不足视为不合格。
不要分轮，不要写“下一轮补写”，不要重复已有小节；写到目标字数附近自然收尾。
直接开始写正文，不要复述任务要求。"""


def build_more(t, text, need):
    heads = re.findall(r"^###\s+(.+)$", text, re.M)
    avoid = "；".join(heads[-8:]) if heads else "（无）"
    return STYLE.format(
        sid=t["id"], title=t["title"], target=t["target_cjk"], minc=t["min_cjk"],
        formulas=t["formulas"], derivs=t["derivations"], tables=t["tables"], figures=t["figures"],
    ) + f"""

本次任务：为第 {t['id']} 节《{t['title']}》补写 2 个深化小节。
已有小标题（不要重复，也不要换词重讲）：
{avoid}

这一轮写 2 个新的 `###` 小节，标题必须是 `### 深入：<具体主题>` 或 `### 补论：<具体主题>`；
不要复用“问题/对象/定理/离散化/误差界/实验映射/小结与陷阱”这些已有标题。
合计约 {need} 个汉字；分别推进到尚未覆盖的内容：常数与阶的完整推导、两个具体模型的最小实验、
三条失效判据与反例。至少含 1 个公式或 1 张表；不要导语，不要总结前文，不要重复已有段落。
直接开始写正文。"""


def gen_one(t, force=False):
    path = os.path.join(OUTDIR, f"{t['id']}.md")
    target_vis = int(t["budget"] * 0.99)
    old = ""
    if os.path.exists(path):
        old = open(path, encoding="utf-8").read()
        if not force and visible(old) >= int(t["budget"] * 0.85):
            return {"id": t["id"], "status": "skip", "cjk": cjk(old), "visible": visible(old)}
    started = time.time()
    try:
        if old and not force:
            txt, fin, rounds = old, "resume", 0
        else:
            txt, fin = call(build_first(t), max_tokens=20480)
            txt = clean(txt, t)
            rounds = 0
        while visible(txt) < target_vis and rounds < 3:
            rounds += 1
            need = max(1200, int((target_vis - visible(txt)) / 2.2))
            frag, fin = call(build_more(t, txt, need), max_tokens=10240)
            frag = clean(frag, t)
            # 去掉重复的节标题
            frag = re.sub(r"^##\s+.*\n+", "", frag)
            txt = merge_duplicate_headings(txt.rstrip() + "\n\n" + frag.strip() + "\n")
        txt = clean(txt, t)
        os.makedirs(OUTDIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(txt)
        rec = {
            "id": t["id"], "status": "ok", "cjk": cjk(txt), "visible": len(re.sub(r"\s", "", txt)),
            "target": t["target_cjk"],
            "formulas": count_formulas(txt), "tables": count_tables(txt),
            "figures": count_figures(txt), "derivations": count_derivations(txt),
            "rounds": rounds, "elapsed": round(time.time() - started, 1), "finish": fin,
        }
    except Exception as e:
        rec = {"id": t["id"], "status": "error", "err": repr(e)[:200], "elapsed": round(time.time() - started, 1)}
    with open(PROGRESS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ids", type=str, default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    tasks = json.load(open(BOOK, encoding="utf-8"))
    if args.ids:
        want = set(x.strip() for x in args.ids.split(","))
        tasks = [t for t in tasks if t["id"] in want]
    if args.limit:
        tasks = tasks[: args.limit]
    if args.dry:
        print(build_first(tasks[0]))
        return
    os.makedirs(OUTDIR, exist_ok=True)
    total = len(tasks)
    done = [0]
    lock = threading.Lock()

    def run(t):
        rec = gen_one(t, args.force)
        with lock:
            done[0] += 1
            line = f"[{done[0]}/{total}] {rec.get('status')} {rec['id']} cjk={rec.get('cjk','-')} " \
                   f"f={rec.get('formulas','-')} t={rec.get('tables','-')} el={rec.get('elapsed','-')}s"
            print(line, flush=True)
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(time.strftime("%H:%M:%S ") + line + "\n")
        return rec

    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(run, tasks))
    print(f"done {total} tasks in {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
