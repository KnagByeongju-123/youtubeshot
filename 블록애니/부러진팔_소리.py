"""《부러진 팔》 소리: 밝은 오르골(놀이) → 넘어질 때 멈춤 → 슬픈 오르골 → 밤은 작게 → 팔을 건넬 때 따뜻하게 → 끝 밝게.  자체 합성
   사용: xvfb-run -a python -X utf8 블록애니/부러진팔_소리.py <결과.wav>"""
import sys, os, importlib.util
import numpy as np
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m', os.path.join(BASE,'shorts_novel_maker_supertonic.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SR=m.SR; L=45.0; n=int(L*SR); rng=np.random.default_rng(44)
t=np.arange(n)/SR
def env(points):
    xs,ys=zip(*points); return np.interp(t,xs,ys).astype(np.float32)[:,None]
bright=m.gen_musicbox(n,rng,'warm',104); sad=m.gen_musicbox(n,np.random.default_rng(7),'sad',60); warm=m.gen_musicbox(n,np.random.default_rng(15),'warm',76)
pad=m.gen_pad(n,rng,'warm'); spad=m.gen_pad(n,rng,'sad')
music=bright*env([(0,0),(0.4,0.8),(6.4,0.8),(6.7,0),(45,0)]) \
     +sad*env([(0,0),(7.6,0),(9.0,0.75),(15,0.6),(15.5,0.3),(22,0.3),(23,0.55),(25.5,0.55),(26.5,0),(45,0)]) \
     +warm*env([(0,0),(25.5,0),(27,0.8),(33,0.7),(34,0.55),(38,0.6),(40,0.9),(45,0)]) \
     +pad*env([(0,0),(26,0),(28,0.3),(38,0.3),(40.5,0.45),(45,0)]) + spad*env([(0,0),(7,0),(8.5,0.35),(22,0.3),(24,0),(45,0)])
# 넘어지는 소리: 나무가 부딪치는 '톡·딱'
hit=np.zeros(n,np.float32)
def knock(t0,f=520,a=1.0,d=0.09):
    k=int(d*SR); tt=np.arange(k)/SR; s=np.sin(2*np.pi*f*tt)*np.exp(-tt/0.025)+0.5*np.sin(2*np.pi*f*2.7*tt)*np.exp(-tt/0.012)
    i=int(t0*SR); hit[i:i+k]+=(s*a)[:max(0,min(k,n-i))]
for t0,f,a in [(6.72,420,1.0),(6.86,560,0.7),(7.05,640,0.5),(7.22,700,0.35),(19.35,480,0.6),(37.0,600,0.4),(40.05,620,0.5)]: knock(t0,f,a)
crickets=m.band(m.colored_noise(n,rng,0.5),lo=4000,hi=7000)*(0.5+0.5*np.sign(np.sin(2*np.pi*14*t)))
crickets=(m._norm(crickets)[:,None]*np.ones((1,2)))*env([(0,0),(15,0),(15.3,0.12),(21.8,0.12),(22,0),(45,0)])
mix=m._norm(music,0.55)+(m._norm(hit)[:,None]*np.ones((1,2)))*0.35+crickets
mix=mix*env([(0,0),(0.4,1),(43.5,1),(45,0)])
m.write_wav(sys.argv[1],m._norm(mix,0.89)); print('ok')
