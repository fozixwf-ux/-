# Download a CBETA work via API and convert to line-referenced plain text: "<lineid>\t<text>"
import json,re,sys,subprocess,html
work=sys.argv[1]; n=int(sys.argv[2]); out=sys.argv[3]
lines=[]
for j in range(1,n+1):
    r=subprocess.run(['curl','-s','-m','60',f'https://cbdata.dila.edu.tw/stable/juans?work={work}&juan={j}'],capture_output=True).stdout
    h=json.loads(r)['results'][0]
    h=re.sub(r'<span class="lb" id="([^"]+)">[^<]*</span>',r'\n@@\1@@',h)
    h=re.sub(r'<(div|p)[^>]*>','',h)
    h=re.sub(r'<[^>]+>','',h)
    h=html.unescape(h)
    cur=None
    for seg in h.split('\n'):
        m=re.match(r'@@([^@]+)@@(.*)',seg,re.S)
        if m:
            lines.append([m.group(1),f'[卷{j}]',m.group(2).replace('\n','')])
        elif lines:
            lines[-1][2]+=seg
with open(out,'w',encoding='utf8') as f:
    for a,b,c in lines:
        f.write(f'{a}\t{b}\t{c.strip()}\n')
print(work,len(lines))
