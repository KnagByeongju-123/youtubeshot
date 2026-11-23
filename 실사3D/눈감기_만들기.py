# 3D 모델 눈 감기(깜빡임) 입 모양 만들기 — 메시 AI 모델은 눈이 그림으로 그려져 있어 눈꺼풀 모양키(Blink)가 거의 안 움직임
# → 눈 그림(윗눈꺼풀~아랫눈꺼풀 띠)을 아래 눈꺼풀 줄로 모으고 윗눈꺼풀 피부를 끌어내려 덮음
# 사용: .bpy_venv/bin/python -I 실사3D/눈감기_만들기.py <입.blend> <결과.blend> '{"eyes":[[x,z_위,z_아래,반폭],...]}'
#   좌표는 m: 눈을 정면 직교로 찍어 잰 눈 가운데 x, 윗눈꺼풀 줄 z, 아랫눈꺼풀 줄 z, 눈 반폭
import bpy,sys,json,numpy as np
blend,out=sys.argv[1],sys.argv[2]; J=json.loads(sys.argv[3])
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene
o=max((x for x in sc.objects if x.type=='MESH' and x.data.shape_keys),key=lambda x:len(x.data.vertices)); me=o.data
n=len(me.vertices); co=np.zeros(n*3,np.float32); me.vertices.foreach_get('co',co); co=co.reshape(n,3)
arr=co.copy(); LID=J.get('lid',0.009)
for ex,zu,zl,hw in J['eyes']:
    reg=(np.abs(co[:,0]-ex)<hw*1.4)&(co[:,2]>zl-0.004)&(co[:,2]<zu+LID+0.004)
    idx=np.where(reg)[0]
    if not len(idx): continue
    cx_,cz_=np.floor(co[idx,0]/0.0015).astype(int),np.floor(co[idx,2]/0.0015).astype(int)   # 1.5mm 칸마다 가장 앞 겉면만
    front={}
    for i,a_,b_ in zip(idx,cx_,cz_): front[(a_,b_)]=min(front.get((a_,b_),9),co[i,1])
    idx=np.array([i for i,a_,b_ in zip(idx,cx_,cz_) if co[i,1]<front[(a_,b_)]+0.003])
    x,z=co[idx,0],co[idx,2]
    u=np.clip(1-((x-ex)/(hw*1.25))**2,0,1)                        # 눈 가운데 1 → 눈꼬리 0
    zl_x=zl+(zu-zl)*0.25*(1-u)                                    # 눈꼬리 쪽은 감는 줄이 조금 위
    nz=z.copy()
    a=(z>=zl_x)&(z<=zu); nz[a]=zl_x[a]+(z[a]-zl_x[a])*0.06        # 눈 그림 띠 → 아래 줄로 납작하게
    b=(z>zu)&(z<zu+LID); t=(z[b]-zu)/LID; top=zl_x[b]+(zu-zl_x[b])*0.06
    nz[b]=top+(zu+LID-top)*t                                      # 윗눈꺼풀 피부를 끌어내림
    arr[idx,2]=z+(nz-z)*u+(nz-z)*(1-u)*0.6
kb=o.data.shape_keys.key_blocks
if '눈감기' in kb: o.shape_key_remove(kb['눈감기'])
k=o.shape_key_add(name='눈감기',from_mix=False); k.data.foreach_set('co',arr.ravel())
bpy.ops.wm.save_as_mainfile(filepath=out); print("DONE")
