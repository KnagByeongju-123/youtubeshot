"""《마지막 잎새》 소리: 쓸쓸한 오르골(겨울) → 비바람·천둥(밤) → 따뜻한 아침 → 밝은 봄(새소리) → 세월 바람 → 다시 쓸쓸 → 눈 오는 밤(조용) → 끝 따뜻하게.  자체 합성
   사용: xvfb-run -a python -X utf8 블록애니/잎새_소리.py <결과.wav>"""
import sys, os, importlib.util
import numpy as np
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m', os.path.join(BASE,'shorts_novel_maker_supertonic.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SR=m.SR; L=45.0; n=int(L*SR); rng=np.random.default_rng(21)
t=np.arange(n)/SR
def env(points):
    xs,ys=zip(*points); return np.interp(t,xs,ys).astype(np.float32)[:,None]
sad=m.gen_musicbox(n,rng,'sad',62); warm=m.gen_musicbox(n,np.random.default_rng(9),'warm',76); bright=m.gen_musicbox(n,np.random.default_rng(4),'warm',100)
pad=m.gen_pad(n,rng,'warm'); spad=m.gen_pad(n,rng,'sad')
music=sad*env([(0,0),(0.6,0.6),(10.6,0.6),(11.4,0.18),(18.8,0.18),(19.6,0),(32.6,0),(33.4,0.6),(37.6,0.6),(38.2,0.25),(41.0,0.25),(41.6,0),(45,0)]) \
     +warm*env([(0,0),(19.4,0),(20.6,0.75),(23.6,0.8),(24.2,0),(41.2,0),(42.2,0.95),(45,0.9)]) \
     +bright*env([(0,0),(23.8,0),(24.4,0.85),(32.4,0.75),(33.2,0),(45,0)]) \
     +pad*env([(0,0),(18.8,0),(20.2,0.4),(24,0.25),(33,0.2),(33.4,0),(40.6,0),(42,0.45),(45,0.4)]) \
     +spad*env([(0,0),(0.5,0.25),(19.2,0.3),(19.8,0),(33,0),(34,0.25),(41.2,0.3),(41.8,0),(45,0)])
rain=m.gen_rain(n,rng)*env([(0,0),(10.8,0),(11.2,0.75),(19.2,0.7),(19.5,0),(45,0)])
wind=m.gen_wind(n,rng)*env([(0,0),(0.4,0.18),(10.8,0.2),(11.2,0.6),(19.2,0.55),(19.5,0.05),(24,0),(29.8,0),(30.4,0.25),(31.0,0.05),(31.6,0.3),(32.4,0.1),(33,0.18),(38,0.18),(38.3,0.1),(41.2,0.08),(41.6,0),(45,0)])
fx=np.zeros(n,np.float32)
def add(sig,t0,a=1.0):
    i=int(t0*SR); k=min(len(sig),n-i); fx[i:i+k]+=sig[:k]*a
add(m.ne_thunder_near(np.random.default_rng(3)),11.25,0.9); add(m.ne_thunder_far(np.random.default_rng(5)),15.6,0.7)
def chirp(t0,f0=3200,f1=4200,d=0.09):
    k=int(d*SR); tt=np.arange(k)/SR; f=np.linspace(f0,f1,k); s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*tt/d)
    add(s.astype(np.float32),t0,0.25)
for t0 in (24.6,24.75,25.9,26.05,27.3,27.42,28.5,30.0,30.15):
    chirp(t0, 3000+rng.uniform(0,600), 4000+rng.uniform(0,800))
def rustle(t0,d=0.35,a=0.15):   # 잎 떨어지는 바스락
    k=int(d*SR); s=m.band(m.colored_noise(k,rng,0.5),lo=2500,hi=8000)*np.sin(np.pi*np.arange(k)/k)
    add(m._norm(s),t0,a)
for t0 in (1.6,4.3,9.4,12.6,34.4,37.2): rustle(t0)
def tock(t0,f=480,a=0.4):        # 나무 인형 발·사다리 '톡'
    k=int(0.08*SR); tt=np.arange(k)/SR; s=np.sin(2*np.pi*f*tt)*np.exp(-tt/0.02)
    add(s.astype(np.float32),t0,a)
for t0 in (14.4,14.9,15.4,15.9,38.4,38.73,39.07,39.4): tock(t0,520,0.35)
for i,t0 in enumerate(np.arange(6.0,7.6,0.31)): tock(t0,300,0.25)
for i,t0 in enumerate(np.arange(35.4,36.8,0.31)): tock(t0,300,0.25)
for t0 in (7.0,7.25,7.5): tock(t0,220,0.3)    # 기침 (어깨 들썩)
fx2=m._norm(fx)[:,None]*np.ones((1,2))
mix=m._norm(music,0.55)+rain*0.42+wind*0.3+fx2*0.32
mix=mix*env([(0,0),(0.5,1),(43.4,1),(45,0)])
m.write_wav(sys.argv[1],m._norm(mix,0.89)); print('ok')
