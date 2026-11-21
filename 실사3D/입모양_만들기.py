# 사용: .bpy_venv/bin/python -I 실사3D/입모양_만들기.py <뼈대_완성.blend> <결과.blend>
#  메시 AI 모델은 입술 위아래가 붙어 있고 자동 입 모양은 엉뚱한 곳(코 밑)을 벌림 → 그려진 입술(텍스처)에서 잰 줄을 기준으로 직접 만듦
#  MID 줄은 이 모델(아나운서, 2026-11-21) 값: 다른 모델은 mouth_cam 으로 입을 정면 직교로 찍어 이 사이 줄을 다시 잼
# 그려진 입술 자리에 입 모양 새로 만들기 (아·이·오·ㅁㅂㅍ) — 잘못된 예전 입 모양은 지움
import bpy,sys,numpy as np
blend,out=sys.argv[1],sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene
o=next(x for x in sc.objects if x.type=='MESH' and x.data.shape_keys); me=o.data
# 입 사진(정면 직교 0.14m/700px, 가운데 x=-0.03 z=0.73)에서 잰 선: 위·아래 이 사이 가운데 줄
CX,CZ,R=-0.03,0.73,0.14/700
toX=lambda px: CX+(px-350)*R; toZ=lambda py: CZ-(py-350)*R
MID=[(150,388),(175,392),(235,403),(330,410),(400,405),(470,383),(500,375)]
mx=np.array([toX(p) for p,_ in MID]); mz=np.array([toZ(q) for _,q in MID])
XM,HW=toX(328),0.031
T1,T3=15*R,12*R                                  # 줄에서 윗니 위끝·아랫입술 위끝까지
for k in list(me.shape_keys.key_blocks)[1:]:
    if k.name not in('Smile','Frown'): o.shape_key_remove(k)
n=len(me.vertices); co=np.zeros(n*3,np.float32); me.vertices.foreach_get('co',co); co=co.reshape(n,3)
# 앞 겉면만 (입속·뒤통수 제외): 2mm 칸마다 가장 앞(y 최소)에서 4mm 안
reg=(np.abs(co[:,0]-XM)<0.07)&(co[:,2]>0.64)&(co[:,2]<0.77)
cell=lambda a,b:(np.floor(a/0.002).astype(int),np.floor(b/0.002).astype(int))
front={}
ix,iz=cell(co[:,0],co[:,2])
for i in np.where(reg)[0]:
    k=(ix[i],iz[i]); front[k]=min(front.get(k,9),co[i,1])
fr=np.array([reg[i] and co[i,1]<front[(ix[i],iz[i])]+0.004 for i in range(n)])
x,y,z=co[:,0],co[:,1],co[:,2]
d=z-np.interp(x,mx,mz)                            # 입 줄 위(+)·아래(-)
u=(x-XM)/HW
cl=lambda a:np.clip(a,0,1)
fx=cl(1-(u/1.15)**2); fxc=cl(1-(u/1.9)**2)
def add(name,dx,dy,dz):
    kb=o.shape_key_add(name=name,from_mix=False); arr=co.copy()
    m=fr[:,None]*1.0; arr+=np.stack([dx,dy,dz],1)*m
    kb.data.foreach_set('co',arr.ravel())
# 아: 턱·아랫입술 내려감(뒤로 조금), 윗입술 살짝 위
A=0.010; dn=-d
blend_l=cl(dn/0.010); fxx=fx*(1-blend_l)+fxc*blend_l
fall=np.where(dn<0.035,1.0,cl(1-(dn-0.035)/0.025))
lo=(d<0)*fxx*fall; up=(d>=0)*fx*cl(1-d/0.015)
add('입_아',0*x,0.3*A*lo,-A*lo+0.12*A*up)
# 이: 양옆으로 넓게 + 조금 벌림
fv=cl(1-np.abs(d)/0.02)
add('입_이',0.005*np.clip(u,-1.2,1.2)*fv*cl(1.3-np.abs(u)), 0*x, -0.25*A*lo+0.05*A*up)
# 오: 가운데로 모으고 앞으로 + 둥글게 벌림
fxn=cl(1-(u/0.75)**2)
add('입_오',-0.30*(x-XM)*cl(1-np.abs(u)/1.5)*fv, -0.004*fx*fv, -0.5*A*(d<0)*fxn*fall+0.15*A*up*fxn)
# 우: 더 모으고 더 앞으로, 조금만 벌림
add('입_우',-0.42*(x-XM)*cl(1-np.abs(u)/1.5)*fv, -0.006*fx*fv, -0.2*A*(d<0)*fxn*fall)
# ㅁㅂㅍ: 이가 보이는 띠를 줄로 모아 입술을 닫음
dz=np.zeros(n)
s=(d>0)&(d<T1); dz[s]=-d[s]
s=(d>=T1); dz[s]=-T1*cl(1-(d[s]-T1)/0.008)
s=(d<=0)&(d>-T3); dz[s]=-d[s]
s=(d<=-T3); dz[s]=T3*cl(1-(-d[s]-T3)/0.015)
add('입_다묾',0*x,0*x,dz*fx)
# 입 줄을 걸친 면 = 입속(어두운 재질) → 벌리면 어둡게 보임
dark=next(i for i,m in enumerate(me.materials) if m and 'Mouth' in m.name)
cnt=0
for p in me.polygons:
    vs=list(p.vertices)
    if fr[vs].all() and (d[vs]>0).any() and (d[vs]<0).any() and (np.abs(u[vs])<0.98).all():
        p.material_index=dark; cnt+=1
print("dark faces",cnt,"front verts",fr.sum())
bpy.ops.wm.save_as_mainfile(filepath=out); print("DONE",[k.name for k in me.shape_keys.key_blocks])
