"""블록 모형(.bbmodel)에서 '면 겹침(z-fighting)'을 찾음 — 두 상자의 같은 쪽 면이 같은 자리(같은 깊이)에 겹치면
   촬영할 때 두 색이 번갈아 비침(창틀+유리, 문+손잡이 등).  사용: python 면겹침검사.py <파일.bbmodel> [--자세히]
   (움직임은 보지 않고 놓인 자리만 봄. 숨김(크기 0) 상자도 같이 셈)"""
import json, sys
from collections import defaultdict
path=sys.argv[1]; verbose='--자세히' in sys.argv
m=json.load(open(path,encoding='utf-8'))
els=[e for e in m['elements'] if e.get('type','cube')=='cube']
EPS=0.02
def name(e): return e.get('name','?')
hits=[]
def inside(p,e,skip):
    if e in skip: return False
    return all(min(e['from'][q],e['to'][q])+1e-4<p[q]<max(e['from'][q],e['to'][q])-1e-4 for q in range(3))
def hidden(a,b,ax,side,o):
    """겹친 면 바로 바깥(0.05)이 다른 상자 속이면 안 보이는 면 → 셈하지 않음 (땅에 묻힌 바닥 등)"""
    p=[0,0,0]
    for q in o:
        a0,a1=sorted((a['from'][q],a['to'][q])); b0,b1=sorted((b['from'][q],b['to'][q])); p[q]=(max(a0,b0)+min(a1,b1))/2
    v=max(a['from'][ax],a['to'][ax]) if side else min(a['from'][ax],a['to'][ax])
    p[ax]=v+(0.05 if side else -0.05)
    return any(inside(p,e,(a,b)) for e in els)
# 축(0 x,1 y,2 z)과 쪽(min/max)마다 면 높이를 모아 같은 높이끼리만 비교 (빠르게)
for ax in range(3):
    o=[a for a in range(3) if a!=ax]
    for side in (0,1):   # 0 = from 쪽 면, 1 = to 쪽 면 (같은 방향을 보는 면끼리)
        buck=defaultdict(list)
        for e in els:
            lo=min(e['from'][ax],e['to'][ax]); hi=max(e['from'][ax],e['to'][ax])
            if hi-lo<1e-6: continue
            v=hi if side else lo
            buck[round(v/EPS)].append(e)
        for k,lst in buck.items():
            if len(lst)<2: continue
            for i in range(len(lst)):
                a=lst[i]
                for b in lst[i+1:]:
                    ov=1.0
                    for q in o:
                        a0,a1=sorted((a['from'][q],a['to'][q])); b0,b1=sorted((b['from'][q],b['to'][q]))
                        d=min(a1,b1)-max(a0,b0)
                        if d<=1e-6: ov=0; break
                        ov*=d
                    if ov>0 and not hidden(a,b,ax,side,o):
                        hits.append((ov,ax,side,name(a),name(b),k*EPS))
hits.sort(reverse=True)
AX='xyz'
pairs=defaultdict(lambda:[0,0.0])
for ov,ax,side,na,nb,v in hits:
    key=tuple(sorted((na,nb)))+(AX[ax]+('+' if side else '-'),); pairs[key][0]+=1; pairs[key][1]+=ov
print(f'{path}: 면 겹침 {len(hits)}곳 (상자 이름 쌍 {len(pairs)}종)')
for (na,nb,f),(c,ov) in sorted(pairs.items(),key=lambda x:-x[1][1])[:40 if not verbose else 10**6]:
    print(f'  {na} ↔ {nb}  ({f} 면, {c}곳, 넓이 {ov:.1f})')
