"""《자격루》 캐릭터 시트용 .bbmodel (인물·자격루 하나씩).  사용: python 자격루_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 조선인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, g, M):
    A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
for name,kind,s,tool in [('장영실','yeongsil',1.0,None),('막동이','makdong',0.75,None),('세종','sejong',1.0,None),('서운관_관원','gwanwon',1.0,None),
                         ('나무인형_종치기','doll',1.0,'mallet'),('나무인형_열두띠','doll_g',1.0,'sipae')]:
    M=BigModel(); joseon_palette(M); g=person(M,'p_',kind,s,tool); save(name,g,M)
M=BigModel(); joseon_palette(M); g,_=jagyeongnu(M); save('자격루',g,M)
print('ok')
