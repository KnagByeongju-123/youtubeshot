# 팔·몸 가중치 다시 나누기 (메시 AI 자동 리깅: 팔을 옆으로 들면 소매와 몸통 사이가 박쥐 날개처럼 늘어남 — 사용자 지적 2026-11-22)
# 높이마다 팔과 몸 사이 빈틈(가운데 줄)을 재 두고(아래 GAP), 줄 바깥 = 팔 뼈만, 안쪽 = 몸 뼈만. 겨드랑이~어깨(z 0.34~0.56)는 줄 둘레 ±2cm 를 부드럽게 섞음
# GAP 은 두 번째 메시 AI 아나운서(A 자세) 값 — 다른 모델은 높이마다 |x| 분포에서 빈틈을 다시 잼
# 사용: .bpy_venv/bin/python -I 실사3D/팔가중치_고치기.py <입.blend> <결과.blend> ['[[z,빈틈x],...]']  (빈틈 표를 주면 그것, 없으면 아래 GAP)
#  다른 모델: 높이마다 x>0.05 점의 |x| 를 정렬해 가장 큰 빈틈의 가운데를 잼 (여자아나운서1 2026-11-23 예: 실사3D.md)
import bpy,sys,numpy as np
src,out=sys.argv[1],sys.argv[2]
GAP=[(-0.14,0.33),(-0.10,0.30),(-0.06,0.28),(-0.02,0.26),(0.02,0.235),(0.06,0.22),(0.10,0.21),(0.14,0.20),(0.18,0.19),(0.22,0.18),(0.26,0.165),(0.30,0.155),(0.34,0.155),(0.45,0.17),(0.56,0.195)]
import json
if len(sys.argv)>3: GAP=json.loads(sys.argv[3])
gz=np.array([g[0] for g in GAP]); gx=np.array([g[1] for g in GAP])
Z0,Z1,BL=0.34,0.56,0.02
bpy.ops.wm.open_mainfile(filepath=src)
o=max((x for x in bpy.data.objects if x.type=='MESH' and x.data.shape_keys),key=lambda x:len(x.data.vertices))
names={g.index:g.name for g in o.vertex_groups}; idx_of={g.name:g.index for g in o.vertex_groups}
fixed=0
for side,sg in(('L',1),('R',-1)):
    # 손가락 뼈(Thumb1·Index2…)가 있는 모델도 손으로 셈
    arm={idx_of[n] for n in idx_of if n.endswith('.'+side) and n.split('.')[0].rstrip('0123456789') in('UpperArm','ForeArm','Hand','Thumb','Index','Middle','Ring','Little')}
    for v in o.data.vertices:
        x,z=v.co.x*sg,v.co.z
        if x<=0.08 or z>Z1 or z<-0.2: continue
        b=float(np.interp(z,gz,gx))
        if z<=Z0: s=1.0 if x>b else 0.0
        else:     s=min(1.0,max(0.0,(x-b+BL)/(2*BL)))
        ws={g.group:g.weight for g in v.groups}
        aw={k:w for k,w in ws.items() if k in arm}; tw={k:w for k,w in ws.items() if k not in arm}
        sa,st=sum(aw.values()),sum(tw.values())
        if s>0 and sa<=0: aw={idx_of['UpperArm.'+side]:1.0}; sa=1.0
        if s<1 and st<=0: tw={idx_of['Chest']:1.0}; st=1.0
        new={}
        for k,w in aw.items(): new[k]=new.get(k,0)+s*w/sa
        for k,w in tw.items(): new[k]=new.get(k,0)+(1-s)*w/st
        if all(abs(new.get(k,0)-ws.get(k,0))<1e-3 for k in set(new)|set(ws)): continue
        for k in ws: o.vertex_groups[k].remove([v.index])
        for k,w in new.items():
            if w>1e-4: o.vertex_groups[k].add([v.index],w,'REPLACE')
        fixed+=1
bpy.ops.wm.save_as_mainfile(filepath=out); print("다시 나눈 점",fixed)
