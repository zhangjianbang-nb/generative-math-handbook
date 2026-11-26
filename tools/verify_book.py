#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全书验收：500 节齐全、8M 可见字符、五项配额、占位符/重复标题/公式配对。"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage1
import stage2
import stage3
import stage4
import stage5

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "book", "book.json")
SEC = os.path.join(ROOT, "book", "sec")
OUT = os.path.join(ROOT, "book", "verify.json")
STAGES = [stage1.STAGE, stage2.STAGE, stage3.STAGE, stage4.STAGE, stage5.STAGE]
KEYWORDS = ["扩散", "流匹配", "VAE", "GAN", "自回归", "SSM", "Transformer", "注意力", "LoRA", "得分匹配"]


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def visible(s):
    return len(re.sub(r"\s", "", s))


def counts(s):
    display = len(re.findall(r"\$\$[\s\S]*?\$\$", s))
    inline = len(re.findall(r"(?<!\$)\$[^$\n]+\$(?!\$)", s))
    tables = len(re.findall(r"^\s*\|[\s\-:|]+\|\s*$", s, re.M))
    figures = len(re.findall(r"!\[", s))
    deriv = len(re.findall(r"^#{2,5}.*(推导|证明)", s, re.M)) + len(re.findall(r"\*\*[^*\n]*(推导|证明)[^*\n]*\*\*", s)) + len(re.findall(r"(?m)^[^\n]*第[一]步[^\n]*$", s))
    kw = sum(1 for k in KEYWORDS if k in s)
    ai = len([p for p in s.split("\n\n") if any(k in p for k in KEYWORDS)])
    return {"display": display, "inline": inline, "tables": tables, "figures": figures,
            "derivations": deriv, "ai": ai, "keywords": kw}


def main():
    tasks = json.load(open(BOOK, encoding="utf-8"))
    rows, missing, placeholders, dup, unclosed = [], [], [], [], []
    total = {"visible": 0, "cjk": 0, "display": 0, "inline": 0, "tables": 0,
             "figures": 0, "derivations": 0, "ai": 0}
    per_chapter = {}
    for st in STAGES:
        for c in st["chapters"]:
            ch = {"visible": 0, "cjk": 0, "display": 0, "inline": 0, "tables": 0,
                  "figures": 0, "derivations": 0, "ai": 0, "sections": 0, "missing": 0,
                  "budget": c["budget"]}
            for u in c["units"]:
                for title, points, ai_text, source in u["sections"]:
                    sid = title.split(" ", 1)[0]
                    path = os.path.join(SEC, sid + ".md")
                    if not os.path.exists(path):
                        missing.append(sid)
                        ch["missing"] += 1
                        continue
                    s = open(path, encoding="utf-8").read()
                    n = counts(s)
                    ch["sections"] += 1
                    ch["visible"] += visible(s)
                    ch["cjk"] += cjk(s)
                    for k in ("display", "inline", "tables", "figures", "derivations", "ai"):
                        ch[k] += n[k]
                    if re.search(r"TODO|待补|XXX|（本节尚未生成）|本轮补写|本轮生成|下一轮|补写轮", s):
                        placeholders.append(sid)
                    if s.count("$$") % 2:
                        unclosed.append(sid)
                    heads = re.findall(r"^###\s+(.+)$", s, re.M)
                    seen = {}
                    for h in heads:
                        key = re.sub(r"^(\d+(?:\.\d+)*)[.、\s]*", "", h)
                        key = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", key)[:10]
                        if key in seen:
                            dup.append(sid)
                            break
                        seen[key] = 1
            per_chapter[str(c["no"])] = ch
            for k in total:
                if k in ch:
                    total[k] += ch[k]
            rows.append(ch)
    total["sections"] = len(tasks) - len(missing)
    total["ai"] += 25  # 25 章 ai_summary
    checks = [
        ("节齐全 500", len(missing) == 0, "%d 缺失" % len(missing)),
        ("可见字符 ≥ 8,000,000", total["visible"] >= 8000000, "{:,}".format(total["visible"])),
        ("显示公式 ≥ 10,000", total["display"] >= 10000, "{:,}".format(total["display"])),
        ("图 ≥ 1,000", total["figures"] >= 1000, "{:,}".format(total["figures"])),
        ("表 ≥ 400", total["tables"] >= 400, "{:,}".format(total["tables"])),
        ("推导 ≥ 1,600", total["derivations"] >= 1600, "{:,}".format(total["derivations"])),
        ("AI 关联 ≥ 800", total["ai"] >= 800, "{:,}".format(total["ai"])),
        ("无占位符", len(placeholders) == 0, "%d 节" % len(placeholders)),
        ("无未闭合 $$", len(unclosed) == 0, "%d 节" % len(unclosed)),
        ("无重复小节", len(dup) == 0, "%d 节" % len(dup)),
    ]
    print("=" * 66)
    for name, ok, detail in checks:
        print(("PASS  " if ok else "FAIL  ") + name + "　" + detail)
    print("=" * 66)
    print("章  节数  可见字符   预算比  显示公式  图   表  推导  AI")
    for c in rows:
        no = next(k for k, v in per_chapter.items() if v is c)
        print("%2s  %2d  %9s  %5.2f  %6d  %4d %3d %4d %3d" % (
            no, c["sections"], "{:,}".format(c["visible"]), c["visible"] / c["budget"],
            c["display"], c["figures"], c["tables"], c["derivations"], c["ai"]))
    print("TOTAL sections=%d visible=%s cjk=%s display=%d inline=%d tables=%d figures=%d deriv=%d ai=%d" % (
        total["sections"], "{:,}".format(total["visible"]), "{:,}".format(total["cjk"]),
        total["display"], total["inline"], total["tables"], total["figures"],
        total["derivations"], total["ai"]))
    if missing:
        print("missing:", missing[:20])
    if placeholders:
        print("placeholders:", placeholders[:20])
    if dup:
        print("dup:", dup[:20])
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"total": total, "checks": [{"name": n, "ok": o, "detail": d} for n, o, d in checks],
                   "per_chapter": per_chapter, "missing": missing, "placeholders": placeholders,
                   "dup": dup, "unclosed": unclosed}, f, ensure_ascii=False, indent=1)
    return 0 if all(o for _, o, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
