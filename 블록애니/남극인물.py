"""《남극에 남겨진 타로와 지로》 블록 부품: 사할린 썰매개(dog) · 남극 대원(explorer).
   블록인물.py 의 Model·Anim·move 를 그대로 씀.  앞 = -z (개 머리·대원 얼굴이 -z 쪽)"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import *

# 개 털 색: (몸, 짙은 등, 밝은 배·가슴, 앞발 끝, 목줄)
DOGS = {
    'taro':  ((92, 62, 40), (60, 40, 26), (190, 150, 110), (92, 62, 40), (200, 40, 35)),    # 짙은 갈색, 빨간 목줄
    'jiro':  ((32, 30, 32), (18, 18, 20), (235, 235, 230), (240, 240, 236), (40, 90, 200)), # 검정, 앞발 끝·가슴 흰색, 파란 목줄
    'grey':  ((150, 150, 150), (105, 105, 108), (225, 225, 222), (150, 150, 150), (120, 85, 50)),
    'white': ((228, 226, 220), (200, 198, 192), (245, 245, 242), (228, 226, 220), (120, 85, 50)),
    'brown': ((150, 105, 60), (110, 75, 42), (220, 195, 150), (150, 105, 60), (120, 85, 50)),
}

def dog_palette(M, kind):
    body, back, belly, paw, collar = DOGS[kind]
    p = kind + '_'
    M.swatch(p+'body', body, 7); M.swatch(p+'back', back, 6); M.swatch(p+'belly', belly, 5)
    M.swatch(p+'paw', paw, 4); M.swatch(p+'collar', collar, 4)
    M.swatch('nose', (20, 18, 18), 2) if 'nose' not in M.sw else None
    def face(d, x, y):   # 머리 앞면: 털색 + 밝은 눈썹 + 눈 두 개
        d.rectangle([x, y, x+15, y+15], fill=body)
        for ex in (2, 10):
            d.rectangle([x+ex, y+1, x+ex+3, y+2], fill=belly)              # 눈 위 밝은 점(사할린개 무늬)
            d.rectangle([x+ex, y+4, x+ex+3, y+7], fill=(250, 250, 245))
            d.rectangle([x+ex+1, y+5, x+ex+3, y+7], fill=(25, 20, 18))
        d.rectangle([x+4, y+12, x+11, y+15], fill=belly)                   # 주둥이 쪽 밝은 털
    M.paint(p+'face', face)
    def snout(d, x, y):
        d.rectangle([x, y, x+15, y+15], fill=belly); d.rectangle([x+4, y, x+11, y+6], fill=(20, 18, 18))  # 코
        d.rectangle([x+5, y+12, x+10, y+13], fill=(90, 50, 45))
    M.paint(p+'snout', snout)

def dog(M, tag, kind='taro', s=1.0):
    """사할린 썰매개. 사람(키 32)의 무릎~허리 높이 (등 높이 약 12). 묶음: root > body > head·tail·leg_fl/fr/bl/br
       움직임용 묶음: tag+'head', tag+'tail', tag+'leg_fl' ... , 목줄 고리 tag+'collar_pt'"""
    p = kind + '_'
    c = lambda name, fr, to, col, **f: M.cube(name, [v*s for v in fr], [v*s for v in to], p+col if col != 'nose' else col,
                                              **{k: (p+v if v != 'nose' else v) for k, v in f.items()})
    O = lambda v: [x*s for x in v]
    def leg(n, x0, z0, front):
        k = [c('leg', [x0, 0.8, z0], [x0+2.2, 6, z0+2.2], 'body'),
             c('paw', [x0-0.1, 0, z0-0.4], [x0+2.3, 1.4, z0+2.3], 'paw' if front else 'body')]
        return M.group(tag+n, O([x0+1.1, 6, z0+1.1]), k)
    legs = [leg('leg_fl', 0.9, -6.5, True), leg('leg_fr', -3.1, -6.5, True), leg('leg_bl', 0.9, 2.3, False), leg('leg_br', -3.1, 2.3, False)]
    body = [c('torso', [-3.3, 5.5, -7], [3.3, 12, 5], 'body', up='back', down='belly'),
            c('chest', [-2.8, 6, -7.4], [2.8, 11.5, -6.6], 'belly'),
            c('back_fur', [-3.4, 11.4, -6.5], [3.4, 12.6, 4.5], 'back'),
            c('collar', [-2.9, 12, -8.8], [2.9, 13.4, -6.4], 'collar'),
            M.group(tag+'collar_pt', O([0, 12.7, -8.6]), [])]
    head = [c('neck', [-2.6, 10.5, -9], [2.6, 15, -6], 'body'),
            c('head', [-3.2, 12, -12], [3.2, 18, -7], 'body', north='face', up='back'),
            c('snout', [-1.8, 12, -15], [1.8, 14.8, -12], 'belly', north='snout', up='body'),
            c('ear_l', [1, 18, -10.5], [2.9, 20.4, -9], 'back'), c('ear_r', [-2.9, 18, -10.5], [-1, 20.4, -9], 'back')]
    tail = [c('tail1', [-1.1, 11, 4.5], [1.1, 15, 6.7], 'body'),           # 위로 말린 꼬리
            c('tail2', [-1.1, 14, 2.6], [1.1, 16.4, 5.2], 'body', up='belly')]
    hd = M.group(tag+'head', O([0, 13, -7]), head)
    tl = M.group(tag+'tail', O([0, 12, 5]), tail)
    bod = M.group(tag+'body', O([0, 6, 0]), body + [hd, tl] + legs)
    return M.group(tag+'root', [0, 0, 0], [bod])

# ---------------- 대원 ----------------
SKIN = (238, 200, 165)
def explorer_palette(M):
    M.swatch('ex_skin', SKIN, 3); M.swatch('ex_parka', (40, 55, 95), 6); M.swatch('ex_parka_d', (30, 42, 75), 5)
    M.swatch('ex_pants', (70, 70, 72), 6); M.swatch('ex_boot', (60, 40, 28), 5); M.swatch('ex_glove', (120, 80, 45), 5)
    M.swatch('ex_fur', (225, 215, 195), 10); M.swatch('ex_hat', (150, 40, 35), 6)
    M.swatch('ex_gog', (30, 30, 34), 3); M.swatch('ex_lens', (120, 170, 190), 4); M.swatch('ex_hair', (30, 26, 24), 3)
    def face(d, x, y):
        d.rectangle([x, y, x+15, y+15], fill=SKIN); d.rectangle([x, y, x+15, y+2], fill=(30, 26, 24))
        for ex in (2, 10):
            d.rectangle([x+ex, y+6, x+ex+3, y+9], fill=(255, 255, 255)); d.rectangle([x+ex+1, y+7, x+ex+3, y+9], fill=(25, 20, 20))
            d.rectangle([x+ex, y+5, x+ex+3, y+5], fill=(30, 26, 24))
        d.rectangle([x+7, y+9, x+8, y+11], fill=(215, 170, 135))
        d.rectangle([x+5, y+13, x+10, y+13], fill=(150, 80, 70))   # 입
    M.paint('ex_face', face)

def explorer(M, tag, s=1.0):
    """1950년대 남극 대원: 남색 방한복, 털 달린 깃, 빨간 털모자, 이마에 고글, 갈색 장갑·장화. 키 약 33"""
    c = lambda name, fr, to, col, **f: M.cube(name, [v*s for v in fr], [v*s for v in to], col, **f)
    O = lambda v: [x*s for x in v]
    legL = M.group(tag+'leg_left', O([2, 12, 0]), [c('leg', [0, 2, -2.2], [4.2, 12, 2.2], 'ex_pants'),
                                                  c('boot', [-0.2, 0, -3], [4.4, 4, 2.4], 'ex_boot')])
    legR = M.group(tag+'leg_right', O([-2, 12, 0]), [c('leg', [-4.2, 2, -2.2], [0, 12, 2.2], 'ex_pants'),
                                                    c('boot', [-4.4, 0, -3], [0.2, 4, 2.4], 'ex_boot')])
    armL = M.group(tag+'arm_left', O([6, 22, 0]), [c('arm', [4, 13, -2.2], [8.4, 24, 2.2], 'ex_parka'),
                   c('glove', [4, 10.5, -2.4], [8.6, 13.5, 2.4], 'ex_glove'), M.group(tag+'hand_l', O([6.3, 11, 0]), [])])
    armR = M.group(tag+'arm_right', O([-6, 22, 0]), [c('arm', [-8.4, 13, -2.2], [-4, 24, 2.2], 'ex_parka'),
                   c('glove', [-8.6, 10.5, -2.4], [-4, 13.5, 2.4], 'ex_glove'), M.group(tag+'hand_r', O([-6.3, 11, 0]), [])])
    body = [c('torso', [-4.4, 10, -2.6], [4.4, 24, 2.6], 'ex_parka', down='ex_parka_d'),
            c('zip', [-0.4, 11, -2.8], [0.4, 23, -2.6], 'ex_parka_d'),
            c('pocket_l', [1.2, 14, -2.9], [3.6, 17, -2.6], 'ex_parka_d'), c('pocket_r', [-3.6, 14, -2.9], [-1.2, 17, -2.6], 'ex_parka_d'),
            c('belt', [-4.6, 13, -2.8], [4.6, 14, 2.8], 'ex_parka_d'),
            c('collar_fur', [-4.8, 23, -3], [4.8, 25.4, 3], 'ex_fur')]
    hk = [c('head', [-4, 24.5, -4], [4, 32.5, 4], 'ex_skin', north='ex_face', up='ex_hair'),
          c('hair_back', [-4.2, 27.5, 2], [4.2, 31, 4.2], 'ex_hair'),
          c('hat', [-4.4, 30.5, -4.4], [4.4, 34, 4.4], 'ex_hat'), c('hat_band', [-4.6, 30, -4.6], [4.6, 31.4, 4.6], 'ex_fur'),
          c('hat_pom', [-1.2, 34, -1.2], [1.2, 35.6, 1.2], 'ex_fur'),
          c('gog_band', [-4.5, 31.4, -4.5], [4.5, 32.2, 4.5], 'ex_gog'),
          c('gog_l', [0.6, 31.2, -4.9], [3.6, 33, -4.4], 'ex_lens'), c('gog_r', [-3.6, 31.2, -4.9], [-0.6, 33, -4.4], 'ex_lens')]
    head = M.group(tag+'head', O([0, 24.5, 0]), hk)
    bod = M.group(tag+'body', O([0, 12, 0]), body + [head, armL, armR])
    return M.group(tag+'root', [0, 0, 0], [bod, legL, legR])
