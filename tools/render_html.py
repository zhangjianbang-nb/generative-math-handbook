# -*- coding: utf-8 -*-
"""生成单文件 HTML 书地图：site/index.html"""
import html
import io
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
OUT = os.path.join(ROOT, "site", "index.html")

STAGE_META = {
    "I": ("#8a5a2b", "第一部"),
    "II": ("#3d6b57", "第二部"),
    "III": ("#35567d", "第三部"),
    "IV": ("#7a4a63", "第四部"),
    "V": ("#a04a2f", "第五部"),
}

CSS = """
:root{
  --paper:#f7f4ec; --ink:#1c1a17; --muted:#6b6358; --line:#d9d2c3;
  --card:#fffdf7; --accent:#8a5a2b;
  --serif:"Noto Serif CJK SC","Songti SC",serif;
  --sans:"Noto Sans CJK SC","PingFang SC",system-ui,sans-serif;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif);line-height:1.65}
a{color:inherit;text-decoration:none}
code{font-family:ui-monospace,Menlo,monospace;font-size:.9em;background:#efe9dc;padding:.05em .3em;border-radius:3px}

/* 侧栏 */
#side{position:fixed;left:0;top:0;bottom:0;width:296px;background:#efeade;border-right:1px solid var(--line);
  display:flex;flex-direction:column;z-index:10}
#side .brand{padding:22px 20px 14px;border-bottom:1px solid var(--line)}
#side .brand h1{margin:0;font-size:19px;letter-spacing:.04em}
#side .brand p{margin:4px 0 0;font-size:12px;color:var(--muted);font-family:var(--sans)}
#side .stats{display:flex;gap:6px;flex-wrap:wrap;padding:12px 20px;border-bottom:1px solid var(--line)}
#side .stats span{font-family:var(--sans);font-size:11px;border:1px solid var(--line);border-radius:20px;padding:2px 8px;color:var(--muted)}
#search{margin:12px 20px 6px;padding:8px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);
  font-family:var(--sans);font-size:13px;color:var(--ink);outline:none;width:calc(100% - 40px)}
#search:focus{border-color:var(--accent)}
#nav{overflow-y:auto;flex:1;padding:6px 12px 20px}
#nav .grp{margin:10px 8px 4px;font-family:var(--sans);font-size:11px;letter-spacing:.12em;color:var(--muted);text-transform:uppercase}
#nav a{display:block;padding:4px 8px;border-radius:4px;font-size:13px;color:#3a352c}
#nav a:hover{background:#e3dccb}
#nav a .n{font-family:var(--sans);font-size:11px;color:var(--muted);margin-right:5px}

/* 正文 */
main{margin-left:296px;max-width:1120px;padding:0 44px 80px}
.hero{padding:56px 0 34px;border-bottom:2px solid var(--ink)}
.hero .kicker{font-family:var(--sans);font-size:12px;letter-spacing:.18em;color:var(--accent)}
.hero h1{font-size:44px;line-height:1.15;margin:12px 0 10px;letter-spacing:.02em}
.hero .sub{font-size:17px;color:var(--muted);max-width:760px}
.nw{white-space:nowrap}
#search-status{margin:0 20px 6px;font-family:var(--sans);font-size:11px;color:var(--muted);min-height:16px}
.hero .big{display:flex;gap:34px;margin-top:26px;flex-wrap:wrap}
.hero .big div{border-left:2px solid var(--accent);padding-left:12px}
.hero .big b{display:block;font-family:var(--sans);font-size:26px;letter-spacing:.02em}
.hero .big small{font-family:var(--sans);font-size:11px;color:var(--muted);letter-spacing:.06em}

h2.stage{font-size:30px;margin:64px 0 6px;padding-top:14px;border-top:1px solid var(--line)}
h2.stage .cn{font-family:var(--sans);font-size:12px;letter-spacing:.18em;margin-right:10px}
.stage-sub{color:var(--muted);font-size:15px;margin:0 0 14px}
.stage-intro{font-size:14.5px;color:#453f35;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px 18px;margin:0 0 26px}
.stage-bar{display:flex;gap:4px;align-items:center;font-family:var(--sans);font-size:11px;color:var(--muted);margin:0 0 22px}
.stage-bar .bar{height:8px;background:var(--accent);border-radius:4px;opacity:.75}

.ch{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:0 0 22px;overflow:hidden}
.ch-head{padding:18px 20px 12px;border-bottom:1px dashed var(--line)}
.ch-head .row{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.ch-no{font-family:var(--sans);font-size:12px;letter-spacing:.12em;color:#fff;background:var(--accent);border-radius:4px;padding:2px 7px}
.ch-title{font-size:22px;margin:0}
.ch-en{font-family:var(--sans);font-size:12px;color:var(--muted);letter-spacing:.04em}
.ch-meta{font-family:var(--sans);font-size:11.5px;color:var(--muted);margin-top:8px;display:flex;gap:14px;flex-wrap:wrap}
.ch-ai{padding:12px 20px;font-size:13.5px;color:#3d372d;background:#f3eee1;border-bottom:1px solid var(--line)}
.ch-ai b{font-family:var(--sans);font-size:10.5px;letter-spacing:.1em;color:var(--accent);margin-right:8px}
details.src{padding:8px 20px;border-bottom:1px solid var(--line);font-size:12.5px;color:var(--muted)}
details.src summary{cursor:pointer;font-family:var(--sans);font-size:11.5px;letter-spacing:.04em}
details.src ul{margin:8px 0 4px;padding-left:18px}
details.unit{border-top:1px solid var(--line)}
details.unit>summary{cursor:pointer;padding:10px 20px;font-size:14px;display:flex;gap:10px;align-items:baseline}
details.unit>summary:hover{background:#f1ebdd}
details.unit>summary .u-no{font-family:var(--sans);font-size:11px;color:var(--accent);letter-spacing:.08em}
details.unit>summary .u-budget{margin-left:auto;font-family:var(--sans);font-size:11px;color:var(--muted)}
details.unit[open]>summary{border-bottom:1px dashed var(--line)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid #e7e0d2}
th{font-family:var(--sans);font-size:10.5px;letter-spacing:.08em;color:var(--muted);background:#f4efe2;font-weight:500}
td.no{font-family:var(--sans);font-size:11px;color:var(--accent);white-space:nowrap}
td.name{font-weight:600;min-width:180px}
td.src-cell{color:var(--muted);font-size:11.5px}
tbody tr:hover{background:#faf6ea}

.quota{margin:34px 0 10px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.quota div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;text-align:center}
.quota b{display:block;font-family:var(--sans);font-size:20px}
.quota small{font-family:var(--sans);font-size:10.5px;color:var(--muted);letter-spacing:.06em}

footer{margin-top:60px;padding-top:18px;border-top:1px solid var(--line);font-family:var(--sans);font-size:11.5px;color:var(--muted)}
.hidden{display:none!important}
@media(max-width:900px){
  #side{position:static;width:auto;height:auto;border-right:none;border-bottom:1px solid var(--line)}
  #nav{max-height:220px}
  main{margin-left:0;padding:0 18px 60px}
  .hero h1{font-size:32px}
  .quota{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:700px){
  table,thead,tbody,tr,td{display:block}
  thead{display:none}
  tr{padding:10px 14px;border-bottom:1px solid var(--line)}
  td{border:none;padding:2px 0}
  td.no{display:inline-block;margin-right:6px}
  td.name{display:inline;font-size:14px}
  td[data-label]::before{content:attr(data-label) "：";font-family:var(--sans);font-size:10.5px;
    color:var(--muted);letter-spacing:.06em;display:block;margin-top:4px}
  td[data-label]{color:#3d372d;font-size:12px}
}
@media print{
  #side{display:none} main{margin:0;max-width:none;padding:0}
  .ch{break-inside:avoid}
}
"""

