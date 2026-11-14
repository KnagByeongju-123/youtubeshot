import json
DAY=['#7cc3f0','#f3e7c8']; DUSK=['#5a6fb0','#ff9a5a','#ffd39a']; DUST=['#c9a26b','#efd8a8']; MORN=['#9fc8f0','#ffe2b8']
def C(*k): return [{'u':u,'pos':p,'tgt':t} for u,p,t in k]
S=[
 dict(name='p00_하늘',set='G',t0=0,t1=16.5,fps=12,ropes=False,sky=DAY,cam=C((0,[700,520,800],[-560,80,0]),(1,[320,260,380],[-560,100,0]))),
 dict(name='p01_오늘',set='G',t0=16.5,t1=29.7,fps=12,ropes=False,sky=DAY,cam=C((0,[320,40,-160],[-560,100,0]),(1,[220,32,-70],[-560,110,0]))),
 dict(name='p02_동굴밖',set='C',t0=29.7,t1=46.2,fps=12,ropes=False,sky=DAY,cam=C((0,[0,70,-420],[0,40,200]),(1,[0,38,-70],[0,24,200]))),
 dict(name='p03_파피루스',set='C',t0=46.2,t1=52.4,fps=12,ropes=False,cam=C((0,[0,30,110],[0,0,185]),(1,[0,20,135],[0,0,190]))),
 dict(name='p04_메레르',set='T',t0=52.4,t1=67.3,fps=24,ropes=False,sky=MORN,cam=C((0,[-70,32,-140],[0,24,-60]),(1,[-45,27,-105],[0,24,-60]))),
 dict(name='p05_싣기',set='T',t0=67.3,t1=81.5,fps=24,ropes=False,sky=MORN,cam=C((0,[-300,100,-200],[-40,20,-10]),(1,[-280,90,-260],[-80,20,-60]))),
 dict(name='p06_강길',set='G',t0=81.5,t1=94.5,fps=24,ropes=False,sky=DAY,follow='b1_root',cam=C((0,[240,120,-230],[0,30,0]),(1,[190,90,-170],[-40,30,0]))),
 dict(name='p07_빛남',set='G',t0=94.5,t1=104.6,fps=12,ropes=False,sky=DAY,cam=C((0,[-150,160,-520],[-560,110,0]),(1,[-120,150,420],[-560,110,0]))),
 dict(name='p08_모래밭',set='G',t0=104.6,t1=121.8,fps=12,ropes=False,sky=DAY,cam=C((0,[260,45,-260],[-450,70,0]),(1,[200,36,-190],[-450,80,0]))),
 dict(name='p09_위성',set='G',t0=121.8,t1=143.7,fps=12,ropes=False,sky=DAY,cam=C((0,[0,1500,-12],[0,0,0]),(1,[0,1050,-12],[0,0,0]))),
 dict(name='p10_강따라',set='G',t0=143.7,t1=164.4,fps=12,ropes=False,sky=DAY,cam=C((0,[260,300,600],[-300,0,0]),(1,[260,260,-1900],[-300,0,-2500]))),
 dict(name='p11_항구',set='G',t0=164.4,t1=188.3,fps=24,ropes=False,sky=DAY,cam=C((0,[160,90,-210],[-150,20,0]),(1,[110,70,-160],[-150,20,0]))),
 dict(name='p12_썰매',set='G',t0=188.3,t1=216.4,fps=24,sky=DAY,follow='sled',cam=C((0,[-30,55,-170],[-50,14,0]),(1,[-50,45,-150],[-60,14,0]))),
 dict(name='p13_마름',set='G',t0=216.4,t1=243.0,fps=12,ropes=False,sky=DUST,cam=C((0,[520,260,-520],[0,0,-200]),(1,[420,220,-360],[0,0,-200]))),
 dict(name='p14_쌓기',set='G',t0=243.0,t1=266.8,fps=12,ropes=False,sky=DAY,cam=C((0,[-330,150,-1180],[-560,60,-900]),(1,[-360,130,-1080],[-560,80,-820]))),
 dict(name='p15_노을',set='G',t0=266.8,t1=287.0,fps=24,ropes=False,sky=DUSK,cam=C((0,[200,60,-150],[-200,40,0]),(1,[280,210,-420],[-450,90,0]))),
]
json.dump({'shots':S},open('/home/user/youtubeshot/연재/피라미드강/장면/샷목록.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(S),'shots',sum(round((s['t1']-s['t0'])*s['fps']) for s in S),'frames')
