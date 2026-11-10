"""《증기 기차 여관》 캐릭터 시트용 .bbmodel.  사용: python 증기_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 증기기구 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def mk():
    M=BigModel(); silla_palette(M); pagoda_palette(M); hwaseong_palette(M); chapssal_palette(M); clock_palette(M); steam_palette(M); return M
def save(name,g,M):
    A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
for name,kind in [('오웬','owen'),('레나','lena'),('그림스','grimes')]:
    M=mk(); save(name,person(M,'p_',kind,1.0),M)
M=mk(); save('톡',tok(M,'k_',0,0,0,s=1.6),M)
M=mk(); g,_=inn_train(M,'tr_'); save('기차여관',g,M)
M=mk(); save('비행선',airship(M,'a_',0,60,0),M)
M=mk(); save('증기차',walking_car(M,'s_',0,0),M)
print('ok')
