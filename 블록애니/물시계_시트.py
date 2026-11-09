"""《물시계탑》 캐릭터 시트용 .bbmodel.  사용: python 물시계_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 물시계기구 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def mk():
    M=BigModel(); silla_palette(M); pagoda_palette(M); hwaseong_palette(M); chapssal_palette(M); clock_palette(M); return M
def save(name,g,M):
    A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
for name,kind,s in [('소송','susong',1.0),('한공렴','han',1.0),('아밍','aming',0.8)]:
    M=mk(); save(name,person(M,'p_',kind,s),M)
M=mk(); g,_=clock_tower(M,'t_'); save('시계탑',g,M)
M=mk(); save('물레바퀴',waterwheel(M,'w',0,50,0,r=48,n=12),M)
print('ok')
