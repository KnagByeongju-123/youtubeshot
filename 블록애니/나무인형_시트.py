"""나무 인형 캐릭터 시트.  사용: python 나무인형_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 나무인형 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
for name,kind in [('나무소년','boy'),('나무소녀','girl'),('목수할아버지','grandpa')]:
    M=Model(256); palette(M); g=doll(M,'d_',kind=kind); M.save(f'{out}/{name}.bbmodel',[g],[],name=name)
M=Model(256); palette(M); g=wood_dog(M,'w_'); M.save(f'{out}/나무강아지.bbmodel',[g],[],name='나무강아지')
# 움직임 확인용: 블록 인물처럼 걷는 자세 (팔·다리 통째로)
M=Model(256); palette(M); g=doll(M,'d_')
for n,r in [('arm_left',[-30,0,0]),('arm_right',[30,0,0]),('leg_left',[28,0,0]),('leg_right',[-28,0,0]),('head',[0,-20,0])]:
    find(g,'d_'+n)['rotation']=r
M.save(f'{out}/나무인형_자세.bbmodel',[g],[],name='나무인형_자세')
print('ok')
