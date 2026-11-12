"""《할아버지의 우산》 캐릭터 시트용 .bbmodel.  사용: python 우산_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 우산인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
def save(name, fn):
    M=Model(256); palette(M); HIDE.clear(); g=fn(M); M.els=[e for e in M.els if e['uuid'] not in HIDE]; A=Anim(1); A.bake([g]); M.save(f'{out}/{name}.bbmodel',[g],[A.json()],name=name)
HIDE=[]
def hide_wet(g):
    for n in ('wet_l','wet_r'):
        w=find(g,g['name'].replace('root',n)); HIDE.extend(w['children']); w['children']=[]   # 시트에서는 젖은 자국 없이
    return g
save('할아버지', lambda M: hide_wet(person(M,'p_','grandpa')))
save('늙은할아버지', lambda M: hide_wet(person(M,'p_','grandpa_old')))
save('꼬마손녀', lambda M: hide_wet(person(M,'p_','girl',0.68)))
save('어른손녀', lambda M: hide_wet(person(M,'p_','woman')))
save('우산', lambda M: umbrella(M,'u_'))
save('접은우산', lambda M: umbrella_closed(M,'c_'))
save('버스', lambda M: bus(M,'b_'))
save('정류장', lambda M: bus_stop(M,'s_'))
print('ok')
