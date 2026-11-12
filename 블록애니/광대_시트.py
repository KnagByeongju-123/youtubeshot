"""《줄 끊긴 광대》 캐릭터 시트.  사용: python 광대_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 광대인물 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
M=Model(512); palette_all(M); g=clown(M,'c_'); M.save(f'{out}/광대인형.bbmodel',[g],[],name='광대인형')
M=Model(512); palette_all(M); g=mouse(M,'m_',1.0); M.save(f'{out}/쥐.bbmodel',[g],[],name='쥐')
M=Model(512); palette_all(M); g=stage(M,'s_'); b=control_bar(M,'b_',70); M.save(f'{out}/인형극무대.bbmodel',[g,b],[],name='인형극무대')
print('ok')
