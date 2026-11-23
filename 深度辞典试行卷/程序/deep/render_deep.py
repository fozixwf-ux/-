"""Render deep/out/deep.json into print HTML (then PDF via tools/pdf.js) and export JSON/CSV/SKOS."""
import json, os, re, csv, html, sys
import pyewts, opencc
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..') + '/'
t2s = opencc.OpenCC('t2s')
conv = pyewts.pyewts()
S = lambda x: t2s.convert(x or '')
esc = html.escape
def bo(w):
    first = re.split(r'\s*/\s*', w)[0]
    return conv.toUnicode(first)

E = json.load(open(os.path.join(HERE, 'out', 'deep.json'), encoding='utf8'))
byid = {e['id']: e for e in E}
for k, e in enumerate(E, 1): e['no'] = f'{k:02d}'
LAYER_ORDER = ['印度原典', '宗喀巴', '克主杰', '後期教本', '現代研究']
LAYER_TAG = {'印度原典': '原典', '宗喀巴': '宗喀巴', '克主杰': '克主杰', '後期教本': '後期教本', '現代研究': '現代', '編者': '編者'}

def expand(b):
    b = re.sub(r'RL\s*', '《五次第明燈》葉', b); b = re.sub(r'SR\s*', '《廣論》葉', b)
    return b
def tag(basis):
    return f'<span class="basis">〔{esc(S(expand(basis)))}〕</span>' if basis else ''

def entry(e):
    h = [f'<article class="dentry" id="d-{e["id"]}">']
    kb = '<span class="kb">考辨</span>' if e.get('kind') == '考辨' else ''
    h.append(f'<div class="dhd"><span class="no">{e["no"]}</span>{kb}<span class="zh">{esc(S(e["zh"]))}</span><span class="bo" lang="bo">{esc(bo(e["wylie"]))}</span></div>')
    sa = e.get('sa', {})
    eq = [f'<span class="k">藏</span><span class="wy">{esc(e["wylie"])}</span>']
    if sa.get('form') and sa['form'] != '—':
        eq.append(f'<span class="k">梵</span><span class="sk">{esc(sa["form"])}</span><span class="st">{esc(S(sa.get("status","")))}</span>')
    else:
        eq.append(f'<span class="k">梵</span><span class="st">{esc(S(sa.get("status","無")))}</span>')
    eq.append(f'<span class="k">英</span><span class="en">{esc("; ".join(e.get("en", [])))}</span>')
    h.append('<div class="eq">' + ''.join(eq) + '</div>')
    if e.get('zh_alt'): h.append(f'<div class="alt"><span class="lab">异名</span>{esc(S("；".join(e["zh_alt"])))}</div>')
    # concordance
    if e.get('concord'):
        rows = ''.join(f'<tr><td lang="bo">{esc(c["term"])}</td><td>{c["SR"]}</td><td>{c["RL"]}</td></tr>' for c in e['concord'])
        h.append(f'<table class="conc"><thead><tr><th>通检词形</th><th>《广论》</th><th>《五次第明灯》</th></tr></thead><tbody>{rows}</tbody></table>')
    x = e.get('xing', {})
    h.append(f'<p class="def"><span class="lab">{"题旨" if e.get("kind")=="考辨" else "性相"}</span>{esc(S(x.get("text","")))}{tag(x.get("basis"))}</p>')
    if e.get('dbye'):
        rows = ''.join(f'<tr><td class="szh">{esc(S(d["name"]))}</td><td>{esc(S(d.get("note","")))}</td><td class="bs">{esc(S(expand(d.get("basis",""))))}</td></tr>' for d in e['dbye'])
        h.append(f'<table class="subt"><thead><tr><th>分类</th><th>说明</th><th>依据</th></tr></thead><tbody>{rows}</tbody></table>')
    for m in e.get('mtshams', []):
        h.append(f'<p class="mt"><span class="lab">界限</span>{esc(S(m["text"]))}{tag(m.get("basis"))}</p>')
    # sources by layer
    h.append('<div class="src"><div class="lab2">原典分层</div>')
    for layer in LAYER_ORDER:
        Ls = [L for L in e.get('layers', []) if L['layer'] == layer]
        if not Ls: continue
        h.append(f'<div class="layer"><span class="ltag">{esc(S(LAYER_TAG[layer]))}</span>')
        for L in Ls:
            if L.get('sa_cite'):
                h.append(f'<blockquote class="skq"><span class="qt">{esc(L["sa"])}</span><cite>—— {esc(S(L["sa_cite"]))}</cite></blockquote>')
            if L.get('bo_raw'):
                h.append(f'<blockquote class="boq"><span class="qt" lang="bo">{esc(L["bo_raw"])}</span><cite>—— {esc(S(L["bo_cite"]))}</cite></blockquote>')
            if L.get('zh_q'):
                h.append(f'<blockquote lang="zh-Hant"><span class="qt">{esc(L["zh_q"])}</span><cite>—— {esc(S(L["zh_cite"]))}</cite></blockquote>')
            if L.get('zh_tr'):
                h.append(f'<p class="trn"><span class="lab3">编者译</span>{esc(S(L["zh_tr"]))}</p>')
        h.append('</div>')
    h.append('</div>')
    for d in e.get('disputes', []):
        views = ''.join(f'<li><b>{esc(S(v["who"]))}</b>：{esc(S(v["view"]))}{tag(v.get("basis"))}</li>' for v in d.get('views', []))
        h.append(f'<div class="disp"><span class="lab">诤论</span><b>{esc(S(d["issue"]))}</b><ul>{views}</ul><p class="self"><span class="lab3">自宗</span>{esc(S(d.get("self","")))}</p></div>')
    if e.get('history'): h.append(f'<p class="hist"><span class="lab">语义史</span>{esc(S(e["history"]))}</p>')
    tr = e.get('trans');
    for t in ([tr] if isinstance(tr, str) else (tr or [])):
        h.append(f'<p class="tr"><span class="lab">译名</span>{esc(S(t))}</p>')
    for o in e.get('open', []):
        h.append(f'<p class="open"><span class="lab">待补</span>{esc(S(o))}</p>')
    if e.get('see'):
        links = '；'.join(f'<a href="#d-{i}">{byid[i]["no"]} {esc(S(byid[i]["zh"]))}</a>' for i in e['see'] if i in byid)
        h.append(f'<p class="see"><span class="lab">参见</span>{links}</p>')
    h.append('</article>')
    return ''.join(h)

