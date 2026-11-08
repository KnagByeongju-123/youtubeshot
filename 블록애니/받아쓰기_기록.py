"""녹음(캐시) 기준 Whisper 받아쓰기 검사 기록 → <프로젝트>_나레이션검증.txt
사용: xvfb-run -a python -X utf8 블록애니/받아쓰기_기록.py <프로젝트.json>"""
import json, os, sys
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,HERE)
pj_path=os.path.abspath(sys.argv[1]); os.chdir(HERE)
import shorts_novel_maker_supertonic as m
pj=json.load(open(pj_path,encoding='utf-8'))
app=m.App(); app.withdraw(); app.update()
s=app.get_settings(); s.update(pj.get('settings',{})); s['narration']='on'
m.set_tts_cfg(s)
narr=app.narration_for(pj['story'],s,print)
NV=getattr(m,'_NV',None)
if NV is None: print('검증 모듈 없음'); sys.exit(1)
out=os.path.splitext(pj_path)[0]+'_나레이션검증.txt'
open(out,'w',encoding='utf-8').write(NV.report_text(pj.get('title','')))
print('기록',len(NV.REPORT),'문단, 문제',sum(1 for r in NV.REPORT if not r[2]['ok']),'→',out)
