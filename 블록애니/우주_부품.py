"""우주 전쟁 블록 부품 (모두 새로 지은 모양): 지구 전투기·순양함·기함·방위 기지 / 외계 요격기·초대형 모함 / 지구·달·별 벽
   - 모든 함선은 상자마다 묶음(조각)으로 감쌈 → explode() 로 **블록이 흩어지며 분해**
   - 앞 = -z.  크기: 전투기 16, 순양함 130, 기함 240, 기지 지름 260, 모함 1700×650×900"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import ImageDraw
from 블록인물 import Model, move, anchor, Anim, find, U
from 신라인물 import BigModel

def _panel(base,line,lights=(),n=0,seed=0,size=64):
    def fn(im,x,y,w,h):
        d=ImageDraw.Draw(im); r=random.Random(seed); d.rectangle([x,y,x+w-1,y+h-1],fill=base)
        for k in range(6):
            x0=r.randint(0,w-12); y0=r.randint(0,h-10); d.rectangle([x+x0,y+y0,x+min(w-1,x0+r.randint(8,26)),y+min(h-1,y0+r.randint(6,20))],outline=line)
        for k in range(n):
            px=r.randint(2,w-4); py=r.randint(2,h-3); c=r.choice(lights); d.rectangle([x+px,y+py,x+px+r.choice([1,1,2,4]),y+py+1],fill=c)
        px_=im.load()
        for yy in range(y,y+h):
            for xx in range(x,x+w):
                c=px_[xx,yy]; dd=r.randint(-4,4); px_[xx,yy]=(max(0,min(255,c[0]+dd)),max(0,min(255,c[1]+dd)),max(0,min(255,c[2]+dd)),255)
    return fn
def _stars(seed,n=260,neb=None):
    def fn(im,x,y,w,h):
        d=ImageDraw.Draw(im); r=random.Random(seed); d.rectangle([x,y,x+w-1,y+h-1],fill=(3,4,12))
        if neb:
            for k in range(900):
                cx=int(r.gauss(w*neb[0],w*0.16)); cy=int(r.gauss(h*neb[1],h*0.10))
                if 0<=cx<w and 0<=cy<h: d.point((x+cx,y+cy),fill=r.choice(neb[2]))
        for k in range(n):
            px=r.randint(0,w-2); py=r.randint(0,h-2); b=r.choice([120,150,180,210,255]); c=r.choice([(b,b,b),(b,b,int(b*0.8)),(int(b*0.8),int(b*0.9),b)])
            d.point((x+px,y+py),fill=c)
            if b==255 and r.random()<0.35: d.rectangle([x+px,y+py,x+px+1,y+py+1],fill=c)
    return fn
def space_palette(M):
    S=M.swatch; B=M.big
    S('e_w',(226,230,236),4); S('e_g',(150,158,170),5); S('e_d',(84,90,104),5); S('e_blue',(50,110,220),5); S('e_or',(255,150,40),4); S('e_glass',(120,220,255),3); S('e_red',(220,50,50),4)
    S('glow_c',(150,240,255),2); S('glow_w',(255,255,240),2); S('glow_o',(255,190,80),3); S('glow_y',(255,240,140),2)
    S('a_k',(26,20,36),4); S('a_p',(70,40,110),6); S('a_m',(255,60,200),3); S('a_mc',(255,190,240),2); S('a_g',(120,255,120),3)
    S('fire1',(255,220,90),10); S('fire2',(255,130,40),14); S('fire3',(255,250,220),4); S('smoke',(90,86,92),10)
    S('sea',(40,90,190),8); S('sea2',(54,112,206),8); S('land',(70,150,80),10); S('land2',(150,140,90),10); S('ice',(240,244,248),4); S('cloud',(232,238,244),5); S('atm',(120,180,255),4)
    S('moon',(170,170,176),8); S('moon_d',(128,128,136),8); S('sun',(255,244,200),2); S('black',(4,4,8),1)
    B('hull_e',64,64,_panel((196,202,212),(150,156,170),[(60,130,240),(255,230,120)],10,1)); B('hull_e2',64,64,_panel((160,168,182),(116,124,140),[(255,230,120)],14,2))
    B('hull_a',64,64,_panel((30,24,42),(64,40,96),[(255,60,200),(150,90,255),(120,255,120)],22,3)); B('hull_a2',64,64,_panel((22,18,32),(48,30,76),[(255,60,200),(150,90,255)],34,4))
    B('hull_a3',64,64,_panel((40,30,56),(84,52,124),[(255,60,200)],10,5)); B('maw',64,64,_panel((255,70,210),(255,200,245),[(255,255,255)],40,6))
    B('win_e',64,16,_panel((60,66,80),(60,66,80),[(255,230,120),(150,220,255)],26,7)); B('solar',64,32,_panel((30,50,120),(90,130,220),[],0,8))
    B('stars1',256,256,_stars(1)); B('stars2',256,256,_stars(2,neb=(0.4,0.5,[(40,20,70),(60,30,90),(30,40,90)]))); B('stars3',256,256,_stars(3,neb=(0.6,0.4,[(20,50,80),(30,70,90),(50,30,60)])))

class Ship:
    """상자마다 묶음(조각)으로 감싼 함선. cube() 로 조각을 더하고, group() 으로 뿌리 묶음을 얻음"""
    def __init__(s,M,tag,scale=1.0): s.M=M; s.tag=tag; s.k=scale; s.pcs=[]; s.extra=[]
    def cube(s,fr,to,col,**f):
        k=s.k; fr=[v*k for v in fr]; to=[v*k for v in to]; c=[(a+b)/2 for a,b in zip(fr,to)]
        u=s.M.cube('pc',fr,to,col,**f); g=s.M.group(f'{s.tag}pc{len(s.pcs)}',c,[u]); s.pcs.append((g,c)); return g
    def glow(s,name,fr,to,col):
        k=s.k; fr=[v*k for v in fr]; to=[v*k for v in to]; g=s.M.group(s.tag+name,[(a+b)/2 for a,b in zip(fr,to)],[s.M.cube('glow',fr,to,col)]); s.extra.append(g); return g
    def group(s): s.root=s.M.group(s.tag+'root',[0,0,0],[g for g,_ in s.pcs]+s.extra); return s.root

def explode(A,ship,t0,center=(0,0,0),power=60,dur=2.2,seed=0,delay=0.0,keep_scale=0.0,spin=260):
    """블록 분해: 조각마다 바깥으로 흩어지며 돌고 작아짐. delay>0 이면 center 에서 먼 조각일수록 늦게 터짐(물결처럼). 엔진 불빛 등은 바로 꺼짐"""
    r=random.Random(seed); far=max(1e-6,max(math.dist(c,center) for _,c in ship.pcs))
    for g,c in ship.pcs:
        d=[c[i]-center[i]+r.uniform(-0.25,0.25)*far*0.3 for i in range(3)]; n=math.sqrt(sum(v*v for v in d)) or 1; f=power*r.uniform(0.5,1.4)
        t=t0+delay*math.dist(c,center)/far+r.uniform(0,0.12); off=(-d[0]/n*f,d[1]/n*f,d[2]/n*f)
        A.add(g,'position',[(0,(0,0,0)),(t,(0,0,0)),(t+dur*0.3,tuple(v*0.55 for v in off)),(t+dur,off)],'catmullrom')
        A.add(g,'rotation',[(0,(0,0,0)),(t,(0,0,0)),(t+dur,(r.uniform(-spin,spin),r.uniform(-spin,spin),r.uniform(-spin,spin)))])
        A.add(g,'scale',[(0,(1,1,1)),(t+dur*0.5,(1,1,1)),(t+dur,(keep_scale,)*3)])
    for g in ship.extra: A.add(g,'scale',[(0,(1,1,1)),(t0,(1,1,1)),(t0+0.05,(0,0,0))])

def fighter(M,tag,stripe='e_blue'):
    s=Ship(M,tag); c=s.cube
    c([-2,-1.5,-6],[2,1.5,6],'e_w'); c([-1.2,-1,-10],[1.2,1,-6],'e_g'); c([-1.4,1.5,-4],[1.4,3,1],'e_glass'); c([2,-0.6,-2],[9,0.4,4],'e_w'); c([-9,-0.6,-2],[-2,0.4,4],'e_w')
    c([8,-1.4,-4],[10,1.2,5],stripe); c([-10,-1.4,-4],[-8,1.2,5],stripe); c([-0.5,1.5,3],[0.5,5,7],stripe); c([2,-1.4,4],[4.4,1.2,8],'e_d'); c([-4.4,-1.4,4],[-2,1.2,8],'e_d')
    c([-2.2,-1.7,-1],[2.2,-1.5,3],stripe)
    s.glow('engine',[-4,-1,8],[4,0.8,10.5],'glow_c'); return s
def interceptor(M,tag):
    s=Ship(M,tag); c=s.cube
    c([-2.4,-2,-3],[2.4,2,4],'a_k'); c([-1,-0.8,-9],[1,0.8,-3],'a_p'); c([3,-0.6,-8],[4.4,0.6,2],'a_p'); c([-4.4,-0.6,-8],[-3,0.6,2],'a_p')
    c([2.4,-3.6,0],[3.6,3.6,6],'a_k'); c([-3.6,-3.6,0],[-2.4,3.6,6],'a_k'); c([-0.6,2,-1],[0.6,6,5],'a_p'); c([-1.4,-1,-3.6],[1.4,1,-3],'a_m')
    s.glow('engine',[-1.6,-1.2,4],[1.6,1.2,6.2],'a_m'); return s
def cruiser(M,tag):
    s=Ship(M,tag); c=s.cube
    c([-12,-8,-60],[12,8,-20],'hull_e'); c([-15,-10,-20],[15,10,25],'hull_e'); c([-13,-9,25],[13,9,55],'hull_e2'); c([-7,-5,-72],[7,5,-60],'e_g'); c([-3,-2,-80],[3,2,-72],'e_blue')
    c([-8,10,-4],[8,18,18],'e_w',north='win_e',east='win_e',west='win_e',south='win_e'); c([-5,18,2],[5,23,12],'e_g'); c([-0.6,23,6],[0.6,34,7.2],'e_d')
    c([15,-4,-30],[23,4,30],'hull_e2'); c([-23,-4,-30],[-15,4,30],'hull_e2'); c([15.2,-1,-34],[22.8,1,-30],'e_blue'); c([-22.8,-1,-34],[-15.2,1,-30],'e_blue')
    for z in (-44,-30):
        c([-4,8,z-4],[4,12,z+4],'e_d'); c([-1,10,z-12],[1,11.6,z-4],'e_g')
    c([-4,-12,-10],[4,-8,6],'e_d'); c([-15.2,-10.2,30],[15.2,-7,34],'e_blue'); c([-10,-6,55],[10,6,62],'e_d'); c([-15.4,2,-18],[15.4,4,22],'win_e')
    s.glow('engine',[-8,-4.5,62],[8,4.5,68],'glow_c'); return s
def flagship(M,tag):
    s=Ship(M,tag); c=s.cube
    c([-18,-12,-110],[18,12,-50],'hull_e'); c([-26,-16,-50],[26,16,30],'hull_e'); c([-22,-14,30],[22,14,100],'hull_e2'); c([-10,-7,-128],[10,7,-110],'e_g'); c([-4,-3,-140],[4,3,-128],'e_or')
    c([-14,16,-20],[14,30,30],'e_w',north='win_e',east='win_e',west='win_e',south='win_e'); c([-9,30,-8],[9,40,20],'e_g',north='win_e'); c([-5,40,0],[5,46,12],'e_w'); c([-0.8,46,5],[0.8,64,6.6],'e_d'); c([-6,58,4],[6,59.4,8],'e_d')
    c([26,-6,-70],[40,6,60],'hull_e2'); c([-40,-6,-70],[-26,6,60],'hull_e2'); c([40,-2,-40],[62,2,40],'e_w'); c([-62,-2,-40],[-40,2,40],'e_w'); c([60,-5,-46],[66,5,46],'e_or'); c([-66,-5,-46],[-60,5,46],'e_or')
    for z in (-90,-66,48,74):
        c([-6,12 if z<0 else 14,z-6],[6,18 if z<0 else 20,z+6],'e_d'); c([-1.5,15 if z<0 else 17,z-20],[1.5,17.4 if z<0 else 19.4,z-6],'e_g')
    c([-26.3,3,-44],[26.3,6,24],'win_e'); c([-26.3,-8,-44],[26.3,-5,24],'win_e'); c([-8,-22,-30],[8,-16,20],'e_d'); c([-26.4,-16.4,36],[26.4,-12,42],'e_or'); c([-18,-10,100],[18,10,112],'e_d')
    c([-36,-4,70],[-24,4,104],'e_d'); c([24,-4,70],[36,4,104],'e_d')
    s.glow('engine',[-14,-7,112],[14,7,122],'glow_c'); s.glow('engine2',[-34,-3,104],[-26,3,112],'glow_c'); s.glow('engine3',[26,-3,104],[34,3,112],'glow_c'); return s
def station(M,tag,R=120):
    s=Ship(M,tag); c=s.cube; n=14
    c([-22,-30,-22],[22,30,22],'hull_e'); c([-14,30,-14],[14,52,14],'e_w',north='win_e',east='win_e',west='win_e',south='win_e'); c([-1,52,-1],[1,84,1],'e_d'); c([-10,-50,-10],[10,-30,10],'e_d'); c([-18,-58,-18],[18,-50,18],'e_blue')
    for i in range(n):
        a=i/n*6.283; x=R*math.cos(a); z=R*math.sin(a); w=30
        c([x-w,-9,z-w],[x+w,9,z+w],'hull_e' if i%2 else 'hull_e2',north='win_e',south='win_e',east='win_e',west='win_e')
    for i in range(4):
        a=i/4*6.283+0.39; x1=R*0.86*math.cos(a); z1=R*0.86*math.sin(a)
        c([min(0,x1)-4 if abs(x1)>abs(z1) else x1/2-5,-4,min(0,z1)-4 if abs(z1)>=abs(x1) else z1/2-5],[max(0,x1)+4 if abs(x1)>abs(z1) else x1/2+5,4,max(0,z1)+4 if abs(z1)>=abs(x1) else z1/2+5],'e_g')
    for sx in (-1,1):
        c([sx*(R+30)-1,-2,-3],[sx*(R+60)+1,2,3],'e_d'); c([min(sx*(R+60),sx*(R+150)),-1,-40],[max(sx*(R+60),sx*(R+150)),1,40],'solar',up='solar',down='solar')
    c([-30,84,-30],[30,88,30],'e_g'); s.glow('beacon',[-3,88,-3],[3,94,3],'e_red'); return s
def mothership(M,tag,cell=130,nx=13,ny=5,nz=7):
    """초대형 외계 모함: 납작한 타원 덩어리(칸마다 조각) + 앞면 한가운데 빛나는 세로 틈(아가리) + 위아래로 솟은 가시들. 중심 = 원점, 앞 = -z"""
    s=Ship(M,tag); r=random.Random(7); cx,cy,cz=(nx-1)/2,(ny-1)/2,(nz-1)/2; tex=['hull_a','hull_a2','hull_a3']
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                u=(i-cx)/(nx/2); v=(j-cy)/(ny/2); w=(k-cz)/(nz/2)
                if u*u+v*v*0.9+w*w>1.02: continue
                x0=(i-nx/2)*cell; y0=(j-ny/2)*cell; z0=(k-nz/2)*cell
                if i==int(cx) and k<=1 and 1<=j<=ny-2: s.cube([x0+cell*0.2,y0,z0+cell*0.6],[x0+cell*0.8,y0+cell,z0+cell],'maw'); continue       # 아가리: 안쪽으로 들어간 빛
                g=r.uniform(-10,10); t=tex[(i*3+j*5+k*7)%3]; s.cube([x0,y0,z0+ (g if k==0 else 0)],[x0+cell,y0+cell,z0+cell],t)
    H=ny/2*cell
    for i,(x,z,h,w) in enumerate([(-520,-60,260,34),(-300,120,380,44),(-80,-140,200,30),(140,60,460,50),(380,-80,300,38),(600,100,220,30),(-640,160,180,26),(260,-240,160,24)]):
        hh=H*math.sqrt(max(0.05,1-(x/(nx/2*cell))**2-(z/(nz/2*cell))**2))
        s.cube([x-w,hh-20,z-w],[x+w,hh+h,z+w],'hull_a3'); s.cube([x-w*0.4,hh+h,z-w*0.4],[x+w*0.4,hh+h+60,z+w*0.4],'a_p'); s.cube([x+60-w*0.7,-hh-h*0.6,z+40-w*0.7],[x+60+w*0.7,-hh+20,z+40+w*0.7],'hull_a2')
    for sx in (-1,1):           # 옆으로 뻗은 날개 발톱
        s.cube([min(sx*820,sx*1040),-30,-200],[max(sx*820,sx*1040),30,160],'hull_a'); s.cube([min(sx*1000,sx*1060),-60,-420],[max(sx*1000,sx*1060),60,-180],'hull_a3'); s.cube([min(sx*1020,sx*1040),-10,-520],[max(sx*1020,sx*1040),10,-420],'a_m')
    s.glow('mawglow',[-22,-170,-nz/2*cell+70],[22,170,-nz/2*cell+82],'a_mc'); return s      # 틈 안쪽 깊숙이 (전투기가 지나갈 수 있게)

def skybox(M,R=9000):
    """별 벽 여섯 장 (안쪽을 보는 얇은 판). 카메라가 어디를 봐도 별이 보임"""
    t=10; k=[]; T=['stars1','stars2','stars3']
    k+= [M.cube('sky',[-R,-R,R],[R,R,R+t],'black',north=T[1]), M.cube('sky',[-R,-R,-R-t],[R,R,-R],'black',south=T[0]), M.cube('sky',[R,-R,-R],[R+t,R,R],'black',west=T[2]),
         M.cube('sky',[-R-t,-R,-R],[-R,R,R],'black',east=T[0]), M.cube('sky',[-R,R,-R],[R,R+t,R],'black',down=T[2]), M.cube('sky',[-R,-R-t,-R],[R,-R,R],'black',up=T[1])]
    return k
def globe(M,name,c,R,cols,step=None,seed=1,ymin=None,spots=26):
    """블록 공: 얇은 판을 원 모양으로 쌓고 얼룩(땅·구름)을 붙임. ymin(중심에서 잰 높이)을 주면 그 위쪽만 만듦 — 아주 큰 행성의 보이는 윗부분만"""
    r=random.Random(seed); cx,cy,cz=c; step=step or R/11; k=[]; y=-R if ymin is None else ymin; i=0
    while y<R-1e-6:
        ym=y+step/2; w=math.sqrt(max(0,R*R-ym*ym)); col=cols[0] if (i//2)%2 else cols[1]
        k.append(M.cube(name,[cx-w,cy+y,cz-w*0.72],[cx+w,cy+y+step,cz+w*0.72],col)); k.append(M.cube(name,[cx-w*0.72,cy+y,cz-w],[cx+w*0.72,cy+y+step,cz+w],col)); y+=step; i+=1
    lo=-R*0.7 if ymin is None else ymin+step
    for j in range(spots if len(cols)>2 else 8):
        yy=r.uniform(lo,R*(0.7 if ymin is None else 0.985)); w=math.sqrt(R*R-yy*yy); a=r.uniform(0,6.283); s=R*r.uniform(0.05,0.14); col=cols[2+j%(len(cols)-2)] if len(cols)>2 else cols[1]
        d=w*(0.86 if ymin is None else r.uniform(0.2,0.9)); px=cx+d*math.cos(a); pz=cz+d*math.sin(a); top=cy+math.sqrt(max(0,R*R-d*d)) if ymin is not None else cy+yy+s*0.45
        k.append(M.cube(name+'_s',[px-s,(top-s*0.5) if ymin is not None else cy+yy-s*0.45,pz-s*0.8],[px+s,top+ (6 if ymin is not None else 0),pz+s*0.8],col))
    return k
EARTH=('sea','sea2','land','land2','cloud','land','ice','cloud'); MOON=('moon','moon_d')

def planet_cap(M,name,c,R,h,step=40,seed=1,patches=70):
    """아주 큰 행성의 윗부분만 (둥근 지평선이 보이게): 얇은 원판을 잘게 쌓고, 그 위에 납작한 땅·구름 조각을 얹음. c=중심, h=만드는 두께"""
    r=random.Random(seed); cx,cy,cz=c; k=[]; y=R-h; i=0
    while y<R-1e-6:
        ym=y+step/2; w=math.sqrt(max(0,R*R-ym*ym)); col='sea' if i%2 else 'sea2'
        k.append(M.cube(name,[cx-w,cy+y,cz-w*0.72],[cx+w,cy+y+step,cz+w*0.72],col)); k.append(M.cube(name,[cx-w*0.72,cy+y,cz-w],[cx+w*0.72,cy+y+step,cz+w],col)); y+=step; i+=1
    dmax=math.sqrt(R*R-(R-h)**2)*0.92
    for j in range(patches):
        a=r.uniform(0,6.283); d=dmax*math.sqrt(r.random()); px=cx+d*math.cos(a); pz=cz+d*math.sin(a); top=cy+math.sqrt(R*R-d*d); cloud=(j%4==0)
        sx=r.uniform(120,460)*(1.5 if cloud else 1); sz=r.uniform(90,320); col='cloud' if cloud else r.choice(['land','land','land2'])
        k.append(M.cube(name+'_p',[px-sx,top-step*1.6,pz-sz],[px+sx,top+(26 if cloud else 6)+r.uniform(0,6),pz+sz],col))
        if not cloud and r.random()<0.6: k.append(M.cube(name+'_p',[px-sx*0.5+r.uniform(-90,90),top-step*1.6,pz-sz*1.5],[px+sx*0.7,top+9+r.uniform(0,5),pz+sz*0.4],r.choice(['land','land2'])))
    return k
def burst(M,A,box,t,pos,n=10,speed=60,size=6,dur=1.1,cols=('fire1','fire2','fire3'),seed=0,bias=(0,0,0)):
    """불꽃 파편: 작은 상자들이 사방으로 튀며 사라짐 (box = 붙일 묶음의 children 목록 또는 top)"""
    r=random.Random(seed*31+int(t*10)); x,y,z=pos
    for i in range(n):
        s=size*r.uniform(0.5,1.4); g=M.group(f'bu{len(M.els)}',[x,y,z],[M.cube('bu',[x-s,y-s,z-s],[x+s,y+s,z+s],cols[i%len(cols)])]); box.append(g)
        d=[r.gauss(0,1)+bias[0],r.gauss(0,1)+bias[1],r.gauss(0,1)+bias[2]]; m=math.sqrt(sum(v*v for v in d)) or 1; f=speed*r.uniform(0.4,1.3)/m
        A.add(g,'position',[(0,(0,0,0)),(t,(0,0,0)),(t+dur*0.35,(-d[0]*f*0.6,d[1]*f*0.6,d[2]*f*0.6)),(t+dur,(-d[0]*f,d[1]*f,d[2]*f))],'catmullrom')
        A.add(g,'rotation',[(t,(0,0,0)),(t+dur,(r.uniform(-300,300),r.uniform(-300,300),0))])
        A.add(g,'scale',[(0,(0,0,0)),(max(0,t-0.02),(0,0,0)),(t,(0.4,)*3),(t+dur*0.25,(1.3,)*3),(t+dur,(0.05,)*3),(t+dur+0.02,(0,0,0))])
