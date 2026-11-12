"""《길 잃은 밤》 샷 목록 (쇼츠 세로 9:16, 24fps) → 연재/길잃은밤/장면/샷목록.json
   s01(소년 앞장)과 s10(강아지 앞장)은 같은 옆모습 카메라 — 처음과 끝의 뒤바뀜이 보이게.  전신이 보이는 거리가 기본"""
import json
DAY=['#7cc3f3','#e2f4ff']; LATE=['#f0b070','#ffe2b8']; SUNSET=['#6a5a9a','#f4a066']; NIGHT=['#0f1630','#2c3a66']
def C(*keys): return [{'u':u,'pos':p,'tgt':t} for u,p,t in keys]
S=[
 dict(name='s01_앞장',t0=0,t1=5.0,sky=DAY,follow='by_root',cam=C((0,[-10,24,-78],[-10,13,0]),(1,[-8,24,-74],[-10,13,0]))),
 dict(name='s02_뛰어감',t0=5.0,t1=7.6,sky=DAY,follow='by_root',cam=C((0,[46,20,-44],[-6,12,0]),(1,[42,19,-42],[-8,12,0]))),
 dict(name='s03_휘청',t0=7.6,t1=10.0,sky=LATE,follow='dg_root',cam=C((0,[10,15,-46],[2,9,0]),(1,[10,15,-44],[2,9,0]))),
 dict(name='s04_갈림길',t0=10.0,t1=15.0,sky=SUNSET,cam=C((0,[206,30,-70],[212,13,4]),(1,[214,27,-62],[220,13,4]))),
 dict(name='s05_웅크림',t0=15.0,t1=19.0,sky=NIGHT,night=True,cam=C((0,[458,24,-46],[458,12,12]),(1,[457,22,-40],[457,11,12]))),
 dict(name='s06_비빔',t0=19.0,t1=22.2,sky=NIGHT,night=True,cam=C((0,[456,18,-30],[456,9,12]),(1,[456,17,-28],[456,9,12]))),
 dict(name='s07_고개',t0=22.2,t1=25.0,sky=NIGHT,night=True,cam=C((0,[470,17,-30],[462,10,8]),(1,[468,16,-28],[462,10,8]))),
 dict(name='s08_불빛',t0=25.0,t1=27.4,sky=NIGHT,night=True,cam=C((0,[444,22,0],[600,10,3]),(1,[450,20,1],[600,10,3]))),
 dict(name='s09_이끔',t0=27.4,t1=30.0,sky=NIGHT,night=True,cam=C((0,[466,22,-50],[466,12,6]),(1,[480,22,-50],[480,12,4]))),
 dict(name='s10_앞장바뀜',t0=30.0,t1=33.0,sky=NIGHT,night=True,follow='by_root',cam=C((0,[10,24,-78],[10,13,0]),(1,[8,24,-74],[10,13,0]))),
 dict(name='s11_공방',t0=33.0,t1=38.0,sky=NIGHT,night=True,cam=C((0,[846,28,-36],[900,15,24]),(1,[858,26,-32],[900,15,22]))),
 dict(name='s12_안아줌',t0=38.0,t1=42.0,sky=NIGHT,night=True,cam=C((0,[888,22,-44],[888,14,16]),(1,[889,21,-40],[889,14,16]))),
 dict(name='s13_집으로',t0=42.0,t1=45.0,sky=NIGHT,night=True,cam=C((0,[966,30,-26],[904,14,30]),(1,[964,32,-30],[908,15,32]))),
]
for s in S: s.setdefault('set','A'); s.setdefault('fps',24)
json.dump({'aspect':'9:16','fov':50,'shots':S},open('/home/user/youtubeshot/연재/길잃은밤/장면/샷목록.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(S),'shots',sum(round((s['t1']-s['t0'])*s['fps']) for s in S),'frames')
