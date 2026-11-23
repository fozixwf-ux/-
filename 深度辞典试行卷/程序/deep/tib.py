"""Tibetan corpus: concordance search and exact-quote verification with folio/line citations.

Sources
  TK<n>   Tsongkhapa collected works e-text (OpenPecha P60DBA47B), volume n; cited as 函-部-叶面行 (e.g. 3-2-125b3)
  D<toh>  Derge Kangyur/Tengyur e-text (Esukhia), cited as Toh + volume + folio side + line (e.g. D1802 ngi 12b.3)
"""
import os, re, sys, json, unicodedata, functools, yaml

CORPUS = os.environ.get('TIB_CORPUS', '/home/user')
TK_DIR = os.path.join(CORPUS, 'openpecha-data/p60dba47b/P60DBA47B.opf')
KG_DIR = os.path.join(CORPUS, 'esukhia/derge-kangyur/text')
TG_DIR = os.path.join(CORPUS, 'esukhia/derge-tengyur/text')

def nfd(s): return unicodedata.normalize('NFD', s)

def norm_keep(s):
    """Normalise for matching: NFD, drop whitespace, shad and markup; keep tsheg as syllable separator."""
    s = nfd(s)
    s = re.sub(r'\(([^,()]*),[^()]*\)', r'\1', s)       # (potential error, correction) -> original
    s = re.sub(r'\{([^,{}]*),[^{}]*\}', r'\1', s)       # {archaic, modern} -> archaic
    s = re.sub(r'\[[0-9a-z.x]+\]', '', s)              # folio/line markers
    s = re.sub(r'\{D[0-9a-z]+\}', '', s)
    s = s.replace('[', '').replace(']', '').replace('#', '')
    s = s.replace('༌', '་')                       # non-breaking tsheg -> tsheg
    s = re.sub('[༄-༊]+', '', s)                   # head marks
    s = re.sub(r'\s+', '', s)                               # whitespace / line breaks
    s = re.sub('[།-༔]+', '་', s)             # shad -> syllable boundary
    s = re.sub('་+', '་', s).lstrip('་')
    return s

class Text:
    """A text with a normalised string and a map from normalised offset to citation."""
    def __init__(self, key, label, raw_units):
        self.key, self.label = key, label
        chars, cites, uidx = [], [], []
        self.units = raw_units
        for k, (cite, chunk) in enumerate(raw_units):
            n = norm_keep(chunk)
            chars.append(n); cites.extend([cite] * len(n)); uidx.extend([k] * len(n))
        self.norm = ''.join(chars); self.cites = cites; self.uidx = uidx

    def find_all(self, q, limit=None):
        nq = norm_keep(q).strip('་')
        out, i = [], self.norm.find(nq)
        while i >= 0:
            out.append(i)
            if limit and len(out) >= limit: break
            i = self.norm.find(nq, i + 1)
        return nq, out

    def cite_range(self, i, n):
        a, b = self.cites[i], self.cites[max(i, i + n - 1)]
        return a if a == b else f'{a}–{b.split("-")[-1] if a.rsplit("-",1)[0]==b.rsplit("-",1)[0] else b}'

    def raw(self, i, n):
        """Original orthography (with shad) of the normalised match [i, i+n)."""
        a, b = self.uidx[i], self.uidx[i + n - 1]
        chunk = ''.join(nfd(self.units[k][1]) for k in range(a, b + 1))
        chunk = re.sub(r'\(([^,()]*),[^()]*\)', r'\1', chunk)
        chunk = re.sub(r'\{([^,{}]*),[^{}]*\}', r'\1', chunk)
        chunk = re.sub(r'\[[0-9a-z.x]+\]|\{D[0-9a-z]+\}|#', '', chunk).replace('\n', '')
        target = self.norm[i:i + n]
        # leftmost start s and shortest end e such that norm(chunk[s:e]) == target
        for st in range(len(chunk)):
            if not norm_keep(chunk[st:]).startswith(target): continue
            for en in range(st + 1, len(chunk) + 1):
                if norm_keep(chunk[st:en]) == target:
                    while en < len(chunk) and chunk[en] in '་ །':
                        en += 1
                    return unicodedata.normalize('NFC', chunk[st:en].strip())
        return None

    def context(self, i, n, w=60):
        return self.norm[max(0, i - w): i + n + w]

WORKS = {  # key: (volume, start offset, end offset, label)
    'SR': (3, 0, None, '宗喀巴《密宗道次第廣論》（sngags rim chen mo）'),
    'RL': (7, 1199, 737150, '宗喀巴《五次第明燈》（rim lnga rab tu gsal ba\'i sgron me）'),
}

