# -*- coding: utf-8 -*-
"""总目录交付物的可编程验收断言。"""
import io
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
DOCS = os.path.join(ROOT, "docs")

TOPICS = [
    "线性代数", "欧几里得空间", "度量空间", "拓扑空间",
    "微分流形", "黎曼几何", "双曲几何", "球面几何", "李群与李代数",
    "泛函分析", "Banach 空间", "Hilbert 空间", "Sobolev 空间", "算子理论",
    "测度论", "概率空间", "Wasserstein 空间", "最优传输", "信息几何",
    "常微分方程", "偏微分方程", "流形上的动力系统", "哈密顿动力学", "连续性方程", "随机微分方程",
]

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS" if cond else "FAIL"), name, detail)


def main():
    chapters = [c for st in STAGES for c in st["chapters"]]
    units = [u for c in chapters for u in c["units"]]
    sections = [s for u in units for s in u["sections"]]

    # 1 结构计数
    check("章数 = 25", len(chapters) == 25, f"实际 {len(chapters)}")
    check("编数 = 100", len(units) == 100, f"实际 {len(units)}")
    check("节数 = 500", len(sections) == 500, f"实际 {len(sections)}")
    check("每章 4 编", all(len(c["units"]) == 4 for c in chapters),
          str([c["no"] for c in chapters if len(c["units"]) != 4]))
    check("每编 5 节", all(len(u["sections"]) == 5 for u in units),
          str([u["title"] for u in units if len(u["sections"]) != 5]))

    # 2 预算
    total = sum(c["budget"] for c in chapters)
    check("预算合计 = 8,000,000", total == 8000000, f"实际 {total:,}")
    bad = []
    for c in chapters:
        ub = c["budget"] // len(c["units"])
        sb = ub // 5
        if ub * len(c["units"]) != c["budget"] or sb * 5 != ub:
            bad.append(c["no"])
    check("每章预算可整除到编/节（整数千字符）", not bad, str(bad))
    sb_min = min(c["budget"] // 20 for c in chapters)
    sb_max = max(c["budget"] // 20 for c in chapters)
    check("每节预算 ∈ [11k, 25k]", 11000 <= sb_min and sb_max <= 25000, f"{sb_min}–{sb_max}")

    # 3 主题覆盖
    titles = [c["title"] for c in chapters]
    check("25 主题按顺序一一对应", titles == TOPICS,
          f"缺失 {set(TOPICS) - set(titles)}；多余 {set(titles) - set(TOPICS)}")

    # 4 节编号连续且唯一
    nums = []
    for c in chapters:
        for ui, u in enumerate(c["units"], 1):
            for si, (title, points, ai, source) in enumerate(u["sections"], 1):
                nums.append(title.split(" ", 1)[0])
    expected = [f"{c['no']}.{i}" for c in chapters for i in range(1, 21)]
    check("节编号 = 章号.1–20 连续", nums == expected,
          f"首个不符 {next(((a, b) for a, b in zip(nums, expected) if a != b), None)}")
    check("节编号无重复", len(set(nums)) == len(nums))

    # 5 每节四要素非空
    empty = []
    for c in chapters:
        for u in c["units"]:
            for title, points, ai, source in u["sections"]:
                if not (title.strip() and points.strip() and ai.strip() and source.strip()):
                    empty.append(title)
    check("每节 标题/要点/AI/来源 四要素非空", not empty, str(empty[:5]))

    # 6 每章来源与 AI 摘要
    check("每章 ≥2 个来源", all(len(c["sources"]) >= 2 for c in chapters),
          str([c["no"] for c in chapters if len(c["sources"]) < 2]))
    check("每章 AI 摘要 ≥40 字", all(len(c["ai_summary"]) >= 40 for c in chapters),
          str([c["no"] for c in chapters if len(c["ai_summary"]) < 40]))

    # 7 配额
    q = {"formula": 800, "figure": 8000, "table": 20000, "derivation": 5000, "ai": 10000}
    expect = {"formula": 10000, "figure": 1000, "table": 400, "derivation": 1600, "ai": 800}
    for key, div in q.items():
        got = total // div
        check(f"配额 {key} = {expect[key]:,}", got == expect[key], f"实际 {got:,}")

    # 8 交付文档断言
    master_path = os.path.join(DOCS, "生成式数学手册-总目录.md")
    mapping_path = os.path.join(DOCS, "书→章合并映射.md")
    budget_path = os.path.join(DOCS, "800万字符预算与配额.md")
    for p in (master_path, mapping_path, budget_path):
        check(f"文件存在 {os.path.basename(p)}", os.path.exists(p), p)
    master = io.open(master_path, encoding="utf-8").read()
    mapping = io.open(mapping_path, encoding="utf-8").read()
    budget = io.open(budget_path, encoding="utf-8").read()

    check("总目录含 25 个章标题", len(re.findall(r"^#### 第 \d+ 章", master, re.M)) == 25,
          str(len(re.findall(r"^#### 第 \d+ 章", master, re.M))))
    check("总目录含 100 个编标题", len(re.findall(r"^##### 第 \d+ 编", master, re.M)) == 100,
          str(len(re.findall(r"^##### 第 \d+ 编", master, re.M))))
    check("总目录含 500 行节表格", len(re.findall(r"^\| \d+\.\d+ \|", master, re.M)) == 500,
          str(len(re.findall(r"^\| \d+\.\d+ \|", master, re.M))))
    check("总目录每个节标题都出现", all(t.split(" ", 1)[1] in master for t in
          [s[0] for s in sections]), "逐节字符串匹配")
    check("映射文档含 25 章", len(re.findall(r"^### 第 \d+ 章", mapping, re.M)) == 25,
          str(len(re.findall(r"^### 第 \d+ 章", mapping, re.M))))
    check("预算文档含 25 章行", len(re.findall(r"^\| \d+ \|", budget, re.M)) >= 25,
          str(len(re.findall(r"^\| \d+ \|", budget, re.M))))
    # 占位符只查目录正文与映射文档；附录 D 的“验收断言表”本身会写出 TODO/待补/XXX 作为断言名
    body = master.split("## 附录 D", 1)[0]
    check("目录正文与映射文档无占位符", not any(x in body + mapping for x in ("TODO", "待补", "XXX", "占位")),
          "TODO/待补/XXX/占位 零出现（附录 D 断言表除外）")
    check("总目录 > 80k 字符", len(master) > 80000, f"{len(master):,}")

    # 9 部预算勾稽
    stage_sum = [sum(c["budget"] for c in st["chapters"]) for st in STAGES]
    check("五部预算 = 1300/1600/1600/1560/1940k",
          stage_sum == [1300000, 1600000, 1600000, 1560000, 1940000], str(stage_sum))

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n=== {passed}/{len(results)} PASS ===")
    if passed != len(results):
        for name, ok, detail in results:
            if not ok:
                print("FAILED:", name, detail)
        sys.exit(1)


if __name__ == "__main__":
    main()
