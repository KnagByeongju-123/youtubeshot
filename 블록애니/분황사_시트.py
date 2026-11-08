"""《분황사 탑》 캐릭터 시트용 .bbmodel (인물·탑 하나씩).  사용: python 분황사_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 신라인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, g, M):
    A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
for name,kind,s,tool in [('바우','bau',0.78,None),('바우_어른','bau_old',1.0,'chisel'),('덕보','deokbo',0.97,'chisel'),
                         ('석공1','man',1.0,None),('석공2','man2',1.0,None),('스님','monk',1.0,None),('선비','seonbi',1.0,None)]:
    M=BigModel(); silla_palette(M); pagoda_palette(M); g=person(M,'p_',kind,s,tool); save(name,g,M)
M=BigModel(); silla_palette(M); pagoda_palette(M); g,_,h=pagoda(M,'t_',3); save('탑_지금3층',g,M); print('3층 높이',h)
M=BigModel(); silla_palette(M); pagoda_palette(M); g,_,h=pagoda(M,'t_',9,ghost_from=3); save('탑_9층상상',g,M); print('9층 높이',h)
print('ok')
