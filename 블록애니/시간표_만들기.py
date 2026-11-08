"""나레이션 녹음(캐시) 기준 문단 시작 시간 → <프로젝트>_시간.json  (블록애니_조립.py·장면 프로그램이 씀)
사용: xvfb-run -a python -X utf8 블록애니/시간표_만들기.py <프로젝트.json>
  나레이션_배경음만.py 와 같은 설정(챕터 제목 쉼 포함)으로 시간을 잼 → 그 mp3 와 시간이 맞음"""
import json, os, sys
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,HERE)
pj_path=os.path.abspath(sys.argv[1]); os.chdir(HERE)
import shorts_novel_maker_supertonic as m
pj=json.load(open(pj_path,encoding='utf-8'))
app=m.App(); app.withdraw(); app.update()
s=app.get_settings(); s.update(pj.get('settings',{})); s['narration']='on'; s['bgm_mul']=1.0
m.set_tts_cfg(s)
if m.is_trad(s.get('bgm_style')): s['chapter_hold']=4.2
narr=app.narration_for(pj['story'],s,print)
r=m.make_renderer(pj['title'],pj['story'],s,narr)
segs=[{'t0':round(sg['t0'],3),'dur':round(sg['dur'],3),'kind':sg['kind'],'text':sg['text']} for sg in r.segs]
out=os.path.splitext(pj_path)[0]+'_시간.json'
json.dump({'duration':r.duration,'segs':segs},open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
print('OK',out,round(r.duration,1),'초',len(segs),'문단')
