"""《돌아온 새》 샷 목록 (24fps).  python 새_샷.py → 쇼츠 세로 샷목록.json / python 새_샷.py 롱폼 → 가로 샷목록_롱폼.json"""
import json, sys
LONG=len(sys.argv)>1 and sys.argv[1]=='롱폼'
STORM=['#5d6670','#9aa3ab']; MORN=['#9fc8f0','#ffe2b8']; DAY=['#6fbcf5','#d6f0ff']; DUSK=['#5a6fb0','#ff9a5a','#ffd39a']
WINTER=['#9aa8bb','#dfe6ef']; SPRING=['#78c2f2','#e6f6ff']; GOLD=['#f0a86a','#ffe2b5']
def C(*keys): return [{'u':u,'pos':p,'tgt':t} for u,p,t in keys]
S=[
 dict(name='s01_바닷가',t0=0,t1=2.5,sky=STORM,cam=C((0,[-38,16,-68],[-10,9,-22]),(1,[-36,15,-66],[-14,9,-28]))),
 dict(name='s02_구함',t0=2.5,t1=5.0,sky=STORM,cam=C((0,[4,18,-62],[-16,9,-35]),(1,[2,17,-60],[-17,9,-36]))),
 dict(name='s03_창가',t0=5.0,t1=8.0,sky=DAY,cam=C((0,[-12,18,-6],[-16,17,30]),(1,[-13,18,-2],[-16,17,30]))),
 dict(name='s04_먹이',t0=8.0,t1=11.0,sky=DAY,cam=C((0,[-15,16,8],[-16,15,28]),(1,[-15,16,10],[-16,15,28]))),
 dict(name='s05_어깨',t0=11.0,t1=13.0,sky=MORN,follow='gm_root',cam=C((0,[10,24,-38],[0,22,0]),(1,[9,23,-36],[0,22,0]))),
 dict(name='s06_연습',t0=13.0,t1=15.0,sky=DAY,cam=C((0,[20,12,-40],[-6,8,-2]),(1,[18,12,-38],[-6,8,-2]))),
 dict(name='s07_노을',t0=15.0,t1=17.0,sky=DUSK,cam=C((0,[34,26,44],[18,4,-60]),(1,[32,25,40],[18,4,-60]))),
 dict(name='s08_떠나보냄',t0=17.0,t1=19.2,sky=DAY,cam=C((0,[8,20,-66],[0,22,-24]),(1,[7,20,-62],[0,25,-24]))),
 dict(name='s09_날아오름',t0=19.2,t1=21.2,sky=DAY,cam=C((0,[14,6,-52],[0,40,-26]),(1,[12,6,-50],[0,42,-28]))),
 dict(name='s10_바다로',t0=21.2,t1=23.0,sky=DAY,cam=C((0,[14,32,26],[0,40,-120]),(1,[12,32,24],[-4,50,-140]))),
 dict(name='s11_겨울',t0=23.0,t1=27.0,sky=WINTER,snow=True,cam=C((0,[40,40,-80],[66,62,70]),(1,[36,40,-74],[64,62,70]))),
 dict(name='s12_빈둥지',t0=27.0,t1=31.0,sky=WINTER,snow=True,cam=C((0,[-12,20,-8],[-16,19,30]),(1,[-13,20,-4],[-16,20,30]))),
 dict(name='s13_봄',t0=31.0,t1=34.0,sky=SPRING,cam=C((0,[-12,18,-6],[-16,17,30]),(1,[-13,18,-3],[-16,17,30]))),
 dict(name='s14_하늘',t0=34.0,t1=37.0,sky=SPRING,cam=C((0,[2,24,-44],[-8,22,14]),(1,[0,24,-42],[-6,24,6]))),
 dict(name='s15_돌아옴',t0=37.0,t1=39.45,sky=SPRING,follow='bd_root',cam=C((0,[6,8,-30],[0,0,20]),(1,[6,8,-28],[0,0,20]))),
 dict(name='s16_새끼들',t0=39.45,t1=42.0,sky=SPRING,cam=C((0,[6,28,-46],[-12,20,18]),(1,[5,27,-44],[-12,20,18]))),
 dict(name='s17_등대',t0=42.0,t1=45.0,sky=GOLD,cam=C((0,[3,27,-38],[-10,20,15]),(0.3,[2,30,-48],[-6,22,12]),(1,[14,60,-110],[22,44,40]))),
]
for s in S: s.setdefault('set','A'); s.setdefault('fps',24)
LONG_FIX={}
if LONG:
    for sh in S: sh.update(LONG_FIX.get(sh['name'],{}))
    json.dump({'aspect':'16:9','fov':34,'shots':S},open('/home/user/youtubeshot/연재/돌아온새/장면/샷목록_롱폼.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
else:
    json.dump({'aspect':'9:16','fov':50,'shots':S},open('/home/user/youtubeshot/연재/돌아온새/장면/샷목록.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(S),'shots',sum(round((s['t1']-s['t0'])*s['fps']) for s in S),'frames')
