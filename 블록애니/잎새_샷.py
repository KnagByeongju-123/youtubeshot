"""《마지막 잎새》 샷 목록 (쇼츠 세로 9:16, 24fps) → 연재/마지막잎새/장면/샷목록.json"""
import json
GREY=['#9aa5b1','#d5dbe0']; ROOM=['#d8c4a0','#f0e2c8']; NIGHT=['#141a2e','#2c3654']; MORN=['#a9cbe8','#ffe8c8']; SPRING=['#8cc8f0','#e8f6ff']
def C(*keys): return [{'u':u,'pos':p,'tgt':t} for u,p,t in keys]
S=[
 dict(name='s01_소녀',t0=0,t1=2.8,sky=GREY,cam=C((0,[24,25,-26],[3,17,1]),(1,[22,24,-23],[3,17,1]))),
 dict(name='s02_창밖',t0=2.8,t1=6.0,sky=GREY,cam=C((0,[-16,25,-7],[60,32,1]),(1,[-10,25,-5],[60,32,1]))),
 dict(name='s03_할아버지',t0=6.0,t1=9.3,sky=GREY,cam=C((0,[-9,31,-72],[-9,18,-6]),(1,[-9,30,-67],[-9,18,-6]))),
 dict(name='s04_올려다봄',t0=9.3,t1=11.0,sky=GREY,cam=C((0,[-30,42,-30],[40,26,2]),(1,[-29,41,-28],[40,26,2]))),
 dict(name='s05_폭풍',t0=11.0,t1=13.4,sky=NIGHT,night=True,rain=True,cam=C((0,[54,37,-8],[69.5,36,0]),(1,[55,37,-7],[69.5,36,0]))),
 dict(name='s06_사다리',t0=13.4,t1=16.2,sky=NIGHT,night=True,rain=True,cam=C((0,[38,30,-62],[60,22,0]),(1,[39,30,-57],[60,24,0]))),
 dict(name='s07_그림',t0=16.2,t1=19.4,sky=NIGHT,night=True,rain=True,cam=C((0,[40,40,-34],[62,30,0]),(1,[42,40,-30],[62,31,0]))),
 dict(name='s08_아침잎',t0=19.4,t1=21.0,sky=MORN,cam=C((0,[14,27,-2],[70,35,0]),(1,[18,28,-1],[70,35,0]))),
 dict(name='s09_손뻗음',t0=21.0,t1=24.0,sky=MORN,cam=C((0,[24,25,-26],[3,17,1]),(1,[22,24,-23],[3,18,1]))),
 dict(name='s10_봄',t0=24.0,t1=29.0,sky=SPRING,cam=C((0,[38,24,-44],[60,18,-1]),(1,[39,24,-40],[60,18,-1]))),
 dict(name='s11_세월',t0=29.0,t1=33.0,sky=SPRING,cam=C((0,[44,30,-28],[69,28,-2]),(1,[46,30,-25],[69,28,-2]))),
 dict(name='s12_다시겨울',t0=33.0,t1=35.4,sky=GREY,cam=C((0,[-13,32,-11],[60,31,2]),(1,[-9,32,-9],[60,31,2]))),
 dict(name='s13_어른소녀',t0=35.4,t1=38.0,sky=GREY,cam=C((0,[-9,31,-72],[-9,18,-6]),(1,[-9,30,-67],[-9,18,-6]))),
 dict(name='s14_눈밤',t0=38.0,t1=39.6,sky=NIGHT,night=True,snow=True,cam=C((0,[38,30,-62],[60,22,0]),(1,[39,30,-57],[60,24,0]))),
 dict(name='s15_새잎',t0=39.6,t1=41.2,sky=NIGHT,night=True,snow=True,cam=C((0,[37,40,-42],[62,30,-3]),(1,[38,40,-38],[62,31,-3]))),
 dict(name='s16_두잎',t0=41.2,t1=43.0,sky=MORN,cam=C((0,[14,27,-3],[70,35,-3]),(1,[18,28,-3],[70,35,-3]))),
 dict(name='s17_함께',t0=43.0,t1=45.0,sky=MORN,cam=C((0,[22,28,-28],[5,17,4]),(1,[30,42,-52],[5,15,4]))),
]
for s in S: s.setdefault('set','A'); s.setdefault('fps',24)
json.dump({'aspect':'9:16','fov':50,'shots':S},open('/home/user/youtubeshot/연재/마지막잎새/장면/샷목록.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(S),'shots',sum(round((s['t1']-s['t0'])*s['fps']) for s in S),'frames')
