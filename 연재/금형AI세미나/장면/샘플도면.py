"""샘플 부품 도면 3장(버링 펀치·버링 다이·펀치 판) → PNG + 한 묶음 PDF
세미나 영상용으로 직접 만든 예시 도면 (고객 도면 아님)"""
import math, os, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages
FONT='/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
fm.fontManager.addfont(FONT); fm.fontManager.addfont('/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf')
plt.rcParams['font.family']='NanumGothic'
OUT=os.path.dirname(os.path.abspath(__file__))

# ---- 펀치 반쪽 단면 (r, z) : z=0 끝, 위로 ----
def arc(cx,cy,R,a0,a1,n=16):
    return [(cx+R*math.cos(math.radians(a0+(a1-a0)*i/n)),cy+R*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)]
PUNCH=[(0,0),(8,0)]+arc(8,7,7,-90,0)[1:]+[(15,54),(18,54),(18,59.5),(17.5,60),(0,60)]
DIE=[(15.6,0),(24,0),(24,30),(16.6,30),(15.6,29)]          # 다이: 바깥 Ø48, 구멍 Ø31.2, 높이 30, 입구 R1 대신 모따기 1
def mirror(p): return [(-r,z) for r,z in reversed(p)]

C='#1a1a1a'; DIM='#1f4fbf'; CEN='#c03030'
def frame(fig, title, no, mat, hrc, qty):
    ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,420); ax.set_ylim(0,297); ax.axis('off')
    ax.add_patch(plt.Rectangle((10,10),400,277,fill=False,lw=1.6,color=C))
    # 표제란
    x0,y0,w,h=250,10,160,48
    ax.add_patch(plt.Rectangle((x0,y0),w,h,fill=False,lw=1.3,color=C))
    rows=[('품명',title),('도면 번호',no),('재질',mat),('경도·처리',hrc),('수량 / 척도',f'{qty} EA  /  1:1')]
    for i,(k,v) in enumerate(rows):
        y=y0+h-(i+1)*h/5
        ax.plot([x0,x0+w],[y,y],color=C,lw=.6)
        ax.text(x0+3,y+3.2,k,fontsize=9,color='#444'); ax.text(x0+42,y+2.6,v,fontsize=11,weight='bold',color=C)
    ax.plot([x0+38,x0+38],[y0,y0+h],color=C,lw=.6)
    ax.text(x0+w,y0+h+3,'AI 금형 세미나 · 샘플 도면 · 2026-11',fontsize=8,ha='right',color='#555')
    ax.text(20,272,'일반 공차 KS B 0412 보통급 · 표시 없는 모서리 C0.3',fontsize=8.5,color='#555')
    return ax
def hdim(ax,x1,x2,y,yref,txt,ext=True):
    ax.annotate('',(x1,y),(x2,y),arrowprops=dict(arrowstyle='<|-|>',color=DIM,lw=.9,mutation_scale=8))
    if ext:
        for x in (x1,x2): ax.plot([x,x],[yref,y+(1.5 if y>yref else -1.5)],color=DIM,lw=.5)
    ax.text((x1+x2)/2,y+1.2,txt,ha='center',va='bottom',fontsize=10,color=DIM)
def vdim(ax,x,y1,y2,xref,txt):
    ax.annotate('',(x,y1),(x,y2),arrowprops=dict(arrowstyle='<|-|>',color=DIM,lw=.9,mutation_scale=8))
    for y in (y1,y2): ax.plot([xref,x+(1.5 if x>xref else -1.5)],[y,y],color=DIM,lw=.5)
    ax.text(x+1.5 if x>xref else x-1.5,(y1+y2)/2,txt,rotation=90,ha='left' if x>xref else 'right',va='center',fontsize=10,color=DIM)
def outline(ax,half,ox,oy,s,hatch=False):
    full=half+mirror(half)
    xs=[ox+r*s for r,z in full]+[ox+full[0][0]*s]; ys=[oy+z*s for r,z in full]+[oy+full[0][1]*s]
    ax.fill(xs,ys,color='#eef3fb'); ax.plot(xs,ys,color=C,lw=1.8)
def centerline(ax,x,y1,y2): ax.plot([x,x],[y1,y2],color=CEN,lw=.8,dashes=(12,3,2,3))

