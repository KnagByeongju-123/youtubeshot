"""《화성의 오디세이》 캐릭터 시트용 .bbmodel (하나씩).  사용: python 화성_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 화성인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, fn):
    M=Model(256); mars_palette(M); g=fn(M); A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
save('자비스', lambda M: human(M,'p_','jarvis'))
save('해리슨', lambda M: human(M,'p_','harrison'))
save('푸츠', lambda M: human(M,'p_','putz'))
save('르루아', lambda M: human(M,'p_','leroy',0.88))
save('팬시롱', lambda M: human(M,'p_','fancy',0.95))
save('트윌', lambda M: tweel(M,'t_'))
save('피라미드생물', lambda M: pyramid_beast(M,'y_'))
save('꿈괴물', lambda M: dream_beast(M,'d_'))
save('통생물', lambda M: barrel_being(M,'b_'))
save('수레', lambda M: cart(M,'c_',load='rubble'))
print('ok')
