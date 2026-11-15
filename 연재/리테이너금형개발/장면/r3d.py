"""리테이너 영상 전용 부품: 제품 · 스트립 · 펀치 불러오기 · 흐름 칩"""
from g3d import *
INFO=json.load(open(os.path.join(DIE,'die_detail_parts.json'),encoding='utf-8'))
SX=INFO['station_x']; PITCH=84.0
AI=os.path.join(HERE,'자료')
def product(loc=(0,0,0),name='product',rgb=None):
    o=stl(os.path.join(PART,'product.stl'),rgb or COL['sheet'],name); o.location=loc; return o
def part(n,rgb,parent=None,dx=0.0,dz=0.0):
    """die_set 부품 STL 하나 (dx, dz 만큼 옮김)"""
    o=stl(os.path.join(DIE,n+'.stl'),rgb,n)
    if parent: o.parent=parent
    o.location=(dx,0,dz); return o
def strip_row(parent=None):
    """스트립 + 공정별 판재 (금형 좌표 그대로)"""
    out=[]
    for f in sorted(glob.glob(os.path.join(DIE,'*.stl'))):
        n=os.path.basename(f)[:-4]
        if n=='strip' or n.startswith('strip_'):
            out.append(part(n,COL['sheet'],parent))
    return out
def chips(names,loc,dx,size=22,col=COL['accent'],t0=0,dt=0.35,w=None,h=60,face=None):
    gs=[]
    for i,nm in enumerate(names):
        g=card(nm,'',(loc[0]+i*dx,loc[1],loc[2]),col,w=w or dx*0.88,h=h,tsize=size,face=face)
        keyv(g,'scale',[(0,(0,0,0)),(t0+i*dt,(0,0,0)),(t0+i*dt+0.2,(1.08,1.08,1.08)),(t0+i*dt+0.3,(1,1,1))]); gs.append(g)
    return gs
def pop(o,t_in,t_out=None,s=1.0):
    keys=[(0,(0,0,0)),(max(0,t_in-0.01),(0,0,0)),(t_in+0.22,(s*1.08,)*3),(t_in+0.32,(s,)*3)]
    if t_out is not None: keys+=[(t_out,(s,)*3),(t_out+0.25,(0,0,0))]
    keyv(o,'scale',keys); return o
def ring(ri,ro,t,loc=(0,0,0),rgb=COL['sheet'],name='ring',seg=128):
    return revolve([(ri,0),(ro,0),(ro,t),(ri,t)],name,seg=seg,rgb=rgb,loc=loc,closed=True)
def circle_line(R,loc,rgb=COL['accent'],bevel=0.3,n=96,name='cl'):
    return curve_line([(loc[0]+R*math.cos(2*math.pi*i/n),loc[1]+R*math.sin(2*math.pi*i/n),loc[2]) for i in range(n)],bevel,rgb,name,closed=True)
def burr_xy(R=32.5,n=14):
    return [(R*math.cos(2*math.pi*k/n),R*math.sin(2*math.pi*k/n)) for k in range(n)]
