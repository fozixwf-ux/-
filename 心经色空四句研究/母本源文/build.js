// 由标记文本生成 Word：node build.js 源文件 输出.docx
// 排版约定（中文学术期刊通行规范）：
//   正文　宋体／Times New Roman 小四（12 pt），1.5 倍行距，首行缩进二字
//   独立引文　楷体／Times New Roman 五号（10.5 pt），左右各缩进二字，引文组前后各空一行
//   脚注　宋体／Times New Roman 小五（9 pt）
//   标题　依 ISO 2145 十进制编号；一级黑体四号，二级黑体小四
//   表格　三线表：顶、底线 1.5 磅，栏目线 0.75 磅；表题在上（黑体五号），表注在下（小五）
// 中西文分字体：汉字及全角标点用中文字体，拉丁字母（含梵文转写附加符号）及其相邻标点用 Times New Roman。
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, FootnoteReferenceRun, AlignmentType,
  HeadingLevel, Table, TableRow, TableCell, WidthType, BorderStyle, Footer,
  PageNumber, VerticalAlign, Tab, TabStopType,
} = require('docx');

const [, , SRC = 'paper.txt', OUT = 'out.docx'] = process.argv;
const lines = fs.readFileSync(SRC, 'utf8').split(/\r?\n/);

const LATIN = 'Times New Roman';
const FONTS = { song: 'SimSun', kai: 'KaiTi', hei: 'SimHei' };

// ---------- 中西文分段 ----------
const isCJK = (ch) => /[⺀-⿿　-〿㐀-䶿一-鿿豈-﫿︰-﹏＀-￯《》〈〉「」『』【】、。，；：？！（）]/.test(ch);
const isLatin = (ch) => /[A-Za-z0-9À-ɏḀ-ỿ̀-ͯ]/.test(ch);
function splitScript(text) {
  const chars = [...text];
  const base = chars.map((c) => (isCJK(c) ? 'C' : isLatin(c) ? 'L' : 'N'));
  // 中性字符（空格、西文标点、弯引号、连接号等）：相邻任一侧为汉字即随中文，否则随西文
  const cls = base.map((b, i) => {
    if (b !== 'N') return b;
    let prev = null, next = null;
    for (let j = i - 1; j >= 0; j--) if (base[j] !== 'N') { prev = base[j]; break; }
    for (let j = i + 1; j < chars.length; j++) if (base[j] !== 'N') { next = base[j]; break; }
    return prev === 'C' || next === 'C' ? 'C' : 'L';
  });
  const out = [];
  let cur = '', curC = null;
  chars.forEach((c, i) => {
    const k = cls[i];
    if (k !== curC && cur) { out.push([cur, curC]); cur = ''; }
    curC = k; cur += c;
  });
  if (cur) out.push([cur, curC]);
  return out;
}
const fontFor = (script, cjk) => (script === 'C'
  ? { ascii: LATIN, hAnsi: LATIN, cs: LATIN, eastAsia: cjk }
  : { ascii: LATIN, hAnsi: LATIN, cs: LATIN, eastAsia: LATIN });

// ---------- 行内：*斜体*、**粗体**、{{fn:脚注}} ----------
const footnotes = {};
let fnCount = 0;
function runs(text, o = {}) {
  const cjk = o.cjk || FONTS.song;
  const size = o.size || 24;
  const out = [];
  const pushText = (t, extra = {}) => {
    if (!t) return;
    for (const [seg, sc] of splitScript(t)) {
      out.push(new TextRun({ text: seg, font: fontFor(sc, cjk), size, bold: o.bold || extra.bold, italics: extra.italics }));
    }
  };
  const re = /\{\{fn:([\s\S]*?)\}\}|\*\*([^*]+)\*\*|\*([^*]+)\*/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    pushText(text.slice(last, m.index));
    if (m[1] !== undefined) {
      if (o.noFootnote) throw new Error('nested footnote: ' + text);
      fnCount += 1;
      footnotes[fnCount] = {
        children: [new Paragraph({
          spacing: { line: 240, after: 40 },
          alignment: AlignmentType.JUSTIFIED,
          children: runs(m[1].trim(), { size: 18, noFootnote: true }),
        })],
      };
      out.push(new FootnoteReferenceRun(fnCount));
    } else if (m[2] !== undefined) {
      pushText(m[2], { bold: true });
    } else {
      pushText(m[3], { italics: true });
    }
    last = re.lastIndex;
  }
  pushText(text.slice(last));
  return out;
}

