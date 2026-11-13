"""《서툰 아빠의 머리 묶기》 캐릭터 시트.  사용: python 머리묶기_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 머리묶기인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, fn):
    M=Model(); palette(M); g=fn(M); A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
save('딸_1풀린머리', lambda M: girl(M,'g_',only='loose'))
save('딸_2엉망머리', lambda M: girl(M,'g_',only='messy'))
save('딸_3양갈래', lambda M: girl(M,'g_',only='neat'))
save('아빠', lambda M: dad(M,'d_',ribbon=False))
save('아빠_리본', lambda M: dad(M,'d_'))
save('인형_엉킴', lambda M: girl(M,'o_',0.28,doll=True,only='messy'))
save('인형_양갈래', lambda M: girl(M,'o_',0.28,doll=True,only='neat'))
print('ok')
