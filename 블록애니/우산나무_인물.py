"""《할아버지의 우산》 나무 인형판 인물 (doll2 옷 설정) + 색"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 나무인형 import *
import 우산인물 as U

def palette_all(M):
    U.palette(M); palette(M)    # 우산·버스·정류장 색 + 나무 인형 색 (같은 이름 'wood' 는 나무결로)
    M.swatch('p_vest',wood_fn((125,85,55),(95,62,38),31),3); M.swatch('p_cream',wood_fn((232,222,196),(205,192,165),32),3); M.swatch('p_cream_wet',wood_fn((175,165,140),(150,140,118),33),3)
    M.swatch('p_beige',wood_fn((190,170,135),(160,140,108),34),3); M.swatch('p_brown_shoe',wood_fn((90,62,42),(65,44,30),35),3)
    M.swatch('p_grey_hair',wood_fn((150,150,150),(120,120,120),36),3); M.swatch('p_white_hair',wood_fn((236,234,228),(205,203,196),37),3)
    M.swatch('p_pink',wood_fn((245,140,175),(215,110,145),38),3); M.swatch('p_pink_wet',wood_fn((205,105,138),(175,85,115),39),3); M.swatch('p_yellow_boot',wood_fn((250,205,45),(220,175,30),40),3)
    M.swatch('p_navy',wood_fn((48,62,104),(34,46,80),41),3); M.swatch('p_navy_wet',wood_fn((28,38,66),(20,28,50),42),3); M.swatch('p_tights',(60,55,60),3); M.swatch('p_boot_k',wood_fn((48,42,42),(32,28,28),43),3)

GP=dict(shirt='p_cream',vest='p_vest',bottom='pants',bottom_col='p_beige',shoe='p_brown_shoe',hair='short',hair_col='p_grey_hair',mustache='p_grey_hair',wet='p_cream_wet')
GPO=dict(GP,hair_col='p_white_hair',mustache='p_white_hair',cane=True)
GIRL=dict(shirt='p_pink',bottom='coat',bottom_col='p_pink',shoe='p_yellow_boot',hair='pigtails',hood='p_pink_wet',wet='p_pink_wet')
WOMAN=dict(shirt='p_navy',bottom='coat',bottom_col='p_navy',shoe='p_boot_k',leg_col='p_tights',hair='ponytail',scarf='p_pink',wet='p_navy_wet')

def person(M, tag, kind='grandpa', s=1.0):
    o={'grandpa':GP,'grandpa_old':GPO,'girl':GIRL,'woman':WOMAN}[kind]
    return doll2(M,tag,s,o)
