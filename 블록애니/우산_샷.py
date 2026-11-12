"""《할아버지의 우산》 샷 목록 (쇼츠 세로 9:16, 24fps) → 연재/할아버지의우산/장면/샷목록.json"""
import json
RAIN=['#6f7a88','#aeb6c0']; SPRING=['#8fc8f2','#ffe6f0']; SUMMER=['#4fa8f0','#cdeeff']; AUTUMN=['#e8a060','#ffe0b0']; WINTER=['#9aa8bb','#e6ecf3']; CLEAR=['#f0b070','#ffe6c0']
def C(*keys): return [{'u':u,'pos':p,'tgt':t} for u,p,t in keys]
S=[
 dict(name='s01_혼자',t0=0,t1=2.6,sky=RAIN,rain=True,cam=C((0,[-2,14,-18],[-5,12,10]),(1,[-3,14,-16],[-5,12,10]))),
 dict(name='s02_우산',t0=2.6,t1=5.0,sky=RAIN,rain=True,cam=C((0,[-6,24,-44],[-7,24,11]),(1,[-6,24,-40],[-7,24,11]))),
 dict(name='s03_기울임',t0=5.0,t1=8.0,sky=RAIN,rain=True,cam=C((0,[-6,40,62],[-6,24,8]),(1,[-6,38,58],[-6,24,8]))),
 dict(name='s04_어깨',t0=8.0,t1=11.0,sky=RAIN,rain=True,cam=C((0,[-40,24,-22],[-8,22,10]),(1,[-38,24,-20],[-8,22,10]))),
 dict(name='s05_버스',t0=11.0,t1=13.0,sky=RAIN,rain=True,cam=C((0,[70,30,-44],[-20,14,-12]),(1,[68,30,-42],[-12,14,-12]))),
 dict(name='s06_탄다',t0=13.0,t1=15.2,sky=RAIN,rain=True,cam=C((0,[30,32,30],[2,14,-6]),(1,[28,32,28],[3,14,-6]))),
 dict(name='s07_떠남',t0=15.2,t1=17.0,sky=RAIN,rain=True,follow='bu_root',cam=C((0,[30,24,50],[12,20,8]),(1,[30,24,50],[12,20,8]))),
 dict(name='s08_봄',t0=17.0,t1=18.25,sky=SPRING,cam=C((0,[-72,24,16],[-62,26,72]),(1,[-72,24,20],[-62,26,72]))),
 dict(name='s09_여름',t0=18.25,t1=19.5,sky=SUMMER,cam=C((0,[-72,24,20],[-62,26,72]),(1,[-72,24,24],[-62,26,72]))),
 dict(name='s10_가을',t0=19.5,t1=20.75,sky=AUTUMN,cam=C((0,[-72,24,24],[-62,26,72]),(1,[-72,24,28],[-62,26,72]))),
 dict(name='s11_겨울',t0=20.75,t1=22.0,sky=WINTER,snow=True,cam=C((0,[-72,24,28],[-62,26,72]),(1,[-72,24,32],[-62,26,72]))),
 dict(name='s12_늙은',t0=22.0,t1=27.0,sky=RAIN,rain=True,cam=C((0,[-2,20,-30],[-5,18,10]),(1,[-3,20,-27],[-5,18,10]))),
 dict(name='s13_손녀',t0=27.0,t1=30.0,sky=RAIN,rain=True,cam=C((0,[-6,24,-44],[-7,24,11]),(1,[-6,24,-40],[-7,24,11]))),
 dict(name='s14_기울임',t0=30.0,t1=32.0,sky=RAIN,rain=True,cam=C((0,[-6,40,62],[-6,24,8]),(1,[-6,38,58],[-6,24,8]))),
 dict(name='s15_알아봄',t0=32.0,t1=35.0,sky=RAIN,rain=True,cam=C((0,[2,22,-26],[-8,24,10]),(1,[1,22,-24],[-8,24,10]))),
 dict(name='s16_등',t0=35.0,t1=38.0,sky=RAIN,rain=True,cam=C((0,[-18,22,-18],[-9,20,10]),(1,[-17,21,-16],[-9,20,10]))),
 dict(name='s17_함께',t0=38.0,t1=42.0,sky=RAIN,rain=True,follow='og_root',cam=C((0,[6,24,-50],[-2,18,0]),(1,[6,24,-48],[-2,18,0]))),
 dict(name='s18_갬',t0=42.0,t1=45.0,sky=CLEAR,follow='og_root',cam=C((0,[6,24,-48],[-2,18,0]),(1,[-30,70,-90],[0,15,0]))),
]
for s in S: s.setdefault('set','A'); s.setdefault('fps',24)
json.dump({'aspect':'9:16','fov':50,'shots':S},open('/home/user/youtubeshot/연재/할아버지의우산/장면/샷목록.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(S),'shots',sum(round((s['t1']-s['t0'])*s['fps']) for s in S),'frames')
