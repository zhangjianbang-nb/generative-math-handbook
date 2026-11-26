#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""结构断言：每节必须含七段式标题（问题/对象/定理/离散化/误差界/实验映射/小结与陷阱）。"""
import glob
import os
import re

SEC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "book", "sec")
NEED = ["问题", "对象", "定理", "离散化", "误差界", "实验映射", "小结与陷阱"]
bad = []
for f in sorted(glob.glob(os.path.join(SEC, "*.md"))):
    s = open(f, encoding="utf-8").read()
    heads = re.findall(r"^###\s+(.+)$", s, re.M)
    miss = [k for k in NEED if not any(k in h for h in heads)]
    if miss:
        bad.append((os.path.basename(f)[:-3], miss))
print(f"sections {len(glob.glob(os.path.join(SEC, '*.md')))}  incomplete {len(bad)}")
for sid, miss in bad[:30]:
    print(sid, "缺", "/".join(miss))
