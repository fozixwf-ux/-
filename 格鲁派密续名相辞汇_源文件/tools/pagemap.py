import sys,json
from pypdf import PdfReader
r=PdfReader(sys.argv[1]); m={}
keys={'凡例':'fm-guide','引用文献与版本':'fm-abbr','参考书目':'bib','汉文索引':'ix-zhx','藏文索引':'ix-wyx','梵文索引':'ix-skx','英文索引':'ix-enx'}
nums='一二三四五六七八九十'
def walk(o):
    for x in o:
        if isinstance(x,list): walk(x); continue
        t=x.title; p=r.get_destination_page_number(x)+1
        for k,v in keys.items():
            if t.startswith(k): m.setdefault(v,p)
        if t.startswith('第') and '部' in t[:4]:
            n=t[1:t.index('部')]
            val = 10+nums.index(n[1])+1 if n.startswith('十') and len(n)>1 else (10 if n=='十' else nums.index(n)+1)
            m.setdefault(f'sec-{val}',p)
walk(r.outline)
json.dump(m,open(sys.argv[2],'w'),indent=1); print(len(r.pages),'pages',m)
