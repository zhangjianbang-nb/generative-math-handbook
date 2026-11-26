# -*- coding: utf-8 -*-
"""把 book/sec/*.md 装配成 book/全书.md（含总目/章取材/统计），并输出 stats.json"""
import io
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

STAGES = [stage1.STAGE, stage2.STAGE, stage3.STAGE, stage4.STAGE, stage5.STAGE]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC = os.path.join(ROOT, "book", "sec")
OUT = os.path.join(ROOT, "book", "全书.md")
STATS = os.path.join(ROOT, "book", "stats.json")
STAGE_CN = {"I": "第一部", "II": "第二部", "III": "第三部", "IV": "第四部", "V": "第五部"}
KEYWORDS = ["扩散", "流匹配", "VAE", "GAN", "自回归", "SSM", "Transformer", "注意力", "LoRA", "得分匹配"]


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def visible(s):
    return len(re.sub(r"\s", "", s))


def counts(s):
    return {
        "cjk": cjk(s),
        "visible": visible(s),
        "display": len(re.findall(r"\$\$[\s\S]*?\$\$", s)),
        "inline": len(re.findall(r"(?<!\$)\$[^$\n]+\$(?!\$)", s)),
        "tables": len(re.findall(r"^\s*\|[\s\-:|]+\|\s*$", s, re.M)),
        "figures": len(re.findall(r"!\[", s)),
        "derivations": len(re.findall(r"^#{2,5}.*(推导|证明)", s, re.M)) + len(re.findall(r"\*\*[^*\n]*(推导|证明)[^*\n]*\*\*", s)) + len(re.findall(r"(?m)^[^\n]*第[一]步[^\n]*$", s)),
        "ai": len([p for p in s.split("\n\n") if any(k in p for k in KEYWORDS)]),
    }


def shift_headings(s):
    out = []
    for line in s.splitlines():
        if line.startswith("### "):
            out.append("#### " + line[4:])
        elif line.startswith("## "):
            out.append("### " + line[3:])
        else:
            out.append(line)
    return "\n".join(out)


def main():
    L = []
    a = L.append
    a("# 生成式数学手册")
    a("")
    a("## 生成模型数学基础路线")
    a("")
    a("> 五部 25 章 100 编 500 节 ｜ 目标 8,000,000 字符 ｜ 2026-11-25 起生成")
    a("")
    a("## 阅读说明")
    a("")
    a("每一节按七段式写作：**问题 → 对象 → 定理 → 离散化 → 误差界 → 实验映射 → 小结与陷阱**。")
    a("定理写全条件，并给出至少一个“去掉条件会怎样”的反例；公式用 LaTeX，图以 `fig://` 图注给出；")
    a("“实验映射”落到具体模型与最小可复现实验，不写“可用于深度学习”一类空话。")
    a("")
    a("## 总目")
    a("")
    for st in STAGES:
        a(f"- **{STAGE_CN[st['id']]}　{st['title']}**")
        for c in st["chapters"]:
            a(f"  - 第 {c['no']} 章　{c['title']}")
            for ui, u in enumerate(c["units"], 1):
                a(f"    - 第 {ui} 编　{u['title']}")
                for title, points, ai, source in u["sections"]:
                    sid, name = title.split(" ", 1)
                    a(f"      - {sid}　{name}")
    a("")
    total = {k: 0 for k in ("cjk", "visible", "display", "inline", "tables", "figures", "derivations", "ai")}
    per_chapter = {}
    missing = []
    for st in STAGES:
        a(f"# {STAGE_CN[st['id']]}　{st['title']}")
        a("")
        a(f"*{st['subtitle']}*")
        a("")
        a(st["intro"])
        a("")
        for c in st["chapters"]:
            a(f"# 第 {c['no']} 章　{c['title']}")
            a("")
            a(f"> {c['ai_summary']}")
            a("")
            src = "；".join(f"{b}（{ch}）" for b, ch in c["sources"])
            a(f"> **本章取材**：{src}")
            a("")
            ch = {k: 0 for k in total}
            ch["missing"] = 0
            for ui, u in enumerate(c["units"], 1):
                a(f"## 第 {ui} 编　{u['title']}")
                a("")
                for title, points, ai, source in u["sections"]:
                    sid = title.split(" ", 1)[0]
                    path = os.path.join(SEC, f"{sid}.md")
                    if not os.path.exists(path):
                        missing.append(sid)
                        ch["missing"] += 1
                        a(f"### {sid} {title.split(' ', 1)[1]}")
                        a("")
                        a("> （本节尚未生成）")
                        a("")
                        continue
                    s = io.open(path, encoding="utf-8").read()
                    c2 = counts(s)
                    for k in total:
                        ch[k] += c2[k]
                    a(shift_headings(s).strip())
                    a("")
            per_chapter[str(c["no"])] = ch
            for k in total:
                total[k] += ch[k]
    a("")
    a("---")
    a("")
    a("## 全书统计")
    a("")
    a("| 指标 | 数值 |")
    a("|---|---:|")
    for k, v in total.items():
        a(f"| {k} | {v:,} |")
    a(f"| 缺失节 | {len(missing)} |")
    a("")
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with io.open(STATS, "w", encoding="utf-8") as f:
        json.dump({"total": total, "missing": missing, "per_chapter": per_chapter}, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {total}")
    print(f"missing {len(missing)}: {missing[:10]}")


if __name__ == "__main__":
    main()
