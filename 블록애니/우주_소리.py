"""《마지막 방어선》 소리: 웅장한 음악(직접 합성) + 효과음(시간표.json 의 cues) → wav
사용: python 우주_소리.py <시간표.json> <결과.wav> [--전투만]   (--전투만 = 쇼츠용: 처음부터 전투 음악)
  음악: 고요(낮은 현 화음) → 도착(낮은 뿔나팔·북) → 전투(빠른 북 + 금관 가락) → 주포(무거운 정적) → 돌입(가장 빠르게) → 붕괴(긴 화음) → 새벽(밝은 장조)"""
import json, sys, wave
import numpy as np
from 탈출_소리 import SR, P, env, tone, noise, put, sfx as sfx0
N=lambda s: 440*2**((s-9)/12)
def brass(f,d,vol=0.2,a=0.08,r=0.4):
    n=int(d*SR); t=np.arange(n)/SR; y=sum(np.sin(2*np.pi*f*k*t)/k for k in (1,2,3,4,5,6))*(1+0.004*np.sin(2*np.pi*5*t)); return (vol*y/2.4*env(n,a,r)).view(P)
def strings(freqs,d,vol=0.1):
    n=int(d*SR); t=np.arange(n)/SR; y=0
    for f in freqs:
        for det in (0.997,1.0,1.004): y=y+(2*((f*det*t)%1)-1)
    y=y/(len(freqs)*3); k=np.ones(64)/64; y=np.convolve(y,k,'same'); return (vol*y*env(n,min(1.5,d/3),min(1.5,d/3))).view(P)
def drum(vol=0.8,f=60): return (vol*tone(f,0.5,r=0.45,f1=34)+0.3*vol*noise(0.08,60,500,r=0.07)).view(P)
def sfx(kind,i=0):
    K=kind
    if K=='laser': return 0.5*tone(1800,0.16,r=0.12,f1=500,shape='saw')
    if K=='laser2': return 0.5*tone(900,0.2,r=0.15,f1=250,shape='sq')
    if K=='cannon': return 0.7*tone(300,0.35,r=0.3,f1=70,shape='saw')+0.4*noise(0.2,100,1500,r=0.18,seed=i)
    if K=='boom': return 0.9*noise(0.9,40,1600,r=0.8,seed=i)+0.7*tone(80,0.8,r=0.7,f1=30)
    if K=='bigboom': return 1.0*noise(2.6,25,1200,r=2.3,seed=i)+0.9*tone(55,2.4,r=2.2,f1=22)+0.3*noise(0.5,1500,7000,r=0.45,seed=i+1)
    if K=='beam': return 0.6*tone(140,2.0,a=0.05,r=0.5,shape='saw')+0.4*tone(1400,2.0,a=0.02,r=0.5,f1=900)+0.4*noise(2.0,800,6000,a=0.05,r=0.6,seed=i)
    if K=='charge': return 0.5*tone(60,9.5,a=6,r=0.2,f1=420,shape='saw')+0.25*noise(9.5,2000,9000,a=8,r=0.2,seed=i)
    if K=='horn': return brass(N(-27),4.0,0.5,a=0.6,r=1.5)+brass(N(-20),4.0,0.3,a=0.6,r=1.5)
    if K=='launch': return 0.5*noise(0.8,300,5000,a=0.05,r=0.7,seed=i)+0.3*tone(200,0.8,r=0.6,f1=700)
    if K=='whiteout': return 0.8*noise(3.5,200,9000,a=0.3,r=3.0,seed=i)+0.5*tone(40,3.5,a=0.2,r=3)
    return sfx0(kind,i)
