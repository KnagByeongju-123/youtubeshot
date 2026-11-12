"""《할아버지의 우산》 소리: 빗소리 + 오르골(슬픔 → 세월 장면 커짐 → 다시 작게 → 손잡을 때 따뜻하게) + 버스 엔진.  자체 합성
   사용: xvfb-run -a python -X utf8 블록애니/우산_소리.py <결과.wav>"""
import sys, os, importlib.util
import numpy as np
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m', os.path.join(BASE,'shorts_novel_maker_supertonic.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SR=m.SR; L=45.0; n=int(L*SR); rng=np.random.default_rng(33)
t=np.arange(n)/SR
def env(points):
    xs,ys=zip(*points); return np.interp(t,xs,ys).astype(np.float32)[:,None]
sad=m.gen_musicbox(n,rng,'sad',64); warm=m.gen_musicbox(n,np.random.default_rng(12),'warm',76); pad=m.gen_pad(n,rng,'warm')
music=sad*env([(0,0),(0.8,0.55),(16.5,0.6),(17.2,0.9),(21.5,0.9),(22.5,0.45),(32.0,0.5),(33.5,0)]) \
     +warm*env([(0,0),(32.0,0),(34.0,0.8),(42.0,0.9),(43.0,1.0),(45,0)]) \
     +pad*env([(0,0),(16.5,0),(18,0.4),(21.5,0.35),(23,0.1),(33,0.2),(38,0.4),(45,0)])
rain=m.gen_rain(n,rng)*env([(0,0),(0.4,0.6),(16.8,0.6),(17.2,0),(21.8,0),(22.3,0.6),(41.5,0.55),(43.0,0)])
f0=np.interp(t,[0,11,12.6,15.2,16,17,45],[30,48,34,32,46,56,56]); ph=2*np.pi*np.cumsum(f0)/SR
eng=(np.sin(ph)+0.5*np.sin(2*ph)+0.3*np.sin(3*ph))*(0.7+0.3*np.sin(ph*0.5))+0.4*m.band(m.colored_noise(n,rng,2.0),hi=400)
eng=(m._norm(eng)[:,None]*np.ones((1,2)))*env([(0,0),(10.9,0),(11.6,0.35),(12.6,0.3),(15.2,0.25),(16.0,0.4),(17.0,0.15),(17.1,0),(45,0)])
mix=m._norm(music,0.55)+rain*0.5+eng*0.5
mix=mix*env([(0,0),(0.5,1),(43.5,1),(45,0)])
m.write_wav(sys.argv[1],m._norm(mix,0.89)); print('ok')
