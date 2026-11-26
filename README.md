# 生成式数学手册

**从线性代数到随机微分方程：生成模型的数学基础路线**

一本为生成模型（diffusion / flow matching / VAE / GAN / autoregressive / state-space）准备的数学手册。全书按「空间与几何 → 几何结构 → 函数与算子 → 概率与分布 → 动力学与生成理论」五个阶段展开，共 **5 部 / 25 章 / 100 编 / 500 节**。

**在线阅读：<https://zhangjianbang-nb.github.io/generative-math-handbook/>**

## 规模

| 指标 | 数量 |
|---|---|
| 可见字符 | **8,330,753** |
| 章 / 编 / 节 | 25 / 100 / 500 |
| 显示公式 | 13,179 |
| 图（内联 SVG） | 1,593 |
| 表 | 1,320 |
| 推导 | 3,200 |
| AI 关联段落 | 8,033 |

验收口径：`tools/verify_book.py` 十项断言全 PASS；`tools/check_structure.py` 500 节七段结构齐全；全量 KaTeX 扫描 0 坏公式。

## 目录

### 第一部 空间与几何基础（预算 1,300,000 字符）

1. 线性代数
2. 欧几里得空间
3. 度量空间
4. 拓扑空间

### 第二部 几何结构（1,600,000 字符）

5. 微分流形
6. 黎曼几何
7. 双曲几何
8. 球面几何
9. 李群与李代数

### 第三部 函数与算子（1,600,000 字符）

10. 泛函分析
11. Banach 空间
12. Hilbert 空间
13. Sobolev 空间
14. 算子理论

### 第四部 概率与分布（1,560,000 字符）

15. 测度论
16. 概率空间
17. Wasserstein 空间
18. 最优传输
19. 信息几何

### 第五部 动力学与生成理论（1,940,000 字符）

20. 常微分方程
21. 偏微分方程
22. 流形上的动力系统
23. 哈密顿动力学
24. 连续性方程
25. 随机微分方程

## 每节的七段式结构

每一节都按固定顺序写：**问题 → 对象 → 定理 → 离散化 → 误差界 → 实验映射 → 小结与陷阱**。前四段建立数学骨架，第五段给出可计算的误差预算，第六段把数学对象映射到具体的生成模型组件（注意力、LoRA、扩散采样器、流匹配、SDE 求解器……），第七段收束并列出常见误区。

## 阅读方式

- **HTML 阅读器**：`docs/index.html`（在线版即 GitHub Pages；每章一页，侧栏目录、全文搜索、本地 KaTeX、内联 SVG 图、移动端自适应、打印样式）
- **单文件全书**：`book/全书.md`（约 17 MB，纯 Markdown，公式为 `$…$` / `$$…$$`）
- **PDF**：A4，5,607 页，共 126 MB。仓库内按五部分卷：`book/pdf/part-I.pdf`（846 页）、`part-II.pdf`（1,110 页）、`part-III.pdf`（1,048 页）、`part-IV.pdf`（1,165 页）、`part-V.pdf`（1,438 页）。完整单文件 `book/pdf/全书.pdf` 因超过 GitHub 单文件 100 MB 限制不进仓库，可用 `node tools/build_pdf.js --force` 重建，或 `pdfunite book/pdf/part-*.pdf 全书.pdf` 合并。

## 生成管线

```
book/book.json              500 节任务（主题/预算/配额）
tools/gen_book.py           逐节生成（七段式协议 + 预算控制 + 失败扰动重试）
tools/assemble.py           装配 book/全书.md + stats.json
tools/verify_book.py        十项配额断言
tools/check_structure.py    七段结构断言
tools/render_book_html.py   → site/book/（HTML 阅读器）
tools/build_pdf.js          → book/pdf/全书.pdf
tools/pdf_check.py          PDF 页数/空页/文本层验收
tools/shoot_book.js         桌面/搜索/移动 DOM 断言
tools/check_katex.js        全量公式渲染扫描
```

生成引擎：DeepSeek-V4.1-Flash-1017-TF（tensorfold-native，4 lane）。内容为 AI 生成，供学习与研究参考；引用前请自行核对数学细节。

## 许可

文字内容采用 CC BY-NC-SA 4.0；代码（`tools/`）采用 MIT。
