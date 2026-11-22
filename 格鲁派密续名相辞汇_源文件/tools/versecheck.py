import json, re, unicodedata, sys
sys.path.insert(0,'.')
import build
d=json.load(open('../out/entries.json',encoding='utf8'))
def norm_with_map(t):
    t=unicodedata.normalize('NFC',t).replace('ṁ','ṃ')
    out=[];mp=[]
    i=0
    # remove verse markers so they don't break matching but record them
    return t
src={}
for k,(fn,_,_) in build.SK.items():
    src[k]=unicodedata.normalize('NFC',open(build.SRC+fn,encoding='utf8').read()).replace('ṁ','ṃ')
def find_pos(text,quote):
    # build normalized text with index map
    keep=[];idx=[]
    for i,ch in enumerate(text):
        keep.append(ch);idx.append(i)
    s=''.join(keep)
    q=build.sk_norm(quote.split('…')[0])
    # normalized source with positions
    ns=[];pos=[]
    t2=re.sub(r'(pk|sekoddeśa|sekod)_\s*[\d.\s]+',lambda m:' '*len(m.group(0)),text)
    for i,ch in enumerate(t2):
        c=build.sk_norm(ch)
        if c: ns.append(c);pos.append(i)
    j=''.join(ns).find(q)
    return pos[j] if j>=0 else None
for s in d:
    for e in s['entries']:
        for q,loc in e['qs_out']:
            pass
# re-parse raw qs heads
import glob
for p in sorted(glob.glob('../data/*.txt')):
    for line in open(p,encoding='utf8'):
        if not line.startswith('qs:'): continue
        head,quote=[x.strip() for x in line[3:].split('|',1)]
        key,ref=head.split(' ',1)
        t=src[key]; i=find_pos(t,quote)
        if i is None: print('NOTFOUND',head); continue
        after=t[i:]
        if key=='PK':
            m=re.search(r'pk_(\d+\.\s*\d+)',after); got=m.group(1).replace(' ','') if m else '?'
        elif key=='SU':
            m=re.search(r'sekod(?:deśa)?_(\d+)',after); got=m.group(1) if m else '?'
        elif key=='GST':
            m=re.search(r'\|\|\s*(\d+)\s*\|\|',after); v=m.group(1) if m else '?'
            ch=len(re.findall(r'paṭalaḥ\s*(?:atha|\n|$)|paṭalaḥatha',t[:i]))
            heads=[mm.start() for mm in re.finditer(r'(prathamaḥ|dvitīyaḥ|tṛtīyaḥ|caturthaḥ|pañcamaḥ|ṣaṣṭhaḥ|saptamaḥ|aṣṭamaḥ|navamaḥ|daśamaḥ|ekādaśaḥ|dvādaśaḥ|trayādaśaḥ|caturdaśaḥ|pañcadaśaḥ|ṣoḍaśaḥ|saptadaśaḥ|aṣṭādaśaḥ) paṭalaḥ',t)]
            ch=sum(1 for h in heads if h<i)
            got=f'{ch}.{v}'
        elif key=='GMV':
            m=re.search(r'\|\|\s*(\d+)',after); got=m.group(1) if m else '?'
        else: got='-'
        print(f'{p[8:20]:12} {head:22} -> {got}')
