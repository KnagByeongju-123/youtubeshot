"""캐릭터 시트용 .bbmodel 들을 만듦 (인물 1명씩).  사용: python 시트_만들기.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from 블록인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
for name,kind,s,skirt in [('아투','atu',0.8,'tapa'),('마타','mata',1.0,'tapa2'),('마을사람1','man',1.0,'tapa2'),('마을사람2','man2',1.0,'tapa3')]:
    M=Model(); islander_palette(M); g=person(M,'p_',kind,s,skirt); M.save(f'{out}/{name}.bbmodel',[g],name=name)
for name,road,eyes in [('모아이_길','road',False),('모아이_제단',False,True)]:
    M=Model(); moai_palette(M); g=moai(M,'m_',road=bool(road),eyes=eyes); M.save(f'{out}/{name}.bbmodel',[g],name=name)
print('ok')
