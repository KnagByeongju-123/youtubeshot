"""《눈 위 발자국》 캐릭터 시트용 .bbmodel.  사용: python 발자국_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 발자국인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, fn):
    M=Model(256); palette(M); g=fn(M); A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
def prints(M):   # 큰 발자국 두 줄 + 그 안에 쏙 들어간 작은 발자국 (시트에서 크기 비교)
    gs=[]
    for i,(x,z) in enumerate([(-2.6,6),(2.6,-4)]):
        b=footprint(M,f'b{i}_',True); move(M,b,x,0,z); gs.append(b)
        k=footprint(M,f'k{i}_',False); move(M,k,x,0.2,z+0.3); gs.append(k)
    return M.group('prints_root',[0,0,0],gs)
save('아빠', lambda M: person(M,'p_','dad'))
save('늙은아빠', lambda M: person(M,'p_','dad_old'))
save('꼬마아들', lambda M: person(M,'p_','kid',0.68))
save('어른아들', lambda M: person(M,'p_','son'))
# 발자국은 옆에서 보면 납작한 판이라 시트에서 빼고 시험 촬영(위에서 내려다봄)으로 확인
print('ok')
