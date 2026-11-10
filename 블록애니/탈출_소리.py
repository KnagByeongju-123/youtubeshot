"""대사 없는 블록 애니의 소리: 음악(직접 합성) + 효과음(시간표.json 의 cues) → wav
사용: python 탈출_소리.py <시간표.json> <결과.wav> [--시작 초 --끝 초]   (쇼츠용으로 한 구간만 뽑을 수 있음)
  음악: 처음(고요한 패드) → 경보 뒤 추격(낮은 박동 + 긴장 음) → 지상(따뜻한 화음 + 오르골 가락).  모두 numpy 로 직접 만든 소리"""
import json, sys, wave
import numpy as np
SR=44100
class P(np.ndarray):
    """길이가 다른 소리를 더하면 짧은 쪽 뒤를 0 으로 채움"""
    def __add__(self,o):
        if isinstance(o,np.ndarray) and o.ndim==1 and len(o)!=len(self):
            n=max(len(self),len(o)); a=np.zeros(n); a[:len(self)]=self; a[:len(o)]+=o; return a.view(P)
        return np.add(np.asarray(self),np.asarray(o)).view(P)
    __radd__=__add__
def env(n,a=0.01,r=0.3):
    e=np.ones(n); na=max(1,int(a*SR)); nr=max(1,min(n-1,int(r*SR))); e[:na]=np.linspace(0,1,na); e[-nr:]*=np.linspace(1,0,nr); return e
def tone(f,d,a=0.01,r=0.2,shape='sin',f1=None):
    n=int(d*SR); t=np.arange(n)/SR; fr=np.linspace(f,f1 if f1 else f,n); ph=2*np.pi*np.cumsum(fr)/SR
    w=np.sin(ph) if shape=='sin' else (np.sign(np.sin(ph))*0.5 if shape=='sq' else 2*(ph/(2*np.pi)%1)-1)
    return (w*env(n,a,r)).view(P)
def noise(d,lo=200,hi=4000,a=0.005,r=0.2,seed=0):
    n=int(d*SR); x=np.random.default_rng(seed).standard_normal(n); X=np.fft.rfft(x); f=np.fft.rfftfreq(n,1/SR); X[(f<lo)|(f>hi)]=0
    y=np.fft.irfft(X,n); y/=np.abs(y).max()+1e-9; return (y*env(n,a,r)).view(P)
def cat(*xs):
    return np.concatenate(xs)
def rep(x,k,gap):
    g=np.zeros(int(gap*SR)); return np.concatenate([np.concatenate([x,g]) for _ in range(k)])
