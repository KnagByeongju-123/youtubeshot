"""《창문 너머 종이비행기》 캐릭터 시트.  사용: python 종이비행기_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 종이비행기인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, fn):
    M=Model(); palette(M); g=fn(M); A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
save('도윤_병실', lambda M: child(M,'k_','doyun'))
save('도윤_퇴원', lambda M: child(M,'k_','doyun2'))
save('하은', lambda M: child(M,'k_','haeun'))
save('새아이', lambda M: child(M,'k_','new'))
save('종이비행기', lambda M: plane(M,'p_',3.0))
print('ok')
