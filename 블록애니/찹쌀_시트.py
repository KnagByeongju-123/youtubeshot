"""《찹쌀 성벽》 캐릭터 시트용 .bbmodel.  사용: python 찹쌀_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 찹쌀기구 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def mk():
    M=BigModel(); silla_palette(M); pagoda_palette(M); hwaseong_palette(M); chapssal_palette(M); return M
def save(name,g,M):
    A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
for name,kind,s,tool in [('아푸','apu',0.82,None),('삼촌','uncle',1.0,None),('왕할머니','grandma',0.9,None),('연구원','sci',1.0,None)]:
    M=mk(); save(name,person(M,'p_',kind,s,tool),M)
M=mk(); save('가마솥',cauldron(M,'c_',0,0),M)
M=mk(); save('이름벽돌',name_brick(M,'b',0,0,0),M)
M=mk(); save('성벽',M.group('w',[0,0,0],nanjing_wall(M,'w_',-80,80,0,H=150,T=60)),M)
print('ok')
