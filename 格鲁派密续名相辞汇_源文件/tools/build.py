# -*- coding: utf-8 -*-
"""Parse glossary entry files, verify every quotation against downloaded e-texts,
and emit a print-ready HTML file.

Entry format (one block per entry, blocks start with '=== id'):
  zh: 中文词头        alt: 异名（；分隔）
  bo: Wylie          sa: IAST          en: English
  def: 定义           exp: 释义（可多段，段间用 ¶）
  q:  WORK | quote（CBETA 引文，分段用 …… ）
  qs: KEY ref | sanskrit quote（梵本引文）
  ref: 延伸参考        tr: 译注        see: id, id
"""
import re, sys, os, json, bisect, html, unicodedata
import pyewts

BASE = os.path.dirname(os.path.abspath(__file__)) + '/../'
SRC = BASE + 'src/'
DATA = BASE + 'data/'
conv = pyewts.pyewts()

# ---------- CBETA sources ----------
CB = {
    'B0068': ('宗喀巴《密宗道次第廣論》', '法尊譯', 'B10', 68),
    'B0057': ('克主杰《密宗道次第論》', '法尊譯', 'B10', 57),
    'B0067': ('宗喀巴《菩提道次第廣論》', '法尊譯', 'B10', 67),
    'T0892': ('《佛說大悲空智金剛大教王儀軌經》（喜金剛本續）', '宋·法護譯', 'T18', 892),
    'T0885': ('《一切如來金剛三業最上祕密大教王經》（密集本續）', '宋·施護譯', 'T18', 885),
}
CN_NUM = '〇一二三四五六七八九'
def cn(n):
    n = int(n)
    if n <= 10: return '十' if n == 10 else CN_NUM[n]
    if n < 20: return '十' + (CN_NUM[n-10] if n > 10 else '')
    t, u = divmod(n, 10)
    return CN_NUM[t] + '十' + (CN_NUM[u] if u else '')

_cb_cache = {}
def cb_load(work):
    if work in _cb_cache: return _cb_cache[work]
    ids, offs, juans, txt = [], [], [], []
    pos = 0
    for l in open(SRC + work + '.txt', encoding='utf8'):
        a, b, c = l.rstrip('\n').split('\t')
        offs.append(pos); ids.append(a); juans.append(int(b[2:-1]))
        txt.append(c); pos += len(c)
    _cb_cache[work] = (''.join(txt), offs, ids, juans)
    return _cb_cache[work]

def lid_fmt(lid):
    m = re.search(r'_p0*(\d+)([abc])(\d+)$', lid)
    return m.group(1), m.group(2), int(m.group(3))

def cb_locate(work, quote):
    txt, offs, ids, juans = cb_load(work)
    segs = [s for s in re.split(r'……', quote) if s.strip()]
    start = None; cur = 0; first = None; last_end = None
    for s in segs:
        i = txt.find(s, cur if first is not None else 0)
        if i < 0: return None
        if first is None: first = i
        elif i - last_end > 4000: return None
        last_end = i + len(s); cur = last_end
    k1 = bisect.bisect_right(offs, first) - 1
    k2 = bisect.bisect_right(offs, last_end - 1) - 1
    p1, c1, l1 = lid_fmt(ids[k1]); p2, c2, l2 = lid_fmt(ids[k2])
    if (p1, c1) == (p2, c2):
        loc = f'p. {p1}{c1}{l1}' + (f'–{l2}' if l2 != l1 else '')
    elif p1 == p2:
        loc = f'p. {p1}{c1}{l1}–{c2}{l2}'
    else:
        loc = f'pp. {p1}{c1}{l1}–{p2}{c2}{l2}'
    title, tr, vol, no = CB[work]
    return f'{title}卷{cn(juans[k1])}，{tr}，CBETA, {vol}, no. {no}, {loc}'

# ---------- Sanskrit sources ----------
SK = {
    'GST': ('dsbc_723.txt', 'Guhyasamājatantra', 'DSBC 電子本，品.偈'),
    'PK': ('sa_nAgArjuna-paJcakrama.txt', 'Nāgārjuna, Pañcakrama', 'ed. Tripathi 2001（GRETIL 電子本），次第.偈'),
    'SU': ('sa_nAropa-sekoddeza.txt', 'Sekoddeśa', 'ed. Gnoli in Orofino 1994（GRETIL 電子本），偈'),
    'GMV': ('sa_dIpaMkarabhadra-guhyasamAjamaNDalavidhi.txt', 'Dīpaṅkarabhadra, Guhyasamājamaṇḍalavidhi', 'GRETIL 電子本（據 Dhīḥ 42, 2006），偈'),
    'PU': ('dsbc_737.txt', 'Candrakīrti, Pradīpoddyotana', '第十一品“六邊釋”，DSBC 電子本'),
}
_sk_cache = {}
def sk_norm(s):
    s = unicodedata.normalize('NFC', s).replace('ṁ', 'ṃ').replace('ṅ', 'ṅ')
    s = re.sub(r'(pk|sekoddeśa|sekod)_\s*[\d.\s]+', '', s)
    s = re.sub(r"[\s|/।॥\d\(\)\[\]\-_'’.,;:]+", '', s)
    return s.lower()
def sk_check(key, quote):
    fn = SK[key][0]
    if fn not in _sk_cache:
        _sk_cache[fn] = sk_norm(open(SRC + fn, encoding='utf8').read())
    segs = [x for x in quote.split('…') if x.strip()]
    return all(sk_norm(x) in _sk_cache[fn] for x in segs)

