import re,sys,subprocess,html,os
book=sys.argv[1]; out=sys.argv[2]
def get(u):
    return subprocess.run(['curl','-s','-m','40',u],capture_output=True).stdout.decode('utf8','replace')
t=get(f'https://www.dsbcproject.org/canon-text/book/{book}')
links=[]
for m in re.finditer(r'href="(https://www.dsbcproject.org/canon-text/content/%s/\d+)"[^>]*>\s*([^<]*)'%book,t):
    if m.group(1) not in [l[0] for l in links]: links.append((m.group(1),m.group(2).strip()))
with open(out,'w',encoding='utf8') as f:
    for u,title in links:
        p=get(u)
        m=re.search(r'<div[^>]*class="[^"]*(?:content|field-item|text)[^"]*"[^>]*>(.*?)</div>\s*</div>',p,re.S)
        body=re.sub(r'<br\s*/?>','\n',p)
        body=re.sub(r'<script.*?</script>|<style.*?</style>','',body,flags=re.S)
        body=re.sub(r'<[^>]+>','',body)
        body=html.unescape(body)
        body=re.sub(r'\n\s*\n+','\n',body)
        f.write(f'\n===== {title} ({u}) =====\n'+body)
print(book,len(links))