def sfx(kind,i=0):
    K=kind
    if K=='glass': return 0.8*noise(0.5,3000,12000,r=0.4,seed=i)+0.4*tone(2600,0.3,r=0.25)+0.3*tone(3900,0.25,r=0.2)
    if K=='alarm': return 0.35*rep(cat(tone(880,0.28,shape='sq',r=0.03),tone(660,0.28,shape='sq',r=0.03)),5,0.02)
    if K=='blink' or K=='beep': return 0.4*rep(tone(1500,0.07,r=0.04),3,0.09)
    if K=='ok': return 0.4*cat(tone(1046,0.1,r=0.05),tone(1568,0.25,r=0.2))
    if K in('run','patter'): return 0.5*rep(noise(0.05,150,900,r=0.04,seed=i),10 if K=='run' else 14,0.13 if K=='run' else 0.07)
    if K=='tiptoe': return 0.25*rep(noise(0.04,300,1500,r=0.03,seed=i),8,0.5)
    if K=='stomp' or K=='thud': return 0.9*tone(70,0.3,r=0.25,f1=40)+0.4*noise(0.12,60,400,r=0.1,seed=i)
    if K=='door': return 0.5*noise(0.9,300,2500,a=0.2,r=0.3,seed=i)+0.2*tone(180,0.9,a=0.2,r=0.3,f1=120)
    if K=='creak': return 0.4*tone(300,1.2,a=0.1,r=0.3,shape='saw',f1=520)*(0.6+0.4*np.sin(np.arange(int(1.2*SR))/SR*2*np.pi*11))
    if K in('whoosh','slide','jump'): return 0.5*noise(0.5 if K!='jump' else 0.3,400,6000,a=0.15,r=0.25,seed=i)
    if K=='elevator': return 0.4*tone(55,6,a=1,r=1.5,shape='saw')+0.2*noise(6,100,700,a=1,r=1.5,seed=i)
    if K in('clang','slam','hit','crunch','crash'): 
        d={'clang':0.7,'slam':0.9,'hit':0.35,'crunch':0.5,'crash':0.9}[K]
        return 0.9*noise(d,80,3500,r=d*0.8,seed=i)+0.5*tone(180 if K!='slam' else 60,d,r=d*0.8)+0.3*tone(733,d*0.6,r=d*0.5)
    if K=='climb' or K=='drag': return 0.3*rep(noise(0.12,200,1800,a=0.02,r=0.08,seed=i),10,0.5)
    if K=='snap': return 0.8*noise(0.08,1500,9000,r=0.06,seed=i)+0.5*tone(1200,0.15,r=0.12,f1=300)
    if K=='zap' or K=='spark': return 0.6*noise(0.35,2000,12000,r=0.2,seed=i)*(np.random.default_rng(i).random(int(0.35*SR))>0.4)+0.3*tone(90,0.35,shape='sq',r=0.2)
    if K=='steam' or K=='fan': return 0.5*noise(4 if K=='steam' else 5,1500 if K=='steam' else 100,9000 if K=='steam' else 1500,a=0.2,r=2,seed=i)
    if K=='rumble': return 0.7*noise(3.5,30,220,a=0.6,r=1.2,seed=i)+0.4*tone(45,3.5,a=0.6,r=1.2)
    if K in('burst','water','wade','plop'):
        d={'burst':1.2,'water':6,'wade':5,'plop':0.25}[K]; return (0.5 if K!='water' else 0.3)*noise(d,300,5000,a=0.05 if K!='water' else 1,r=d*0.5,seed=i)
    if K=='drone': return 0.3*tone(210,2.5,a=0.3,r=0.8,shape='saw')*(0.6+0.4*np.sin(np.arange(int(2.5*SR))/SR*2*np.pi*38))
    if K=='lever': return 0.7*noise(0.12,400,3000,r=0.1,seed=i)+0.5*tone(220,0.2,r=0.15,f1=110)
    if K=='powerdown': return 0.5*tone(520,1.6,r=0.8,f1=60)
    if K=='powerup': return 0.5*tone(120,1.2,a=0.3,r=0.3,f1=880)+np.pad(0.3*tone(1320,0.5,r=0.4),(int(0.7*SR),0))
    if K=='attach': return 0.5*noise(0.06,800,5000,r=0.05,seed=i)+0.4*tone(660,0.18,r=0.15)
    if K=='birds':
        r=np.random.default_rng(i); out=np.zeros(int(6*SR))
        for k in range(14):
            t0=int(r.uniform(0,5.5)*SR); c=0.25*tone(r.uniform(2400,3600),0.12,r=0.08,f1=r.uniform(3000,4400)); out[t0:t0+len(c)]+=c[:len(out)-t0]
        return out
    return 0.3*noise(0.2,300,3000,seed=i)
def put(buf,x,t,vol=1.0):
    x=np.asarray(x)
    i=int(t*SR)
    if i>=len(buf) or i+len(x)<=0: return
    a=max(0,-i); x=x[a:]; i=max(0,i); n=min(len(x),len(buf)-i); buf[i:i+n]+=x[:n]*vol
