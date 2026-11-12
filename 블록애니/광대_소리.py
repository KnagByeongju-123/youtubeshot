"""《줄 끊긴 광대》 소리: 기계 같은 오르골(무대) → 조용한 밤 → 줄이 끊길 때 '팅' → 첫걸음에 따뜻하게 → 바깥 밝게.  자체 합성
   사용: xvfb-run -a python -X utf8 블록애니/광대_소리.py <결과.wav>"""
import sys, os, importlib.util
import numpy as np
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m', os.path.join(BASE,'shorts_novel_maker_supertonic.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SR=m.SR; L=45.0; n=int(L*SR); rng=np.random.default_rng(66)
t=np.arange(n)/SR
def env(points):
    xs,ys=zip(*points); return np.interp(t,xs,ys).astype(np.float32)[:,None]
box=m.gen_musicbox(n,rng,'warm',124); sad=m.gen_musicbox(n,np.random.default_rng(3),'sad',60); warm=m.gen_musicbox(n,np.random.default_rng(21),'warm',84)
pad=m.gen_pad(n,rng,'sad'); wpad=m.gen_pad(n,rng,'warm')
music=box*env([(0,0),(0.3,0.75),(7.6,0.75),(8.4,0),(45,0)]) \
     +sad*env([(0,0),(8.4,0),(10,0.45),(25.4,0.5),(26.4,0.2),(28.5,0),(45,0)]) \
     +warm*env([(0,0),(28.0,0),(30,0.55),(35,0.7),(38,0.9),(45,0.9)]) \
     +pad*env([(0,0),(8.4,0),(10,0.3),(26,0.35),(28,0),(45,0)])+wpad*env([(0,0),(28,0),(31,0.3),(45,0.4)])
# 무대 박자 '똑딱' (줄에 당겨지는 느낌) 0~8초
tick=np.zeros(n,np.float32)
def click(t0,f=1800,a=1.0,d=0.04):
    k=int(d*SR); tt=np.arange(k)/SR; s=np.sin(2*np.pi*f*tt)*np.exp(-tt/0.008)
    i=int(t0*SR); tick[i:i+k]+=(s*a)[:max(0,min(k,n-i))]
for k in range(16): click(0.25+k*0.5,1500 if k%2 else 2000,0.6)
# 줄이 끊길 때 '팅'
def ping(t0,f=880):
    k=int(1.2*SR); tt=np.arange(k)/SR; s=(np.sin(2*np.pi*f*tt)+0.4*np.sin(2*np.pi*f*2.01*tt))*np.exp(-tt/0.35)
    i=int(t0*SR); tick[i:i+k]+=(s*0.8)[:max(0,min(k,n-i))]
for t0,f in [(15.6,880),(19.2,988),(22.4,1046),(25.4,1175)]: ping(t0,f)
click(26.2,220,1.0,0.12); click(29.8,200,0.8,0.12)   # 털썩·넘어짐
birds=np.zeros(n,np.float32)
r=np.random.default_rng(2); tt0=37.5
while tt0<44.5:
    k=int(0.09*SR); x=np.arange(k)/SR; f=np.linspace(r.uniform(2800,3500),r.uniform(4200,5000),k)
    s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*x/0.09)**2; i=int(tt0*SR); birds[i:i+k]+=s[:max(0,min(k,n-i))]*r.uniform(0.4,0.8); tt0+=r.uniform(0.3,0.9)
mix=m._norm(music,0.55)+(m._norm(tick)[:,None]*np.ones((1,2)))*0.3+(birds[:,None]*np.ones((1,2)))*0.08
mix=mix*env([(0,0),(0.3,1),(43.5,1),(45,0)])
m.write_wav(sys.argv[1],m._norm(mix,0.89)); print('ok')
