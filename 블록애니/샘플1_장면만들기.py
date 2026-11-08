import json, uuid, base64, io, random
from PIL import Image, ImageDraw
random.seed(3)
U=lambda: str(uuid.uuid4())
T=128; S=16
im=Image.new('RGBA',(T,T),(0,0,0,0)); d=ImageDraw.Draw(im); sw={}; slot=[0]
def jit(c,a=14): return tuple(max(0,min(255,v+random.randint(-a,a))) for v in c)
def swatch(name,col,noise=10,fn=None):
    i=slot[0]; slot[0]+=1; x,y=(i%8)*S,(i//8)*S
    for yy in range(S):
        for xx in range(S):
            c=col(xx,yy) if callable(col) else col
            im.putpixel((x+xx,y+yy),jit(c,noise)+(255,))
    if fn: fn(x,y)
    sw[name]=[x,y,x+S,y+S]
swatch('grass_top',(95,170,70))
swatch('grass_side',lambda x,y:(95,170,70) if y<4+(x%3==0) else (130,90,60))
swatch('dirt',(130,90,60))
swatch('stone',(150,150,155),12)
swatch('plank',lambda x,y:(185,140,90) if y%4 else (140,100,60),6)
swatch('log',lambda x,y:(110,80,50) if x%4 else (85,60,38),6)
swatch('leaves',(60,140,60),25)
swatch('roof',lambda x,y:(170,60,50) if y%4 else (130,40,35),6)
swatch('glass',lambda x,y:(240,240,230) if x in(0,15,7,8) or y in(0,15,7,8) else (150,205,235),4)
swatch('door',lambda x,y:(120,80,45) if not(x==11 and y==8) else (230,200,80),6)
swatch('cloud',(250,250,252),3)
swatch('flower_r',(220,60,70),5); swatch('flower_y',(245,215,60),5); swatch('stem',(70,150,60),5)
swatch('path',(200,180,130),12)
# character solid colours
C={'skin':(240,196,160),'coat':(250,200,40),'coat_d':(222,168,25),'pants':(60,140,90),'hair':(40,35,45),'shoe':(90,60,40),'cap':(220,70,60),
   'hood':(140,100,200),'hood_d':(120,82,180),'jeans':(110,160,215),'hair2':(120,75,45),'shoe2':(245,245,245)}
for k,c in C.items(): swatch(k,c,0)
def face(name,hair,top_rows,lash=False):
    i=slot[0]; slot[0]+=1; x,y=(i%8)*S,(i//8)*S
    d.rectangle([x,y,x+S-1,y+S-1],fill=C['skin']); d.rectangle([x,y,x+S-1,y+top_rows-1],fill=hair)
    for ex in (2,10):
        d.rectangle([x+ex,y+7,x+ex+3,y+10],fill=(30,30,40)); d.rectangle([x+ex,y+7,x+ex+1,y+8],fill=(255,255,255))
        if lash: d.rectangle([x+ex-1,y+6,x+ex+4,y+6],fill=(30,30,40))
    d.rectangle([x+6,y+13,x+9,y+13],fill=(190,90,80))
    if lash:
        for cx in (1,13): d.rectangle([x+cx,y+11,x+cx+1,y+12],fill=(240,150,150))
    sw[name]=[x,y,x+S,y+S]
face('face_kid',C['hair'],3); face('face_girl',C['hair2'],4,True)
buf=io.BytesIO(); im.save(buf,'PNG'); im.save('tex.png')
tex={'name':'scene.png','id':'0','uuid':U(),'width':T,'height':T,'uv_width':T,'uv_height':T,'source':'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()}

els=[]
def cube(name,fr,to,col,**over):
    f={k:{'uv':sw[col],'texture':0} for k in ['north','east','south','west','up','down']}
    for k,v in over.items(): f[k]={'uv':sw[v],'texture':0}
    e={'name':name,'type':'cube','uuid':U(),'from':fr,'to':to,'origin':[0,0,0],'rotation':[0,0,0],'faces':f,'box_uv':False,'color':0}
    els.append(e); return e['uuid']
def group(name,origin,children):
    return {'name':name,'uuid':U(),'origin':origin,'rotation':[0,0,0],'export':True,'visibility':True,'children':children}
B=16
# ---- world ----
world=[]
for gx in range(-14,14):
    for gz in range(-8,14):
        x0,z0=gx*B,gz*B
        if gz==-2 : world.append(cube('path',[x0,-B,z0],[x0+B,0,z0+B],'path',north='grass_side',south='grass_side',east='grass_side',west='grass_side'))
        else: world.append(cube('grass',[x0,-B,z0],[x0+B,0,z0+B],'grass_side',up='grass_top',down='dirt'))
# house  x 48..128, z 16..80
hx0,hx1,hz0,hz1=48,128,16,80
for i,(a,b) in enumerate([(hx0,hx1)]):
    pass
world.append(cube('wall_front_l',[hx0,0,hz0],[80,64,hz0+B],'plank'))
world.append(cube('wall_front_r',[96,0,hz0],[hx1,64,hz0+B],'plank'))
world.append(cube('wall_over_door',[80,40,hz0],[96,64,hz0+B],'plank'))
world.append(cube('door',[80,0,hz0+4],[96,40,hz0+8],'door'))
world.append(cube('wall_body',[hx0,0,hz0+B],[hx1,64,hz1],'plank'))
for cx in (hx0-4,hx1-4):
    for cz in (hz0-4,hz1-12):
        world.append(cube('pillar',[cx,0,cz],[cx+8,64,cz+8+4],'log'))
world.append(cube('win_l',[56,24,hz0-1],[72,48,hz0],'glass'))
world.append(cube('win_r',[104,24,hz0-1],[120,48,hz0],'glass'))
for k in range(4):  # stepped roof
    world.append(cube('roof',[hx0-12+k*12,64+k*10,hz0-10],[hx1+12-k*12,74+k*10,hz1+10],'roof'))
# trees
def tree(tx,tz,h=4):
    world.append(cube('trunk',[tx,0,tz],[tx+B,h*B,tz+B],'log',up='log'))
    world.append(cube('leaf1',[tx-2*B,h*B-B,tz-2*B],[tx+3*B,h*B+B,tz+3*B],'leaves'))
    world.append(cube('leaf2',[tx-B,h*B+B,tz-B],[tx+2*B,h*B+2*B,tz+2*B],'leaves'))
tree(-112,32); tree(210,110,5); tree(-200,128,5); tree(0,150,4); tree(120,170,5)
for fx,fz,c in [(-60,-8,'flower_r'),(-40,8,'flower_y'),(-150,0,'flower_y'),(16,4,'flower_r'),(150,-10,'flower_r'),(-90,-70,'flower_y'),(60,-80,'flower_r'),(-20,-90,'flower_y')]:
    world.append(cube('stem',[fx+3,0,fz+3],[fx+5,6,fz+5],'stem'))
    world.append(cube('flower',[fx+1,6,fz+1],[fx+7,11,fz+7],c))
for cx,cy,cz,w in [(-180,230,300,90),(60,260,330,120),(250,220,280,80)]:
    world.append(cube('cloud',[cx,cy,cz],[cx+w,cy+18,cz+50],'cloud'))
    world.append(cube('cloud2',[cx+20,cy+18,cz+10],[cx+w-25,cy+30,cz+40],'cloud'))
world.append(cube('far_ground',[-2000,-40,-2000],[2000,-0.3,3000],'grass_top',north='grass_top',south='grass_top',east='grass_top',west='grass_top'))
world_g=group('world',[0,0,0],world)

# ---- characters ----
def character(tag,pal):
    p=pal
    legL=group(tag+'leg_left',[2,12,0],[cube('leg',[0,2,-2],[4,12,2],p['pants']),cube('shoe',[0,0,-2.5],[4,2,2],p['shoe'])])
    legR=group(tag+'leg_right',[-2,12,0],[cube('leg',[-4,2,-2],[0,12,2],p['pants']),cube('shoe',[-4,0,-2.5],[0,2,2],p['shoe'])])
    armL=group(tag+'arm_left',[6,22,0],[cube('arm',[4,14,-2],[8,24,2],p['coat_d']),cube('hand',[4.5,12,-1.5],[7.5,14,1.5],'skin')])
    armR=group(tag+'arm_right',[-6,22,0],[cube('arm',[-8,14,-2],[-4,24,2],p['coat_d']),cube('hand',[-7.5,12,-1.5],[-4.5,14,1.5],'skin')])
    hk=[cube('head',[-4,24,-4],[4,32,4],'skin',north=p['face'],up=p['hair'])]+p['hairfn']()
    head=group(tag+'head',[0,24,0],hk)
    body=group(tag+'body',[0,12,0],[cube('torso',[-4,12,-2.2],[4,24,2.2],p['coat']),head,armL,armR])
    root=group(tag+'root',[0,0,0],[body,legL,legR])
    return root
kid=character('kid_',{'pants':'pants','shoe':'shoe','coat':'coat','coat_d':'coat_d','face':'face_kid','hair':'hair',
  'hairfn':lambda:[cube('hair_back',[-4.2,28,1.5],[4.2,32.2,4.2],'hair'),cube('cap',[-4.5,31,-4.5],[4.5,33,4.5],'cap'),cube('brim',[-4,31,-7.5],[4,31.6,-4.5],'cap')]})
girl=character('girl_',{'pants':'jeans','shoe':'shoe2','coat':'hood','coat_d':'hood_d','face':'face_girl','hair':'hair2',
  'hairfn':lambda:[cube('hair_back',[-4.3,24,-1],[4.3,32.4,4.3],'hair2'),cube('hair_top',[-4.3,31,-4.3],[4.3,32.6,4.3],'hair2'),
     cube('side_l',[3.6,25,-4.3],[4.4,31,0],'hair2'),cube('side_r',[-4.4,25,-4.3],[-3.6,31,0],'hair2'),
     cube('tie',[-1,29,4.2],[1,31,5.2],'cap'),cube('pony',[-1.5,23,5],[1.5,30,7.5],'hair2')]})
ids={}
def collect(g):
    ids[g['name']]=g['uuid']
    for c in g['children']:
        if isinstance(c,dict): collect(c)
collect(kid); collect(girl)

# ---- animation ----
L=12.0
def kf(t,v,ch='rotation',interp='linear'):
    return {'channel':ch,'data_points':[{'x':str(round(v[0],3)),'y':str(round(v[1],3)),'z':str(round(v[2],3))}],'uuid':U(),'time':round(t,4),'color':-1,'interpolation':interp}
A={}
def add(bone,ch,pts,interp='linear'):
    A.setdefault(bone,[]).extend(kf(t,v,ch,interp) for t,v in pts)
# kid: walks x -150 -> -20 from 0 to 6s, faces +x
WALK=6.0
add('kid_root','position',[(0,(-150,0,-24)),(WALK,(-20,0,-24)),(L,(-20,0,-24))])
add('kid_root','rotation',[(0,(0,-90,0)),(WALK,(0,-90,0)),(6.6,(0,-60,0)),(L,(0,-60,0))])
sw_=[]
t=0;s=1
while t<WALK-1e-6: sw_.append((t,s));t+=0.5;s=-s
def swing(bone,amp,sign):
    pts=[(t,(sign*s*amp,0,0)) for t,s in sw_]+[(WALK,(0,0,0)),(L,(0,0,0))]
    add(bone,'rotation',pts,'catmullrom')
swing('kid_leg_left',32,1); swing('kid_leg_right',32,-1); swing('kid_arm_left',28,-1)
# kid right arm: walk swing then wave 8.0-10.0
pts=[(t,(s*28,0,0)) for t,s in sw_]+[(WALK,(0,0,0)),(7.8,(0,0,0)),(8.1,(0,0,-150))]
tt=8.1;k=0
while tt<9.9: tt+=0.25;k+=1; pts.append((tt,(0,0,-125 if k%2 else -150)))
pts+= [(10.2,(0,0,0)),(L,(0,0,0))]
add('kid_arm_right','rotation',pts,'catmullrom')
bob=[(i*0.25,(0,1.0 if i%2 else 0,0)) for i in range(int(WALK/0.25)+1)]
add('kid_body','position',bob+[(L,(0,0,0))])
# girl: stands at x 40 facing camera, turns to kid at 5.0, waves 6.3-8.5
add('girl_root','position',[(0,(36,0,-24)),(L,(36,0,-24))])
add('girl_root','rotation',[(0,(0,0,0)),(5.0,(0,0,0)),(5.6,(0,60,0)),(L,(0,60,0))],'linear')
pts=[(0,(0,0,0)),(6.2,(0,0,0)),(6.5,(0,0,150))]; tt=6.5;k=0
while tt<8.5: tt+=0.25;k+=1; pts.append((tt,(0,0,125 if k%2 else 150)))
pts+=[(8.8,(0,0,0)),(L,(0,0,0))]
add('girl_arm_left','rotation',pts,'catmullrom')
add('girl_head','rotation',[(0,(0,0,0)),(1.5,(0,0,4)),(3,(0,0,-4)),(4.5,(0,0,0)),(6.4,(-8,0,0)),(7,(0,0,6)),(7.6,(0,0,-6)),(8.2,(0,0,0)),(L,(0,0,0))],'catmullrom')
# both hop 10.4-11.8
for root in ('kid_','girl_'):
    base=(-20,0,-24) if root=='kid_' else (36,0,-24)
    hp=[(10.3,base),(10.5,(base[0],6,base[2])),(10.7,base),(11.0,(base[0],6,base[2])),(11.2,base)]
    A[root+'root']=[k_ for k_ in A[root+'root'] if not(k_['channel']=='position' and 10<k_['time']<L)]
    add(root+'root','position',hp)
    add(root+'arm_left','rotation',[]) 
anim={'uuid':U(),'name':'scene1','loop':'once','length':L,'snapping':24,
      'animators':{ids[b]:{'name':b,'type':'bone','keyframes':k} for b,k in A.items() if k}}
m={'meta':{'format_version':'4.10','model_format':'free','box_uv':False},'name':'block_village',
   'resolution':{'width':T,'height':T},'elements':els,'outliner':[world_g,kid,girl],'textures':[tex],'animations':[anim]}
json.dump(m,open('블록마을_장면1.bbmodel','w'),ensure_ascii=False)
print(len(els),'cubes', len(A),'animated bones')
