"""《13층 아래》 블록 부품: 모프(청소 로봇) · 핍(작은 로봇) · 경비 로봇 · 감시 드론.  블록인물.py 의 Model·move·Anim·find 를 씀.
   앞 = -z.  모프는 부품마다 묶음(shell·tank·antenna·headshell·armor …) → 하나씩 떼어 낼 수 있음"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 블록인물 import Model, move, anchor, Anim, find, U

def robot_palette(M):
    S=M.swatch
    S('w',(236,238,240),3); S('w_d',(200,204,210),3); S('teal',(60,170,170),5); S('teal_d',(42,130,134),5)
    S('frame',(62,66,76),4); S('frame_d',(40,42,50),3); S('joint',(110,114,124),4)
    S('eye',(110,235,255),2); S('eye_dim',(40,80,92),2); S('chest',(255,170,60),4)
    S('tank',(70,130,220),5); S('tank_d',(50,96,170),5); S('brush',(230,200,90),6); S('handle',(150,110,70),5)
    S('pip',(250,205,60),4); S('pip_d',(210,160,40),4); S('pip_eye',(255,255,255),2); S('k',(18,18,22),2); S('pip_l',(120,255,160),2)
    S('g_body',(36,38,48),4); S('g_d',(22,22,30),3); S('g_red',(255,60,50),3); S('g_stripe',(230,190,40),4); S('g_steel',(120,124,134),5)
    # 고물 부품 색 (다시 맞춘 모프)
    S('p_or',(230,130,50),6); S('p_gr',(110,170,90),6); S('p_pu',(140,100,180),6); S('p_rd',(200,70,60),6); S('p_ye',(230,200,70),6); S('rust',(150,90,60),8)
    def num7(d,x,y):
        d.rectangle([x,y,x+15,y+15],fill=(236,238,240)); d.rectangle([x,y+11,x+15,y+13],fill=(60,170,170))
        d.rectangle([x+5,y+2,x+10,y+3],fill=(42,130,134)); d.rectangle([x+9,y+3,x+10,y+5],fill=(42,130,134)); d.rectangle([x+7,y+5,x+8,y+8],fill=(42,130,134))
    M.paint('front7',num7)

def mop(M, tag, patch=False, s=1.0):
    """모프: 키 약 34 (더듬이 포함). patch=True 면 고물 부품으로 다시 맞춘 모습(색이 제각각)"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]; G=M.group
    P=(lambda a,b: b) if patch else (lambda a,b: a)
    # 다리: 뼈대 + 덮개(armor)
    def leg(sx):
        x0,x1=(1,5) if sx>0 else (-5,-1); nm='leg_left' if sx>0 else 'leg_right'
        arm=G(tag+nm+'_armor',O([(x0+x1)/2,5,0]),[c('legarmor',[x0-0.6,2.4,-2.8],[x1+0.6,8.4,2.8],P('w','p_gr' if sx>0 else 'rust'))])
        return G(tag+nm,O([(x0+x1)/2,8,0]),[c('leg',[x0+0.8,1.5,-1.4],[x1-0.8,8,1.4],'frame'), c('foot',[x0,0,-3.4],[x1,1.6,2.4],'frame_d'), arm])
    # 팔
    def arm(sx):
        x0,x1=(6.4,9.6) if sx>0 else (-9.6,-6.4); nm='arm_left' if sx>0 else 'arm_right'; m=(x0+x1)/2
        k=[c('shoulder',[x0-0.4,17.4,-2.4],[x1+0.4,20.6,2.4],P('teal','p_or' if sx>0 else 'p_pu')), c('arm',[x0+0.6,9,-1.3],[x1-0.6,17.6,1.3],'frame'),
           c('cuff',[x0,9,-2],[x1,11.4,2],P('w','p_ye' if sx>0 else 'rust'))]
        if sx<0: k+= [c('mop_handle',[m-0.6,3,-7],[m+0.6,4.2,1],'handle'), c('mop_head',[m-3,2.2,-10],[m+3,5,-7],'brush')]       # 오른손: 걸레 솔
        else: k+= [c('grip1',[x0+0.2,7,-1.6],[x0+1.2,9,1.6],'joint'), c('grip2',[x1-1.2,7,-1.6],[x1-0.2,9,1.6],'joint')]
        k.append(G(tag+('hand_l' if sx>0 else 'hand_r'),O([m,8,0]),[]))
        return G(tag+nm,O([m,19,0]),k)
    # 몸: 속 뼈대(core) + 겉 껍데기(shell) + 물통(tank)
    core=[c('core',[-4,9,-3],[4,20,3],'frame'), c('core_rib',[-4.4,13,-3.4],[4.4,14.2,3.4],'joint'), c('chest',[-1.6,15,-3.6],[1.6,18,-2.9],'chest'), c('hip',[-5,7.6,-2.6],[5,9.6,2.6],'frame_d')]
    shell=G(tag+'shell',O([0,14,0]),[(c('shell',[-6,9.4,-4.4],[6,21,4.4],'p_gr') if patch else c('shell',[-6,9.4,-4.4],[6,21,4.4],'w',north='front7')), c('shell_band',[-6.3,11.4,-4.7],[6.3,13,4.7],P('teal','p_rd')),
            c('shell_top',[-5.2,21,-3.8],[5.2,22,3.8],P('w_d','rust'))])
    tank=G(tag+'tank',O([0,15,6]),[c('tank',[-4,10.5,4.4],[4,20,8.6],P('tank','p_or')), c('tank_cap',[-2,20,5.2],[2,21.4,7.8],P('tank_d','rust')), c('tank_band',[-4.3,14.4,4.2],[4.3,15.8,8.9],P('tank_d','rust'))])
    # 머리: 속(head) + 껍데기(headshell) + 더듬이(antenna)
    eye=G(tag+'eye',O([0,26,-3.6]),[c('eye',[-3,24.6,-3.9],[3,27.2,-3.1],'eye')])
    hs=G(tag+'headshell',O([0,26,0]),[c('helm',[-4.6,22.6,-3.4],[4.6,30,4.4],P('w','p_ye')), c('helm_brow',[-4.9,27.6,-4.4],[4.9,30.3,-3.2],P('teal','p_rd')),
          c('helm_l',[4.5,24,-4.2],[5.3,28,0],P('teal','p_rd')), c('helm_r',[-5.3,24,-4.2],[-4.5,28,0],P('teal','p_rd'))])
    ant=G(tag+'antenna',O([2.6,30,1]),[c('ant',[2.1,30,0.5],[3.1,34.6,1.5],'joint'), c('ant_tip',[1.7,34.6,0.1],[3.5,36.4,1.9],P('chest','pip_l'))])
    head=G(tag+'head',O([0,22,0]),[c('head',[-3.4,22.4,-3],[3.4,28.6,3],'frame'), c('eye_back',[-3,24.6,-3.3],[3,27.2,-3],'eye_dim'), c('neck',[-1.6,20.6,-1.4],[1.6,22.6,1.4],'joint'), eye, hs, ant])
    body=G(tag+'body',O([0,9,0]),core+[shell,tank,head,arm(1),arm(-1)])
    return G(tag+'root',[0,0,0],[body,leg(1),leg(-1)])

