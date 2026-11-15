"""《마지막 잎새》 나무 인형 시트.  사용: python 잎새_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 잎새인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
for name,kind,s in [('꼬마소녀','girl',0.72),('화가할아버지','grandpa',1.0),('어른소녀','woman',1.0),('늙은할아버지','grandpa_old',1.0)]:
    M=Model(512); palette_all(M); g=person(M,'p_',kind,s)
    if kind in ('grandpa','woman'): find(g,'p_hand_r')['children'].append(brush(M,'p_',[-5.4*s,11.2*s,0],s))
    M.save(f'{out}/{name}.bbmodel',[g],[],name=name)
# 소품: 사다리·등불·벽에 붙은 잎(진짜 초록·노란 잎, 그린 잎)
M=Model(512); palette_all(M)
wall=M.cube('wall',[-8,0,3],[8,20,4],'wood_l')
lv=[]
for i,(x,y,col,fl) in enumerate([(-4,15,'l_leaf',False),(0,12,'l_leaf_y',False),(4,15,'l_leaf_paint',True)]): lv+=leaf(M,f'lf{i}',[x,y,2.8],col,1.6,fl)
g=M.group('props',[0,0,0],[ladder(M,'s_',[14,0,0],h=30), lamp(M,'s_',[-14,0,0],1.4), wall]+lv)
M.save(f'{out}/소품.bbmodel',[g],[],name='소품')
print('ok')
