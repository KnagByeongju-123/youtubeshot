# 메시 AI 자동 리깅: 손끝 점이 엉덩이(Hips)·허리(Spine) 뼈에도 20% 쯤 묶여 있어 팔을 움직이면 손끝이 가늘게 늘어나 '잔상'처럼 남음 (2026-11-21)
# → 몸통에서 떨어진 팔·손 점(|x| > 몸 반폭)은 팔 뼈(UpperArm·ForeArm·Hand)에만 묶이게 다시 나눔
# 사용: .bpy_venv/bin/python -I 실사3D/손가중치_고치기.py <입.blend> <결과.blend> [몸반폭 0.30] [높이 위 0.3]
import bpy,sys
src,out=sys.argv[1],sys.argv[2]; XMIN=float(sys.argv[3]) if len(sys.argv)>3 else 0.30; ZMAX=float(sys.argv[4]) if len(sys.argv)>4 else 0.3
bpy.ops.wm.open_mainfile(filepath=src)
o=max((x for x in bpy.data.objects if x.type=='MESH' and x.data.shape_keys),key=lambda x:len(x.data.vertices))
names={g.index:g.name for g in o.vertex_groups}
fixed=0
for side,sg in(('L',1),('R',-1)):
    arm={i for i,nm in names.items() if nm.endswith('.'+side) and nm.split('.')[0] in('UpperArm','ForeArm','Hand')}
    for v in o.data.vertices:
        if v.co.x*sg>XMIN and v.co.z<ZMAX:
            other=[g for g in v.groups if g.group not in arm]
            if not other: continue
            keep=[(g.group,g.weight) for g in v.groups if g.group in arm]; t=sum(w for _,w in keep)
            if t<=0: continue
            for g in other: o.vertex_groups[g.group].remove([v.index])
            for gi,w in keep: o.vertex_groups[gi].add([v.index],w/t,'REPLACE')
            fixed+=1
bpy.ops.wm.save_as_mainfile(filepath=out); print("고친 점",fixed)
