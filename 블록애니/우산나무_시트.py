"""《할아버지의 우산》 나무 인형판 시트.  사용: python 우산나무_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 우산나무_인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
for name,kind,s in [('할아버지','grandpa',1.0),('늙은할아버지','grandpa_old',1.0),('꼬마손녀','girl',0.72),('어른손녀','woman',1.0)]:
    M=Model(512); palette_all(M); g=person(M,'p_',kind,s)
    for n in ('wet_l','wet_r'):
        w=find(g,'p_'+n)
        if w: ids=set(w['children']); w['children']=[]; M.els=[e for e in M.els if e['uuid'] not in ids]
    M.save(f'{out}/{name}.bbmodel',[g],[],name=name)
print('ok')
