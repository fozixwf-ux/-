# -*- coding: utf-8 -*-
"""Render out/entries.json into a print-ready HTML (out/glossary.html).
Usage: render.py [pagemap.json]   (second pass inserts page numbers into the TOC)"""
import json, re, sys, os, html, unicodedata
import pyewts, opencc
from pypinyin import lazy_pinyin

BASE = os.path.dirname(os.path.abspath(__file__)) + '/../'
conv = pyewts.pyewts()
t2s = opencc.OpenCC('t2s')
FIX = {'干闼婆': '乾闼婆', '乾闼婆': '乾闼婆', '于阗': '于阗'}

def S(x):
    """traditional -> simplified for editorial text (never for quotations)."""
    y = t2s.convert(x)
    for a, b in FIX.items(): y = y.replace(a, b)
    return y

def esc(x): return html.escape(x, quote=False)

def iast(x):
    return unicodedata.normalize('NFC', x).replace('ṁ', 'ṃ')

def skfmt(x):
    x = iast(x)
    x = re.sub(r'\s*(\|\||//)\s*', ' ‖ ', x)
    x = re.sub(r'\s*[|/]\s*', ' | ', x)
    x = re.sub(r'\s*…\s*', ' … ', x)
    return re.sub(r'\s+', ' ', x).strip(' |‖')

def bo_uni(w):
    parts = re.split(r'(\s*[/:,;]\s*)', w)
    out = []
    for p in parts:
        if not p.strip(): continue
        if re.fullmatch(r'\s*[/:,;]\s*', p):
            out.append({'/': ' / ', ':': '：', ',': '，', ';': '；'}[p.strip()])
        else:
            out.append(conv.toUnicode(p.strip()))
    return ''.join(out)

def inline(x):
    """editorial text: simplified, escape, italicise IAST words in （ ）? keep simple."""
    return esc(S(x))

sections = json.load(open(BASE + 'out/entries.json', encoding='utf8'))
pagemap = json.load(open(sys.argv[1], encoding='utf8')) if len(sys.argv) > 1 else {}
byid = {e['id']: e for s in sections for e in s['entries']}

def pg(key):
    return str(pagemap.get(key, '')) if pagemap else '000'

# ---------------- body ----------------
body = []
for s in sections:
    sid = 'sec-' + s['num']
    body.append(f'<section class="part" id="{sid}"><span class="marker">@@{sid}@@</span><h2><span class="pn">第{["","一","二","三","四","五","六","七","八","九","十","十一"][int(s["num"])]}部</span>{inline(s["title"])}</h2>')
    if s['intro']: body.append(f'<p class="intro">{inline(s["intro"])}</p>')
    for e in s['entries']:
        eid = 'e-' + e['id']
        h = [f'<article class="entry" id="{eid}">']
        h.append(f'<div class="hd"><span class="no">{e["no"]}</span><span class="zh">{inline(e["zh"])}</span>'
                 f'<span class="bo" lang="bo">{esc(bo_uni(re.sub(r"\s*\([^)]*\)", "", e["bo"]).split(":")[0]))}</span></div>')
        eq = [f'<span class="k">藏</span><span class="wy">{esc(e["bo"])}</span>']
        if e.get('sa') and e['sa'].strip() not in ('—', '-'):
            eq.append(f'<span class="k">梵</span><span class="sk">{esc(iast(e["sa"]))}</span>')
        eq.append(f'<span class="k">英</span><span class="en">{esc(e["en"])}</span>')
        h.append('<div class="eq">' + ''.join(f'<span class="cell">{x}</span>' if False else x for x in eq) + '</div>')
        if e.get('alt'): h.append(f'<div class="alt"><span class="lab">异名</span>{inline(e["alt"])}</div>')
        h.append(f'<p class="def"><span class="lab">定义</span>{inline(e["def"])}</p>')
        for k, x in enumerate(e.get('exp', [])):
            h.append(f'<p class="exp">{"<span class=lab>释义</span>" if k == 0 else ""}{inline(x)}</p>')
        if e['q_out'] or e['qs_out']:
            h.append('<div class="src"><div class="lab2">原典引文</div>')
            for q, loc in e['q_out']:
                h.append(f'<blockquote lang="zh-Hant"><span class="qt">{esc(q)}</span><cite>——{esc(S(loc))}</cite></blockquote>')
            for q, loc in e['qs_out']:
                h.append(f'<blockquote class="skq"><span class="qt">{esc(skfmt(q))}</span><cite>—— {esc(S(loc))}</cite></blockquote>')
            h.append('</div>')
        for x in e.get('tr', []):
            h.append(f'<p class="tr"><span class="lab">译注</span>{inline(x)}</p>')
        for x in e.get('ref', []):
            h.append(f'<p class="ref"><span class="lab">参考</span>{inline(x)}</p>')
        sees = [t.strip() for t in e.get('see', '').split(',') if t.strip()]
        if sees:
            links = '；'.join(f'<a href="#e-{t}">{byid[t]["no"]} {inline(byid[t]["zh"])}</a>' for t in sees)
            h.append(f'<p class="see"><span class="lab">参见</span>{links}</p>')
        h.append('</article>')
        body.append(''.join(h))
    body.append('</section>')

