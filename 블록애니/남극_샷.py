"""《남극에 남겨진 타로와 지로》 샷 목록 (세로 9:16) → 연재/남극의타로지로/장면/샷목록.json"""
import json
DAY=['#7fb6e6','#e3f0fb']; GREY=['#8d98a8','#d5dbe3']; NIGHT=['#05081a','#0d2a3a','#1f6b5a','#0b1a33']
DAWN=['#24305e','#c96a5a','#ffb36b','#ffe0a8']; DUSK=['#3a4a8a','#e8846a','#ffc98a']
def C(*keys): return [{'u':u,'pos':p,'tgt':t} for u,p,t in keys]
S=[
 # 게임 카메라 (사용자 결정 2026-11-11): orbit 빙 돌기 · chase 3인칭 추적 · shoulder 어깨 너머 · track 따라 보기, lag = 살짝 늦게 따라옴
 dict(name='s01_기지',t0=0,t1=4,fps=12,sky=DAY,cam=dict(type='orbit',center=[0,0,0],a=[-30,8],r=[210,120],h=[95,40],look=[0,8,0])),
 dict(name='s02_쓰다듬기',t0=4,t1=9,fps=24,sky=DAY,cam=dict(type='shoulder',target='e_root',back=[46,38],up=[42,38],side=17,lookAt='L6_head',look=[6,-3,0],lag=0.3,sway=0.4)),
 dict(name='s03_헬기떠남',t0=9,t1=14,fps=12,sky=DAY,cam=dict(type='track',pos=[-30,16,35],target='h_root',look=[0,10,0],lag=0.4)),
 dict(name='s04_겨울밤',t0=14,t1=19,fps=12,sky=NIGHT,cam=dict(type='orbit',center=[-6,0,0],a=[-45,-12],r=[75,55],h=[26,16],look=[0,4,0],sway=0.3)),
 dict(name='s05_빈목줄',t0=19,t1=23.5,fps=12,sky=GREY,cam=C((0,[-35,24,-50],[0,0,-8]),(1,[25,24,-50],[0,0,-8]))),
 dict(name='s06_달림',t0=23.5,t1=28.5,fps=24,sky=DAY,cam=dict(type='chase',target='J_root',back=[60,44],up=20,side=16,ahead=22,look=[0,6,0],lag=0.25,sway=0.5)),
 dict(name='s07_해돋이',t0=28.5,t1=33,fps=12,sky=DAWN,cam=dict(type='chase',target='J_root',back=[80,46],up=[12,22],side=-6,ahead=50,look=[0,14,0],lag=0.3)),
 dict(name='s08_헬기옴',t0=33,t1=37,fps=12,sky=DAY,cam=dict(type='track',pos=[40,14,-150],pos2=[52,12,-158],target='h_root',look=[0,8,0],lag=0.5)),
 dict(name='s09_달려나옴',t0=37,t1=41.5,fps=24,sky=DAY,cam=dict(type='chase',target='J_root',back=42,up=18,side=12,ahead=25,look=[0,8,0],lag=0.3,sway=0.4)),
 dict(name='s10_지로',t0=41.5,t1=46,fps=24,sky=DAY,cam=dict(type='shoulder',target='J_root',back=[30,24],up=27,side=14,lookAt='e_head',look=[0,-3,0],lag=0.3,sway=0.3)),
 dict(name='s11_타로',t0=46,t1=50,fps=24,sky=DAY,cam=dict(type='orbit',target='e_root',a=[140,195],r=[75,66],h=[30,26],look=[0,10,12])),
 dict(name='s12_함께',t0=50,t1=55,fps=12,sky=DUSK,cam=dict(type='orbit',target='e_root',a=[200,285],r=[60,165],h=[24,85],look=[0,8,12])),
]
for s in S: s['set']='A'
json.dump({'aspect':'9:16','shots':S},open('/home/user/youtubeshot/연재/남극의타로지로/장면/샷목록.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(S),'shots',sum(round((s['t1']-s['t0'])*s['fps']) for s in S),'frames')