const children = [];
const CONTENT_WIDTH = 9026; // A4 减去左右各 2.54 cm

// ---------- 正文段落 ----------
const body = (text, opt = {}) => new Paragraph({
  spacing: { line: 360, before: 0, after: 0 },
  indent: { firstLine: opt.noIndent ? 0 : 480 },
  alignment: AlignmentType.JUSTIFIED,
  children: runs(text),
});

// ---------- 独立引文：> 原文，>> 译文；连续行为一组，组前后各空一行 ----------
let quoteGroup = [];
function flushQuotes() {
  if (!quoteGroup.length) return;
  const n = quoteGroup.length;
  quoteGroup.forEach(([kind, text], i) => {
    const prevKind = i > 0 ? quoteGroup[i - 1][0] : null;
    children.push(new Paragraph({
      spacing: {
        line: 300,
        before: i === 0 ? 240 : (kind === 'tr' && prevKind === 'src' ? 120 : 0),
        after: i === n - 1 ? 240 : 0,
      },
      indent: { left: 480, right: 480 },
      alignment: kind === 'verse' || !/[\u4E00-\u9FFF]{4}/.test(text) ? AlignmentType.LEFT : AlignmentType.JUSTIFIED,
      children: runs(text, { cjk: FONTS.kai, size: 21 }),
    }));
  });
  quoteGroup = [];
}

// ---------- 三线表 ----------
let table = null, tableWidths = null, tableAlign = null;
const RULE_THICK = { style: BorderStyle.SINGLE, size: 12, color: '000000' }; // 1.5 磅
const RULE_THIN = { style: BorderStyle.SINGLE, size: 6, color: '000000' };   // 0.75 磅
const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
function flushTable() {
  const rows = table;
  table = null;
  const ncol = rows[0].length;
  const widths = tableWidths ? tableWidths.slice() : Array.from({ length: ncol }, () => Math.floor(CONTENT_WIDTH / ncol));
  const sum = widths.reduce((a, b) => a + b, 0);
  widths[widths.length - 1] += CONTENT_WIDTH - sum;
  children.push(new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    alignment: AlignmentType.CENTER,
    rows: rows.map((cells, r) => new TableRow({
      tableHeader: r === 0,
      cantSplit: true,
      children: cells.map((c, i) => new TableCell({
        width: { size: widths[i], type: WidthType.DXA },
        verticalAlign: VerticalAlign.CENTER,
        borders: {
          top: r === 0 ? RULE_THICK : r === 1 ? RULE_THIN : NONE,
          bottom: r === 0 ? RULE_THIN : r === rows.length - 1 ? RULE_THICK : NONE,
          left: NONE, right: NONE,
        },
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({
          spacing: { line: 260 },
          alignment: r === 0 || (tableAlign && tableAlign[i] === 'c') ? AlignmentType.CENTER : AlignmentType.LEFT,
          children: runs(c, { size: 21, cjk: r === 0 ? FONTS.hei : FONTS.song }),
        })],
      })),
    })),
  }));
  tableWidths = null; tableAlign = null;
}