# ---------------- indices ----------------
def wylie_key(w): return re.sub(r"[^a-z ]", '', w.lower())
SKORD = 'a ā i ī u ū ṛ ṝ ḷ e ai o au ṃ ḥ k kh g gh ṅ c ch j jh ñ ṭ ṭh ḍ ḍh ṇ t th d dh n p ph b bh m y r l v ś ṣ s h'.split()
def sk_key(w):
    w = iast(w).lower(); key = []; i = 0
    while i < len(w):
        for L in (2, 1):
            seg = w[i:i+L]
            if seg in SKORD and (L == 2 or True):
                key.append(SKORD.index(seg) + 1); i += L; break
        else:
            i += 1
    return key

idx_bo, idx_sa, idx_en, idx_zh = [], [], [], []
for s in sections:
    for e in s['entries']:
        ref = (e['no'], e['id'])
        bo_clean = re.sub(r'\s*\([^)]*\)', '', e['bo'])
        for w in re.split(r'\s*/\s*', bo_clean):
            w = w.split(':')[0].strip()
            if w: idx_bo.append((w, ref))
        if e.get('sa') and e['sa'].strip() not in ('—', '-'):
            sa_clean = re.sub(r'\s*\([^)]*\)', '', e['sa'])
            sa_clean = re.sub(r'^[^:]*:\s*', '', sa_clean) if ':' in sa_clean else sa_clean
            for w in re.split(r'\s*[;/,]\s*', sa_clean):
                w = w.strip()
                if w and len(w) < 40: idx_sa.append((iast(w), ref))
        for w in re.split(r'\s*;\s*|\s+/\s+', e['en']):
            w = w.strip()
            if w: idx_en.append((w, ref))
        idx_zh.append((S(e['zh']), ref))
        for w in re.split(r'[；;]', e.get('alt', '')):
            w = w.strip()
            if not w or '：' in w or ':' in w: continue
            subs = [re.sub(r'（.*?）', '', x).strip() for x in w.split('、')] if '、' in w else [w]
            if '、' in w and all(0 < len(x) <= 8 for x in subs):
                for x in subs: idx_zh.append((S(x), ref))
            elif len(w) <= 16 and '、' not in w:
                idx_zh.append((S(re.sub(r'（.*?）', '', w)), ref))

def idx_html(title, items, key, cls=''):
    seen = set(); rows = []
    for w, (no, eid) in sorted(items, key=lambda x: key(x[0])):
        if (w, no) in seen: continue
        seen.add((w, no))
        extra = f' <span class="ixbo" lang="bo">{esc(conv.toUnicode(w))}</span>' if cls == 'wyx' else ''
        rows.append(f'<div class="ix"><a href="#e-{eid}">{no}</a><span class="w {cls}">{esc(w)}{extra}</span></div>')
    return f'<section class="index ix-{cls}"><span class="marker">@@ix-{cls}@@</span><h2 id="ix-{cls or "zh"}">{title}</h2><div class="cols">{"".join(rows)}</div></section>'

def zh_key(w): return ' '.join(lazy_pinyin(w))
indices = [
    idx_html('汉文索引（依汉语拼音）', idx_zh, zh_key, 'zhx'),
    idx_html('藏文索引（依威利转写）', [(w, r) for w, r in idx_bo], wylie_key, 'wyx'),
    idx_html('梵文索引（依梵文字母顺序）', idx_sa, sk_key, 'skx'),
    idx_html('英文索引', idx_en, lambda w: w.lower(), 'enx'),
]

# ---------------- front & back matter ----------------
N = sum(len(s['entries']) for s in sections)
NQ = sum(len(e['q_out']) for s in sections for e in s['entries'])
NS = sum(len(e['qs_out']) for s in sections for e in s['entries'])

toc = ['<nav class="toc"><h2 id="toc">目录</h2>']
for key, label in [('fm-guide', '凡例'), ('fm-abbr', '引用文献与版本')]:
    toc.append(f'<div class="t1"><a href="#{key}">{label}</a><span class="pg">{pg(key)}</span></div>')
for s in sections:
    sid = 'sec-' + s['num']
    toc.append(f'<div class="t1"><a href="#{sid}">第{["","一","二","三","四","五","六","七","八","九","十","十一"][int(s["num"])]}部　{inline(s["title"])}</a><span class="pg">{pg(sid)}</span></div>')
    toc.append('<div class="t2">' + '　'.join(f'<a href="#e-{e["id"]}">{e["no"]} {inline(e["zh"])}</a>' for e in s['entries']) + '</div>')
for key, label in [('bib', '参考书目'), ('ix-zhx', '汉文索引'), ('ix-wyx', '藏文索引'), ('ix-skx', '梵文索引'), ('ix-enx', '英文索引')]:
    toc.append(f'<div class="t1"><a href="#{key}">{label}</a><span class="pg">{pg(key)}</span></div>')
toc.append('</nav>')

front = open(BASE + 'tools/front.html', encoding='utf8').read()
front = front.replace('id="fm-guide">', 'id="fm-guide"><span class="marker">@@fm-guide@@</span>').replace('id="fm-abbr">', 'id="fm-abbr"><span class="marker">@@fm-abbr@@</span>')
front = front.replace('{{N}}', str(N)).replace('{{NQ}}', str(NQ)).replace('{{NS}}', str(NS))
back = open(BASE + 'tools/back.html', encoding='utf8').read().replace('id="bib">', 'id="bib"><span class="marker">@@bib@@</span>')
css = open(BASE + 'tools/style.css', encoding='utf8').read()

doc = f'''<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8">
<title>格鲁派密续名相辞汇</title><style>{css}</style></head><body>
{front}
{''.join(toc)}
<main>{''.join(body)}</main>
{back}
{''.join(indices)}
</body></html>'''
open(BASE + 'out/glossary.html', 'w', encoding='utf8').write(doc)
print('html written', len(doc))
