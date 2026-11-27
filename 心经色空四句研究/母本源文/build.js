// 由 paper.txt 生成 Word 母本：node build.js paper.txt 输出.docx
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, FootnoteReferenceRun, AlignmentType,
  HeadingLevel, Table, TableRow, TableCell, WidthType, BorderStyle, Footer,
  PageNumber, ShadingType,
} = require('docx');

const [, , SRC = 'paper.txt', OUT = 'out.docx'] = process.argv;
const lines = fs.readFileSync(SRC, 'utf8').split(/\r?\n/);

const LATIN = 'Times New Roman';
const font = (cjk) => ({ ascii: LATIN, hAnsi: LATIN, cs: LATIN, eastAsia: cjk });
const BODY = font('SimSun');
const QUOTE = font('KaiTi');
const HEAD = font('SimHei');

const footnotes = {};
let fnCount = 0;

// 行内解析：*斜体* 与 {{fn:脚注}}
function runs(text, opts = {}) {
  const out = [];
  const re = /\{\{fn:([\s\S]*?)\}\}|\*([^*]+)\*/g;
  let last = 0, m;
  const push = (t, extra = {}) => {
    if (t) out.push(new TextRun({ text: t, font: opts.font || BODY, size: opts.size || 24, bold: opts.bold, ...extra }));
  };
  while ((m = re.exec(text)) !== null) {
    push(text.slice(last, m.index));
    if (m[1] !== undefined) {
      if (opts.noFootnote) throw new Error('nested footnote: ' + text);
      fnCount += 1;
      footnotes[fnCount] = {
        children: [new Paragraph({
          spacing: { line: 260 },
          children: runs(m[1].trim(), { size: 18, noFootnote: true }),
        })],
      };
      out.push(new FootnoteReferenceRun(fnCount));
    } else {
      push(m[2], { italics: true });
    }
    last = re.lastIndex;
  }
  push(text.slice(last));
  return out;
}

const body = (text) => new Paragraph({
  spacing: { line: 360, before: 0, after: 0 },
  indent: { firstLine: 480 },
  alignment: AlignmentType.JUSTIFIED,
  children: runs(text),
});

const children = [];
let table = null;
const CONTENT_WIDTH = 9026; // A4 减去左右各 1 英寸

let tableWidths = null;
function flushTable() {
  const rows = table;
  table = null;
  const ncol = rows[0].length;
  const widths = tableWidths
    ? tableWidths.slice()
    : ncol === 5 && rows[0][0] === '组'
    ? [700, 2150, 2650, 1500, 2026]
    : Array.from({ length: ncol }, (_, i) => (i === 0 ? 2226 : Math.floor((CONTENT_WIDTH - 2226) / (ncol - 1))));
  tableWidths = null;
  const sum = widths.reduce((a, b) => a + b, 0);
  widths[widths.length - 1] += CONTENT_WIDTH - sum;
  const border = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
  const none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
  children.push(new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((cells, r) => new TableRow({
      tableHeader: r === 0,
      children: cells.map((c, i) => new TableCell({
        width: { size: widths[i], type: WidthType.DXA },
        borders: {
          top: r <= 1 ? border : none,
          bottom: r === 0 || r === rows.length - 1 ? border : none,
          left: none, right: none,
        },
        shading: r === 0 ? { type: ShadingType.CLEAR, color: 'auto', fill: 'F2F2F2' } : undefined,
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        children: [new Paragraph({
          spacing: { line: 280 },
          children: runs(c, { size: 19, font: r === 0 ? HEAD : BODY }),
        })],
      })),
    })),
  }));
  children.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
}

for (const raw of lines) {
  const line = raw.trimEnd();
  if (table) {
    if (line === '@endtable') { flushTable(); continue; }
    if (line.startsWith('|')) {
      table.push(line.replace(/^\||\|$/g, '').split('|').map((s) => s.trim()));
      continue;
    }
  }
  if (!line) continue;
  if (line.startsWith('@table')) {
    const w = line.match(/^@table\s+([\d,]+)$/);
    tableWidths = w ? w[1].split(',').map(Number) : null;
    table = [];
    continue;
  }
  const cmd = line.match(/^@(\w+)\s?(.*)$/);
  if (cmd) {
    const [, k, v] = cmd;
    if (k === 'title') children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 120 }, children: runs(v, { font: HEAD, size: 40 }) }));
    else if (k === 'subtitle') children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: runs(v, { font: HEAD, size: 28 }) }));
    else if (k === 'entitle') children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: runs(v, { size: 22 }) }));
    else if (k === 'label') children.push(new Paragraph({ spacing: { before: 200, after: 80 }, keepNext: true, children: runs(v, { font: HEAD, size: 22 }) }));
    else if (k === 'abstract') children.push(new Paragraph({ spacing: { line: 320 }, indent: { firstLine: 420 }, alignment: AlignmentType.JUSTIFIED, children: runs(v, { size: 21 }) }));
    else if (k === 'ref') children.push(new Paragraph({ spacing: { line: 300, after: 40 }, indent: { left: 420, hanging: 420 }, alignment: AlignmentType.LEFT, children: runs(v, { size: 21 }) }));
    else if (k === 'noindent') children.push(new Paragraph({ spacing: { line: 300, before: 80 }, children: runs(v, { size: 21 }) }));
    else if (k === 'h1') children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs(v, { font: HEAD, size: 28 }) }));
    else if (k === 'prop') children.push(new Paragraph({ spacing: { line: 340, before: 40, after: 40 }, indent: { left: 480 }, alignment: AlignmentType.JUSTIFIED, children: runs(v, { font: QUOTE }) }));
    else throw new Error('unknown command @' + k);
    continue;
  }
  if (line.startsWith('> ')) {
    children.push(new Paragraph({
      spacing: { line: 320, before: 100, after: 100 },
      indent: { left: 480, right: 240 },
      alignment: AlignmentType.JUSTIFIED,
      children: runs(line.slice(2), { font: QUOTE, size: 21 }),
    }));
    continue;
  }
  children.push(body(line));
}
if (table) flushTable();

const doc = new Document({
  creator: '',
  title: process.env.DOC_TITLE || '空不在色外——“空即是色”的成立关系与无遮的界限',
  styles: {
    default: {
      document: { run: { font: BODY, size: 24 } },
      heading1: {
        run: { font: HEAD, size: 28, bold: false },
        paragraph: { spacing: { before: 360, after: 200 }, keepNext: true },
      },
    },
  },
  footnotes,
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: {
      default: new Footer({
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: BODY, size: 18 })] })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log('wrote', OUT, 'footnotes:', fnCount);
});
