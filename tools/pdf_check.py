#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 验收：页数、空白页、文本层字符数、首末页内容。"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "book", "pdf", "全书.pdf")
TXT = os.path.join(ROOT, "book", "pdf", "全书.txt")


def main():
    info = subprocess.run(["pdfinfo", PDF], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    size_mb = os.path.getsize(PDF) / 1048576
    subprocess.run(["pdftotext", PDF, TXT], check=True)
    raw = open(TXT, encoding="utf-8").read()
    chunks = raw.split("\f")
    if chunks and not chunks[-1].strip():
        chunks = chunks[:-1]
    empties = [i + 1 for i, c in enumerate(chunks) if len(re.sub(r"\s", "", c)) < 40]
    chars = len(re.sub(r"\s", "", raw))
    checks = {
        "pages": pages,
        "text_pages": len(chunks),
        "empty_pages": len(empties),
        "empty_first": empties[:20],
        "chars": chars,
        "size_mb": round(size_mb, 1),
        "has_title": "生成式数学手册" in raw,
        "has_ch1": "线性代数" in raw,
        "has_ch25": "随机微分方程" in raw,
        "first_page_head": re.sub(r"\s+", " ", chunks[0])[:80],
        "last_page_tail": re.sub(r"\s+", " ", chunks[-1])[-80:],
    }
    print(json.dumps(checks, ensure_ascii=False, indent=1))
    ok = pages == len(chunks) and len(empties) == 0 and checks["has_title"] and checks["has_ch25"]
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