JS = """
const q = document.getElementById('search');
const status = document.getElementById('search-status');
const chapters = [...document.querySelectorAll('.ch')];
const units = [...document.querySelectorAll('details.unit')];
const sections = [...document.querySelectorAll('section[data-stage]')];
q.addEventListener('input', () => {
  const s = q.value.trim().toLowerCase();
  if (!s) {
    chapters.forEach(c => c.classList.remove('hidden'));
    units.forEach(u => { u.open = false; u.classList.remove('hidden'); });
    sections.forEach(x => x.classList.remove('hidden'));
    status.textContent = '';
    return;
  }
  let chHit = 0, unitHit = 0;
  chapters.forEach(c => {
    let any = false;
    c.querySelectorAll('details.unit').forEach(u => {
      const hit = u.textContent.toLowerCase().includes(s);
      u.classList.toggle('hidden', !hit);
      u.open = hit;
      if (hit) { any = true; unitHit++; }
    });
    c.classList.toggle('hidden', !any);
    if (any) chHit++;
  });
  sections.forEach(x => {
    const visible = [...x.querySelectorAll('.ch')].some(c => !c.classList.contains('hidden'));
    x.classList.toggle('hidden', !visible);
  });
  status.textContent = chHit ? `匹配 ${chHit} 章 / ${unitHit} 编` : '无匹配结果';
});
document.querySelectorAll('#nav a').forEach(a => {
  a.addEventListener('click', () => {
    q.value = '';
    chapters.forEach(c => c.classList.remove('hidden'));
    units.forEach(u => { u.classList.remove('hidden'); u.open = false; });
    sections.forEach(x => x.classList.remove('hidden'));
    status.textContent = '';
  });
});
window.addEventListener('beforeprint', () => units.forEach(u => u.open = true));
"""


