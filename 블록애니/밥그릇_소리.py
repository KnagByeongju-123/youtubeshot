"""《빈 밥그릇》 소리: 오르골(슬픔 → 따뜻함) + 빗소리(0~11초) + 트럭 엔진(23~35.6초).  자체 합성(저작권 걱정 없음)
   사용: xvfb-run -a python -X utf8 블록애니/밥그릇_소리.py <결과.wav>"""
import sys, os, importlib.util
import numpy as np
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m', os.path.join(BASE,'shorts_novel_maker_supertonic.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SR=m.SR; L=45.0; n=int(L*SR); rng=np.random.default_rng(11)
t=np.arange(n)/SR
def env(points):
    xs,ys=zip(*points); return np.interp(t,xs,ys).astype(np.float32)[:,None]
sad=m.gen_musicbox(n,rng,'sad',66); warm=m.gen_musicbox(n,np.random.default_rng(5),'warm',72)
pad=m.gen_pad(n,rng,'warm')
music=sad*env([(0,0),(0.8,0.5),(11,0.55),(11.5,0.8),(23,0.8),(24,1.0),(34.5,1.0),(36,0)]) \
     +warm*env([(0,0),(34.5,0),(36,0.95),(43,0.95),(45,0)]) \
     +pad*env([(0,0),(23,0),(26,0.35),(34,0.45),(36,0.25),(43,0.25),(45,0)])
rain=m.gen_rain(n,rng)*env([(0,0),(0.4,0.55),(10.6,0.55),(11.0,0)])
# 트럭 엔진: 낮게 웅웅(시동 23초) → 멀어짐, 30~35.6초는 안에서 듣는 작은 소리
f0=np.interp(t,[0,23,24,26,30,35,35.6,45],[28,28,40,52,55,48,30,30])
ph=2*np.pi*np.cumsum(f0)/SR
eng=(np.sin(ph)+0.5*np.sin(2*ph)+0.3*np.sin(3*ph))*(0.7+0.3*np.sin(ph*0.5))
eng=eng+0.4*m.band(m.colored_noise(n,rng,2.0),hi=400)
eng=(m._norm(eng)[:,None]*np.ones((1,2)))*env([(0,0),(22.9,0),(23.1,0.5),(24.5,0.45),(29.8,0.08),(30.0,0.18),(35.0,0.18),(35.7,0),(45,0)])
mix=m._norm(music,0.55)+rain*0.5+eng*0.55
mix=mix*env([(0,0),(0.5,1),(43.5,1),(45,0)])
mix=m._norm(mix,0.89)
m.write_wav(sys.argv[1],mix); print('ok',sys.argv[1])
