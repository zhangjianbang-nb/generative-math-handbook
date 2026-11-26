# -*- coding: utf-8 -*-
"""把五部结构展开成 500 节生成任务 book/book.json"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage1
import stage2
import stage3
import stage4
import stage5

STAGES = [stage1.STAGE, stage2.STAGE, stage3.STAGE, stage4.STAGE, stage5.STAGE]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "book", "book.json")

tasks = []
for st in STAGES:
    for c in st["chapters"]:
        nu = len(c["units"])
        per_section = c["budget"] // (nu * 5)
        for ui, u in enumerate(c["units"], 1):
            for title, points, ai, source in u["sections"]:
                sid, name = title.split(" ", 1)
                tasks.append({
                    "id": sid,
                    "chapter": c["no"],
                    "chapter_title": c["title"],
                    "stage": st["id"],
                    "stage_title": st["title"],
                    "unit": ui,
                    "unit_title": u["title"],
                    "title": name,
                    "points": points,
                    "ai": ai,
                    "source": source,
                    "budget": per_section,
                    "target_cjk": int(per_section * 0.55),
                    "min_cjk": int(per_section * 0.45),
                    "formulas": max(8, per_section // 800),
                    "tables": max(1, per_section // 20000),
                    "figures": max(1, per_section // 8000),
                    "derivations": max(2, per_section // 5000),
                })

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8") as f:
    json.dump(tasks, f, ensure_ascii=False, indent=1)
print(f"wrote {OUT}: {len(tasks)} tasks")
print("first:", tasks[0]["id"], tasks[0]["budget"], "last:", tasks[-1]["id"], tasks[-1]["budget"])