def esc(s):
    return html.escape(s, quote=False)


def stage_stats(stage):
    chapters = stage["chapters"]
    budget = sum(c["budget"] for c in chapters)
    units = sum(len(c["units"]) for c in chapters)
    sections = sum(len(u["sections"]) for c in chapters for u in c["units"])
    return budget, units, sections


def render():
    L = []
    a = L.append
    a("<!DOCTYPE html>")
    a('<html lang="zh-CN">')
    a("<head>")
    a('<meta charset="utf-8">')
    a('<meta name="viewport" content="width=device-width, initial-scale=1">')
    a("<title>生成式数学手册 · 书地图</title>")
    a(f"<style>{CSS}</style>")
    a("</head>")
    a("<body>")
    a('<aside id="side">')
    a('<div class="brand"><h1>生成式数学手册</h1><p>生成模型数学基础路线 · 总目录</p></div>')
    a('<div class="stats"><span>8,000,000 字符</span><span>25 章</span><span>100 编</span><span>500 节</span></div>')
    a('<input id="search" type="search" placeholder="搜索节标题 / 要点 / AI 关联…">')
    a('<div id="search-status"></div>')
    a('<nav id="nav">')
    for st in STAGES:
        color, cn = STAGE_META[st["id"]]
        a(f'<div class="grp">{cn} · {esc(st["title"])}</div>')
        for c in st["chapters"]:
            a(f'<a href="#ch-{c["no"]}"><span class="n">{c["no"]:02d}</span>{esc(c["title"])}</a>')
    a("</nav>")
    a("</aside>")

    a("<main>")
    a('<header class="hero">')
    a('<div class="kicker">GENERATIVE MATHEMATICS HANDBOOK · 2026</div>')
    a("<h1>生成式数学手册</h1>")
    a('<p class="sub">从空间到动力学：五部 25 章，把生成模型用到的数学一次铺完。'
      '每节按“<span class="nw">问题</span> → <span class="nw">对象</span> → <span class="nw">定理</span> → '
      '<span class="nw">离散化</span> → <span class="nw">误差界</span> → <span class="nw">实验</span>”六步写，'
      '每章标注主源书与 AI 落点。</p>')
    a('<div class="big">')
    a("<div><b>8,000,000</b><small>目标字符</small></div>")
    a("<div><b>500</b><small>节 / 100 编 / 25 章</small></div>")
    a("<div><b>5</b><small>部：空间 → 几何 → 算子 → 分布 → 动力学</small></div>")
    a("</div>")
    a("</header>")

    a('<div class="quota">')
    for n, label in [("10,000", "公式"), ("1,000", "图"), ("400", "表"), ("1,600", "推导"), ("800", "AI 关联")]:
        a(f"<div><b>{n}</b><small>{label}</small></div>")
    a("</div>")

    for st in STAGES:
        color, cn = STAGE_META[st["id"]]
        budget, units, sections = stage_stats(st)
        a(f'<section data-stage="{st["id"]}" style="--accent:{color}">')
        a(f'<h2 class="stage" id="stage-{st["id"]}"><span class="cn">{cn}</span>{esc(st["title"])}</h2>')
        a(f'<p class="stage-sub">{esc(st["subtitle"])}</p>')
        a(f'<div class="stage-bar"><span>{budget//1000:,}k 字符</span>'
          f'<span class="bar" style="width:{budget/1940000*100:.0f}%"></span>'
          f'<span>{len(st["chapters"])} 章 · {units} 编 · {sections} 节</span></div>')
        a(f'<p class="stage-intro">{esc(st["intro"])}</p>')
        for c in st["chapters"]:
            nu = len(c["units"])
            ub = c["budget"] // nu
            a(f'<article class="ch" id="ch-{c["no"]}">')
            a('<div class="ch-head">')
            a('<div class="row">')
            a(f'<span class="ch-no">第 {c["no"]} 章</span>')
            a(f'<h3 class="ch-title">{esc(c["title"])}</h3>')
            a(f'<span class="ch-en">{esc(c["en"])}</span>')
            a("</div>")
            a(f'<div class="ch-meta"><span>{c["budget"]//1000:,}k 字符</span>'
              f'<span>{nu} 编 × 5 节</span><span>每编 {ub//1000}k</span>'
              f'<span>每节 {ub//5000}k</span></div>')
            a("</div>")
            a(f'<div class="ch-ai"><b>AI 关联</b>{esc(c["ai_summary"])}</div>')
            a('<details class="src"><summary>主源书与章节（' + str(len(c["sources"])) + ' 本）</summary><ul>')
            for book, chap in c["sources"]:
                a(f"<li><b>{esc(book)}</b> — {esc(chap)}</li>")
            a("</ul></details>")
            for ui, u in enumerate(c["units"], 1):
                a('<details class="unit">')
                a(f'<summary><span class="u-no">第 {ui} 编</span>{esc(u["title"])}'
                  f'<span class="u-budget">{ub//1000}k</span></summary>')
                a("<table><thead><tr><th>节</th><th>标题</th><th>核心要点</th><th>AI 关联</th><th>来源</th></tr></thead><tbody>")
                for title, points, ai, source in u["sections"]:
                    no, name = title.split(" ", 1)
                    a(f'<tr><td class="no">{esc(no)}</td><td class="name">{esc(name)}</td>'
                      f'<td data-label="要点">{esc(points)}</td><td data-label="AI 关联">{esc(ai)}</td>'
                      f'<td data-label="来源" class="src-cell">{esc(source)}</td></tr>')
                a("</tbody></table>")
                a("</details>")
            a("</article>")
        a("</section>")

    a("<footer>")
    a('配套文档：<a href="../docs/生成式数学手册-总目录.md">生成式数学手册-总目录.md</a>（完整蓝图）· '
      '<a href="../docs/书→章合并映射.md">书→章合并映射.md</a> · '
      '<a href="../docs/800万字符预算与配额.md">800万字符预算与配额.md</a><br>')
    a("骨架来源：Mac mini 数学-物理学书库 2,132 册 / 658,706 页 · AI_MATH_DESIGN.md（17 节 / 110 公式）· math-design-theory skill 六步协议")
    a("</footer>")
    a("</main>")
    a(f"<script>{JS}</script>")
    a("</body></html>")
    return "\n".join(L)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    text = render()
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {OUT}  {len(text)} chars")


if __name__ == "__main__":
    main()