def pad_chord(freqs,d,vol=0.12,trem=0.15):
    n=int(d*SR); t=np.arange(n)/SR; y=sum(np.sin(2*np.pi*f*t)+0.4*np.sin(2*np.pi*f*2.003*t)+0.2*np.sin(2*np.pi*f*0.5*t) for f in freqs)/len(freqs)
    return vol*y*(1-trem+trem*np.sin(2*np.pi*0.2*t))*env(n,min(2,d/3),min(2,d/3))
def music(L,calm_end=36.0,ground=315.0):
    m=np.zeros(int(L*SR)); N=lambda s: 440*2**((s-9)/12)        # 0 = 가온 다
    # 1) 처음: 고요한 패드 (가단조)
    put(m,pad_chord([N(-15),N(-8),N(0),N(4)],calm_end+1,0.10),0)
    for k,s in enumerate([12,16,19,16,12,7,9,12]): put(m,0.07*tone(N(s),1.6,a=0.02,r=1.4),4+k*4)
    # 2) 추격: 낮은 박동(1초 2.4번 → 뒤로 갈수록 빠르게) + 긴장 음 + 오르는 음
    t=calm_end; k=0
    while t<ground-1:
        bpm=132+ (t-calm_end)/(ground-calm_end)*36; step=60/bpm/2
        put(m,0.5*tone(55 if k%8 else 41,0.16,r=0.13,f1=38),t)                       # 쿵
        if k%2==1: put(m,0.10*noise(0.04,5000,11000,r=0.03,seed=k),t)               # 칙
        if k%4==0: put(m,0.10*tone(N([-12,-12,-9,-7][(k//16)%4]),step*3.6,a=0.01,r=0.1,shape='saw'),t)
        if k%16==12: put(m,0.07*tone(N([7,8,10,12][(k//16)%4]),step*3,r=0.2,shape='sq'),t)
        t+=step; k+=1
    put(m,pad_chord([N(-12),N(-5),N(3)],ground-calm_end,0.06,0.3),calm_end)
    # 3) 지상: 따뜻한 화음(다장조) + 오르골 가락
    ch=[[N(-12),N(-5),N(0),N(4)],[N(-15),N(-8),N(0),N(4)],[N(-19),N(-7),N(-3),N(5)],[N(-17),N(-5),N(-1),N(2)]]
    t=ground; k=0
    while t<L: put(m,pad_chord(ch[k%4],8.5,0.11),t); t+=8; k+=1
    mel=[4,7,12,11,7,4,5,9,12,9,5,2,4,7,12,16,14,12,7,9,12,14,16,19,16,12]
    for j,s in enumerate(mel):
        tt=ground+26+j*2.0
        if tt<L-3: put(m,0.10*tone(N(s+12),2.2,a=0.005,r=2.0),tt); put(m,0.03*tone(N(s+24),1.2,a=0.005,r=1.0),tt)
    return m
if __name__=='__main__':
    tj=json.load(open(sys.argv[1],encoding='utf-8')); out=sys.argv[2]; L=tj['duration']
    a=float(sys.argv[sys.argv.index('--시작')+1]) if '--시작' in sys.argv else 0.0; b=float(sys.argv[sys.argv.index('--끝')+1]) if '--끝' in sys.argv else L
    buf=music(L,calm_end=0.0,ground=L+99) if '--추격만' in sys.argv else music(L)      # 쇼츠: 처음부터 끝까지 추격 음악
    for i,c in enumerate(tj['cues']): put(buf,sfx(c['kind'],i),c['t'],0.55*c.get('vol',1.0))
    buf=buf[int(a*SR):int(b*SR)]; n=len(buf); f=int(0.4*SR); buf[:f]*=np.linspace(0,1,f); buf[-f*3:]*=np.linspace(1,0,f*3)
    buf=np.tanh(buf*1.3); buf=buf/(np.abs(buf).max()+1e-9)*0.89
    w=wave.open(out,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf*32767).astype('<i2').tobytes()); w.close()
    print('OK',out,round(n/SR,1),'초')
