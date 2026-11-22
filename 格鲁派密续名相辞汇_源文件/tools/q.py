# batch search: q.py WORK ctx_before ctx_after maxhits phrase1 phrase2 ...
import sys, cb
w=sys.argv[1]; b=int(sys.argv[2]); a=int(sys.argv[3]); mx=int(sys.argv[4])
for ph in sys.argv[5:]:
    txt,res=cb.find(w,ph)
    print(f'## {ph}: {len(res)}')
    for i,lid,j in res[:mx]:
        print(f'  [{j}{lid[-9:]}] {txt[max(0,i-b):i]}【{ph}】{txt[i+len(ph):i+len(ph)+a]}')