// ---------- 逐行解析 ----------
for (const raw of lines) {
  const line = raw.trimEnd();
  if (table) {
    if (line === '@endtable') { flushTable(); continue; }
    if (line.startsWith('|')) { table.push(line.replace(/^\||\|$/g, '').split('|').map((s) => s.trim())); continue; }
  }
  const q = line.match(/^(>>|>\||>) (.*)$/);
  if (q) {
    quoteGroup.push([q[1] === '>>' ? 'tr' : q[1] === '>|' ? 'verse' : 'src', q[2]]);
    continue;
  }
  flushQuotes();
  if (!line) continue;
  if (line.startsWith('@table')) {
    const w = line.match(/^@table\s+([\d,]+)(?:\s+([lc]+))?$/);
    tableWidths = w ? w[1].split(',').map(Number) : null;
    tableAlign = w && w[2] ? w[2].split('') : null;
    table = [];
    continue;
  }
  const cmd = line.match(/^@(\w+)\s?(.*)$/);
  if (cmd) {
    const [, k, v] = cmd;
    const P = (opts) => children.push(new Paragraph(opts));
    if (k === 'title') P({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 120 }, children: runs(v, { cjk: FONTS.hei, size: 36 }) });
    else if (k === 'subtitle') P({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: runs(v, { cjk: FONTS.kai, size: 30 }) });
    else if (k === 'entitle') P({ alignment: AlignmentType.CENTER, spacing: { before: 360, after: 200 }, children: runs(v, { size: 26, bold: true }) });
    else if (k === 'abs' || k === 'kw') {
      // @abs 标签｜内容：标签黑体（西文粗体），内容楷体五号
      const [label, text] = v.split('｜');
      const latin = /^[A-Za-z]/.test(label);
      P({
        spacing: { line: 300, before: k === 'abs' ? 120 : 80, after: 80 },
        alignment: AlignmentType.JUSTIFIED,
        children: [...runs(label, { cjk: FONTS.hei, size: 21, bold: latin }), ...runs(text, { cjk: FONTS.kai, size: 21 })],
      });
    }
    else if (k === 'h1') P({ heading: HeadingLevel.HEADING_1, children: runs(v, { cjk: FONTS.hei, size: 28 }) });
    else if (k === 'h2') P({ heading: HeadingLevel.HEADING_2, children: runs(v, { cjk: FONTS.hei, size: 24 }) });
    else if (k === 'hu') P({ heading: HeadingLevel.HEADING_1, children: runs(v, { cjk: FONTS.hei, size: 28 }) });
    else if (k === 'label') P({ spacing: { before: 200, after: 80 }, keepNext: true, children: runs(v, { cjk: FONTS.hei, size: 22 }) });
    else if (k === 'caption') P({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 80 }, keepNext: true, children: runs(v, { cjk: FONTS.hei, size: 21 }) });
    else if (k === 'tnote') P({ spacing: { line: 260, before: 60, after: 240 }, alignment: AlignmentType.JUSTIFIED, children: runs(v, { size: 18 }) });
    else if (k === 'ref') P({ spacing: { line: 300, after: 60 }, indent: { left: 420, hanging: 420 }, alignment: AlignmentType.LEFT, children: runs(v, { size: 21 }) });
    else if (k === 'abbr') {
      // 略语表：略语与说明之间以制表位对齐（悬挂缩进 1260 twips）
      const sp = v.indexOf('　');
      const label = sp > 0 ? v.slice(0, sp) : v, text = sp > 0 ? v.slice(sp + 1) : '';
      P({
        spacing: { line: 300, after: 60 }, indent: { left: 1260, hanging: 1260 },
        tabStops: [{ type: TabStopType.LEFT, position: 1260 }], alignment: AlignmentType.LEFT,
        children: [...runs(label, { size: 21 }), new TextRun({ children: [new Tab()], size: 21 }), ...runs(text, { size: 21 })],
      });
    }
    else if (k === 'noindent') P({ spacing: { line: 300, before: 80 }, alignment: AlignmentType.JUSTIFIED, children: runs(v, { size: 21 }) });
    else if (k === 'abstract') P({ spacing: { line: 320 }, indent: { firstLine: 420 }, alignment: AlignmentType.JUSTIFIED, children: runs(v, { size: 21 }) });
    else if (k === 'prop') P({ spacing: { line: 340, before: 40, after: 40 }, indent: { left: 480 }, alignment: AlignmentType.JUSTIFIED, children: runs(v, { cjk: FONTS.kai }) });
    else throw new Error('unknown command @' + k);
    continue;
  }
  children.push(body(line));
}
flushQuotes();
if (table) flushTable();

const doc = new Document({
  creator: '',
  title: process.env.DOC_TITLE || '空不在色外——“空即是色”的成立关系与无遮的界限',
  styles: {
    default: {
      document: { run: { font: { ascii: LATIN, hAnsi: LATIN, cs: LATIN, eastAsia: FONTS.song }, size: 24 } },
      heading1: {
        run: { font: { ascii: LATIN, hAnsi: LATIN, eastAsia: FONTS.hei }, size: 28, bold: false, color: '000000' },
        paragraph: { spacing: { before: 480, after: 240, line: 360 }, keepNext: true, outlineLevel: 0 },
      },
      heading2: {
        run: { font: { ascii: LATIN, hAnsi: LATIN, eastAsia: FONTS.hei }, size: 24, bold: false, italics: false, color: '000000' },
        paragraph: { spacing: { before: 240, after: 120, line: 360 }, keepNext: true, outlineLevel: 1 },
      },
    },
  },
  footnotes,
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: {
      default: new Footer({
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: LATIN, size: 18 })] })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log('wrote', OUT, 'footnotes:', fnCount);
});
