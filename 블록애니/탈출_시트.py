"""《13층 아래》 캐릭터 시트용 .bbmodel.  사용: python 탈출_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 탈출인물 import *
import 겹침면_검사
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, fn, lift=0):
    M=Model(256); robot_palette(M); g=fn(M)
    if lift: move(M,g,0,lift,0)
    겹침면_검사.fix(M.els,[g]); A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
save('모프', lambda M: mop(M,'m_')); save('모프_다시맞춘', lambda M: mop(M,'m_',patch=True)); save('핍', lambda M: pip(M,'p_',2.0))
save('경비로봇', lambda M: guard(M,'g_')); save('드론', lambda M: drone(M,'d_',1.6), lift=10)
print('ok')