# ---------- parse entries ----------
FIELDS = ['zh', 'alt', 'bo', 'sa', 'en', 'def', 'plain', 'exp', 'q', 'qs', 'ref', 'tr', 'see', 'after']
def parse_file(path):
    sections = []; cur_sec = None; entries = []
    cur = None; field = None
    for raw in open(path, encoding='utf8'):
        line = raw.rstrip('\n')
        if line.startswith('#SECTION '):
            num, title = line[9:].split(' ', 1)
            cur_sec = {'num': num, 'title': title, 'intro': '', 'entries': []}
            sections.append(cur_sec); cur = None; field = None; continue
        if line.startswith('#INTRO '):
            cur_sec['intro'] = line[7:]; continue
        if line.startswith('=== '):
            cur = {'id': line[4:].strip(), 'q': [], 'qs': [], 'ref': [], 'tr': [], 'exp': [], 'plain': []}
            if cur_sec is None:
                cur_sec = {'num': 'PATCH', 'title': '', 'intro': '', 'entries': []}; sections.append(cur_sec)
            cur_sec['entries'].append(cur); field = None; continue
        if cur is None or not line.strip():
            continue
        m = re.match(r'^(zh|alt|bo|sa|en|def|plain|exp|q|qs|ref|tr|see|after):\s?(.*)$', line)
        LIST = ('q', 'qs', 'ref', 'tr', 'exp', 'plain')
        if m:
            field, val = m.group(1), m.group(2)
            if field in LIST: cur[field].append(val)
            else: cur[field] = val
        else:  # continuation
            if field in LIST: cur[field][-1] += line.strip()
            elif field: cur[field] += line.strip()
    return sections

def main():
    files = sorted(f for f in os.listdir(DATA) if f.endswith('.txt'))
    raw = []
    for f in files: raw += parse_file(DATA + f)
    errors = []; ids = {}
    # merge sections with same number; place entries with 'after'; apply patches
    sections = []; bynum = {}; pending = []; patches = []
    for sec in raw:
        if sec['num'] == 'PATCH': patches += sec['entries']; continue
        if sec['num'] not in bynum:
            bynum[sec['num']] = {'num': sec['num'], 'title': sec['title'], 'intro': sec['intro'], 'entries': []}
            sections.append(bynum[sec['num']])
        for e in sec['entries']:
            if e.get('after'): pending.append((sec['num'], e))
            else: bynum[sec['num']]['entries'].append(e)
    for _ in range(5):
        rest = []
        for num, e in pending:
            lst = bynum[num]['entries']
            pos = next((k for k, x in enumerate(lst) if x['id'] == e['after']), None)
            if pos is None: rest.append((num, e)); continue
            k = pos + 1
            while k < len(lst) and lst[k].get('after_chain') == e['after']: k += 1
            e['after_chain'] = e['after']; lst.insert(k, e)
        pending = rest
    for num, e in pending: errors.append(f'{e["id"]}: after-target {e["after"]} not found in section {num}')
    sections.sort(key=lambda x: int(x['num']))
    allmap = {e['id']: e for s_ in sections for e in s_['entries']}
    for pch in patches:
        if pch['id'] not in allmap: errors.append(f'patch for unknown id {pch["id"]}'); continue
        tgt = allmap[pch['id']]
        for fld in ('plain', 'exp', 'q', 'qs', 'tr', 'ref'):
            tgt[fld] = tgt.get(fld, []) + pch.get(fld, [])
    # numbering
    for s in sections:
        for k, e in enumerate(s['entries'], 1):
            e['no'] = f"{s['num']}.{k}"
            if e['id'] in ids: errors.append(f'duplicate id {e["id"]}')
            ids[e['id']] = e
    nq = nqs = 0
    for s in sections:
        for e in s['entries']:
            for fld in ('zh', 'bo', 'en', 'def'):
                if fld not in e: errors.append(f'{e["id"]}: missing {fld}')
            if not e.get('plain'): errors.append(f'{e["id"]}: missing plain')
            e['bo_uni'] = ' / '.join(conv.toUnicode(w.strip()) for w in e.get('bo', '').split(' / ')) if e.get('bo') else ''
            e['q_out'] = []
            for q in e['q']:
                work, quote = [x.strip() for x in q.split('|', 1)]
                loc = cb_locate(work, quote)
                if not loc: errors.append(f'{e["id"]}: CBETA quote not found [{work}] {quote[:40]}')
                else: e['q_out'].append((quote, loc)); nq += 1
            e['qs_out'] = []
            for q in e['qs']:
                head, quote = [x.strip() for x in q.split('|', 1)]
                key, ref = head.split(' ', 1)
                if not sk_check(key, quote): errors.append(f'{e["id"]}: Sanskrit quote not found [{head}] {quote[:40]}')
                else:
                    e['qs_out'].append((quote, f'{SK[key][1]} {ref}（{SK[key][2]}）')); nqs += 1
            for t in [x.strip() for x in e.get('see', '').split(',') if x.strip()]:
                if t not in ids: errors.append(f'{e["id"]}: see-ref to unknown id {t}')
    json.dump(sections, open(BASE + 'out/entries.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    n = sum(len(s['entries']) for s in sections)
    print(f'sections={len(sections)} entries={n} cbeta_quotes={nq} sanskrit_quotes={nqs}')
    if errors:
        print('ERRORS:'); print('\n'.join(errors)); sys.exit(1)

if __name__ == '__main__':
    main()
