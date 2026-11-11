"""《빈 밥그릇》 캐릭터 시트용 .bbmodel (인물·소품 하나씩).  사용: python 밥그릇_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 밥그릇인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, fn):
    M=Model(); palette(M); g=fn(M); A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
save('꼬마', lambda M: person(M,'p_','kid',0.7))
save('아빠', lambda M: person(M,'p_','dad',1.0))
save('강아지', lambda M: dog(M,'d_',1.0))
save('강아지_그릇물기', lambda M: dog(M,'d_',1.0,with_bowl=True))
save('밥그릇', lambda M: bowl(M,'b_',1.0))
save('트럭', lambda M: truck(M,'t_'))
print('ok')
