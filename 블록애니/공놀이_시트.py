"""《마지막 공놀이》 캐릭터 시트.  사용: python 공놀이_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 밥그릇인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, fn):
    M=Model(); palette(M); g=fn(M); A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
save('꼬마', lambda M: person(M,'p_','kid',0.7))
save('어른', lambda M: person(M,'p_','adult',1.0))
save('어린강아지', lambda M: dog(M,'d_',0.8))
save('늙은강아지', lambda M: dog(M,'d_',1.0,old=True))
save('공', lambda M: ball(M,'b_'))
print('ok')
