"""《마지막 공놀이》 소리: 밝은 오르골 → 세월 장면 조금 커짐 → 슬픈 오르골 → 꼬리 흔들 때 따뜻하게 → 노을에서 조용히.  자체 합성
   사용: xvfb-run -a python -X utf8 블록애니/공놀이_소리.py <결과.wav>"""
import sys, os, importlib.util
import numpy as np
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m', os.path.join(BASE,'shorts_novel_maker_supertonic.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SR=m.SR; L=45.0; n=int(L*SR); rng=np.random.default_rng(55)
t=np.arange(n)/SR
def env(points):
    xs,ys=zip(*points); return np.interp(t,xs,ys).astype(np.float32)[:,None]
bright=m.gen_musicbox(n,rng,'warm',100); sad=m.gen_musicbox(n,np.random.default_rng(8),'sad',58); warm=m.gen_musicbox(n,np.random.default_rng(16),'warm',70)
pad=m.gen_pad(n,rng,'warm')
music=bright*env([(0,0),(0.4,0.8),(13.5,0.8),(14.2,0.5),(17.6,0.4),(18.5,0),(45,0)]) \
     +sad*env([(0,0),(17.5,0),(19,0.65),(30,0.6),(33.5,0.5),(34.8,0),(45,0)]) \
     +warm*env([(0,0),(33.8,0),(35.2,0.8),(42,0.7),(45,0)]) \
     +pad*env([(0,0),(13.5,0),(15,0.35),(18,0.25),(24,0.3),(34,0.35),(38,0.45),(45,0)])
# 공 튀는 소리
hit=np.zeros(n,np.float32)
def bump(t0,a=1.0):
    k=int(0.08*SR); tt=np.arange(k)/SR; s=np.sin(2*np.pi*180*tt)*np.exp(-tt/0.03)+0.4*m.band(rng.standard_normal(k).astype(np.float32),hi=900)*np.exp(-tt/0.02)
    i=int(t0*SR); hit[i:i+k]+=(s*a)[:max(0,min(k,n-i))]
for t0,a in [(2.98,1),(3.25,0.5),(9.9,1),(10.15,0.5),(20.4,0.9),(20.65,0.45),(33.0,0.25),(34.4,0.3)]: bump(t0,a)
wind=m.gen_wind(n,rng)*env([(0,0.12),(45,0.12)])
mix=m._norm(music,0.55)+(m._norm(hit)[:,None]*np.ones((1,2)))*0.3+wind*0.25
mix=mix*env([(0,0),(0.4,1),(43,1),(45,0)])
m.write_wav(sys.argv[1],m._norm(mix,0.89)); print('ok')
