"""《수원 화성》 캐릭터 시트용 .bbmodel (인물·기구 하나씩).  사용: python 화성_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 화성기구 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def mk():
    M=BigModel(); silla_palette(M); pagoda_palette(M); hwaseong_palette(M); return M
def save(name,g,M):
    A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
for name,kind,s,tool in [('막동','makdong',0.88,None),('오서방','oh',1.0,'chisel'),('정약용','dasan',1.0,None),('일꾼','man',1.0,None),('일꾼2','man2',1.0,None)]:
    M=mk(); save(name,person(M,'p_',kind,s,tool),M)
for name,fn in [('거중기',lambda M:geojunggi(M,'g_')),('유형거',lambda M:yuhyeonggeo(M,'y_')),('녹로',lambda M:noklo(M,'n_')),('팔달문',lambda M:gate(M,'d_'))]:
    M=mk(); save(name,fn(M),M)
M=mk(); rows=hwaseong_wall(M,'w_',-80,80,0,H=100,T=40); save('성벽',M.group('wall',[0,0,0],rows),M)
print('ok')
