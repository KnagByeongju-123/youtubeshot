"""Poly Haven(polyhaven.com, 모든 자료 CC0) 블렌더 모델 받기
사용: .bpy_venv/bin/python -I 실사3D/폴리헤이븐_받기.py 목록 [낱말]      → 인기순 모델 이름
      .bpy_venv/bin/python -I 실사3D/폴리헤이븐_받기.py <모델이름> [1k|2k|4k] → models/polyhaven/<이름>/ 에 .blend + 겉면 그림
"""
import json,sys,os,urllib.request
o=urllib.request.build_opener(); o.addheaders=[("User-Agent","asset-fetcher/1.0")]; urllib.request.install_opener(o)
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","models","polyhaven")
def get(u): return json.load(urllib.request.urlopen(u))
if sys.argv[1]=="목록":
    w=sys.argv[2].lower() if len(sys.argv)>2 else ""
    d=get("https://api.polyhaven.com/assets?t=models")
    for k,v in sorted(d.items(),key=lambda x:-x[1].get('download_count',0)):
        s=(k+' '+v['name']+' '+' '.join(v['categories'])+' '+' '.join(v.get('tags',[]))).lower()
        if w in s: print(k,'|',v['name'],'|',', '.join(c for c in v['categories'] if not c.startswith('collection')))
    sys.exit()
name=sys.argv[1]; res=sys.argv[2] if len(sys.argv)>2 else "1k"; out=os.path.join(ROOT,name)
b=get(f"https://api.polyhaven.com/files/{name}")['blend'][res]['blend']; os.makedirs(out,exist_ok=True)
urllib.request.urlretrieve(b['url'],os.path.join(out,os.path.basename(b['url'])))
for k,v in b.get('include',{}).items():
    p=os.path.join(out,k); os.makedirs(os.path.dirname(p),exist_ok=True); urllib.request.urlretrieve(v['url'],p)
print("받음",os.path.join(out,os.path.basename(b['url'])))
