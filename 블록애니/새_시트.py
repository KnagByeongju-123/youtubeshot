"""《돌아온 새》 캐릭터 시트용 .bbmodel.  사용: python 새_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 새인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, fn, bake=True):
    M=Model(256); palette(M); g=fn(M)
    if bake: A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
    else: M.save(f'{out}/{name}.bbmodel',[g],[],name=name)
def spread(M):
    g=bird(M,'b_',1.0,bandage=False)
    find(g,'b_wing_l')['rotation']=[0,0,80]; find(g,'b_wing_r')['rotation']=[0,0,-80]; return g
save('할머니', lambda M: grandma(M,'g_'))
save('파랑새', lambda M: bird(M,'b_',1.0))
save('파랑새_날개편', spread, bake=False)
save('새끼새', lambda M: bird(M,'c_',0.6,chick=True,bandage=False))
save('둥지상자', lambda M: nest_box(M,'n_'))
save('등대', lambda M: lighthouse(M,'l_'))
save('오두막', lambda M: cottage(M,'h_'))
print('ok')
