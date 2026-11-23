# 손가락 살짝 오므리기 모양키 '손_오므림' (사용자 2026-11-21: '손바닥은 살짝 오므리는 게 자연스러움') — 메시 AI 뼈대엔 손가락 뼈가 없어서 모양키로
# 손 점(Hand 뼈에 묶인 점)을 손목→손끝 방향으로 재서, 손가락 뿌리(손 길이의 THR) 너머를 손바닥 쪽으로 점점 더 굽힘 (손끝일수록 많이)
# 사용: .bpy_venv/bin/python -I 실사3D/손오므림_만들기.py <입.blend> <결과.blend> [굽힘각 55] [손가락 뿌리 비율 0.5]
import bpy,sys,math,numpy as np,mathutils
src,out=sys.argv[1],sys.argv[2]; ANG=math.radians(float(sys.argv[3]) if len(sys.argv)>3 else 55); THR=float(sys.argv[4]) if len(sys.argv)>4 else 0.5
bpy.ops.wm.open_mainfile(filepath=src)
o=max((x for x in bpy.data.objects if x.type=='MESH' and x.data.shape_keys),key=lambda x:len(x.data.vertices)); ar=next(x for x in bpy.data.objects if x.type=='ARMATURE')
me=o.data; n=len(me.vertices); co=np.zeros(n*3,np.float32); me.vertices.foreach_get('co',co); co=co.reshape(n,3); new=co.copy()
for side,sg in(('L',1),('R',-1)):
    gi=o.vertex_groups['Hand.'+side].index
    hg={g.index for g in o.vertex_groups if g.name.endswith('.'+side) and g.name.split('.')[0].rstrip('0123456789') in('Hand','Thumb','Index','Middle','Ring','Little')}   # 손가락 뼈가 있는 모델도
    idx=np.array([v.index for v in me.vertices if v.co.x*sg>0.3 and sum(g.weight for g in v.groups if g.group in hg)>0.5])
    wr=np.array(ar.matrix_world@ar.data.bones['Hand.'+side].head_local)          # 손목
    p=co[idx]; far=p[np.argsort(-np.linalg.norm(p-wr,axis=1))[:200]].mean(0)
    d=(far-wr)/np.linalg.norm(far-wr)                                              # 손목 → 손끝
    inw=np.array([-sg,0,0.0]); nrm=inw-inw.dot(d)*d; nrm/=np.linalg.norm(nrm)     # 손바닥 쪽(몸 쪽)
    t=(p-wr)@d; L=t.max(); tk=THR*L
    axis=np.cross(d,nrm); axis/=np.linalg.norm(axis)
    piv=wr+d*tk
    for j,i in enumerate(idx):
        if t[j]<=tk: continue
        a=ANG*((t[j]-tk)/(L-tk))**0.8
        R=mathutils.Matrix.Rotation(a,3,mathutils.Vector(axis))
        q=R@mathutils.Vector(co[i]-piv)+mathutils.Vector(piv)
        # 방향 확인: 손끝이 손바닥 쪽으로 가야 함
        new[i]=np.array(q)
    tip=new[idx][t>0.95*L].mean(0)-co[idx][t>0.95*L].mean(0)
    if tip.dot(nrm)<0:                                                             # 반대로 굽었으면 다시
        for j,i in enumerate(idx):
            if t[j]<=tk: continue
            a=-ANG*((t[j]-tk)/(L-tk))**0.8
            R=mathutils.Matrix.Rotation(a,3,mathutils.Vector(axis))
            new[i]=np.array(R@mathutils.Vector(co[i]-piv)+mathutils.Vector(piv))
    print(side,"손 점",len(idx),"손 길이",round(L,3))
kb=me.shape_keys.key_blocks
if '손_오므림' in kb: o.shape_key_remove(kb['손_오므림'])
k=o.shape_key_add(name='손_오므림',from_mix=False); k.data.foreach_set('co',new.ravel())
bpy.ops.wm.save_as_mainfile(filepath=out); print("DONE")
