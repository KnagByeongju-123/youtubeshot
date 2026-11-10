"""대사 없는 블록 애니 조립: 샷 프레임을 차례로 이어 붙임 + 글자(제목·층 번호·HUD) + 소리
사용: python 탈출_조립.py <샷목록.json> <프레임폴더> <소리.wav> <결과.mp4> <글자.json> [--크기 1920x1080]
  샷은 목록 순서대로 이어 붙임(쇼츠는 골라 낸 샷만). 글자.json = [{t0,t1,text,style}] — 시간은 '결과 영상' 기준 초
  style: Title(가운데 큰 제목) Floor(왼쪽 위 층 번호) Blink(아래 가운데 작은 뜻) Hook(위쪽 큰 글) Hud(위 가운데 상태 표시) End(가운데)"""
import json, os, subprocess, sys
shot_path,fdir,audio,out,cap_path=sys.argv[1:6]
W,H=(int(v) for v in (sys.argv[sys.argv.index('--크기')+1] if '--크기' in sys.argv else '1920x1080').split('x'))
out=os.path.abspath(out); fdir=os.path.abspath(fdir); audio=os.path.abspath(audio)
shots=json.load(open(shot_path,encoding='utf-8'))['shots']; caps=json.load(open(cap_path,encoding='utf-8'))
work=os.path.splitext(out)[0]+'_작업'; os.makedirs(work,exist_ok=True); parts=[]; total=0
for sh in shots:
    d=os.path.join(fdir,sh['name']); dur=sh['t1']-sh['t0']; o=os.path.join(work,sh['name']+'.mp4'); total+=dur
    if not os.path.exists(o):
        subprocess.run(['ffmpeg','-v','error','-y','-framerate',str(sh['fps']),'-i',os.path.join(d,'f%05d.png'),
            '-vf',f'scale={W}:{H}:flags=lanczos,fps=24,tpad=stop_mode=clone:stop_duration=2,format=yuv420p','-t',f'{dur:.3f}','-c:v','libx264','-crf','18','-preset','medium','-r','24',o],check=True)
    parts.append(o)
lst=os.path.join(work,'목록.txt'); open(lst,'w').write(''.join(f"file '{p}'\n" for p in parts))
def ts(t): t=max(0,t); return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
k=H/1080 if W>H else W/1080; F='NanumGothicExtraBold'; z=lambda v:int(v*k)
ass=f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,{F},{z(150)},&H00FFFFFF,&H00FFFFFF,&H00101010,&H90000000,1,0,0,0,100,100,6,0,1,{z(9)},{z(4)},5,40,40,0,1
Style: Floor,{F},{z(84)},&H003CDCFF,&H00FFFFFF,&H00101010,&HA0000000,1,0,0,0,100,100,2,0,3,{z(16)},0,7,{z(50)},40,{z(46)},1
Style: Blink,{F},{z(70)},&H00A0FF78,&H00FFFFFF,&H00101010,&H90000000,1,0,0,0,100,100,4,0,1,{z(6)},{z(2)},2,40,40,{z(110)},1
Style: Hook,{F},{z(92)},&H00FFFFFF,&H00FFFFFF,&H00101010,&H90000000,1,0,0,0,100,100,0,0,1,{z(8)},{z(3)},8,30,30,{z(250)},1
Style: Hud,{F},{z(60)},&H003CDCFF,&H00FFFFFF,&H00101010,&HA0000000,1,0,0,0,100,100,2,0,3,{z(14)},0,8,30,30,{z(120)},1
Style: End,{F},{z(110)},&H0060E0FF,&H00FFFFFF,&H00101010,&H90000000,1,0,0,0,100,100,2,0,1,{z(8)},{z(3)},5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""+'\n'.join(f"Dialogue: 0,{ts(c['t0'])},{ts(c['t1'])},{c.get('style','Blink')},,0,0,0,,{{\\fad(300,400)}}{c['text']}" for c in caps)+'\n'
assp=os.path.join(work,'자막.ass'); open(assp,'w',encoding='utf-8').write(ass)
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',lst,'-i',audio,'-vf',f"ass={assp}",'-map','0:v','-map','1:a','-c:v','libx264','-crf','20','-preset','medium','-r','24',
  '-c:a','aac','-b:a','192k','-t',f'{total:.2f}','-movflags','+faststart',out],check=True)
print('OK',out,round(total,1),'초')
