# 格鲁派圆满次第核心名相·深度辞典试行卷

本卷收密集圣派五次第及光明、幻身、双运之核心名相 15 条，以宗喀巴藏文原著为本，逐条立性相、分类、界限，原典按层排列（印度原典、宗喀巴、克主杰、后期教本、现代研究），并录诤论、语义史与译名考辨。

本卷为试行本，尚未经具格格西与相关学者审定。审定程序与材料见 `审定材料.xlsx`。

## 内容

| 文件 | 说明 |
|---|---|
| `格鲁派圆满次第核心名相·试行卷.pdf` | 排印本 |
| `审定材料.xlsx` | 盲审表（甲、乙）、辩经质询题、抽样与审定方案、一致率计算（Cohen κ）、引文核验日志、逐词通检 |
| `数据/deep.json` | 全部条目之结构化数据（含核验后之藏文原文与叶行） |
| `数据/terms.csv` | 名相表（汉、藏、梵、英、性相、通检次数） |
| `数据/terms.skos.ttl` | SKOS 概念表，可导入术语管理系统 |
| `数据/verify_log.csv` | 每一引文之出处与核验结果 |
| `程序/deep/entries.yml` | 条目底稿（唯一需人工编辑之文件） |
| `程序/deep/tib.py` | 藏文通检、引文核对、原文回取 |
| `程序/deep/build_deep.py` | 逐条核对藏、汉、梵引文，生成 `deep.json` 与核验日志 |
| `程序/deep/render_deep.py` | 排版并导出 CSV、SKOS |
| `程序/deep/review_kit.py` | 生成审定材料 |

## 所据电子本

| 简称 | 文献 | 来源（版本） |
|---|---|---|
| SR | 宗喀巴《密宗道次第广论》（sngags rim chen mo），全集第 3 函（ga） | OpenPecha `P60DBA47B`（github.com/OpenPecha-Data/p60dba47b，提交 5f897aa） |
| RL | 宗喀巴《五次第明灯》（rim lnga rab tu gsal ba'i sgron me），全集第 7 函（ja） | 同上 |
| D | 德格版甘珠尔、丹珠尔（引作 Toh 号、函、叶、行） | Esukhia `derge-kangyur`（a582cf4）、`derge-tengyur`（1746531） |
| B0057、B0068 | 克主杰《密宗道次第论》、宗喀巴《密宗道次第广论》法尊汉译 | CBETA 电子佛典（引作册、号、页、栏、行） |
| PK 等 | 《五次第》等梵本 | GRETIL、DSBC 电子本（校本见 `程序/tools/build.py` 中 `SK` 表） |

电子本不随本卷分发，请自行取得。

## 复现

```bash
pip install pyyaml pyewts opencc openpyxl pypdf
# 藏文电子本置于同一目录下：
#   $TIB_CORPUS/openpecha-data/p60dba47b/
#   $TIB_CORPUS/esukhia/derge-kangyur/
#   $TIB_CORPUS/esukhia/derge-tengyur/
# 汉、梵电子本置于 程序/src/（文件名见 程序/tools/build.py）
export TIB_CORPUS=/path/to/corpus
cd 程序/deep
python3 build_deep.py        # 核对全部引文；任何一处不符即报错
python3 render_deep.py       # 生成 out/deep.html、terms.csv、terms.skos.ttl
node ../tools/pdf.js $PWD/out/deep.html $PWD/out/deep.pdf   # 需 Playwright 与 Noto 字体
python3 review_kit.py        # 生成 out/审定材料.xlsx
```

通检与回取原文：

```bash
python3 tib.py count RL 'སྒྱུ་ལུས'          # 词形出现次数
python3 tib.py kwic  RL 'དཔེའི་འོད་གསལ' 20   # 上下文
python3 tib.py verify SR '<藏文引文>'          # 核对引文并给出叶行
```

藏文比对前统一作 Unicode NFD 规范化，去除校勘标记与空白，单、双垂符并视为音节点；所显示之引文为电子本原文。

## 审定

1. 两位审稿人各用一张盲审表，逐项判“同意／部分同意／不同意”，互不相见。
2. “一致率计算”表自动给出百分比一致率与 Cohen κ；通过标准为 κ ≥ 0.60，且凡“不同意”者逐项有书面处理。
3. “辩经质询题”交辩经者实际质询，答辩不能成立者，条目须修订。
4. 另请专研密集文献之学者匿名审读全卷。

## 尚未完成者

- 后期教本（央金嘎威洛哲、阿旺班丹等）之原文未得电子本，相关处注“待补”。
- 未与《五次第》Mimaki–Tomabechi 校本（1994）、《密集续》Matsunaga 校本（1978）逐字对勘；梵文引文据 GRETIL、DSBC 电子本。
- 上述审定尚未进行。
