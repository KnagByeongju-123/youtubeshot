"""블록 애니 조립: 샷 프레임 → 24fps 영상 + 나레이션 소리 + 자막(한 줄씩) + 챕터 제목 + 숫자 상자
사용: python 블록애니_조립.py <프로젝트.json> <샷목록.json> <프레임폴더> <소리.mp3> <결과.mp4> [--숫자 숫자.json]"""
import json, os, re, subprocess, sys
pj_path, shot_path, fdir, audio, out = sys.argv[1:6]
pj=json.load(open(pj_path,encoding='utf-8')); shots=json.load(open(shot_path,encoding='utf-8'))['shots']
tim=json.load(open(os.path.splitext(pj_path)[0]+'_시간.json',encoding='utf-8'))
nums=json.load(open(sys.argv[sys.argv.index('--숫자')+1],encoding='utf-8')) if '--숫자' in sys.argv else []
work=os.path.splitext(out)[0]+'_작업'; os.makedirs(work,exist_ok=True)
# 1) 샷 → 24fps 조각
parts=[]
for sh in shots:
    d=os.path.join(fdir,sh['name']); dur=sh['t1']-sh['t0']; o=os.path.join(work,sh['name']+'.mp4')
    if not os.path.exists(o):
        subprocess.run(['ffmpeg','-v','error','-y','-framerate',str(sh['fps']),'-i',os.path.join(d,'f%05d.png'),
            '-vf','scale=1920:1080:flags=lanczos,fps=24,tpad=stop_mode=clone:stop_duration=2,format=yuv420p','-t',f'{dur:.3f}',
            '-c:v','libx264','-crf','18','-preset','medium','-r','24',o],check=True)
    parts.append(o)
lst=os.path.join(work,'목록.txt'); open(lst,'w').write(''.join(f"file '{p}'\n" for p in parts))
# 2) 자막 (ASS)
def ts(t): t=max(0,t); return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
def esc(s): return s.replace('{','(').replace('}',')')
def pieces(text):
    out=[]
    for sent in re.split(r'(?<=[.?!])\s+(?=[^"”])|(?<=[.?!]")\s+',text.strip()):
        sent=sent.strip()
        if not sent: continue
        if len(sent)<=24: out.append(sent); continue
        cur=''
        for w in re.split(r'(?<=,)\s+',sent):
            if cur and len(cur)+len(w)>24: out.append(cur); cur=w
            else: cur=(cur+' '+w).strip()
        if cur: out.append(cur)
    # 쉼표가 없어 여전히 긴 조각(28자 넘음)은 가운데 가까운 띄어쓰기에서 둘로 (화면 밖으로 넘치지 않게)
    res=[]
    for p in out:
        while len(p)>28 and ' ' in p:
            mid=len(p)//2; sp=[i for i,ch in enumerate(p) if ch==' ']; k=min(sp,key=lambda i:abs(i-mid))
            res.append(p[:k]); p=p[k+1:]
        res.append(p)
    return res
F='NanumGothicExtraBold'
ev=[]
_tt=pj['title']; _fs=120 if len(_tt)<=14 else max(64,int(120*14/len(_tt)))   # 긴 제목은 글자를 줄여 한 줄에 (화면 밖으로 넘치지 않게)
ev.append(f"Dialogue: 0,{ts(0.2)},{ts(3.2)},Title,,0,0,0,,{{\\fad(400,400)\\fs{_fs}}}{esc(_tt)}")
for sg in tim['segs']:
    t0,dur,txt=sg['t0'],sg['dur'],sg['text']
    if sg['kind']=='chapter':
        ev.append(f"Dialogue: 0,{ts(t0)},{ts(t0+dur+1.2)},Chap,,0,0,0,,{{\\fad(300,400)}}{esc(txt)}"); continue
    ps=pieces(txt.replace('\n',' ')); tot=sum(len(p) for p in ps) or 1; speak=max(0.5,dur-0.35); t=t0
    for p in ps:
        d=speak*len(p)/tot; ev.append(f"Dialogue: 0,{ts(t)},{ts(t+d)},Sub,,0,0,0,,{esc(p)}"); t+=d
for n in nums:
    sg=tim['segs'][n['seg']]
    ev.append(f"Dialogue: 0,{ts(sg['t0']+0.3)},{ts(sg['t0']+sg['dur']+n.get('extra',0))},Num,,0,0,0,,{{\\fad(250,250)}}{esc(n['text'])}")
ass=f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{F},64,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,80,80,70,1
Style: Chap,{F},96,&H00FFFFFF,&H00FFFFFF,&H00202020,&H90000000,1,0,0,0,100,100,2,0,1,7,3,5,80,80,0,1
Style: Title,{F},120,&H0060E0FF,&H00FFFFFF,&H00151515,&H90000000,1,0,0,0,100,100,2,0,1,8,4,5,80,80,0,1
Style: Num,{F},60,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0101010,1,0,0,0,100,100,0,0,3,18,0,8,80,80,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""+'\n'.join(ev)+'\n'
assp=os.path.join(work,'자막.ass'); open(assp,'w',encoding='utf-8').write(ass)
# 3) 합치기
total=tim['duration']
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',lst,'-i',audio,
  '-vf',f"ass={assp}",'-map','0:v','-map','1:a','-c:v','libx264','-crf','19','-preset','medium','-r','24',
  '-c:a','aac','-b:a','192k','-t',f'{total:.2f}','-movflags','+faststart',out],check=True)
print('OK',out)
