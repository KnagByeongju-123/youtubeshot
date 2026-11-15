"""영상용 2D 자료: 가정 고객 도면 · 성형해석 장면(버링 · 리스트라이크) 잘라 내기 · 얇아짐 확대"""
import os, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image
H=os.path.dirname(os.path.abspath(__file__)); O=os.path.join(H,'자료')
FEM='/home/user/mold_sold/parts/TEST_RETAINER_SPCC/burr_cell/reverse/iter2_d5.646'
fp=fm.FontProperties(fname='/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf')
plt.rcParams['font.family']=fp.get_name(); fm.fontManager.addfont('/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf')
# 1) 가정 고객 도면 (요청 그대로: ID50 · OD60 · 버링 14 · 높이 4, 버링 지름 미지정)
fig=plt.figure(figsize=(16,9),dpi=120); fig.patch.set_facecolor('white')
ax=fig.add_axes([0.03,0.12,0.5,0.82]); ax.set_aspect('equal'); ax.axis('off')
th=[i*2*math.pi/200 for i in range(201)]
for R in (25,30): ax.plot([R*math.cos(a) for a in th],[R*math.sin(a) for a in th],'k',lw=2)
for k in range(14):
    a=2*math.pi*k/14; cx,cy=27.5*math.cos(a),27.5*math.sin(a)
    ax.plot([cx+1.6*math.cos(b) for b in th],[cy+1.6*math.sin(b) for b in th],'k',lw=1.2)
ax.plot([-34,34],[0,0],'k-.',lw=0.6); ax.plot([0,0],[-34,34],'k-.',lw=0.6)
ax.annotate('',xy=(-25,-36),xytext=(25,-36),arrowprops=dict(arrowstyle='<->',lw=1.2)); ax.text(0,-38.5,'Ø50',ha='center',va='top',fontsize=20)
ax.annotate('',xy=(-30,36),xytext=(30,36),arrowprops=dict(arrowstyle='<->',lw=1.2)); ax.text(0,38.5,'Ø60 (정도)',ha='center',va='bottom',fontsize=20)
ax.text(31,22,'버링 14개 같은 간격',fontsize=18,color='#c0392b'); ax.set_xlim(-42,62); ax.set_ylim(-44,44)
bx=fig.add_axes([0.56,0.45,0.41,0.45]); bx.axis('off'); bx.set_xlim(0,10); bx.set_ylim(0,6)
bx.add_patch(plt.Rectangle((0.6,3.0),8.8,0.5,color='0.75')); bx.add_patch(plt.Rectangle((4.6,1.2),0.35,1.8,color='0.75')); bx.add_patch(plt.Rectangle((5.45,1.2),0.35,1.8,color='0.75'))
bx.annotate('',xy=(9.7,3.5),xytext=(9.7,1.2),arrowprops=dict(arrowstyle='<->')); bx.text(9.8,2.3,'H 4',fontsize=20,va='center')
bx.text(5.2,0.7,'버링 안지름 · 바깥지름 : ?',fontsize=19,ha='center',color='#c0392b'); bx.text(5,5.3,'단면 (버링 = 스프링 코킹부)',fontsize=19,ha='center')
cx=fig.add_axes([0.56,0.08,0.41,0.3]); cx.axis('off'); cx.set_xlim(0,10); cx.set_ylim(0,4)
cx.add_patch(plt.Rectangle((0,0),10,4,fill=False,lw=2))
for y in (1,2,3): cx.plot([0,10],[y,y],'k',lw=0.8)
cx.plot([3,3],[0,4],'k',lw=0.8)
for i,(a,b) in enumerate((('품명','리테이너'),('재질','SPCC  t1.4'),('수량','버링 14'),('비고','가정 도면 (교육용)'))):
    cx.text(1.5,3.5-i,a,ha='center',va='center',fontsize=18); cx.text(6.5,3.5-i,b,ha='center',va='center',fontsize=18)
fig.savefig(os.path.join(O,'고객도면.png')); plt.close(fig)
# 2) 성형해석 장면: GIF 프레임에서 버링 주변(r 0~17 mm)만 잘라 크게
for nm,fr in (('S2_burring',(0,4,8,12,16,22)),('S3_restrike',(13,))):
    im=Image.open(os.path.join(FEM,nm+'.gif'))
    for k in fr:
        im.seek(min(k,im.n_frames-1)); c=im.convert('RGB').crop((268,30,500,325)).resize((696,885),Image.LANCZOS)
        c.save(os.path.join(O,'%s_%02d.png'%(nm,k)))
s=Image.open(os.path.join(FEM,'S2_burring_summary.png')).convert('RGB')
s.crop((205,400,752,765)).save(os.path.join(O,'얇아짐_확대.png'))
s.crop((80,805,880,1195)).save(os.path.join(O,'얇아짐_그래프.png'))
print(sorted(os.listdir(O)))
