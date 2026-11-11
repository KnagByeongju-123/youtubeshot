"""겹침면 검사 — 두 상자의 면이 같은 방향으로 '같은 높이' 또는 '거의 같은 높이'로 겹치면 화면에서 색이 번갈아 바뀌어 보임(깜박임).
   (사용자 지적 2026-11-10: 전시실 액자 / 2026-11-11: 우주 편 함선 — 얇게 덧댄 줄무늬·창문 띠(틈 0.2~0.4)가 멀리서 깜박임, 밑면 겹침)
사용: python 겹침면_검사.py <모형.bbmodel 또는 폴더> [--자세히] [--틈 1.0] [--밑면제외]
  - 틈: 이 값보다 가까운 두 면도 겹침으로 봄 (기본 1.0). 멀리서 찍는 큰 장면(우주)은 깊이 정밀도가 떨어져 틈 0.3 도 깜박임
  - 밑면도 검사함 (우주·공중 장면은 아래에서 올려다봄). 땅에 놓인 세트만 --밑면제외
  - 같은 무늬끼리 겹친 것, 서로 다른 맨 바깥 묶음끼리, 잠깐 나타나는 파편(bu·fb·puff·bolt·smk)은 넘김
  - 고치는 법: 저장 전에 fix(M.els, top) — 바깥쪽 면을 틈만큼 더 밀어냄"""
import json, sys, glob, os, collections
AX=[('west','east'),('down','up'),('north','south')]; SKIP=('bu','fb','puff','bolt','smk','peb_c')
def _find(els, outliner, gap, bottoms):
    grp={}
    def rec(n,top):
        for c in n['children']:
            if isinstance(c,dict): rec(c,top)
            else: grp[c]=top
    for n in outliner:
        if isinstance(n,dict): rec(n,n['uuid'])
        else: grp[n]='top'
    B=collections.defaultdict(list)
    for e in els:
        if e['uuid'] not in grp or e['name'] in SKIP: continue
        f,t=e['from'],e['to']
        for ax in range(3):
            o=[a for a in range(3) if a!=ax]
            for side in (0,1):
                if ax==1 and side==0 and not bottoms: continue
                B[(ax,side,grp[e['uuid']])].append(((f,t)[side][ax],f[o[0]],t[o[0]],f[o[1]],t[o[1]],tuple(e['faces'][AX[ax][side]]['uv']),id(e),e))
    out=[]
    for (ax,side,g),L in B.items():
        L.sort(key=lambda x:x[:5])
        for i,a in enumerate(L):
            for b in L[i+1:]:
                d=b[0]-a[0]
                if d>=gap-1e-6: break
                w=min(a[2],b[2])-max(a[1],b[1]); h=min(a[4],b[4])-max(a[3],b[3])
                if w>0.05 and h>0.05 and a[5]!=b[5]: out.append((ax,side,a,b,w*h))
    return out
def fix(els, outliner, passes=24, gap=1.0, bottoms=True):
    """저장 전에 부름: 겹치거나 틈이 gap 보다 좁은 면을 찾아 바깥쪽 면을 더 밀어 틈을 gap 이상으로. 고친 곳 수를 돌려줌"""
    total=0
    for _ in range(passes):
        hits=_find(els,outliner,gap,bottoms)
        if not hits: break
        moved=set()
        for k,(ax,side,a,b,_) in enumerate(hits):
            e=(b if side else a)[7]            # 바깥쪽: 큰 쪽 면(side=1)은 좌표가 큰 것, 작은 쪽 면은 좌표가 작은 것
            if id(e) in moved: continue
            moved.add(id(e)); inner=(a if side else b)[0]; size=max(q-p for p,q in zip(e['from'],e['to'])); g=max(gap,size*0.004)*(1+0.13*(k%4))
            if side: e['to'][ax]=max(e['to'][ax],inner+g)
            else: e['from'][ax]=min(e['from'][ax],inner-g)
        total+=len(moved)
    return total
def check(path, detail=False, gap=1.0, bottoms=True):
    m=json.load(open(path,encoding='utf-8')); hits=_find(m['elements'],m['outliner'],gap,bottoms); c=collections.Counter(); ar=collections.Counter()
    for ax,side,a,b,area in hits: k=tuple(sorted((a[7]['name'],b[7]['name']))); c[k]+=1; ar[k]+=area
    print(os.path.basename(path),'→','겹침 없음' if not hits else f'{len(hits)}곳')
    for k,n in sorted(c.items(),key=lambda x:-ar[x[0]])[:(40 if detail else 8)]: print(f'   {k[0]} × {k[1]} : {n}곳, 넓이 {ar[k]:.0f}')
    return len(hits)
if __name__=='__main__':
    p=sys.argv[1]; fs=sorted(glob.glob(os.path.join(p,'*.bbmodel'))) if os.path.isdir(p) else [p]
    gap=float(sys.argv[sys.argv.index('--틈')+1]) if '--틈' in sys.argv else 1.0
    tot=sum(check(f,'--자세히' in sys.argv,gap,'--밑면제외' not in sys.argv) for f in fs); print('합계',tot,'곳'); sys.exit(1 if tot else 0)