def music(L,battle_only=False):
    m=np.zeros(int(L*SR))
    def sec(a,b): return (0,L) if battle_only else (a,b)
    if not battle_only:
        # 0~22 고요: 낮은 현 (라단조), 드문 높은 음
        for k,ch in enumerate([[N(-22),N(-15),N(-10)],[N(-24),N(-17),N(-12)],[N(-19),N(-12),N(-7)]]): put(m,strings(ch,9,0.11),k*7.4)
        for k,s in enumerate([14,17,21,19]): put(m,0.05*tone(N(s),3,a=0.4,r=2.5),3+k*4.6)
        # 22~50 도착: 깊은 지속음 + 느린 북
        put(m,strings([N(-34),N(-27)],30,0.16),21); put(m,brass(N(-34),26,0.14,a=6,r=4),23)
        for t in np.arange(26,50,2.0): put(m,drum(0.7,48),t)
        # 50~80 출격: 북이 빨라지고 금관 가락이 오름
        t=50.0; k=0
        while t<80:
            put(m,drum(0.6 if k%4 else 0.9,55),t); 
            if k%2: put(m,0.12*noise(0.05,3000,9000,r=0.04,seed=k),t)
            t+=0.5; k+=1
        for k,s in enumerate([-10,-10,-7,-5,-3,-3,0,2]): put(m,brass(N(s),3.6,0.16),50+k*3.7)
        put(m,strings([N(-22),N(-15),N(-10)],30,0.08),50)
    # 전투: 1초 2.6번 북 + 낮은 반복음 + 금관 가락
    a,b=sec(80,150); mel=[2,2,5,7,5,2,0,-3,2,2,5,9,7,5,3,2]
    t=a; k=0
    while t<b:
        st=0.19; put(m,drum(0.9 if k%8==0 else (0.5 if k%4==0 else 0.25),58),t)
        if k%2==0: put(m,0.11*tone(N([-22,-22,-19,-17][(k//32)%4]),st*1.8,a=0.005,r=0.08,shape='saw'),t)
        if k%4==2: put(m,0.10*noise(0.05,4000,10000,r=0.04,seed=k),t)
        if k%16==0: put(m,brass(N(mel[(k//16)%16]-12),st*14,0.17),t); put(m,brass(N(mel[(k//16)%16]-5),st*14,0.08),t)
        t+=st; k+=1
    if battle_only: return m
    put(m,strings([N(-22),N(-15),N(-10),N(-7)],70,0.07),80)
    # 150~185 주포: 음악이 걷히고 낮은 떨림 + 느린 큰 북
    put(m,strings([N(-34),N(-33)],36,0.15),149)
    for t in (152,156,160.9,166,170,172.9,178,182): put(m,drum(1.0,42),t)
    # 185~232 돌입: 가장 빠른 북, 반음씩 오르는 긴장
    t=185.0; k=0
    while t<230:
        st=0.16; put(m,drum(0.9 if k%8==0 else 0.3,62),t)
        if k%2==0: put(m,0.12*tone(N(-22+((k//64)%6)),st*1.7,a=0.005,r=0.07,shape='saw'),t)
        if k%16==8: put(m,brass(N(-10+((k//64)%6)*1+[0,3,5,7][(k//16)%4]),st*10,0.15),t)
        t+=st; k+=1
    # 232~266 붕괴: 긴 화음이 무너져 내림 → 고요
    for k,ch in enumerate([[N(-22),N(-15),N(-10),N(-3)],[N(-24),N(-17),N(-12),N(-5)],[N(-26),N(-19),N(-14)],[N(-27),N(-20),N(-15)]]): put(m,strings(ch,10,0.16-k*0.02),232+k*8); put(m,brass(ch[0]/2,9,0.12,a=1,r=3),232+k*8)
    # 266~300 새벽: 밝은 장조 (바 장조), 느린 금관 가락
    for k,ch in enumerate([[N(-19),N(-12),N(-7),N(-3)],[N(-24),N(-12),N(-8),N(-5)],[N(-17),N(-10),N(-5),N(-2)],[N(-19),N(-12),N(-7),N(0)]]): put(m,strings(ch,9.5,0.14),266+k*8.5)
    for k,s in enumerate([-7,-3,0,5,4,0,2,5,9,5]): put(m,brass(N(s),3.6,0.14,a=0.2,r=1.5),270+k*2.9)
    for t in (266,274.5,283,291.5): put(m,drum(0.7,46),t)
    return m
if __name__=='__main__':
    tj=json.load(open(sys.argv[1],encoding='utf-8')); out=sys.argv[2]; L=tj['duration']; buf=music(L,'--전투만' in sys.argv)
    for i,c in enumerate(tj['cues']): put(buf,sfx(c['kind'],i),c['t'],0.5*c.get('vol',1.0))
    f=int(0.4*SR); buf[:f]*=np.linspace(0,1,f); buf[-f*4:]*=np.linspace(1,0,f*4); buf=np.tanh(buf*1.25); buf=buf/(np.abs(buf).max()+1e-9)*0.89
    w=wave.open(out,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf*32767).astype('<i2').tobytes()); w.close(); print('OK',out,round(len(buf)/SR,1),'초')
