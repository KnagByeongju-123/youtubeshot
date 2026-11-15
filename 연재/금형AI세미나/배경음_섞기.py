"""잔잔한 패드 + 긴장 펄스를 장면에 맞춰 섞은 최종 소리 (나레이션 포함)
python 배경음_섞기.py  → 금형AI세미나_최종소리.mp3
긴장 구간: 2장 조립·금형 내부, 5장 성형해석, 6장 역설계 반복 (앞뒤 2초 겹쳐 바뀜)"""
import json, os, subprocess, sys
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0,ROOT); os.chdir(ROOT)
import shorts_novel_maker_supertonic as m
pj=json.load(open(os.path.join(HERE,'금형AI세미나.json'),encoding='utf-8'))
tim=json.load(open(os.path.join(HERE,'금형AI세미나_시간.json'),encoding='utf-8'))['segs']
app=m.App(); app.withdraw(); app.update()
s=app.get_settings(); s.update(pj['settings']); s['narration']='on'
m.set_tts_cfg(s)
narr=app.narration_for(pj['story'],s,print)
r=m.make_renderer(pj['title'],pj['story'],s,narr)
pad=m.build_audio(r,dict(s,narr_volume=0),'잔잔한 패드')
ten=m.build_audio(r,dict(s,narr_volume=0,bgm_style='긴장 펄스'),'긴장 펄스')
n=min(len(pad),len(ten)); t=np.arange(n)/m.SR
T=lambda i: tim[i]['t0']
zones=[(T(27),T(30)),(T(48),T(58)),(T(62),T(66))]      # 2장 '금형 한 벌'~끝, 5장 전체, 6장 반복 계산
w=np.zeros(n,np.float32)
for a,b in zones: w=np.maximum(w,np.clip(np.minimum((t-a)/2.0+0.5,(b-t)/2.0+0.5),0,1))
out=pad[:n]*(1-w)[:,None]+ten[:n]*(0.9*w)[:,None]
# 효과음 (장면 프로그램이 남긴 _sfx/*.json): 직접 합성 — 휙·불릿 타임·딸깍·톡
import glob
SR=m.SR; rng=np.random.default_rng(1)
def bandnoise(n,lo,hi):
    x=rng.standard_normal(n); X=np.fft.rfft(x); f=np.fft.rfftfreq(n,1/SR); X[(f<lo)|(f>hi)]=0; y=np.fft.irfft(X,n); return y/(np.abs(y).max()+1e-9)
def whoosh():
    n=int(0.75*SR); tt=np.arange(n)/SR; y=bandnoise(n,250,2600)
    env=np.sin(np.pi*np.clip(tt/0.75,0,1))**2.5
    pan=np.clip(tt/0.75,0,1); return np.stack([y*env*(1-0.6*pan),y*env*(0.4+0.6*pan)],1)*0.22
def slow():
    n=int(1.6*SR); tt=np.arange(n)/SR; f=110*np.exp(-tt*1.1)+35; ph=2*np.pi*np.cumsum(f)/SR
    y=np.sin(ph)*np.exp(-tt*1.2)*0.5+bandnoise(n,80,900)*np.clip(tt/0.3,0,1)*np.exp(-tt*2.2)*0.35
    return np.stack([y,y],1)*0.5
def click():
    n=int(0.12*SR); tt=np.arange(n)/SR
    y=sum(np.sin(2*np.pi*fr*tt)*a for fr,a in ((2200,1),(3700,.6),(5100,.4)))*np.exp(-tt*55)+bandnoise(n,2000,8000)*np.exp(-tt*200)*0.5
    return np.stack([y,y],1)*0.16
def pop():
    n=int(0.09*SR); tt=np.arange(n)/SR; y=np.sin(2*np.pi*(600+3000*tt)*tt)*np.exp(-tt*45); return np.stack([y,y],1)*0.12
GEN={'whoosh':whoosh,'slow':slow,'click':click,'pop':pop}
ev=[]
for f in sorted(glob.glob(os.path.join(HERE,'장면','_sfx','*.json'))): ev+=json.load(open(f))
for e in ev:
    w=GEN[e['kind']]()*float(e.get('vol',1)); i0=int(e['t']*SR)
    if 0<=i0<n: seg=w[:n-i0]; out[i0:i0+len(seg)]+=seg
print('효과음',len(ev),'개')
vol=float(s.get('narr_volume',1.0))
for st,clip in r.narr_at:
    i0=int(st*m.SR); seg=clip[:max(0,n-i0)]
    out[i0:i0+len(seg)]+=(seg[:,None] if seg.ndim==1 else seg)*vol
pk=float(np.abs(out).max())
if pk>0.95: out*=0.95/pk
wav=os.path.join(HERE,'_최종소리.wav'); mp3=os.path.join(HERE,'금형AI세미나_최종소리.mp3')
m.write_wav(wav,out); subprocess.run(['ffmpeg','-v','error','-y','-i',wav,'-b:a','192k',mp3],check=True); os.remove(wav)
print('OK',mp3,round(n/m.SR,1))
