import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
for name,kind,sz,skirt in [('메레르','merer',1.0,'linen'),('일꾼1','worker',1.0,'linen'),('일꾼2','worker2',0.9,'linen2'),('앙크하프','ankhhaf',1.05,'linen')]:
    M=Model(); egypt_palette(M); g=person(M,'p_',kind,sz,skirt); M.save(f'{out}/{name}.bbmodel',[g],name=name)
M=Model(); egypt_palette(M); M.save(f'{out}/화물선.bbmodel',[boat(M,'b_')],name='boat')
print('ok')
