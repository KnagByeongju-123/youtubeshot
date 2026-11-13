"""《서툰 아빠의 머리 묶기》 소리: 장난스러운 오르골(허둥지둥) → 울상일 때 작아짐 → 밤 패드·시계 째깍 → 성공할 때 따뜻하게 → 아침 깡충에 밝게 → 리본에서 가장 따뜻하게.  자체 합성
   사용: xvfb-run -a python -X utf8 블록애니/머리묶기_소리.py <결과.wav>"""
import sys, os, importlib.util
import numpy as np
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m', os.path.join(BASE,'shorts_novel_maker_supertonic.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SR=m.SR; L=45.0; n=int(L*SR); rng=np.random.default_rng(41)
t=np.arange(n)/SR
def env(points):
    xs,ys=zip(*points); return np.interp(t,xs,ys).astype(np.float32)[:,None]
play=m.gen_musicbox(n,rng,'warm',132); sad=m.gen_musicbox(n,np.random.default_rng(8),'sad',58)
warm=m.gen_musicbox(n,np.random.default_rng(16),'warm',80); pad=m.gen_pad(n,rng,'warm')
music=play*env([(0,0),(0.3,0.6),(3.4,0.6),(4.4,0.2),(5.2,0),(25.4,0),(25.8,0.7),(28.5,0.6),(29.5,0),(45,0)]) \
     +sad*env([(0,0),(4.2,0),(5.4,0.5),(11.6,0.45),(12.4,0),(45,0)]) \
     +warm*env([(0,0),(18.4,0),(19.2,0.6),(21.6,0.5),(22.2,0.3),(25.2,0.3),(25.6,0),(29.6,0),(30.6,0.55),(34.0,0.8),(45,0.85)]) \
     +pad*env([(0,0.1),(12,0.15),(12.5,0.4),(18.5,0.4),(22,0.25),(30,0.3),(45,0.45)])
fx=np.zeros(n,np.float32)
def put(t0,s,a=1.0):
    i=int(t0*SR); k=min(len(s),n-i)
    if k>0: fx[i:i+k]+=s[:k]*a
def noise(k): return rng.standard_normal(k).astype(np.float32)
def brush(t0,dur=0.18,a=0.3):
    k=int(dur*SR); tt=np.arange(k)/SR; put(t0,(m.band(noise(k),lo=2500,hi=8000)*np.sin(np.pi*tt/dur)).astype(np.float32),a)
def twang(t0,a=0.35):   # 고무줄 튕기는 소리
    k=int(0.25*SR); tt=np.arange(k)/SR; put(t0,(np.sin(2*np.pi*(260+120*np.exp(-tt/0.02))*tt)*np.exp(-tt/0.07)).astype(np.float32),a)
def tick(t0,a=0.2):
    k=int(0.02*SR); tt=np.arange(k)/SR; put(t0,(m.band(noise(k),lo=2000,hi=6000)*np.exp(-tt/0.003)).astype(np.float32),a)
def door(t0):
    k=int(0.6*SR); tt=np.arange(k)/SR
    put(t0,(np.sin(2*np.pi*(170+90*tt)*tt)*0.3*np.exp(-tt/0.35)+0.3*m.band(noise(k),lo=200,hi=1500)*np.exp(-tt/0.2)).astype(np.float32),0.35)
def step(t0,a=0.2):
    k=int(0.06*SR); tt=np.arange(k)/SR; put(t0,(m.band(noise(k),lo=120,hi=1400)*np.exp(-tt/0.015)).astype(np.float32),a)
def bird(t0,a=0.22):
    for j in range(3):
        k=int(0.09*SR); tt=np.arange(k)/SR; f=3300+900*np.sin(np.pi*tt/0.09)
        put(t0+j*0.13,(np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*tt/0.09)).astype(np.float32),a)
for t0 in np.arange(0.6,3.2,0.22): brush(t0,0.12,0.25)
twang(1.8); twang(2.9,0.45)
for t0 in np.arange(8.2,11.0,0.25): step(t0,0.15)
door(10.0)
for t0 in np.arange(12.0,22.0,0.5): tick(t0,0.18 if 16<t0<18.8 else 0.12)
twang(13.5); twang(18.5,0.3)
for t0 in np.arange(22.5,25.0,0.45): brush(t0,0.3,0.2)
twang(25.2,0.3)
for t0 in (26.5,26.9): step(t0,0.3)
for t0 in np.arange(37.4,44.6,0.4): step(t0,0.14)
door(38.6)
for t0 in (1.0,23.0,41.5,43.5): bird(t0)
fx2=(m._norm(fx,1.0)*0.45)[:,None]*np.ones((1,2),np.float32)
mix=m._norm(music,0.55)+fx2
mix=mix*env([(0,0),(0.3,1),(43.4,1),(45,0)])
m.write_wav(sys.argv[1],m._norm(mix,0.89)); print('ok')
