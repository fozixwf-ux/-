# usage: cb.py WORK phrase [ctx_before ctx_after] [maxhits]
import sys,bisect,os
SRC='/tmp/claude-0/-home-user--/235f57a6-03e0-5f14-ad10-7ac4f00df5b4/scratchpad/src/'
def load(work):
    ids=[];offs=[];juans=[];txt=''
    for l in open(SRC+work+'.txt',encoding='utf8'):
        a,b,c=l.rstrip('\n').split('\t')
        offs.append(len(txt));ids.append(a);juans.append(b);txt+=c
    return txt,offs,ids,juans
def find(work,phrase):
    txt,offs,ids,juans=load(work)
    res=[];i=txt.find(phrase)
    while i>=0:
        k=bisect.bisect_right(offs,i)-1
        res.append((i,ids[k],juans[k]))
        i=txt.find(phrase,i+1)
    return txt,res
if __name__=='__main__':
    work,ph=sys.argv[1],sys.argv[2]
    b=int(sys.argv[3]) if len(sys.argv)>3 else 60
    a=int(sys.argv[4]) if len(sys.argv)>4 else 120
    mx=int(sys.argv[5]) if len(sys.argv)>5 else 8
    txt,res=find(work,ph)
    print(f'## {ph}: {len(res)} hits')
    for i,lid,j in res[:mx]:
        print(f'[{j} {lid}] …{txt[max(0,i-b):i]}【{ph}】{txt[i+len(ph):i+len(ph)+a]}…')
