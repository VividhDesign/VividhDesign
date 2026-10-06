import sys
from collections import Counter
n=int(sys.argv[1]); S=[tuple(map(int,l.split())) for l in open(sys.argv[2])]
Sset=set(S)
def d(a,b): return (a[0]-b[0])**2+(a[1]-b[1])**2
cnt={b:Counter(d(b,a) for a in S if a!=b) for b in S}
res=[]
for x in range(n):
    for y in range(n):
        v=(x,y)
        if v in Sset: continue
        A=sum(cnt[b][d(b,v)] for b in S)
        c=Counter(d(v,a) for a in S)
        P=sum(m*(m-1)//2 for m in c.values())
        res.append((P+A,v))
res.sort()
print("min damage to add one point:", res[:12])
print("histogram:", Counter(s for s,_ in res).most_common()[:0] or sorted(Counter(min(s,10) for s,_ in res).items()))
