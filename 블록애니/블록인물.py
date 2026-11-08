"""블록 애니 공용 부품: 색 견본 그림 + 상자(cube)·묶음(group) 만들기 + 인물·모아이 모형.
   다른 장면 프로그램에서 import 해서 씀.  (Blockbench .bbmodel, 'free' 형식)"""
import json, uuid, base64, io, random
from PIL import Image, ImageDraw
U=lambda: str(uuid.uuid4())

class Model:
    def __init__(self, tex_size=128, seed=3):
        self.T=tex_size; self.S=16; random.seed(seed)
        self.im=Image.new('RGBA',(self.T,self.T),(0,0,0,0)); self.d=ImageDraw.Draw(self.im)
        self.sw={}; self.slot=0; self.els=[]
    # ---- 색 견본 ----
    def _jit(self,c,a):
        r=random.randint(-a,a)  # 밝기만 흔듦 (무지개 얼룩 방지)
        return tuple(max(0,min(255,v+r+random.randint(-2,2))) for v in c)
    def _next(self):
        i=self.slot; self.slot+=1; return (i%(self.T//16))*16,(i//(self.T//16))*16
    def swatch(self,name,col,noise=8):
        x,y=self._next()
        for yy in range(16):
            for xx in range(16):
                c=col(xx,yy) if callable(col) else col
                self.im.putpixel((x+xx,y+yy),self._jit(c,noise)+(255,))
        self.sw[name]=[x,y,x+16,y+16]; return name
    def paint(self,name,fn):
        """fn(draw,x,y) 로 직접 그리는 16x16 칸 (얼굴 등)"""
        x,y=self._next(); fn(self.d,x,y); self.sw[name]=[x,y,x+16,y+16]; return name
    # ---- 상자·묶음 ----
    def cube(self,name,fr,to,col,**faces):
        f={k:{'uv':self.sw[col],'texture':0} for k in ['north','east','south','west','up','down']}
        for k,v in faces.items(): f[k]={'uv':self.sw[v],'texture':0}
        e={'name':name,'type':'cube','uuid':U(),'from':[round(v,3) for v in fr],'to':[round(v,3) for v in to],
           'origin':[0,0,0],'rotation':[0,0,0],'faces':f,'box_uv':False,'color':0}
        self.els.append(e); return e['uuid']
    @staticmethod
    def group(name,origin,children,rotation=(0,0,0)):
        return {'name':name,'uuid':U(),'origin':list(origin),'rotation':list(rotation),'export':True,'visibility':True,'children':children}
    def save(self,path,outliner,animations=(),name='model'):
        buf=io.BytesIO(); self.im.save(buf,'PNG')
        tex={'name':'tex.png','id':'0','uuid':U(),'width':self.T,'height':self.T,'uv_width':self.T,'uv_height':self.T,
             'source':'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()}
        m={'meta':{'format_version':'4.10','model_format':'free','box_uv':False},'name':name,
           'resolution':{'width':self.T,'height':self.T},'elements':self.els,'outliner':list(outliner),
           'textures':[tex],'animations':list(animations)}
        json.dump(m,open(path,'w',encoding='utf-8'),ensure_ascii=False)

# ---------------- 라파누이 사람들 ----------------
SKIN=(170,112,72); HAIR=(28,24,24); GREY=(205,205,200)
def islander_palette(M):
    M.swatch('skin',SKIN,4); M.swatch('skin_d',(150,96,60),4); M.swatch('skin_t',(152,98,62),4)
    M.swatch('hair',HAIR,4); M.swatch('grey',GREY,6)
    M.swatch('tapa',lambda x,y:(225,205,165) if (x+y)%6 else (150,95,55),5)        # 나무껍질 천 (무늬)
    M.swatch('tapa2',lambda x,y:(200,150,95) if (x//4+y//4)%2 else (175,120,70),5)
    M.swatch('tapa3',lambda x,y:(235,225,200) if y%5 else (120,70,45),4)
    M.swatch('shell',(245,240,225),4); M.swatch('band',(185,50,40),5)
    M.swatch('wood',(120,80,45),6); M.swatch('feather',(30,30,30),6); M.swatch('stone_t',(90,90,95),8)
    def face(name,hair,beard=None,young=False):
        def fn(d,x,y):
            d.rectangle([x,y,x+15,y+15],fill=SKIN); d.rectangle([x,y,x+15,y+2],fill=hair)
            for ex in (2,10):
                d.rectangle([x+ex,y+6,x+ex+3,y+9],fill=(255,255,255)); d.rectangle([x+ex+1,y+7,x+ex+3,y+9],fill=(25,20,20))
                d.rectangle([x+ex,y+5,x+ex+3,y+5],fill=hair)
            d.rectangle([x+7,y+9,x+8,y+11],fill=(150,96,60))
            if beard: d.rectangle([x+2,y+12,x+13,y+15],fill=beard); d.rectangle([x+6,y+13,x+9,y+13],fill=(120,60,50))
            else: d.rectangle([x+5,y+13,x+10,y+13],fill=(120,60,50))
            if young: d.rectangle([x+1,y+11,x+2,y+11],fill=(200,120,95)); d.rectangle([x+13,y+11,x+14,y+11],fill=(200,120,95))
        M.paint(name,fn)
    face('face_atu',HAIR,young=True); face('face_mata',GREY,beard=GREY); face('face_man',HAIR); face('face_man2',HAIR,beard=HAIR)

def person(M,tag,kind='man',s=1.0,skirt='tapa2',tool=None):
    """kind: atu(소년) / mata(할아버지 석공 우두머리) / man / man2 (마을 사람)"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*s for v in fr],[v*s for v in to],col,**f)
    O=lambda v:[x*s for x in v]
    legL=M.group(tag+'leg_left',O([2,12,0]),[c('leg',[0,0,-2],[4,12,2],'skin',down='skin_d')])
    legR=M.group(tag+'leg_right',O([-2,12,0]),[c('leg',[-4,0,-2],[0,12,2],'skin',down='skin_d')])
    armL=M.group(tag+'arm_left',O([6,22,0]),[c('arm',[4,12,-2],[8,24,2],'skin'),M.group(tag+'hand_l',O([6,12.5,0]),[])])
    armRk=[c('arm',[-8,12,-2],[-4,24,2],'skin')]
    face={'atu':'face_atu','mata':'face_mata','man':'face_man','man2':'face_man2',
          'merer':'face_merer','worker':'face_worker','worker2':'face_worker2','ankhhaf':'face_ankh'}[kind]
    hair='grey' if kind=='mata' else 'hair'
    hk=[c('head',[-4,24,-4],[4,32,4],'skin',north=face,up=hair),
        c('hair_back',[-4.2,26,1],[4.2,32.2,4.2],hair), c('hair_top',[-4.2,31.2,-4.2],[4.2,32.4,4.2],hair)]
    body=[c('torso',[-4,12,-2],[4,24,2],'skin_t'), c('skirt',[-4.4,8,-2.4],[4.4,14,2.4],skirt)]
    if kind=='atu':
        body+= [c('shell1',[-3,19,-2.6],[-1,21,-2],'shell'),c('shell2',[-1,18,-2.6],[1,20,-2],'shell'),c('shell3',[1,19,-2.6],[3,21,-2],'shell')]
        hk+= [c('topknot',[-1.5,32,-0.5],[1.5,35,2.5],'hair')]
    if kind=='mata':
        body+= [c('cape',[-4.6,13,-2.6],[4.6,24.4,2.6],'tapa',north='tapa3')]
        body+= [c('cape_open',[-2,13,-2.7],[2,22,-2.5],'skin')]
        hk+= [c('beard',[-3,21,-4.4],[3,25,-3.6],'grey'), c('feather_band',[-4.4,30,-4.4],[4.4,31.4,4.4],'band')]
        armRk+= [c('staff',[-7,-2,-6],[-5,30,-4],'wood')]
    if kind in ('man','man2'):
        hk+= [c('headband',[-4.4,29,-4.4],[4.4,30.4,4.4],'band')]
    if kind in ('merer','ankhhaf'):   # 이집트 가발(단발) + 넓은 목걸이
        hk+= [c('wig_l',[3.8,24.5,-4.4],[4.8,32.6,4.6],'hair'),c('wig_r',[-4.8,24.5,-4.4],[-3.8,32.6,4.6],'hair'),
              c('wig_b',[-4.8,24,3.6],[4.8,32.6,4.8],'hair'),c('wig_t',[-4.8,31.4,-4.6],[4.8,33,4.8],'hair')]
        body+= [c('collar',[-4.3,20.5,-2.4],[4.3,24,2.4],'collar' if kind=='merer' else 'gold')]
    if kind=='ankhhaf':
        body+= [c('kilt_long',[-4.5,4,-2.5],[4.5,9,2.5],'linen')]
        armRk+= [c('staff',[-7,-2,-6],[-5,30,-4],'gold')]
    if kind=='merer':
        armRk+= [c('scroll',[-7.5,11,-3.5],[-4.5,13,1.5],'papyrus')]
    if kind=='worker2':
        hk+= [c('headcloth',[-4.4,29.5,-4.4],[4.4,32.6,4.4],'linen')]
    if tool=='axe': armRk+= [c('axe_h',[-6.6,8,-1],[-5.4,14,0],'wood'), c('axe_s',[-7.5,6,-3.5],[-4.5,9,0],'stone_t')]
    armR=M.group(tag+'arm_right',O([-6,22,0]),armRk+[M.group(tag+'hand_r',O([-6,12.5,0]),[])])
    head=M.group(tag+'head',O([0,24,0]),hk)
    bod=M.group(tag+'body',O([0,12,0]),body+[head,armL,armR])
    return M.group(tag+'root',[0,0,0],[bod,legL,legR])

# ---------------- 모아이 ----------------
def moai_palette(M):
    M.swatch('tuff',(150,140,118),14); M.swatch('tuff_d',(118,108,90),12); M.swatch('tuff_l',(172,162,138),12)
    M.swatch('eye_w',(240,240,235),3); M.swatch('eye_k',(30,30,30),3); M.swatch('pukao',(160,70,50),12)

def moai(M,tag,road=True,eyes=False,S=1.0):
    """road=True: 길 위 석상 (넓은 바닥 + 앞쪽 둥근 가장자리 + 앞으로 기욺, 눈 없음)
       road=False: 제단 석상 (곧게, 바닥 좁게). 키 약 80 (사람 32 의 2.5배)"""
    c=lambda name,fr,to,col,**f: M.cube(name,[v*S for v in fr],[v*S for v in to],col,**f)
    k=[]
    if road:  # 넓은 바닥, 앞쪽 가장자리는 계단식으로 둥글게
        k+= [c('base',[-13,0,-7],[13,6,9],'tuff_d'), c('base_round1',[-12,0,-9],[12,4,-7],'tuff_d'), c('base_round2',[-10,0,-10.5],[10,2,-9],'tuff_d')]
    else:
        k+= [c('base',[-11,0,-7],[11,6,8],'tuff_d')]
    k+= [c('belly',[-11,6,-7],[11,30,8],'tuff'), c('chest',[-10,30,-6],[10,42,7],'tuff')]
    # 몸에 새긴 팔·손 (옆에서 배 쪽으로)
    for sx in (-1,1):
        k+= [c('arm',[10.6,13,-2] if sx>0 else [-11.6,13,-2], [11.8,40,1.5] if sx>0 else [-10.6,40,1.5],'tuff_d'),
             c('hand',[3,10,-7.6] if sx>0 else [-11,10,-7.6],[11,13,-6.8] if sx>0 else [-3,13,-6.8],'tuff_d')]
    # 머리: 길고 큰 얼굴
    hd=[c('neck',[-8,42,-5],[8,46,6],'tuff'), c('head',[-9,46,-6],[9,80,7],'tuff',up='tuff_l'),
        c('brow',[-9,68,-8.5],[9,72,-6],'tuff_l'), c('nose',[-2.5,54,-9.5],[2.5,70,-6],'tuff_l'),
        c('nose_tip',[-3.5,53,-10.5],[3.5,56,-6],'tuff_l'),
        c('lips',[-6,48,-8],[6,52,-6],'tuff_l'), c('chin',[-7,44,-7.5],[7,48,-6],'tuff'),
        c('ear_l',[9,52,-2],[10.5,72,2],'tuff_d'), c('ear_r',[-10.5,52,-2],[-9,72,2],'tuff_d')]
    if eyes:
        for ex in (-6,2):
            hd+= [c('eye_w',[ex,63,-6.6],[ex+4,67,-6.2],'eye_w'), c('eye_k',[ex+1,64,-6.8],[ex+3,66,-6.4],'eye_k')]
    hd+= [anchor(M,tag+'rope_L',[-9*S,70*S,0]), anchor(M,tag+'rope_R',[9*S,70*S,0]), anchor(M,tag+'rope_B',[0,70*S,7*S])]
    head=M.group(tag+'head',[0,46*S,0],hd)
    return M.group(tag+'root',[0,0,0],k+[head],rotation=(8 if road else 0,0,0))

# ---------------- 배치·움직임 도우미 ----------------
def move(M, g, dx=0, dy=0, dz=0):
    """묶음 g(안의 모든 상자·묶음)를 (dx,dy,dz) 만큼 옮김"""
    byid={e['uuid']:e for e in M.els}
    def rec(n):
        n['origin']=[n['origin'][0]+dx,n['origin'][1]+dy,n['origin'][2]+dz]
        for c in n['children']:
            if isinstance(c,dict): rec(c)
            else:
                e=byid[c]; e['from']=[e['from'][0]+dx,e['from'][1]+dy,e['from'][2]+dz]; e['to']=[e['to'][0]+dx,e['to'][1]+dy,e['to'][2]+dz]
    rec(g); return g

def anchor(M, name, pos):
    """밧줄 끝을 잡을 보이지 않는 점 (묶음의 중심 = pos)"""
    return M.group(name, pos, [])

class Anim:
    """한 장면 모형의 움직임 하나 (시간 = 영상 시간 그대로)"""
    def __init__(self, length): self.L=length; self.tr={}
    def add(self, g, ch, pts, interp='linear'):
        lst=self.tr.setdefault(g['uuid'],(g['name'],[]))[1]
        for t,v in pts:
            lst.append({'channel':ch,'data_points':[{'x':str(round(v[0],3)),'y':str(round(v[1],3)),'z':str(round(v[2],3))}],
                        'uuid':U(),'time':round(t,4),'color':-1,'interpolation':interp})
    def bake(self, outliner):
        """묶음의 고정 회전(rotation)은 움직임 화면에서 무시됨 → 움직임 키로 옮김"""
        def rec(g):
            r=g.get('rotation',[0,0,0])
            if any(abs(v)>1e-6 for v in r):
                g['rotation']=[0,0,0]
                ent=self.tr.get(g['uuid'])
                keys=[k for k in (ent[1] if ent else []) if k['channel']=='rotation']
                if keys:
                    for k in keys:
                        dp=k['data_points'][0]
                        for ax,v in zip('xyz',r): dp[ax]=str(round(float(dp[ax])+v,3))
                else:
                    self.add(g,'rotation',[(0,tuple(r))])
            for c in g['children']:
                if isinstance(c,dict): rec(c)
        for g in outliner:
            if isinstance(g,dict): rec(g)
    def json(self, name='main'):
        an={}
        for uid,(nm,k) in self.tr.items():
            # 같은 채널·같은 시간 키는 마지막 것만
            seen={}
            for kf in k: seen[(kf['channel'],kf['time'])]=kf
            an[uid]={'name':nm,'type':'bone','keyframes':sorted(seen.values(),key=lambda x:x['time'])}
        return {'uuid':U(),'name':name,'loop':'once','length':self.L,'snapping':24,'animators':an}

def find(g, name):
    if g['name']==name: return g
    for c in g['children']:
        if isinstance(c,dict):
            r=find(c,name)
            if r: return r


# ---------------- 고대 이집트 ----------------
def egypt_palette(M):
    M.swatch('skin',(176,118,74),4); M.swatch('skin_d',(150,98,60),4); M.swatch('skin_t',(160,106,66),4)
    M.swatch('hair',(22,20,22),4); M.swatch('grey',(200,200,195),5)
    M.swatch('linen',(240,236,222),4); M.swatch('linen2',lambda x,y:(240,236,222) if y%5 else (200,190,170),3)
    M.swatch('collar',lambda x,y:[(40,90,170),(230,190,60),(200,60,50),(40,150,130)][(y//4)%4],3)
    M.swatch('gold',(225,185,60),8); M.swatch('papyrus',(225,210,160),5)
    M.swatch('wood',(130,90,50),6); M.swatch('wood_d',(100,68,38),6); M.swatch('stone_t',(90,90,95),8)
    M.swatch('lime',(236,232,220),6); M.swatch('lime_d',(210,204,188),8); M.swatch('core',(200,170,120),12)
    M.swatch('sail',lambda x,y:(235,228,205) if x%6 else (205,195,170),3); M.swatch('rope',(200,170,110),6)
    M.swatch('jar',(170,90,55),6); M.swatch('band',(185,50,40),5); M.swatch('shell',(245,240,225),4)
    def face(name,hair,top_rows=3,young=False,brow=True):
        def fn(d,x,y):
            d.rectangle([x,y,x+15,y+15],fill=(176,118,74)); d.rectangle([x,y,x+15,y+top_rows-1],fill=hair)
            for ex in (2,10):
                d.rectangle([x+ex,y+6,x+ex+3,y+9],fill=(255,255,255)); d.rectangle([x+ex+1,y+7,x+ex+3,y+9],fill=(25,20,20))
                if brow: d.rectangle([x+ex,y+4,x+ex+3,y+4],fill=hair)
            d.rectangle([x+7,y+9,x+8,y+11],fill=(150,98,60)); d.rectangle([x+5,y+13,x+10,y+13],fill=(120,60,50))
            if young: d.rectangle([x+1,y+11,x+2,y+11],fill=(200,120,95)); d.rectangle([x+13,y+11,x+14,y+11],fill=(200,120,95))
        M.paint(name,fn)
    face('face_merer',(22,20,22),3); face('face_worker',(60,50,45),2); face('face_worker2',(22,20,22),3,young=True); face('face_ankh',(22,20,22),3)

def boat(M,tag,L=150,W=34,cargo=3):
    """옛 이집트 화물선: 양 끝이 들린 나무 배 + 돛대·네모 돛 + 키 노 + 석회암 돌. 길이는 z 방향, 뱃머리 = -z"""
    k=[]; _cube=M.cube
    class _M:   # x↔z 바꿔서 만듦 (뱃머리 +x → -z)
        def cube(self,n,fr,to,col): return _cube(n,[fr[2],fr[1],-to[0]],[to[2],to[1],-fr[0]],col)
    M=_M()
    for i,(x0,x1,y0,y1,w) in enumerate([(-L/2+16,L/2-16,0,8,W),(-L/2+6,L/2-6,4,12,W-8),(-L/2,L/2,9,15,W-16)]):
        k.append(M.cube('hull',[x0,y0,-w/2],[x1,y1,w/2],'wood' if i!=1 else 'wood_d'))
    k+= [M.cube('bow',[L/2-4,12,-5],[L/2+4,26,5],'wood'), M.cube('stern',[-L/2-4,12,-5],[-L/2+4,30,5],'wood'),
         M.cube('deck',[-L/2+16,8,-W/2+2],[L/2-16,9,W/2-2],'wood_d'),
         M.cube('mast',[-2,8,-2],[2,90,2],'wood'), M.cube('yard',[-2,86,-30],[2,89,30],'wood'), M.cube('yard2',[-2,40,-30],[2,42,30],'wood'),
         M.cube('sail',[-0.6,42,-29],[0.6,86,29],'sail'),
         M.cube('rudder',[-L/2-12,4,-2],[-L/2+6,22,2],'wood_d')]
    for j in range(cargo):
        x=-L/2+28+j*30
        if abs(x)<8: x+=14
        k.append(M.cube('stone',[x,9,-9],[x+20,25,9],'lime'))
    return Model.group(tag+'root',[0,0,0],k+[Model.group(tag+'bow_a',[0,20,-L/2],[])])

def stone_block(M,tag,x=0,y=0,z=0,s=1.0):
    return M.group(tag,[x,y,z],[M.cube('blk',[x-10*s,y,z-9*s],[x+10*s,y+16*s,z+9*s],'lime')])

def pyramid(M,tag,cx,cz,base=640,step=12,layers=None,casing=True):
    """계단식으로 쌓은 피라미드 (casing=True 면 하얀 겉돌, False 면 누런 속돌). layers=None 이면 꼭대기까지"""
    k=[]; n=int(base/2/step); n=n if layers is None else min(n,layers)
    for i in range(n):
        h=base/2-i*step
        k.append(M.cube('p',[cx-h,i*step*0.95,cz-h],[cx+h,(i+1)*step*0.95,cz+h],'lime' if casing else ('core' if i%2 else 'lime_d')))
    return M.group(tag,[cx,0,cz],k)
