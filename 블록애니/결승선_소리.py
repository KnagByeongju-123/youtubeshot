"""《같이 들어온 결승선》 소리: 밝은 오르골 → 혼자 남을 때 작아짐 → 손 내밀 때 따뜻하게 → 운동회 북·호루라기 → 넷이 멈출 때 조용 → 손잡고 들어올 때 크게 + 환호.  자체 합성
   사용: xvfb-run -a python -X utf8 블록애니/결승선_소리.py <결과.wav>"""
import sys, os, importlib.util
import numpy as np
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m', os.path.join(BASE,'shorts_novel_maker_supertonic.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SR=m.SR; L=45.0; n=int(L*SR); rng=np.random.default_rng(21)
t=np.arange(n)/SR
def env(points):
    xs,ys=zip(*points); return np.interp(t,xs,ys).astype(np.float32)[:,None]
bright=m.gen_musicbox(n,rng,'warm',104); sad=m.gen_musicbox(n,np.random.default_rng(8),'sad',60)
warm=m.gen_musicbox(n,np.random.default_rng(16),'warm',76); pad=m.gen_pad(n,rng,'warm')
music=bright*env([(0,0),(0.3,0.75),(3.0,0.7),(4.6,0.25),(6.0,0),(45,0)]) \
     +sad*env([(0,0),(4.4,0),(6.0,0.55),(11.0,0.5),(13.0,0.3),(14.0,0),(45,0)]) \
     +warm*env([(0,0),(13.0,0),(14.6,0.75),(22.6,0.7),(23.2,0),(28.8,0),(30.2,0),(31.4,0.45),(34.0,0.75),(39.5,0.85),(41.0,1.0),(45,0.9)]) \
     +pad*env([(0,0),(4.0,0.2),(11,0.3),(15,0.4),(23,0.2),(29.2,0.45),(31,0.35),(36,0.45),(45,0.5)])
fx=np.zeros(n,np.float32)
def put(i,s,a=1.0):
    i=int(i*SR); k=min(len(s),n-i)
    if k>0: fx[i:i+k]+=s[:k]*a
def whistle(t0,dur=0.55,a=1.0):
    k=int(dur*SR); tt=np.arange(k)/SR
    f=2900+180*np.sign(np.sin(2*np.pi*28*tt))            # 호루라기 떨림 (구슬 굴러가는 소리)
    s=np.sin(2*np.pi*np.cumsum(f)/SR)+0.15*m.band(rng.standard_normal(k).astype(np.float32),lo=2500,hi=4500)
    s*=np.minimum(1,tt/0.02)*np.minimum(1,(dur-tt)/0.06); put(t0,s.astype(np.float32),a)
def step(t0,a=0.25):
    k=int(0.06*SR); tt=np.arange(k)/SR
    s=m.band(rng.standard_normal(k).astype(np.float32),lo=120,hi=1400)*np.exp(-tt/0.015); put(t0,s,a)
def drum(t0,a=0.6):
    k=int(0.35*SR); tt=np.arange(k)/SR
    s=np.sin(2*np.pi*(70+60*np.exp(-tt/0.03))*tt)*np.exp(-tt/0.12)+0.2*m.band(rng.standard_normal(k).astype(np.float32),hi=500)*np.exp(-tt/0.03)
    put(t0,s.astype(np.float32),a)
whistle(1.0); whistle(24.0)
for t0 in np.arange(1.1,5.2,0.18): step(t0+rng.uniform(0,0.05),0.22*max(0.2,1-(t0-1.1)/4))   # 넷이 달려 나가는 발소리 (멀어짐)
for t0 in np.arange(1.3,4.4,0.4): step(t0,0.3)                                                  # 하준 발소리 (느리게)
for t0 in np.arange(23.0,29.0,0.5): drum(t0,0.55 if int((t0-23)*2)%2==0 else 0.35)            # 운동회 북
for t0 in np.arange(24.1,28.8,0.17): step(t0+rng.uniform(0,0.04),0.18)
for t0 in np.arange(30.0,33.0,0.19): step(t0,0.2)                                               # 되돌아 뛰는 발소리
# 박수·환호: 끊긴 소리 여러 겹 (40.3~), 출발 때 조금
def claps(t0,t1,dens,a):
    for _ in range(int((t1-t0)*dens)):
        k=int(0.03*SR); tt=np.arange(k)/SR
        put(rng.uniform(t0,t1),m.band(rng.standard_normal(k).astype(np.float32),lo=800,hi=5000)*np.exp(-tt/0.006),a*rng.uniform(0.4,1))
claps(24.0,25.6,40,0.25); claps(40.3,44.6,90,0.3)
cheer=m.band(rng.standard_normal(n).astype(np.float32),lo=400,hi=2600)
vib=1+0.3*np.sin(2*np.pi*3.1*t)*np.sin(2*np.pi*0.7*t)
cheer=cheer*vib*np.interp(t,[0,40.2,40.6,43.5,45],[0,0,1,0.8,0])
crowd=m.band(rng.standard_normal(n).astype(np.float32),lo=300,hi=1800)*np.interp(t,[0,23,23.5,28.8,29.2,40.2,40.6,45],[0,0,0.35,0.35,0.08,0.08,0,0])
wind=m.gen_wind(n,rng)*env([(0,0.1),(6,0.18),(11,0.18),(13,0.1),(45,0.1)])
fx2=(m._norm(fx,1.0)*0.55+m._norm(cheer,1.0)*0.22+m._norm(crowd,1.0)*0.12)[:,None]*np.ones((1,2),np.float32)
mix=m._norm(music,0.55)+fx2+wind*0.25
mix=mix*env([(0,0),(0.3,1),(43.4,1),(45,0)])
m.write_wav(sys.argv[1],m._norm(mix,0.89)); print('ok')
