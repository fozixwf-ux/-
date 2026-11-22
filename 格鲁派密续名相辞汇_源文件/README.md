# 格鲁派密续名相辞汇 · 源文件

`../格鲁派密续名相辞汇.pdf` 由本目录生成。

- `data/01_general.txt` … `11_texts.txt`：十一部共 154 条的条目数据。每条的 `q:` 行是 CBETA 引文，`qs:` 行是梵文引文。
- `tools/build.py`：解析条目，逐条在原典电子全文中检索引文；找不到即报错。CBETA 的册、页、栏、行由程序按命中位置生成。
- `tools/render.py`、`style.css`、`front.html`、`back.html`：生成 HTML（正文转简体，引文保留 CBETA 原文）。
- `tools/pdf.js`：用 Chromium（Playwright）输出 PDF；`pagemap.py` 从 PDF 书签读回页码，填入目录。

## 复核步骤

1. 在本目录下建立 `src/` 与 `out/`，再把原典下载到 `src/`：
   - `python3 tools/cbeta.py B0068 22 src/B0068.txt`，B0057（5 卷）、T0892（5 卷）同理。
   - `python3 tools/dsbc.py 723 src/dsbc_723.txt` 下载《密集》，`dsbc.py 737` 下载《明炬论》第十一品。
   - GRETIL 上的 Pañcakrama、Sekoddeśa、Guhyasamājamaṇḍalavidhi 纯文本，以原文件名放入 `src/`。
2. 运行 `python3 tools/build.py`，输出各类引文的核验数量；有任何不符时列出并以非零状态退出。
