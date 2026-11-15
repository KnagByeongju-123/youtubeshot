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
vol=float(s.get('narr_volume',1.0))
for st,clip in r.narr_at:
    i0=int(st*m.SR); seg=clip[:max(0,n-i0)]
    out[i0:i0+len(seg)]+=(seg[:,None] if seg.ndim==1 else seg)*vol
pk=float(np.abs(out).max())
if pk>0.95: out*=0.95/pk
wav=os.path.join(HERE,'_최종소리.wav'); mp3=os.path.join(HERE,'금형AI세미나_최종소리.mp3')
m.write_wav(wav,out); subprocess.run(['ffmpeg','-v','error','-y','-i',wav,'-b:a','192k',mp3],check=True); os.remove(wav)
print('OK',mp3,round(n/m.SR,1))
