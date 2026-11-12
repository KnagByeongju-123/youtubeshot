"""《돌아온 새》 소리: 오르골(슬픔→밝음) + 파도·바람 + 새 지저귐(37초~).  자체 합성
   사용: xvfb-run -a python -X utf8 블록애니/새_소리.py <결과.wav>"""
import sys, os, importlib.util
import numpy as np
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m', os.path.join(BASE,'shorts_novel_maker_supertonic.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SR=m.SR; L=45.0; n=int(L*SR); rng=np.random.default_rng(21)
t=np.arange(n)/SR
def env(points):
    xs,ys=zip(*points); return np.interp(t,xs,ys).astype(np.float32)[:,None]
sad=m.gen_musicbox(n,rng,'sad',66); warm=m.gen_musicbox(n,np.random.default_rng(9),'warm',80); pad=m.gen_pad(n,rng,'warm')
music=sad*env([(0,0),(4,0),(5.5,0.6),(17,0.7),(18.5,0.95),(22.5,0.95),(24,0.25),(30.5,0.25),(31.5,0)]) \
     +warm*env([(0,0),(30.5,0),(32,0.6),(37,0.7),(39,1.0),(43,1.0),(45,0)]) \
     +pad*env([(0,0),(17,0),(19,0.35),(23,0.3),(31,0.15),(38,0.35),(45,0)])
waves=m.gen_waves(n,rng)*env([(0,0.55),(5,0.35),(17,0.3),(23,0.3),(23.5,0.15),(31,0.15),(31.5,0.3),(45,0.25)])
wind=m.gen_wind(n,rng)*env([(0,0.55),(4.5,0.5),(5.5,0),(22.8,0),(24,0.6),(30.5,0.6),(31.5,0)])
# 새 지저귐: 짧게 높아졌다 내려가는 소리 묶음
chirp=np.zeros(n,np.float32)
def tweet(t0,f0=3200,f1=4600,d=0.09,a=1.0):
    k=int(d*SR); tt=np.arange(k)/SR; f=np.linspace(f0,f1,k)
    s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*tt/d)**2*a
    i=int(t0*SR); chirp[i:i+k]+=s[:max(0,min(k,n-i))]
r=np.random.default_rng(4)
for t0 in (4.4,4.7,9.0,9.3,12.0,20.0,20.25):          # 앞부분 몇 번 (작게)
    tweet(t0,a=0.35)
tt0=37.4
while tt0<44.0:
    for j in range(r.integers(2,5)):
        tweet(tt0+j*0.13,f0=r.uniform(2800,3600),f1=r.uniform(4200,5200),a=r.uniform(0.5,0.9))
    tt0+=r.uniform(0.6,1.3)
chirp=(chirp[:,None]*np.ones((1,2)))
mix=m._norm(music,0.55)+waves*0.35+wind*0.3+chirp*0.12
mix=mix*env([(0,0),(0.5,1),(43.5,1),(45,0)])
m.write_wav(sys.argv[1],m._norm(mix,0.89)); print('ok')
