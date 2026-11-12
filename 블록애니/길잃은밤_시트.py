"""《길 잃은 밤》 네 발 나무 강아지 캐릭터 시트 + 나무 소년과 키 비교.  사용: python 길잃은밤_시트.py <폴더>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 나무인형 import *
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
M=Model(256); palette(M); g=wood_dog4(M,'w_',1.0); M.save(f'{out}/나무강아지_네발.bbmodel',[g],[],name='나무강아지_네발')
M=Model(256); palette(M); b=doll(M,'b_',0.9,kind='boy'); d=wood_dog4(M,'w_',0.9); move(M,d,dx=-16)
M.save(f'{out}/소년과강아지.bbmodel',[M.group('all',[0,0,0],[b,d])],[],name='소년과강아지'); print('ok')
