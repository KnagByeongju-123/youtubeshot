"""《빈 밥그릇》 샷 목록 (24fps).  python 밥그릇_샷.py → 쇼츠 세로 9:16 샷목록.json / python 밥그릇_샷.py 롱폼 → 가로 16:9 샷목록_롱폼.json"""
import json, sys
LONG=len(sys.argv)>1 and sys.argv[1]=='롱폼'
RAIN=['#6f7a88','#aeb6c0']; MORN=['#9fc8f0','#ffe2b8']; DAY=['#6fbcf5','#d6f0ff']; DUSK=['#5a6fb0','#ff9a5a','#ffd39a']; GOLD=['#f0a86a','#ffe2b5']
def C(*keys): return [{'u':u,'pos':p,'tgt':t} for u,p,t in keys]
S=[
 dict(name='s01_비',t0=0,t1=5.0,sky=RAIN,rain=True,cam=C((0,[-36,16,-18],[-56,7,30]),(1,[-42,13,-6],[-56,7,30]))),
 dict(name='s02_꼬마',t0=5.0,t1=7.5,sky=RAIN,rain=True,follow='kd_root',cam=C((0,[22,16,-42],[0,12,0]),(1,[16,15,-40],[-4,12,0]))),
 dict(name='s03_그릇',t0=7.5,t1=11.0,sky=RAIN,rain=True,cam=C((0,[-22,50,-95],[-24,12,40]),(1,[-34,40,-78],[-40,10,30]))),
 dict(name='s04_아침',t0=11.0,t1=13.0,sky=MORN,cam=C((0,[-38,40,-30],[-50,4,22]),(1,[-40,36,-26],[-50,4,22]))),
 dict(name='s05_따라감',t0=13.0,t1=15.0,sky=DAY,follow='kd_root',cam=C((0,[8,18,-80],[9,8,0]),(1,[8,18,-76],[9,8,0]))),
 dict(name='s06_저녁',t0=15.02,t1=17.0,sky=DUSK,cam=C((0,[-6,16,12],[-5,9,72]),(1,[-6,14,20],[-5,9,72]))),
 dict(name='s07_이삿날',t0=17.0,t1=19.0,sky=DAY,cam=C((0,[-25,22,-12],[2,14,50]),(1,[-25,20,-10],[6,12,20]))),
 dict(name='s07b_망설임',t0=19.0,t1=20.4,sky=DAY,cam=C((0,[-56,16,-6],[-34,12,16]),(1,[-56,15,-4],[-30,12,14]))),
 dict(name='s08_트럭으로',t0=20.4,t1=23.0,sky=DAY,cam=C((0,[-15,24,52],[-8,10,-15]),(1,[2,24,50],[24,10,-15]))),
 dict(name='s09_떠남',t0=23.0,t1=25.2,sky=DAY,cam=C((0,[-75,16,70],[-10,8,-10]),(1,[-75,16,70],[5,8,-14]))),
 dict(name='s10_빈그릇',t0=25.2,t1=26.5,sky=DAY,cam=C((0,[-30,20,-2],[-50,5,18]),(1,[-31,19,0],[-50,5,18]))),
 dict(name='s11_달림',t0=26.5,t1=30.0,sky=DAY,follow='dg_root',cam=C((0,[22,16,-60],[6,8,0]),(1,[18,15,-56],[6,8,0]))),
 dict(name='s12_창문',t0=30.0,t1=32.0,sky=DAY,follow='tr_root',cam=C((0,[30,26,40],[23,21,6]),(1,[29,25,36],[23,21,6]))),
 dict(name='s13_뒤에',t0=32.0,t1=33.6,sky=DAY,follow='tr_root',cam=C((0,[-25,30,10],[-130,5,34]),(1,[-25,30,10],[-120,5,34]))),
 dict(name='s14_팔잡기',t0=33.6,t1=35.6,sky=DAY,follow='tr_root',cam=C((0,[75,24,0],[24,20,0]),(1,[68,23,0],[24,20,0]))),
 dict(name='s15_멈춤',t0=35.6,t1=38.4,sky=GOLD,cam=C((0,[425,34,75],[425,8,-8]),(1,[415,30,70],[410,8,-2]))),
 dict(name='s16_내려놓기',t0=38.4,t1=40.8,sky=GOLD,cam=C((0,[398,15,50],[402,8,2]),(1,[399,15,46],[402,8,2]))),
 dict(name='s17_함께',t0=40.8,t1=45.0,sky=GOLD,cam=C((0,[410,20,36],[410,14,4]),(0.35,[412,22,42],[412,13,4]),(1,[432,60,78],[432,8,-12]))),
]
for s in S: s.setdefault('set','A'); s.setdefault('fps',24)
LONG_FIX={   # 가로 화면에서 따로 고칠 샷
 's04_아침': dict(cam=C((0,[12,18,16],[-50,8,18]),(1,[8,17,17],[-50,8,18]))),          # 옆에서: 꼬마·그릇·강아지가 한 줄로 보이게
 's17_함께': dict(cam=C((0,[410,24,46],[410,17,4]),(0.35,[412,24,50],[412,15,4]),(1,[432,60,78],[432,8,-12]))),   # 안긴 강아지 머리가 잘리지 않게
}
if LONG:   # 가로: 같은 카메라 자리, 화각만 좁혀 인물 크기를 비슷하게 (옆이 넓게 보임)
    for sh in S: sh.update(LONG_FIX.get(sh['name'],{}))
    json.dump({'aspect':'16:9','fov':34,'shots':S},open('/home/user/youtubeshot/연재/빈밥그릇/장면/샷목록_롱폼.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
else:
    json.dump({'aspect':'9:16','fov':50,'shots':S},open('/home/user/youtubeshot/연재/빈밥그릇/장면/샷목록.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(S),'shots',sum(round((s['t1']-s['t0'])*s['fps']) for s in S),'frames')
