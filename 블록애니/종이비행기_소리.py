"""《창문 너머 종이비행기》 소리: 쓸쓸한 오르골(창가) → 비행기가 날아들 때 밝게 → 날마다 따뜻하게 → 퇴원 날 가장 밝게 → 새 아이를 볼 때 잠깐 조용 → 다시 따뜻하게.  자체 합성
   사용: xvfb-run -a python -X utf8 블록애니/종이비행기_소리.py <결과.wav>"""
import sys, os, importlib.util
import numpy as np
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m', os.path.join(BASE,'shorts_novel_maker_supertonic.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SR=m.SR; L=45.0; n=int(L*SR); rng=np.random.default_rng(33)
t=np.arange(n)/SR
def env(points):
    xs,ys=zip(*points); return np.interp(t,xs,ys).astype(np.float32)[:,None]
sad=m.gen_musicbox(n,np.random.default_rng(8),'sad',62); bright=m.gen_musicbox(n,rng,'warm',96)
warm=m.gen_musicbox(n,np.random.default_rng(16),'warm',78); pad=m.gen_pad(n,rng,'warm')
music=sad*env([(0,0),(0.3,0.55),(6.0,0.5),(8.6,0.2),(9.6,0),(35.2,0),(36.0,0.4),(38.4,0.35),(39.4,0),(45,0)]) \
     +bright*env([(0,0),(8.4,0),(9.4,0.7),(19,0.7),(19.5,0.45),(26.6,0.45),(27.2,0.85),(34.6,0.8),(35.6,0),(45,0)]) \
     +warm*env([(0,0),(18.8,0),(19.6,0.55),(26.8,0.5),(27.4,0),(38.8,0),(40.2,0.75),(45,0.85)]) \
     +pad*env([(0,0.15),(9,0.25),(19,0.35),(27,0.4),(35.6,0.2),(40,0.45),(45,0.45)])
fx=np.zeros(n,np.float32)
def put(t0,s,a=1.0):
    i=int(t0*SR); k=min(len(s),n-i)
    if k>0: fx[i:i+k]+=s[:k]*a
def noise(k): return rng.standard_normal(k).astype(np.float32)
def bump(t0,a=1.0):   # 공 차는 소리
    k=int(0.08*SR); tt=np.arange(k)/SR
    put(t0,(np.sin(2*np.pi*170*tt)*np.exp(-tt/0.03)+0.4*m.band(noise(k),hi=900)*np.exp(-tt/0.02)).astype(np.float32),a)
def rustle(t0,dur=0.5,a=0.4):   # 종이 접는 소리
    k=int(dur*SR); tt=np.arange(k)/SR
    s=m.band(noise(k),lo=1500,hi=7000)*(0.5+0.5*np.abs(np.sin(2*np.pi*9*tt)))*np.minimum(1,(dur-tt)/0.05)
    put(t0,s.astype(np.float32),a)
def whoosh(t0,dur=1.2,a=0.35):   # 비행기 바람 소리
    k=int(dur*SR); tt=np.arange(k)/SR
    s=m.band(noise(k),lo=500,hi=3000)*np.sin(np.pi*tt/dur)**2; put(t0,s.astype(np.float32),a)
def clap(t0,a=0.7):
    k=int(0.05*SR); tt=np.arange(k)/SR; put(t0,(m.band(noise(k),lo=800,hi=5000)*np.exp(-tt/0.008)).astype(np.float32),a)
def door(t0):
    k=int(0.7*SR); tt=np.arange(k)/SR
    s=np.sin(2*np.pi*(180+80*tt)*tt)*0.3*np.exp(-tt/0.4)+0.3*m.band(noise(k),lo=200,hi=1500)*np.exp(-tt/0.2)
    put(t0,s.astype(np.float32),0.4)
def bird(t0,a=0.25):
    for j in range(3):
        k=int(0.09*SR); tt=np.arange(k)/SR; f=3200+900*np.sin(np.pi*tt/0.09)
        put(t0+j*0.13,(np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*tt/0.09)).astype(np.float32),a)
for t0 in (1.0,2.1,3.2,4.2): bump(t0,0.8)
rustle(6.4,1.1); whoosh(8.0); rustle(10.0,0.4,0.3); rustle(14.0,0.6); whoosh(15.05); rustle(16.9,0.4,0.3)
whoosh(19.4,1.0,0.3); whoosh(21.55,1.1,0.3); whoosh(23.4,1.0,0.3)
door(27.0); clap(31.15,0.9); whoosh(39.15,1.2,0.4)
for t0 in (5.0,13.0,20.0,26.0,33.0,42.0,44.0): bird(t0)
wind=m.gen_wind(n,rng)*env([(0,0.12),(23,0.12),(23.2,0.25),(25,0.25),(25.2,0.1),(45,0.1)])
fx2=(m._norm(fx,1.0)*0.5)[:,None]*np.ones((1,2),np.float32)
mix=m._norm(music,0.55)+fx2+wind*0.25
mix=mix*env([(0,0),(0.3,1),(43.4,1),(45,0)])
m.write_wav(sys.argv[1],m._norm(mix,0.89)); print('ok')
