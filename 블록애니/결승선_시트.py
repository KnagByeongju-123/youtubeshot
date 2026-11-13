"""《같이 들어온 결승선》 캐릭터 시트.  사용: python 결승선_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 결승선인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, fn):
    M=Model(); palette(M); g=fn(M); A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
save('하준', lambda M: kid(M,'k_','hajun'))
save('서연', lambda M: kid(M,'k_','seoyeon'))
save('빨강', lambda M: kid(M,'k_','red',0.75))
save('파랑', lambda M: kid(M,'k_','blue'))
save('보라', lambda M: kid(M,'k_','purple'))
save('결승선', lambda M: finish_line(M,'f_'))
print('ok')