@functools.lru_cache(None)
def tk_volume(vol, lo=0, hi=None, label=None):
    base = open(f'{TK_DIR}/base/v{vol:03d}.txt', encoding='utf8').read()
    pag = yaml.safe_load(open(f'{TK_DIR}/layers/v{vol:03d}/Pagination.yml', encoding='utf8'))
    pages = sorted(((a['span']['start'], a['span']['end'], a['metadata']['Img_name']) for a in pag['annotations'].values()))
    units = []
    for s, e, name in pages:
        if e < lo or (hi is not None and s >= hi): continue
        seg = base[max(s, lo):(e + 1 if hi is None else min(e + 1, hi))]
        for ln, line in enumerate(seg.split('\n'), 1):
            units.append((f'{name}{ln}', line))
    return Text(f'TK{vol}', label or f'宗喀巴全集第{vol}函', units)

def _derge_file(toh):
    for d in (KG_DIR, TG_DIR):
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if '{D%s}' % toh in open(p, encoding='utf8').read(): return p
    raise KeyError(toh)

@functools.lru_cache(None)
def derge(toh):
    p = _derge_file(toh); vol = os.path.basename(p).split('_')[-1].replace('.txt', '')
    raw = open(p, encoding='utf8').read().lstrip('﻿')
    start = raw.index('{D%s}' % toh)
    m = re.search(r'\{D\d+[a-z]?\}', raw[start + 3:])
    end = start + 3 + m.start() if m else len(raw)
    # walk line markers before start to know the current folio/line
    units, cur = [], None
    for mm in re.finditer(r'\[(\d+[ab](?:x?)\.\d+|\d+x?[ab])\]', raw[:end]):
        pass
    pos = 0; markers = list(re.finditer(r'\[(\d+x?[ab])(?:\.(\d+))?\]', raw))
    seg_start = None
    for k, mm in enumerate(markers):
        nxt = markers[k + 1].start() if k + 1 < len(markers) else len(raw)
        if mm.group(2) is None: continue
        a, b = max(mm.end(), start), min(nxt, end)
        if a >= b: continue
        units.append((f'{mm.group(1)}.{mm.group(2)}', raw[a:b]))
    t = Text(f'D{toh}', f'德格版 Toh {toh}（{vol}函）', units)
    t.vol = vol
    return t

def get(key):
    if key in WORKS:
        v, lo, hi, label = WORKS[key]; t = tk_volume(v, lo, hi, label); t.key = key; return t
    if key.startswith('TK'): return tk_volume(int(key[2:]))
    if key.startswith('D'): return derge(key[1:])
    raise KeyError(key)

def verify(key, quote):
    t = get(key); nq, hits = t.find_all(quote, limit=1)
    if not hits: return None
    return t.cite_range(hits[0], len(nq))

def extract(key, quote):
    t = get(key); nq, hits = t.find_all(quote, limit=1)
    if not hits: return None, None
    return t.cite_range(hits[0], len(nq)), t.raw(hits[0], len(nq))

if __name__ == '__main__':
    cmd, key = sys.argv[1], sys.argv[2]
    t = get(key)
    if cmd == 'count':
        for q in sys.argv[3:]:
            nq, hits = t.find_all(q); print(len(hits), q)
    elif cmd == 'kwic':
        q = sys.argv[3]; lim = int(sys.argv[4]) if len(sys.argv) > 4 else 20; w = int(sys.argv[5]) if len(sys.argv) > 5 else 80
        nq, hits = t.find_all(q)
        print(f'{len(hits)} hits for {q} in {t.label}')
        for i in hits[:lim]: print(t.cite_range(i, len(nq)), '|', t.context(i, len(nq), w))
    elif cmd == 'verify':
        print(verify(key, sys.argv[3]))
    elif cmd == 'raw':
        print(*extract(key, sys.argv[3]), sep='\n')

def show(key, start, end):
    """Print raw lines whose citation lies between start and end (inclusive), e.g. 7-2-63a5 .. 7-2-64a2 or 55a.3 .. 55a.6."""
    t = get(key); on = False; out = []
    for cite, line in t.units:
        if cite == start: on = True
        if on: out.append(f'[{cite}] ' + re.sub(r'\[[0-9a-z.x]+\]|#', '', unicodedata.normalize('NFC', line)).strip())
        if cite == end: break
    return '\n'.join(out)

if __name__ == '__main__' and sys.argv[1] == 'show':
    print(show(sys.argv[2], sys.argv[3], sys.argv[4]))
