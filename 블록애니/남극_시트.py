"""《남극에 남겨진 타로와 지로》 캐릭터 시트용 .bbmodel.  사용: python 남극_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 남극인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name,g,M):
    A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
for name,kind in [('타로','taro'),('지로','jiro'),('썰매개_회색','grey'),('썰매개_흰색','white'),('썰매개_갈색','brown')]:
    M=Model(); dog_palette(M,kind); save(name,dog(M,'d_',kind),M)
M=Model(); explorer_palette(M); save('대원',explorer(M,'e_'),M)
print('ok')