def punch_page():
    fig=plt.figure(figsize=(16.54,11.69)); ax=frame(fig,'버링 펀치 Ø30','SMP-P-001','SKD11','HRC 60~62',1)
    s=2.6; ox,oy=120,60
    outline(ax,PUNCH,ox,oy,s); centerline(ax,ox,oy-12,oy+60*s+12)
    for z in (7,54): ax.plot([ox-15*s if z==7 else ox-18*s,ox+(15 if z==7 else 18)*s],[oy+z*s]*2,color=C,lw=.8)
    hdim(ax,ox-15*s,ox+15*s,oy+30*s,oy+30*s,'Ø30 h6 (-0.013)',ext=False)
    hdim(ax,ox-18*s,ox+18*s,oy+60*s+10,oy+60*s,'Ø36')
    hdim(ax,ox-8*s,ox+8*s,oy-10,oy,'Ø16')
    vdim(ax,ox+18*s+18,oy,oy+60*s,ox+18*s,'60')
    vdim(ax,ox+18*s+8,oy+54*s,oy+60*s,ox+18*s,'6')
    vdim(ax,ox-18*s-10,oy,oy+7*s,ox-15*s,'7')
    ax.annotate('R7 (선단)',(ox+12.5*s,oy+2.2*s),(ox+26*s,oy-6),fontsize=10,color=DIM,arrowprops=dict(arrowstyle='-|>',color=DIM,lw=.8))
    ax.annotate('고정용 턱',(ox-17*s,oy+57*s),(ox-40*s,oy+66*s),fontsize=10,color=DIM,arrowprops=dict(arrowstyle='-|>',color=DIM,lw=.8))
    ax.text(ox,oy+60*s+26,'정면도',ha='center',fontsize=12,weight='bold')
    # 평면도 (위에서 본 원)
    cx,cy=320,190
    for r,lw in ((18,1.8),(15,1.0)): ax.add_patch(plt.Circle((cx,cy),r*s*.9,fill=False,color=C,lw=lw))
    ax.plot([cx-60,cx+60],[cy,cy],color=CEN,lw=.8,dashes=(12,3,2,3)); ax.plot([cx,cx],[cy-60,cy+60],color=CEN,lw=.8,dashes=(12,3,2,3))
    ax.text(cx,cy+58,'평면도',ha='center',fontsize=12,weight='bold')
    ax.text(20,262,'버링(구멍 가장자리 세우기)용 상형 펀치 · 펀치-다이 틈 한쪽 = 판 두께 0.6',fontsize=10)
    return fig
def die_page():
    fig=plt.figure(figsize=(16.54,11.69)); ax=frame(fig,'버링 다이 Ø31.2','SMP-D-001','SKD11','HRC 60~62',1)
    s=3.0; ox,oy=130,80
    for sign in (1,-1):
        pts=[(ox+sign*r*s,oy+z*s) for r,z in DIE]+[(ox+sign*DIE[0][0]*s,oy+DIE[0][1]*s)]
        ax.fill(*zip(*pts),color='#eef7ee',hatch='///',edgecolor='#7a7a7a',lw=0); ax.plot(*zip(*pts),color=C,lw=1.8)
    centerline(ax,ox,oy-12,oy+30*s+14)
    hdim(ax,ox-24*s,ox+24*s,oy-12,oy,'Ø48')
    hdim(ax,ox-15.6*s,ox+15.6*s,oy+30*s+10,oy+30*s,'Ø31.2 H7')
    vdim(ax,ox+24*s+14,oy,oy+30*s,ox+24*s,'30')
    ax.annotate('C1 (입구)',(ox+16.1*s,oy+29.5*s),(ox+30*s,oy+40*s),fontsize=10,color=DIM,arrowprops=dict(arrowstyle='-|>',color=DIM,lw=.8))
    ax.text(ox,oy+30*s+28,'단면도',ha='center',fontsize=12,weight='bold')
    cx,cy=330,190
    ax.add_patch(plt.Circle((cx,cy),24*2.2,fill=False,color=C,lw=1.8)); ax.add_patch(plt.Circle((cx,cy),15.6*2.2,fill=False,color=C,lw=1.2))
    ax.text(cx,cy+60,'평면도',ha='center',fontsize=12,weight='bold')
    return fig
HOLES=[(-60,0,15.5),(0,0,18.5),(60,0,15.5),(-85,-35,4.25),(85,-35,4.25),(-85,35,4.25),(85,35,4.25)]
def plate_page():
    fig=plt.figure(figsize=(16.54,11.69)); ax=frame(fig,'펀치 고정판','SMP-B-001','SS400 → S50C','-',1)
    s=1.15; ox,oy=150,150
    ax.add_patch(plt.Rectangle((ox-110*s,oy-50*s),220*s,100*s,fill=True,fc='#f3f0ea',ec=C,lw=1.8))
    for x,y,r in HOLES: ax.add_patch(plt.Circle((ox+x*s,oy+y*s),r*s,fill=False,color=C,lw=1.3))
    hdim(ax,ox-110*s,ox+110*s,oy+50*s+12,oy+50*s,'220')
    vdim(ax,ox+110*s+12,oy-50*s,oy+50*s,ox+110*s,'100')
    hdim(ax,ox-60*s,ox+60*s,oy-50*s-14,oy,'120 (구멍 간격 60 × 2)')
    ax.text(ox,oy-50*s-34,'펀치 구멍 Ø31 / Ø37 · 볼트 4-M8 · 두께 20',ha='center',fontsize=10)
    ax.text(ox,oy+50*s+30,'평면도',ha='center',fontsize=12,weight='bold')
    return fig
if __name__=='__main__':
    pages=[('도면_1_버링펀치',punch_page),('도면_2_버링다이',die_page),('도면_3_펀치고정판',plate_page)]
    with PdfPages(os.path.join(OUT,'샘플_부품도면.pdf')) as pdf:
        for name,fn in pages:
            fig=fn(); fig.savefig(os.path.join(OUT,name+'.png'),dpi=120,facecolor='white'); pdf.savefig(fig); plt.close(fig)
    print('OK')
