"""점토 인형 캐릭터 시트용 모형.  사용: python 점토인형_시트.py <폴더>
   → node blockbench_시트촬영.js <폴더> → python 시트_합치기.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 점토인형 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
M=Model(256); clay_palette(M); g=clay_boy(M,'c_'); M.save(f'{out}/점토소년.bbmodel',[g],[],name='점토소년')
M=Model(256); clay_palette(M); g=clay_dog(M,'g_'); M.save(f'{out}/점토강아지.bbmodel',[g],[],name='점토강아지')
print('ok')
