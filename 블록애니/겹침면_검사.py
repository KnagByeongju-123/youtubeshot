"""겹침면 검사 — 두 상자의 면이 '같은 높이(같은 평면)·같은 방향'으로 겹치면 화면에서 색이 번갈아 바뀌어 보임(깜박임).
   (사용자 지적 2026-11-10: 전시실 액자 속 흰 네모·검은 네모가 같은 깊이라 겹친 자리의 색이 변함)
사용: python 겹침면_검사.py <모형.bbmodel 또는 폴더> [--자세히]
  - 같은 무늬(색)끼리 겹친 것, 밑면끼리 겹친 것은 눈에 안 보이므로 넘김. 서로 다른 묶음(따로 움직이는 인물 등)끼리도 넘김
  - 고치는 법: 겹치는 판마다 두께를 다르게 (앞뒤·위아래로 0.3 이상 차이) — 블록애니.md '겹침' 규칙"""
import json, sys, glob, os, collections
def faces(e):
    f,t=e['from'],e['to']; out=[]
    for ax in range(3):
        o=[a for a in range(3) if a!=ax]
        for side,c in ((0,f[ax]),(1,t[ax])):
            name=['west','east','down','up','north','south'][ax*2+side]
            uv=tuple(e['faces'][name]['uv'])
            out.append((ax,side,round(c,2),(f[o[0]],t[o[0]],f[o[1]],t[o[1]]),uv))
    return out
def check(path, detail=False):
    m=json.load(open(path,encoding='utf-8')); grp={}
    def rec(n,top):
        for c in n['children']:
            if isinstance(c,dict): rec(c,top)
            else: grp[c]=top
    for n in m['outliner']:
        if isinstance(n,dict): rec(n,n['uuid'])
        else: grp[n]='top'
    # 맨 바깥 묶음이 움직이는 것(인물)일 수 있으니, 같은 맨 바깥 묶음 안이거나 둘 다 고정(top)일 때만 비교
    planes=collections.defaultdict(list)
    for e in m['elements']:
        if e['uuid'] not in grp: continue
        for ax,side,c,rect,uv in faces(e):
            if ax==1 and side==0: continue          # 밑면은 땅·다른 상자에 가려 안 보임 → 넘김
            planes[(ax,side,c,grp[e['uuid']])].append((rect,uv,e['name']))
    bad=collections.Counter(); area=collections.Counter()
    for key,lst in planes.items():
        if len(lst)<2: continue
        lst.sort()
        for i,(r1,u1,n1) in enumerate(lst):
            for r2,u2,n2 in lst[i+1:]:
                if r2[0]>=r1[1]: break
                w=min(r1[1],r2[1])-max(r1[0],r2[0]); h=min(r1[3],r2[3])-max(r1[2],r2[2])
                if w>0.05 and h>0.05 and u1!=u2:
                    k=tuple(sorted((n1,n2))); bad[k]+=1; area[k]+=w*h
    print(os.path.basename(path),'→', '겹침 없음' if not bad else f'{sum(bad.values())}곳')
    for k,n in sorted(bad.items(),key=lambda x:-area[x[0]])[:(40 if detail else 8)]: print(f'   {k[0]} × {k[1]} : {n}곳, 넓이 {area[k]:.0f}')
    return sum(bad.values())
def fix(els, outliner, passes=6):
    """모형을 저장하기 전에 부름: 같은 평면에서 겹치는 면을 찾아 한쪽 상자를 아주 조금 키워 높낮이를 다르게 함.
       키우는 양 = 상자 크기에 맞춰 (작은 것 0.3, 먼 배경의 큰 덩어리는 1 이상 — 멀수록 깊이 차이가 커야 안 깜박임). 고친 곳 수를 돌려줌"""
    grp={}
    def rec(n,top):
        for c in n['children']:
            if isinstance(c,dict): rec(c,top)
            else: grp[c]=top
    for n in outliner:
        if isinstance(n,dict): rec(n,n['uuid'])
        else: grp[n]='top'
    AX=[('west','east'),('down','up'),('north','south')]; total=0
    for _ in range(passes):
        planes=collections.defaultdict(list)
        for e in els:
            if e['uuid'] not in grp: continue
            f,t=e['from'],e['to']
            for ax in range(3):
                o=[a for a in range(3) if a!=ax]
                for side in (0,1):
                    if ax==1 and side==0: continue
                    c=(f,t)[side][ax]; uv=tuple(e['faces'][AX[ax][side]]['uv'])
                    planes[(ax,side,round(c,2),grp[e['uuid']])].append(((f[o[0]],t[o[0]],f[o[1]],t[o[1]]),uv,e))
        n=0
        for (ax,side,c,g),lst in planes.items():
            if len(lst)<2: continue
            lst.sort(key=lambda x:x[0]); moved=set(); k=0
            for i,(r1,u1,e1) in enumerate(lst):
                for r2,u2,e2 in lst[i+1:]:
                    if r2[0]>=r1[1]: break
                    if id(e2) in moved: continue
                    w=min(r1[1],r2[1])-max(r1[0],r2[0]); h=min(r1[3],r2[3])-max(r1[2],r2[2])
                    if w>0.05 and h>0.05 and u1!=u2:
                        k+=1; size=max(b-a for a,b in zip(e2['from'],e2['to'])); eps=max(0.3,size*0.006)*(1+0.37*(k%5))
                        (e2['to'] if side else e2['from'])[ax]+= eps if side else -eps
                        moved.add(id(e2)); n+=1
        total+=n
        if not n: break
    return total
if __name__=='__main__':
    p=sys.argv[1]; fs=sorted(glob.glob(os.path.join(p,'*.bbmodel'))) if os.path.isdir(p) else [p]
    tot=sum(check(f,'--자세히' in sys.argv) for f in fs); print('합계',tot,'곳'); sys.exit(1 if tot else 0)
