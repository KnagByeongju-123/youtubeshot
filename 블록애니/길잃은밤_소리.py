"""《길 잃은 밤》 소리: 밝은 오르골(숲길) → 해 질 녘 느려지고 작아짐 → 밤은 쓸쓸한 패드 + 귀뚜라미·부엉이
   → 불빛을 볼 때 오르골이 살아남 → 강아지가 이끌 때 따뜻하게 → 할아버지 품에서 가장 따뜻하게.  자체 합성
   사용: xvfb-run -a python -X utf8 블록애니/길잃은밤_소리.py <결과.wav>"""
import sys, os, importlib.util
import numpy as np
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m', os.path.join(BASE,'shorts_novel_maker_supertonic.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SR=m.SR; L=45.0; n=int(L*SR); rng=np.random.default_rng(52)
t=np.arange(n)/SR
def env(points):
    xs,ys=zip(*points); return np.interp(t,xs,ys).astype(np.float32)[:,None]
bright=m.gen_musicbox(n,rng,'warm',108); sad=m.gen_musicbox(n,np.random.default_rng(9),'sad',58); warm=m.gen_musicbox(n,np.random.default_rng(21),'warm',78)
pad=m.gen_pad(n,rng,'warm'); spad=m.gen_pad(n,rng,'sad')
music=bright*env([(0,0),(0.4,0.8),(9.5,0.8),(12,0.35),(15,0),(45,0)]) \
     +sad*env([(0,0),(11,0),(13,0.4),(15,0.6),(21.5,0.55),(22.4,0),(45,0)]) \
     +warm*env([(0,0),(23.5,0),(25,0.5),(27.5,0.75),(33,0.7),(35,0.6),(38,0.9),(42,0.95),(45,0)]) \
     +spad*env([(0,0),(11,0),(14,0.3),(22,0.35),(24,0),(45,0)]) + pad*env([(0,0),(24,0),(27,0.3),(36,0.35),(38.5,0.5),(45,0)])
# 나무 발소리·발 걸림 '톡'
hit=np.zeros(n,np.float32)
def knock(t0,f=520,a=1.0,d=0.08):
    k=int(d*SR); tt=np.arange(k)/SR; s=np.sin(2*np.pi*f*tt)*np.exp(-tt/0.02)+0.4*np.sin(2*np.pi*f*2.7*tt)*np.exp(-tt/0.01)
    i=int(t0*SR); hit[i:i+k]+=(s*a)[:max(0,min(k,n-i))]
for t0,f,a in [(8.05,430,1.0),(8.2,560,0.6),(8.42,500,0.5)]: knock(t0,f,a)
for t0 in np.arange(0.3,10,0.6): knock(t0,780,0.12,0.04)            # 소년 나무 신발 발소리 (작게)
for t0 in np.arange(28.6,33,0.6): knock(t0,760,0.12,0.04)
# 밤: 귀뚜라미 + 부엉이 두 번 '부-엉'
crickets=m.band(m.colored_noise(n,rng,0.5),lo=4000,hi=7000)*(0.5+0.5*np.sign(np.sin(2*np.pi*14*t)))
crickets=(m._norm(crickets)[:,None]*np.ones((1,2)))*env([(0,0),(14.6,0),(15.2,0.1),(32.5,0.1),(34,0.05),(44,0.05),(45,0)])
owl=np.zeros(n,np.float32)
for t0,f in [(16.4,390),(17.1,350)]:
    k=int(0.45*SR); tt=np.arange(k)/SR; e=np.sin(np.pi*tt/0.45)**1.5
    s=np.sin(2*np.pi*(f*tt+3*np.sin(2*np.pi*5*tt)))*e; i=int(t0*SR); owl[i:i+k]+=s
mix=m._norm(music,0.55)+(m._norm(hit)[:,None]*np.ones((1,2)))*0.3+crickets+(m._norm(owl)[:,None]*np.ones((1,2)))*0.18
mix=mix*env([(0,0),(0.4,1),(43.5,1),(45,0)])
m.write_wav(sys.argv[1],m._norm(mix,0.89)); print('ok')