def pip(M, tag, s=1.0):
    """핍: 작은 노란 로봇 (키 약 11). 큰 눈 하나, 머리 위 초록 등"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f); O=lambda v:[x*s for x in v]; G=M.group
    lamp=G(tag+'lamp',O([0,10,0]),[c('lamp_rod',[-0.4,8.4,-0.4],[0.4,10,0.4],'joint'), c('lamp',[-1,10,-1],[1,11.8,1],'pip_l')])
    head=G(tag+'head',O([0,5,0]),[c('body',[-3,2.6,-2.6],[3,8.4,2.6],'pip'), c('belt',[-3.2,3.4,-2.8],[3.2,4.4,2.8],'pip_d'), c('eye_w',[-2,5,-3],[2,7.8,-2.5],'pip_eye'), c('pupil',[-0.8,5.6,-3.3],[0.8,7.2,-2.9],'k'), lamp])
    al=G(tag+'arm_left',O([3.4,6,0]),[c('arm',[3,3.4,-0.6],[4.2,6.6,0.6],'joint')]); ar=G(tag+'arm_right',O([-3.4,6,0]),[c('arm',[-4.2,3.4,-0.6],[-3,6.6,0.6],'joint')])
    ll=G(tag+'leg_left',O([1.4,2.6,0]),[c('leg',[0.8,0,-0.8],[2.2,2.6,0.8],'frame'), c('foot',[0.6,0,-1.8],[2.4,0.8,0.8],'frame_d')])
    lr=G(tag+'leg_right',O([-1.4,2.6,0]),[c('leg',[-2.2,0,-0.8],[-0.8,2.6,0.8],'frame'), c('foot',[-2.4,0,-1.8],[-0.6,0.8,0.8],'frame_d')])
    body=G(tag+'body',O([0,2.6,0]),[head,al,ar])
    return G(tag+'root',[0,0,0],[body,ll,lr])

def guard(M, tag, s=1.0):
    """경비 로봇: 크고 검은 몸(키 약 44), 빨간 눈 띠, 노란 줄무늬 어깨, 전기 봉"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f); O=lambda v:[x*s for x in v]; G=M.group
    def leg(sx):
        x0,x1=(1.5,7) if sx>0 else (-7,-1.5)
        return G(tag+('leg_left' if sx>0 else 'leg_right'),O([(x0+x1)/2,16,0]),[c('leg',[x0,2,-2.6],[x1,16,2.6],'g_body'), c('knee',[x0-0.4,8,-3.2],[x1+0.4,10.4,3.2],'g_steel'), c('foot',[x0-0.6,0,-4.4],[x1+0.6,2.2,3.2],'g_d')])
    def arm(sx):
        x0,x1=(8.6,13) if sx>0 else (-13,-8.6); m=(x0+x1)/2
        k=[c('shoulder',[x0-0.6,30,-3.6],[x1+0.8,35,3.6],'g_stripe'), c('arm',[x0+0.6,16,-2],[x1-0.6,30.4,2],'g_body'), c('fist',[x0,13,-2.8],[x1,16.4,2.8],'g_steel')]
        if sx<0: k+= [c('baton',[m-0.8,13.6,-12],[m+0.8,15.2,-2],'g_d'), c('baton_tip',[m-1.2,13.2,-14.4],[m+1.2,15.6,-12],'g_red')]
        return G(tag+('arm_left' if sx>0 else 'arm_right'),O([m,33,0]),k)
    head=G(tag+'head',O([0,36,0]),[c('head',[-5,36,-4.6],[5,44,4.6],'g_body'), c('visor',[-5.3,39,-5],[5.3,41.6,-4.2],'g_red'), c('crest',[-1,44,-3],[1,46,3],'g_steel'), c('jaw',[-4,36,-5],[4,38,-4.4],'g_steel')])
    body=G(tag+'body',O([0,16,0]),[c('torso',[-8.6,16,-5],[8.6,35,5],'g_body'), c('chest',[-6,24,-5.6],[6,32,-4.8],'g_d'), c('badge',[-1.6,27,-6],[1.6,30,-5.4],'g_red'),
          c('waist',[-7,14.6,-4.2],[7,17,4.2],'g_steel'), c('pack',[-6,20,5],[6,33,8],'g_d'), head, arm(1), arm(-1)])
    return G(tag+'root',[0,0,0],[body,leg(1),leg(-1)])

def drone(M, tag, s=1.0):
    """감시 드론: 검은 상자 + 빨간 눈 + 도는 프로펠러(tag_rotor). 중심 높이 0 (움직임 키로 띄움)"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f); O=lambda v:[x*s for x in v]; G=M.group
    rot=G(tag+'rotor',O([0,4.4,0]),[c('blade',[-8,4.2,-0.9],[8,4.9,0.9],'g_steel'), c('blade2',[-0.9,4.25,-8],[0.9,4.95,8],'g_steel'), c('hub',[-1.2,3,-1.2],[1.2,5.2,1.2],'g_d')])
    return G(tag+'root',[0,0,0],[c('dbody',[-4,-3,-4],[4,3,4],'g_body'), c('deye',[-2,-1.4,-4.6],[2,1.2,-3.9],'g_red'), c('dfin_l',[4,-1,-2],[5.4,1,2],'g_stripe'), c('dfin_r',[-5.4,-1,-2],[-4,1,2],'g_stripe'),
           c('dleg',[-2.6,-4.6,-0.6],[2.6,-3,0.6],'g_steel'), rot])
