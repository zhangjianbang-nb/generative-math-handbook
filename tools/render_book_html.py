#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 book/sec/*.md 渲染成按部拆分的离线 HTML 阅读器（本地 KaTeX，无 CDN）。"""
import html
import json
import os
import re
import shutil
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
SITE = os.path.join(ROOT, "site", "book")
KATEX_SRC = "/home/whu/workspace/ai_workspace/mopd-teaching-20261113/site/vendor/katex"
STAGES = [stage1.STAGE, stage2.STAGE, stage3.STAGE, stage4.STAGE, stage5.STAGE]
STAGE_CN = {"I": "第一部", "II": "第二部", "III": "第三部", "IV": "第四部", "V": "第五部"}
COLORS = {"I": "#8a5a2b", "II": "#3d6b57", "III": "#35567d", "IV": "#7a4a63", "V": "#a04a2f"}
ROMAN = ["I", "II", "III", "IV", "V"]


def esc(s):
    return html.escape(s, quote=False)


def cjk(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def visible(s):
    return len(re.sub(r"\s", "", s))


# ---------------------------------------------------------------- Markdown

def inline(s):
    toks = []

    def stash(m):
        toks.append(m.group(0))
        return "\x00%d\x00" % (len(toks) - 1)

    s = re.sub(r"\$\$[\s\S]*?\$\$", stash, s)
    s = re.sub(r"\\\[[\s\S]*?\\\]", stash, s)
    s = re.sub(r"\\\([\s\S]*?\\\)", stash, s)
    s = re.sub(r"(?<!\$)\$[^$\n]+\$(?!\$)", stash, s)
    s = esc(s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: '<a href="%s">%s</a>' % (esc(m.group(2)), m.group(1)), s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", s)

    def unstash(m):
        raw = toks[int(m.group(1))]
        if raw.startswith("$$"):
            return '<span class="math block">$$%s$$</span>' % esc(raw[2:-2])
        if raw.startswith("\\["):
            return '<span class="math block">$$%s$$</span>' % esc(raw[2:-2])
        if raw.startswith("\\("):
            return '<span class="math">$%s$</span>' % esc(raw[2:-2])
        return '<span class="math">$%s$</span>' % esc(raw[1:-1])

    return re.sub("\x00(\\d+)\x00", unstash, s)


def table_html(rows):
    def cells(line):
        return [c.strip() for c in line.strip().strip("|").split("|")]

    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    h = ['<div class="table-wrap"><table><thead><tr>']
    h += ["<th>%s</th>" % inline(c) for c in head]
    h.append("</tr></thead><tbody>")
    for r in body:
        h.append("<tr>")
        for j, c in enumerate(r):
            label = head[j] if j < len(head) else ""
            h.append('<td data-label="%s">%s</td>' % (esc(re.sub(r"[*`$]", "", label)), inline(c)))
        h.append("</tr>")
    h.append("</tbody></table></div>")
    return "".join(h)


def fig_svg(desc, num):
    seed = sum(ord(c) for c in (num + desc)) % 997

    def jit(n=6):
        return (seed * 13 + len(desc) * 7) % (2 * n + 1) - n

    rules = [
        ("流形|曲面|切空间|拓扑|同胚|纤维|丛", "manifold"),
        ("分布|密度|概率|测度|直方图|高斯|采样", "dist"),
        ("向量场|轨迹|流|动力|相图|ODE|SDE|哈密顿", "flow"),
        ("网络|层|神经|注意|架构|编码器|解码器|残差", "net"),
        ("矩阵|线性|基|秩|特征|空间|投影", "matrix"),
        ("传输|Wasserstein|耦合|搬运|OT", "ot"),
        ("信息几何|统计流形|Fisher|KL|散度", "ig"),
        ("群|对称|旋转|李|作用", "group"),
    ]
    tpl = "axes"
    for pat, t in rules:
        if re.search(pat, desc):
            tpl = t
            break
    W, H = 640, 240
    g = ['<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="%s">' % esc(desc)]
    g.append('<rect width="640" height="240" fill="#fbf7ee"/>')
    for x in range(40, W, 40):
        g.append('<line x1="%d" y1="0" x2="%d" y2="%d" stroke="#e9e0cd" stroke-width="0.6"/>' % (x, x, H))
    for y in range(20, H, 20):
        g.append('<line x1="0" y1="%d" x2="%d" y2="%d" stroke="#e9e0cd" stroke-width="0.6"/>' % (y, W, y))
    ink, accent, soft = "#3a342c", "#a04a2f", "#8fa6b8"

    def txt(x, y, s, size=13, fill=None, anchor="middle"):
        return '<text x="%d" y="%d" font-family="Georgia,serif" font-size="%d" fill="%s" text-anchor="%s">%s</text>' % (
            x, y, size, fill or ink, anchor, esc(s))

    if tpl == "manifold":
        g.append('<path d="M70 170 C140 90, 240 70, 330 110 S480 180, 570 120" fill="none" stroke="%s" stroke-width="2.2"/>' % ink)
        g.append('<path d="M70 170 C140 90, 240 70, 330 110 S480 180, 570 120 L570 150 C480 210, 330 160, 240 150 C150 140, 110 190, 70 200 Z" fill="%s" opacity="0.10"/>' % accent)
        g.append('<path d="M250 118 L360 96 L410 132 L300 154 Z" fill="%s" opacity="0.18" stroke="%s" stroke-width="1.2"/>' % (soft, soft))
        g.append('<line x1="330" y1="110" x2="330" y2="55" stroke="%s" stroke-width="1.6" marker-end="url(#arr)"/>' % accent)
        g.append(txt(330, 45, "T_pM"))
        g.append('<circle cx="330" cy="110" r="4" fill="%s"/>' % accent)
        g.append(txt(318, 128, "p", 12))
        g.append(txt(110, 215, "M", 13, ink))
    elif tpl == "dist":
        g.append('<line x1="60" y1="200" x2="590" y2="200" stroke="%s" stroke-width="1.2"/>' % ink)
        g.append('<line x1="60" y1="200" x2="60" y2="40" stroke="%s" stroke-width="1.2"/>' % ink)
        g.append('<path d="M70 200 C180 200, 200 60, 320 60 C440 60, 460 200, 570 200" fill="none" stroke="%s" stroke-width="2.4"/>' % accent)
        g.append('<path d="M70 200 C180 200, 200 60, 320 60 C440 60, 460 200, 570 200 L570 200 L70 200 Z" fill="%s" opacity="0.10"/>' % accent)
        for k in range(9):
            x = 95 + k * 52 + jit(4)
            hh = 10 + int(70 * (1 - abs(k - 4) / 5.0)) + jit(5)
            g.append('<rect x="%d" y="%d" width="26" height="%d" fill="%s" opacity="0.45"/>' % (x, 200 - hh, hh, soft))
        g.append(txt(320, 225, "x", 12))
        g.append(txt(48, 46, "p(x)", 12, anchor="start"))
    elif tpl == "flow":
        for k in range(5):
            for m in range(4):
                x, y = 80 + k * 105, 55 + m * 40
                g.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1" opacity="0.45" marker-end="url(#arrs)"/>' % (x, y, x + 26 + jit(4), y - 8 + jit(3), soft))
        g.append('<path d="M90 190 C190 150, 250 80, 340 95 S500 160, 570 70" fill="none" stroke="%s" stroke-width="2.4"/>' % accent)
        g.append('<circle cx="90" cy="190" r="4.5" fill="%s"/>' % accent)
        g.append('<circle cx="570" cy="70" r="4.5" fill="%s"/>' % accent)
        g.append(txt(78, 208, "x_0", 12))
        g.append(txt(584, 62, "x_T", 12))
    elif tpl == "net":
        layers = [(150, 4), (320, 5), (490, 3)]
        for li, (x, n) in enumerate(layers):
            ys = [60 + k * (120 / max(1, n - 1)) for k in range(n)]
            for y in ys:
                g.append('<circle cx="%d" cy="%.0f" r="10" fill="#fbf7ee" stroke="%s" stroke-width="1.8"/>' % (x, y, ink))
            if li:
                px, pn = layers[li - 1]
                pys = [60 + k * (120 / max(1, pn - 1)) for k in range(pn)]
                for y1 in pys:
                    for y2 in ys:
                        g.append('<line x1="%d" y1="%.0f" x2="%d" y2="%.0f" stroke="%s" stroke-width="0.5" opacity="0.5"/>' % (px + 10, y1, x - 10, y2, soft))
        g.append(txt(150, 205, "输入", 12))
        g.append(txt(320, 205, "隐层", 12))
        g.append(txt(490, 205, "读出", 12))
    elif tpl == "matrix":
        x0, y0, cw, ch = 200, 50, 44, 30
        for r in range(5):
            for c in range(6):
                fill = accent if (r + c + seed) % 7 == 0 else "none"
                g.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" opacity="0.35" stroke="%s" stroke-width="1"/>' % (x0 + c * cw, y0 + r * ch, cw, ch, fill, ink))
        g.append('<path d="M188 44 L188 208 M188 44 L200 44 M188 208 L200 208" stroke="%s" stroke-width="2" fill="none"/>' % ink)
        g.append('<path d="M476 44 L476 208 M464 44 L476 44 M464 208 L476 208" stroke="%s" stroke-width="2" fill="none"/>' % ink)
        g.append(txt(320, 225, "A ∈ R^{m×n}", 13))
        g.append(txt(120, 130, "rank r", 13, accent))
    elif tpl == "ot":
        g.append('<ellipse cx="170" cy="120" rx="62" ry="42" fill="%s" opacity="0.16" stroke="%s" stroke-width="1.4"/>' % (soft, soft))
        g.append('<ellipse cx="470" cy="120" rx="72" ry="36" fill="%s" opacity="0.16" stroke="%s" stroke-width="1.4"/>' % (accent, accent))
        for k in range(7):
            y1 = 92 + k * 9 + jit(3)
            y2 = 100 + k * 7 + jit(3)
            g.append('<line x1="230" y1="%d" x2="398" y2="%d" stroke="%s" stroke-width="1.2" opacity="0.55" marker-end="url(#arr)"/>' % (y1, y2, ink))
        g.append(txt(170, 180, "μ", 14))
        g.append(txt(470, 180, "ν", 14))
        g.append(txt(320, 218, "T: μ → ν", 13, accent))
    elif tpl == "ig":
        g.append('<path d="M90 190 C220 40, 420 40, 560 190" fill="none" stroke="%s" stroke-width="2.2"/>' % ink)
        g.append('<path d="M150 150 C260 90, 400 90, 500 150" fill="none" stroke="%s" stroke-width="1.6" stroke-dasharray="5 4"/>' % accent)
        for x, y, lab in [(180, 132, "θ₁"), (320, 92, "θ₂"), (470, 138, "θ₃")]:
            g.append('<circle cx="%d" cy="%d" r="4.5" fill="%s"/>' % (x, y, accent))
            g.append(txt(x + 4, y - 12, lab, 12))
        g.append(txt(320, 218, "统计流形 M", 13))
    elif tpl == "group":
        g.append('<circle cx="320" cy="120" r="72" fill="none" stroke="%s" stroke-width="1.6"/>' % ink)
        g.append('<path d="M320 120 L392 120 A72 72 0 0 0 356 58 Z" fill="%s" opacity="0.18"/>' % accent)
        g.append('<path d="M320 120 m 0 -88 a 88 88 0 1 1 -0.1 0" fill="none" stroke="%s" stroke-width="1.4" stroke-dasharray="6 5" marker-end="url(#arr)"/>' % accent)
        g.append('<circle cx="320" cy="120" r="4" fill="%s"/>' % ink)
        g.append(txt(320, 218, "g · x", 13))
    else:
        g.append('<line x1="70" y1="190" x2="580" y2="190" stroke="%s" stroke-width="1.2"/>' % ink)
        g.append('<line x1="70" y1="190" x2="70" y2="40" stroke="%s" stroke-width="1.2"/>' % ink)
        g.append('<path d="M80 150 C160 60, 240 200, 330 110 S480 60, 570 140" fill="none" stroke="%s" stroke-width="2.2"/>' % accent)
        g.append(txt(320, 225, "schematic", 12))
    g.append('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="%s"/></marker>' % ink)
    g.append('<marker id="arrs" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="%s"/></marker></defs>' % soft)
    g.append("</svg>")
    return "".join(g)


def figure_html(alt, cap):
    m = re.match(r"图\s*([\d.]+)[-－](\d+)\s*[：:]\s*(.*)", alt)
    if m:
        num = m.group(1) + "-" + m.group(2)
        desc = m.group(3)
    else:
        num = ""
        desc = alt
    caphtml = inline(" ".join(cap)) if cap else ""
    return ('<figure class="fig" id="fig-%s">%s<figcaption><span class="fignum">图 %s</span>%s'
            '<div class="figcap">%s</div></figcaption></figure>') % (
        esc(num), fig_svg(desc, num), esc(num), inline(desc), caphtml)


def md_to_html(md, sid):
    lines = md.splitlines()
    out = []
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].startswith("## "):
        i += 1
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % esc("\n".join(buf)))
            continue
        if line.startswith("$$"):
            buf = [line]
            if line.count("$$") < 2:
                i += 1
                while i < len(lines):
                    buf.append(lines[i])
                    if "$$" in lines[i]:
                        i += 1
                        break
                    i += 1
            else:
                i += 1
            out.append('<div class="math block">%s</div>' % esc("\n".join(buf)))
            continue
        m = re.match(r"^(#{2,5})\s+(.+)$", line)
        if m:
            lvl = len(m.group(1)) + 2
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2)), lvl))
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            if len(rows) >= 2:
                out.append(table_html(rows))
            continue
        if line.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % inline(" ".join(buf)))
            continue
        if re.match(r"^\s*[-*+]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*+]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*+]\s+", "", lines[i]))
                i += 1
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(x) for x in items))
            continue
        if re.match(r"^\s*\d+[.)]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+[.)]\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+[.)]\s+", "", lines[i]))
                i += 1
            out.append("<ol>%s</ol>" % "".join("<li>%s</li>" % inline(x) for x in items))
            continue
        if line.startswith("!["):
            m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", line)
            alt = m.group(1) if m else ""
            i += 1
            cap = []
            while i < len(lines) and lines[i].strip() and not re.match(
                    r"^(#{2,5}\s|!\[|\||>|\$\$|```|---+$|\s*[-*+]\s|\s*\d+[.)]\s)", lines[i]):
                cap.append(lines[i].strip())
                i += 1
            out.append(figure_html(alt, cap))
            continue
        if re.match(r"^---+$", line):
            out.append("<hr>")
            i += 1
            continue
        buf = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{2,5}\s|!\[|\||>|\$\$|```|---+$|\s*[-*+]\s|\s*\d+[.)]\s)", lines[i]):
            buf.append(lines[i])
            i += 1
        txt = buf[0]
        for x in buf[1:]:
            if re.search(r"[\u4e00-\u9fff]$", txt) and re.match(r"^[\u4e00-\u9fff]", x):
                txt += x
            else:
                txt += " " + x
        out.append("<p>%s</p>" % inline(txt))
    return "\n".join(out)


# ---------------------------------------------------------------- data

def load():
    tasks = json.load(open(BOOK, encoding="utf-8"))
    by_stage = {}
    for st in STAGES:
        by_stage[st["id"]] = {"stage": st, "chapters": []}
        for c in st["chapters"]:
            ch = {"no": c["no"], "title": c["title"], "en": c["en"], "budget": c["budget"],
                  "ai_summary": c["ai_summary"], "units": []}
            for ui, u in enumerate(c["units"], 1):
                unit = {"no": ui, "title": u["title"], "sections": []}
                for title, points, ai, source in u["sections"]:
                    sid = title.split(" ", 1)[0]
                    path = os.path.join(SEC, sid + ".md")
                    body = ""
                    if os.path.exists(path):
                        body = open(path, encoding="utf-8").read()
                    unit["sections"].append({
                        "id": sid, "title": title.split(" ", 1)[1],
                        "html": md_to_html(body, sid) if body else "",
                        "cjk": cjk(body), "visible": visible(body),
                        "done": bool(body),
                    })
                ch["units"].append(unit)
            by_stage[st["id"]]["chapters"].append(ch)
    return tasks, by_stage


def search_index(by_stage):
    out = []
    for r in ROMAN:
        for c in by_stage[r]["chapters"]:
            for u in c["units"]:
                for s in u["sections"]:
                    if not s["done"]:
                        continue
                    text = re.sub(r"<[^>]+>", "", s["html"])
                    text = re.sub(r"\s+", " ", text)[:180]
                    out.append({"id": s["id"], "ch": c["no"], "unit": u["no"], "title": s["title"],
                                "page": "ch-%d.html" % c["no"], "text": text})
    return out


# ---------------------------------------------------------------- html

CSS = r"""
:root{--paper:#f7f3ea;--paper2:#efe8d9;--ink:#2b2620;--muted:#6f665a;--line:#d9cfbc;
--side:#211d18;--side2:#2b261f;--cream:#efe6d4;--accent:#a04a2f;--accent2:#3d6b57}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:"Noto Serif CJK SC","Source Han Serif SC","Songti SC",Georgia,serif;
font-size:16.5px;line-height:1.95;text-rendering:optimizeLegibility}
#progress{position:fixed;top:0;left:0;height:3px;width:0;background:var(--accent);z-index:60}
.topbar{position:sticky;top:0;z-index:50;display:flex;align-items:center;gap:14px;
padding:10px 18px;background:rgba(247,243,234,.94);border-bottom:1px solid var(--line);
backdrop-filter:blur(6px)}
.brand{font-weight:700;font-size:17px;color:var(--ink);text-decoration:none;letter-spacing:.04em;white-space:nowrap}
.topbar .meta{font-size:12px;color:var(--muted);white-space:nowrap;margin-left:auto}
#menu{display:none;border:1px solid var(--line);background:transparent;border-radius:6px;
font-size:18px;line-height:1;padding:4px 9px;color:var(--ink);cursor:pointer}
.searchbox{position:relative;flex:1;max-width:520px}
.searchbox input{width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:8px;
background:#fffdf8;font-family:inherit;font-size:13.5px;color:var(--ink);outline:none}
.searchbox input:focus{border-color:var(--accent)}
#hits{display:none;position:absolute;top:40px;left:0;right:0;background:#fffdf8;
border:1px solid var(--line);border-radius:10px;box-shadow:0 12px 32px rgba(43,38,32,.14);
max-height:62vh;overflow:auto;z-index:70}
#hits.on{display:block}
#hits a{display:block;padding:9px 12px;text-decoration:none;color:var(--ink);border-bottom:1px solid #eee6d6}
#hits a:hover{background:var(--paper2)}
#hits b{color:var(--accent);font-weight:600}
#hits small{display:block;color:var(--muted);font-size:12px;line-height:1.5;margin-top:2px}
#hits .empty{padding:14px;color:var(--muted);font-size:13px}
.shell{display:flex;align-items:flex-start}
#side{position:sticky;top:57px;width:300px;min-width:300px;height:calc(100vh - 57px);overflow:auto;
background:var(--side);color:var(--cream);padding:18px 14px 40px;font-size:13.5px;line-height:1.6}
#side::-webkit-scrollbar{width:8px}
#side::-webkit-scrollbar-thumb{background:#4a4238;border-radius:4px}
.side-title{font-size:15px;letter-spacing:.08em;color:#f3ead9;margin:0 0 14px;font-weight:700}
.part-link{display:block;color:#cbbfa8;text-decoration:none;padding:7px 8px;border-radius:6px;
font-size:13px;letter-spacing:.02em}
.part-link:hover{background:var(--side2);color:#fff}
.part-link.current{background:var(--side2);color:#fff;border-left:3px solid var(--accent)}
.chapters{margin:4px 0 12px}
.chapters details{margin:0 0 3px}
.chapters summary{cursor:pointer;color:#e5dac4;padding:6px 8px;border-radius:6px;font-size:13px}
.chapters summary:hover{background:var(--side2)}
.chapters summary span{color:#8e8270;font-size:11px;float:right}
.unit{margin:2px 0 8px 10px;border-left:1px solid #4a4238;padding-left:9px}
.ut{color:#9c907d;font-size:11.5px;margin:6px 0 3px;letter-spacing:.03em}
.sec-link{display:block;color:#c4b8a3;text-decoration:none;padding:3px 5px;border-radius:4px;font-size:12.5px}
.sec-link:hover{color:#fff;background:var(--side2)}
.sec-link.active{color:#fff;background:#3a3128;border-left:2px solid var(--accent)}
.ch-link{display:block;color:#c4b8a3;text-decoration:none;padding:5px 8px;border-radius:4px;font-size:12.5px}
.ch-link:hover{color:#fff;background:var(--side2)}
.ch-link span{float:right;color:#8e8270;font-size:11px}
.chnav{display:flex;justify-content:space-between;gap:12px;margin:52px 0 0;padding-top:16px;
border-top:1px solid var(--line);font-size:13.5px}
.chnav a{color:var(--accent);text-decoration:none}
.chnav a:hover{text-decoration:underline}
main{flex:1;min-width:0;padding:34px clamp(18px,5vw,72px) 90px;max-width:980px;margin:0 auto}
.part-hero{border-bottom:2px solid var(--ink);padding-bottom:22px;margin-bottom:34px}
.kicker{font-size:12px;letter-spacing:.22em;color:var(--accent);text-transform:uppercase;margin-bottom:8px}
h1{font-size:clamp(30px,4.2vw,44px);line-height:1.25;margin:0 0 10px;font-weight:700}
.lede{color:var(--muted);font-size:16px;line-height:1.85}
.chapter{margin:64px 0 20px;padding-top:10px;border-top:1px solid var(--line)}
.chapter h2{font-size:clamp(23px,2.6vw,29px);line-height:1.35;margin:14px 0 10px}
.chapter .chno{display:inline-block;font-size:12px;letter-spacing:.14em;color:var(--accent);
border:1px solid var(--accent);border-radius:20px;padding:2px 10px;margin-bottom:8px}
.ai{background:var(--paper2);border-left:3px solid var(--accent2);padding:12px 16px;
margin:14px 0 26px;font-size:14.5px;color:#4a4339;line-height:1.8}
.unit-block{margin:34px 0 0}
.unit-block h3{font-size:19px;margin:0 0 6px;color:var(--accent2);letter-spacing:.02em}
.unit-note{font-size:12px;color:var(--muted);margin-bottom:10px}
article.sec{margin:26px 0 34px;padding:4px 0 8px}
article.sec h3{font-size:21px;line-height:1.5;margin:18px 0 12px;scroll-margin-top:76px}
article.sec h3 .sid{color:var(--accent);font-size:14px;letter-spacing:.06em;margin-right:8px;font-weight:600}
article.sec h4{font-size:17px;margin:24px 0 8px;color:#3b342b}
article.sec h5{font-size:15.5px;margin:20px 0 6px;color:#4a4339}
article.sec p{margin:0 0 13px;text-align:justify;text-justify:inter-ideograph}
article.sec strong{color:#1f1b16}
article.sec a{color:var(--accent);text-decoration:none;border-bottom:1px dotted var(--accent)}
article.sec ul,article.sec ol{margin:6px 0 14px;padding-left:24px}
article.sec li{margin:3px 0}
article.sec blockquote{margin:14px 0;padding:10px 16px;background:var(--paper2);
border-left:3px solid var(--line);color:#4a4339;font-size:15px}
article.sec hr{border:0;border-top:1px solid var(--line);margin:26px 0}
code{font-family:"JetBrains Mono","SFMono-Regular",Consolas,monospace;font-size:.88em;
background:#eee6d6;padding:1px 5px;border-radius:4px}
pre{background:#241f1a;color:#efe6d4;padding:14px 16px;border-radius:8px;overflow:auto;font-size:13px;line-height:1.6}
pre code{background:none;padding:0;color:inherit}
.math{font-family:"Latin Modern Math","STIX Two Math",Georgia,serif}
.math.block{display:block;text-align:center;margin:14px 0;overflow-x:auto;overflow-y:hidden;padding:2px 0}
.table-wrap{overflow-x:auto;margin:16px 0 20px}
table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.65}
th,td{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
th{background:var(--paper2);font-weight:600}
tbody tr:nth-child(even){background:#fbf8f0}
.fig{margin:22px 0 26px;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fbf7ee}
.fig svg{display:block;width:100%;height:auto}
.fig figcaption{padding:10px 14px 12px;font-size:13.5px;color:#4a4339;line-height:1.75;border-top:1px solid var(--line)}
.fignum{display:inline-block;color:#fff;background:var(--accent);border-radius:4px;
font-size:11.5px;padding:1px 7px;margin-right:8px;letter-spacing:.03em}
.figcap{color:var(--muted);font-size:12.8px;margin-top:5px}
.hidden{display:none !important}
.status{font-size:12px;color:var(--muted);padding:6px 2px}
footer.bookfoot{margin-top:70px;padding-top:18px;border-top:1px solid var(--line);
font-size:12px;color:var(--muted)}
/* 首页 */
.hero{padding:56px 0 34px;border-bottom:2px solid var(--ink)}
.hero h1{font-size:clamp(36px,6vw,60px)}
.hero .sub{font-size:18px;color:var(--muted);margin-top:12px}
.hero .stats{display:flex;gap:26px;flex-wrap:wrap;margin-top:26px}
.hero .stat b{display:block;font-size:26px;color:var(--accent);line-height:1.2}
.hero .stat span{font-size:12px;color:var(--muted);letter-spacing:.08em}
.parts{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px;margin:34px 0}
.pcard{display:block;text-decoration:none;color:var(--ink);border:1px solid var(--line);
border-radius:12px;padding:20px 18px;background:#fbf8f0;transition:.15s}
.pcard:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(43,38,32,.10);border-color:var(--accent)}
.pcard .pn{font-size:11px;letter-spacing:.2em;color:var(--accent)}
.pcard h3{margin:8px 0 6px;font-size:19px}
.pcard p{margin:0;color:var(--muted);font-size:13.5px;line-height:1.7}
.pcard .pb{margin-top:10px;font-size:12px;color:var(--accent2)}
.chaptable{width:100%;font-size:13.5px}
.chaptable td:first-child{white-space:nowrap;color:var(--accent);font-weight:600}
.chaptable td:last-child{text-align:right;color:var(--muted);white-space:nowrap}
.routes{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:20px 0}
.route{border:1px solid var(--line);border-radius:10px;padding:14px 16px;background:#fbf8f0;font-size:13.5px}
.route b{color:var(--accent2)}
@media(max-width:980px){#side{width:260px;min-width:260px}main{padding:26px 20px 70px}}
@media(max-width:700px){
 #menu{display:block}
 .topbar{flex-wrap:wrap;gap:8px;padding:8px 12px}
 .brand{font-size:15px}
 .searchbox{order:9;flex:1 0 100%;max-width:none}
 #side{position:fixed;top:96px;left:0;z-index:45;transform:translateX(-102%);transition:.2s;
 width:84vw;min-width:0;height:calc(100vh - 96px);box-shadow:12px 0 30px rgba(0,0,0,.25)}
 #side.open{transform:none}
 .topbar .meta{display:none}
 main{padding:20px 14px 60px}
 body{font-size:16px}
 article.sec p{text-align:left}
 .table-wrap table,.table-wrap thead,.table-wrap tbody,.table-wrap th,.table-wrap td{display:block}
 .table-wrap thead{display:none}
 .table-wrap tr{border:1px solid var(--line);border-radius:8px;margin:0 0 10px;padding:6px 8px;background:#fbf8f0}
 .table-wrap td{border:0;padding:4px 2px}
 .table-wrap td:before{content:attr(data-label) "：";color:var(--accent);font-size:12px}
 .fig svg{min-height:180px}
}
@media print{
 @page{size:A4;margin:16mm 14mm}
 #side,.topbar,#progress,.searchbox,.chnav,.bookfoot,#search-status{display:none}
 body{background:#fff;font-size:10.5pt;line-height:1.72}
 main{max-width:none;padding:0;margin:0}
 .part-hero{border-bottom:1.2pt solid #000;padding-bottom:8pt;margin-bottom:12pt}
 h1{font-size:22pt}
 .ai{background:#f4f0e6;padding:8pt 10pt;font-size:9.5pt}
 article.sec{margin:14pt 0}
 article.sec h3{page-break-after:avoid;font-size:14pt}
 article.sec h4,article.sec h5{page-break-after:avoid}
 figure.fig,table,pre,.table-wrap{page-break-inside:avoid}
 .math.block{font-size:9.5pt;max-width:100%}
 p{orphans:2;widows:2}
}
"""

JS = r"""
const SEARCH = __SEARCH__;
const q = document.getElementById('q'), hits = document.getElementById('hits');
const part = document.body.dataset.part || '';
const statusEl = document.getElementById('search-status');
let timer = null;
function runSearch(){
  const v = q.value.trim();
  if(!v){ hits.classList.remove('on'); if(statusEl) statusEl.textContent=''; filterPage(''); return; }
  const res = SEARCH.filter(x => x.title.includes(v) || x.text.includes(v)).slice(0,24);
  hits.innerHTML = res.length ? res.map(x =>
    `<a href="${x.page}#s-${x.id}"><b>${x.id}</b> ${x.title}<small>第 ${x.ch} 章 · 第 ${x.unit} 编 · ${x.text}</small></a>`
  ).join('') : '<div class="empty">没有匹配的节。试试更短的关键词。</div>';
  hits.classList.add('on');
  filterPage(v);
}
function filterPage(v){
  const arts = [...document.querySelectorAll('article.sec')];
  if(!arts.length) return;
  let shown = 0;
  arts.forEach(a => {
    const hit = !v || a.textContent.includes(v);
    a.classList.toggle('hidden', !hit);
    if(hit) shown++;
  });
  document.querySelectorAll('section.chapter').forEach(c => {
    const any = [...c.querySelectorAll('article.sec')].some(a => !a.classList.contains('hidden'));
    c.classList.toggle('hidden', !any);
  });
  if(statusEl) statusEl.textContent = v ? `本页命中 ${shown} 节` : '';
}
q.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(runSearch, 160); });
document.addEventListener('click', e => { if(!e.target.closest('.searchbox')) hits.classList.remove('on'); });
const menu = document.getElementById('menu'), side = document.getElementById('side');
if(menu) menu.addEventListener('click', () => side.classList.toggle('open'));
if(side) side.addEventListener('click', e => { if(e.target.closest('a')) side.classList.remove('open'); });
const prog = document.getElementById('progress');
addEventListener('scroll', () => {
  const h = document.documentElement.scrollHeight - innerHeight;
  prog.style.width = (h > 0 ? (scrollY / h) * 100 : 0) + '%';
}, {passive:true});
const links = [...document.querySelectorAll('.sec-link')];
const map = new Map(links.map(a => [a.getAttribute('href').slice(1), a]));
if('IntersectionObserver' in window && map.size){
  const io = new IntersectionObserver(es => {
    es.forEach(e => {
      if(e.isIntersecting){
        links.forEach(l => l.classList.remove('active'));
        const a = map.get(e.target.id);
        if(a){ a.classList.add('active'); a.scrollIntoView({block:'nearest'}); }
      }
    });
  }, {rootMargin:'-18% 0px -72% 0px'});
  document.querySelectorAll('article.sec').forEach(x => io.observe(x));
}
addEventListener('DOMContentLoaded', () => {
  if(window.renderMathInElement){
    renderMathInElement(document.body, {
      delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],
      throwOnError:false, ignoredTags:['script','noscript','style','textarea','pre','code']
    });
  }
});
"""

HEAD = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="assets/katex/katex.min.css">
<style>__CSS__</style>
</head><body data-part="__PART__">
<div id="progress"></div>
<header class="topbar">
  <button id="menu" aria-label="目录">☰</button>
  <a class="brand" href="index.html">生成式数学手册</a>
  <div class="searchbox"><input id="q" type="search" placeholder="搜索 500 节（标题 / 正文）" autocomplete="off"><div id="hits"></div></div>
  <div class="meta">__META__</div>
</header>
<div class="shell">
"""

TAIL = """</div>
<script src="assets/katex/katex.min.js"></script>
<script src="assets/katex/contrib/auto-render.min.js"></script>
<script>__JS__</script>
</body></html>"""


def sidebar(by_stage, cur_ch):
    h = ['<aside id="side"><div class="side-title">生成式数学手册</div>']
    for r in ROMAN:
        st = by_stage[r]["stage"]
        h.append('<a class="part-link" href="part-%s.html">%s　%s</a>' % (r, STAGE_CN[r], st["title"]))
        h.append('<div class="chapters">')
        for c in by_stage[r]["chapters"]:
            if c["no"] == cur_ch:
                h.append('<details open><summary>第 %d 章　%s <span>%s</span></summary>' % (
                    c["no"], esc(c["title"]), "{:,}k".format(c["budget"] // 1000)))
                for u in c["units"]:
                    h.append('<div class="unit"><div class="ut">第 %d 编　%s</div>' % (u["no"], esc(u["title"])))
                    for s in u["sections"]:
                        h.append('<a class="sec-link" href="#s-%s">%s %s</a>' % (s["id"], s["id"], esc(s["title"])))
                    h.append("</div>")
                h.append("</details>")
            else:
                h.append('<a class="ch-link" href="ch-%d.html">第 %d 章　%s <span>%s</span></a>' % (
                    c["no"], c["no"], esc(c["title"]), "{:,}k".format(c["budget"] // 1000)))
        h.append("</div>")
    h.append("</aside>")
    return "".join(h)


def chapter_page(by_stage, r, c, search):
    st = by_stage[r]["stage"]
    done = sum(1 for u in c["units"] for s in u["sections"] if s["done"])
    total = sum(len(u["sections"]) for u in c["units"])
    h = [HEAD.replace("__TITLE__", "第 %d 章　%s ｜ 生成式数学手册" % (c["no"], c["title"]))
         .replace("__CSS__", CSS).replace("__PART__", str(c["no"]))
         .replace("__META__", "%s　第 %d 章" % (STAGE_CN[r], c["no"]))]
    h.append(sidebar(by_stage, c["no"]))
    h.append('<main><div class="part-hero"><div class="kicker">%s ／ 第 %d 章</div><h1>%s</h1>' % (
        STAGE_CN[r], c["no"], esc(c["title"])))
    h.append('<p class="lede">%s　·　<span class="nw">本章预算 %s 字符</span>　·　<span class="nw">%d 编 / %d 节</span>　·　<span class="nw">已生成 %d 节</span></p>' % (
        esc(c["en"]), "{:,}".format(c["budget"]), len(c["units"]), total, done))
    h.append('<div class="status" id="search-status"></div></div>')
    h.append('<div class="ai"><b>与生成模型的接口　</b>%s</div>' % inline(c["ai_summary"]))
    for u in c["units"]:
        h.append('<div class="unit-block"><h3>第 %d 编　%s</h3>' % (u["no"], esc(u["title"])))
        for s in u["sections"]:
            h.append('<article class="sec" id="s-%s">' % s["id"])
            h.append('<h3><span class="sid">%s</span>%s</h3>' % (s["id"], esc(s["title"])))
            if s["done"]:
                h.append(s["html"])
            else:
                h.append('<p class="status">（本节尚未生成）</p>')
            h.append("</article>")
        h.append("</div>")
    prev = c["no"] - 1 if c["no"] > 1 else None
    nxt = c["no"] + 1 if c["no"] < 25 else None
    h.append('<nav class="chnav">')
    if prev:
        h.append('<a href="ch-%d.html">← 第 %d 章</a>' % (prev, prev))
    h.append('<a href="part-%s.html">%s总览</a>' % (r, STAGE_CN[r]))
    if nxt:
        h.append('<a href="ch-%d.html">第 %d 章 →</a>' % (nxt, nxt))
    h.append('</nav>')
    h.append('<footer class="bookfoot">《生成式数学手册》· 七段式：问题 → 对象 → 定理 → 离散化 → 误差界 → 实验映射 → 小结与陷阱</footer></main>')
    h.append(TAIL.replace("__JS__", JS.replace("__SEARCH__", json.dumps(search, ensure_ascii=False))))
    return "".join(h)


def part_page(by_stage, r, search):
    st = by_stage[r]["stage"]
    h = [HEAD.replace("__TITLE__", "%s　%s ｜ 生成式数学手册" % (STAGE_CN[r], st["title"]))
         .replace("__CSS__", CSS).replace("__PART__", r)
         .replace("__META__", "%s　%s" % (STAGE_CN[r], st["title"]))]
    h.append(sidebar(by_stage, 0))
    h.append('<main><div class="part-hero"><div class="kicker">%s ／ Part %s</div><h1>%s</h1>' % (STAGE_CN[r], r, st["title"]))
    h.append('<p class="lede">%s</p><div class="status" id="search-status"></div></div>' % inline(st["subtitle"]))
    h.append('<div class="parts">')
    for c in by_stage[r]["chapters"]:
        done = sum(1 for u in c["units"] for s in u["sections"] if s["done"])
        total = sum(len(u["sections"]) for u in c["units"])
        h.append('<a class="pcard" href="ch-%d.html"><div class="pn">第 %d 章</div><h3>%s</h3><p>%s</p><div class="pb">%d 编 · %d 节 · 已生成 %d 节 · %s 字符</div></a>' % (
            c["no"], c["no"], esc(c["title"]), inline(c["ai_summary"]), len(c["units"]), total, done, "{:,}".format(c["budget"])))
    h.append('</div>')
    h.append('<footer class="bookfoot">《生成式数学手册》· %s · 五部 25 章 100 编 500 节 · 目标 8,000,000 字符</footer></main>' % STAGE_CN[r])
    h.append(TAIL.replace("__JS__", JS.replace("__SEARCH__", json.dumps(search, ensure_ascii=False))))
    return "".join(h)


def index_page(by_stage, search):
    st_all = [by_stage[r]["stage"] for r in ROMAN]
    done = sum(1 for r in ROMAN for c in by_stage[r]["chapters"] for u in c["units"] for s in u["sections"] if s["done"])
    chars = sum(s["visible"] for r in ROMAN for c in by_stage[r]["chapters"] for u in c["units"] for s in u["sections"])
    h = [HEAD.replace("__TITLE__", "生成式数学手册 ｜ 生成模型数学基础路线").replace("__CSS__", CSS)
         .replace("__PART__", "").replace("__META__", "五部 25 章 100 编 500 节")]
    h.append('<main><section class="hero"><div class="kicker">生成模型数学基础路线 ／ 2026</div>')
    h.append('<h1>生成式数学手册</h1>')
    h.append('<p class="sub">从线性代数到随机微分方程：一条为扩散、流匹配、VAE、GAN、自回归与 SSM 准备的数学主线。</p>')
    h.append('<div class="stats">')
    h.append('<div class="stat"><b>5</b><span>部</span></div>')
    h.append('<div class="stat"><b>25</b><span>章</span></div>')
    h.append('<div class="stat"><b>100</b><span>编</span></div>')
    h.append('<div class="stat"><b>500</b><span>节</span></div>')
    h.append('<div class="stat"><b>8,000,000</b><span>目标字符</span></div>')
    h.append('<div class="stat"><b>%s</b><span>已生成节</span></div>' % done)
    h.append('<div class="stat"><b>%s</b><span>已生成可见字符</span></div>' % "{:,}".format(chars))
    h.append('</div></section>')
    h.append('<div class="parts">')
    for r in ROMAN:
        st = by_stage[r]["stage"]
        n = sum(len(c["units"]) for c in by_stage[r]["chapters"])
        b = sum(c["budget"] for c in by_stage[r]["chapters"])
        h.append('<a class="pcard" href="part-%s.html"><div class="pn">PART %s</div><h3>%s</h3><p>%s</p><div class="pb">%d 章 · %d 编 · %s 字符</div></a>' % (
            r, r, esc(st["title"]), inline(st["subtitle"]), len(by_stage[r]["chapters"]), n, "{:,}".format(b)))
    h.append('</div>')
    h.append('<h2 style="margin:40px 0 12px">25 章总目</h2><div class="table-wrap"><table class="chaptable"><tbody>')
    for r in ROMAN:
        for c in by_stage[r]["chapters"]:
            h.append('<tr><td>第 %d 章</td><td><a href="ch-%d.html">%s</a></td><td>%s</td></tr>' % (
                c["no"], c["no"], esc(c["title"]), "{:,}k".format(c["budget"] // 1000)))
    h.append('</tbody></table></div>')
    h.append('<h2 style="margin:40px 0 12px">三条阅读路线</h2><div class="routes">')
    h.append('<div class="route"><b>路线 A · 工程师精简</b><br>12 章 / 4,120k 字符：第 1、2、10、12、15、16、17、18、20、21、24、25 章。先建立“空间—算子—概率—动力学”四段骨架，再回补几何。</div>')
    h.append('<div class="route"><b>路线 B · 完整阅读</b><br>25 章 / 8,000k 字符：按部顺序读，每章先读“与生成模型的接口”，再读各节七段。</div>')
    h.append('<div class="route"><b>路线 C · 几何方向</b><br>17 章 / 5,560k 字符：第 1–9、10、12、13、15–19、22–25 章。适合做流形上的生成模型与几何深度学习。</div>')
    h.append('</div>')
    h.append('<footer class="bookfoot">正文按七段式写作：问题 → 对象 → 定理 → 离散化 → 误差界 → 实验映射 → 小结与陷阱。公式由本地 KaTeX 渲染，无需联网。</footer></main>')
    h.append(TAIL.replace("__JS__", JS.replace("__SEARCH__", json.dumps(search, ensure_ascii=False))))
    return "".join(h)


COVER = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>生成式数学手册 · 封面</title><style>
@page{size:A4;margin:0}
*{box-sizing:border-box}
body{margin:0;background:#f7f3ea;color:#2b2620;
font-family:"Noto Serif CJK SC","Source Han Serif SC","Songti SC",Georgia,serif}
.cover{width:210mm;height:297mm;padding:30mm 24mm 24mm;display:flex;flex-direction:column;
justify-content:space-between;border:1px solid #d9cfbc}
.top{border-top:3px solid #a04a2f;padding-top:8mm}
.kicker{font-size:10pt;letter-spacing:.28em;color:#a04a2f}
h1{font-size:46pt;line-height:1.18;margin:6mm 0 4mm;font-weight:700;letter-spacing:.02em}
.sub{font-size:15pt;color:#6f665a;line-height:1.8;margin:0}
.line{width:38mm;height:2px;background:#2b2620;margin:9mm 0}
.desc{font-size:10.5pt;color:#4a4339;line-height:1.95;max-width:128mm}
.mid{display:flex;justify-content:center;margin:2mm 0}
.meta{display:flex;justify-content:space-between;align-items:flex-end;
border-top:1px solid #d9cfbc;padding-top:6mm;font-size:9.5pt;color:#6f665a;letter-spacing:.05em}
.meta b{color:#2b2620;font-weight:600}
</style></head><body><div class="cover">
<div class="top"><div class="kicker">生成模型数学基础路线 ／ 2026</div>
<h1>生成式数学手册</h1>
<p class="sub">从线性代数到随机微分方程</p>
<div class="line"></div>
<p class="desc">为扩散模型、流匹配、VAE、GAN、自回归与状态空间模型准备的数学主线：
五部 25 章，每节按“问题 → 对象 → 定理 → 离散化 → 误差界 → 实验映射 → 小结与陷阱”写作。</p>
</div>
<div class="mid"><svg width="420" height="150" viewBox="0 0 420 150" xmlns="http://www.w3.org/2000/svg">
<path d="M30 120 C90 40, 150 40, 210 80 S330 130, 390 55" fill="none" stroke="#a04a2f" stroke-width="2"/>
<path d="M30 120 C90 40, 150 40, 210 80 S330 130, 390 55 L390 150 L30 150 Z" fill="#a04a2f" opacity="0.07"/>
<line x1="30" y1="120" x2="390" y2="120" stroke="#2b2620" stroke-width="1"/>
<line x1="30" y1="120" x2="30" y2="30" stroke="#2b2620" stroke-width="1"/>
<text x="36" y="26" font-family="Georgia,serif" font-size="11" fill="#6f665a">p(x)</text>
<text x="384" y="136" font-family="Georgia,serif" font-size="11" fill="#6f665a">x</text>
</svg></div>
<div class="meta"><div><b>五部 · 25 章 · 100 编 · 500 节</b><br>目标 8,000,000 字符</div>
<div>2026-11-25<br>生成版 · 内部阅读</div></div>
</div></body></html>"""


def main():
    tasks, by_stage = load()
    search = search_index(by_stage)
    os.makedirs(SITE, exist_ok=True)
    if os.path.exists(KATEX_SRC):
        dst = os.path.join(SITE, "assets", "katex")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(KATEX_SRC, dst)
    with open(os.path.join(SITE, "cover.html"), "w", encoding="utf-8") as f:
        f.write(COVER)
    for r in ROMAN:
        path = os.path.join(SITE, "part-%s.html" % r)
        with open(path, "w", encoding="utf-8") as f:
            f.write(part_page(by_stage, r, search))
        print("wrote", path, os.path.getsize(path) // 1024, "KB")
        for c in by_stage[r]["chapters"]:
            path = os.path.join(SITE, "ch-%d.html" % c["no"])
            with open(path, "w", encoding="utf-8") as f:
                f.write(chapter_page(by_stage, r, c, search))
            print("wrote", path, os.path.getsize(path) // 1024, "KB")
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_page(by_stage, search))
    done = sum(1 for r in ROMAN for c in by_stage[r]["chapters"] for u in c["units"] for s in u["sections"] if s["done"])
    chars = sum(s["visible"] for r in ROMAN for c in by_stage[r]["chapters"] for u in c["units"] for s in u["sections"])
    print("done sections %d/500, visible chars %s" % (done, "{:,}".format(chars)))


if __name__ == "__main__":
    main()