nq = {k: sum(1 for e in E for L in e['layers'] if L.get(f) ) for k, f in [('bo', 'bo_cite'), ('zh', 'zh_cite'), ('sa', 'sa_cite')]}
front = open(os.path.join(HERE, 'front_deep.html'), encoding='utf8').read().replace('{{N_ENT}}', str(len(E))).replace('{{N_BO}}', str(nq['bo'])).replace('{{N_ZH}}', str(nq['zh'])).replace('{{N_SA}}', str(nq['sa']))
toc = ['<nav class="toc"><h2 id="toc">目录</h2>'] + [f'<div class="t3d"><a href="#d-{e["id"]}">{e["no"]}　{esc(S(e["zh"]))}</a></div>' for e in E] + ['</nav>']
css = open(BASE + 'tools/style.css', encoding='utf8').read() + open(os.path.join(HERE, 'deep.css'), encoding='utf8').read()
doc = f'''<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><title>格鲁派圆满次第核心名相深度辞典</title><style>{css}</style></head><body>
{front}{''.join(toc)}<main class="part">{''.join(entry(e) for e in E)}</main></body></html>'''
open(os.path.join(HERE, 'out', 'deep.html'), 'w', encoding='utf8').write(doc)

# ---------- exports ----------
with open(os.path.join(HERE, 'out', 'terms.csv'), 'w', encoding='utf8', newline='') as f:
    w = csv.writer(f)
    w.writerow(['編號', 'ID', '漢文', '藏文（威利）', '梵文', '梵文依據', '英譯', '性相', '性相依據', '《廣論》通檢', '《五次第明燈》通檢'])
    for e in E:
        c = e.get('concord', [{}])[0]
        w.writerow([e['no'], e['id'], e['zh'], e['wylie'], e['sa'].get('form', ''), e['sa'].get('status', ''), '; '.join(e.get('en', [])),
                    e['xing']['text'], e['xing'].get('basis', ''), c.get('SR', ''), c.get('RL', '')])
ttl = ['@prefix skos: <http://www.w3.org/2004/02/skos/core#> .', '@prefix gl: <urn:gelug-glossary:deep:> .', '',
       'gl:scheme a skos:ConceptScheme ; skos:prefLabel "格魯派圓滿次第核心名相"@zh-Hant .', '']
q = lambda s: '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
for e in E:
    lines = [f'gl:{e["id"]} a skos:Concept ; skos:inScheme gl:scheme ;',
             f'  skos:prefLabel {q(e["zh"])}@zh-Hant , {q(bo(e["wylie"]))}@bo , {q(e["wylie"])}@bo-Latn ;']
    if e['sa'].get('form') and e['sa']['form'] != '—': lines.append(f'  skos:altLabel {q(e["sa"]["form"])}@sa-Latn ;')
    for en in e.get('en', []): lines.append(f'  skos:altLabel {q(en)}@en ;')
    lines.append(f'  skos:definition {q(e["xing"]["text"])}@zh-Hant ;')
    for s2 in e.get('see', []): lines.append(f'  skos:related gl:{s2} ;')
    lines[-1] = lines[-1].rstrip(' ;') + ' .'
    ttl += lines + ['']
open(os.path.join(HERE, 'out', 'terms.skos.ttl'), 'w', encoding='utf8').write('\n'.join(ttl))
print('rendered', len(E), 'entries; quotes', nq)
