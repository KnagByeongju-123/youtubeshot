// 샷 촬영: node blockbench_샷촬영.js <샷목록.json> <모형폴더> <출력폴더> [샷이름,...] [--test]
// 샷 = {name,set,t0,t1,fps,sky:[색,...],ropes:bool,view:'textured'|'wireframe', cam:[{u,pos:[x,y,z],tgt:[x,y,z]}], follow:'묶음이름'(있으면 pos·tgt 는 그 묶음 위치 기준)}
// 게임 카메라(cam 이 객체): {type:'chase'|'shoulder', target, back, up, side, ahead, look, lookAt, lag, sway} / {type:'orbit', target|center, a:[도,도], r:[,], h:[,], look, lag} / {type:'track', pos, pos2, target, look, lag}
//   back·up·r·h·a 는 [시작,끝] 으로 주면 샷 동안 바뀜. lag = 늦게 따라오는 시간(초)
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
const [,,shotFile,modelDir,outDir,only,testFlag]=process.argv;
const all=JSON.parse(fs.readFileSync(shotFile,'utf8'));
const info=JSON.parse(fs.readFileSync(path.join(modelDir,'세트정보.json'),'utf8'));
const want=(only&&only!=='all')?only.split(','):null;
const shots=all.shots.filter(s=>!want||want.includes(s.name));
(async()=>{
 const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});
 const VERT=all.aspect==='9:16';   // 세로 쇼츠
 const p=await b.newPage({viewport:VERT?{width:1300,height:2000}:{width:1600,height:1100}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('https://web.blockbench.net/',{waitUntil:'load',timeout:120000});
 await p.waitForFunction(()=>window.Codecs&&window.Codecs.project,{timeout:120000});
 let loaded=null, first=true, clip=null;
 for(const sh of shots){
  if(loaded!==sh.set){
   const file=fs.readdirSync(modelDir).find(f=>f.startsWith(sh.set+'_')&&f.endsWith('.bbmodel'));
   const txt=fs.readFileSync(path.join(modelDir,file),'utf8');
   await p.evaluate((t)=>{ try{ if(window.Project) Project.close(true);}catch(e){}; loadModelFile({content:t,path:'m.bbmodel',name:'m.bbmodel'});},txt);
   await p.waitForTimeout(4000);
   await p.evaluate(()=>{Modes.options.animate.select();});
   await p.waitForTimeout(1000);
   if(first){ await p.evaluate(()=>{try{BarItems.toggle_sidebars.click()}catch(e){}}); await p.waitForTimeout(1000);
     await p.addStyleTag({content:'.preview_menu,.preview_view_mode_menu,.orbit_gizmo,.preview_options,.preview_tool_bar{display:none!important}'}); first=false; }
   await p.evaluate(()=>{try{three_grid.visible=false}catch(e){}; try{Transformer.visible=false;Transformer.detach()}catch(e){};
      try{unselectAllElements()}catch(e){}; Animation.all[0].select();});
   await p.waitForTimeout(500);
   const rect=await p.evaluate(()=>{const c=Preview.selected.canvas.getBoundingClientRect();return {x:c.x,y:c.y,width:c.width,height:c.height};});
   const AR=VERT?9/16:16/9; let w=rect.width,h=Math.round(w/AR); if(h>rect.height){h=rect.height;w=Math.round(h*AR);}
   clip={x:Math.round(rect.x+(rect.width-w)/2),y:Math.round(rect.y+(rect.height-h)/2),width:w,height:h};
   loaded=sh.set; console.log('set',sh.set,JSON.stringify(clip));
  }
  const ropes=(sh.ropes===false)?[]:(info[sh.set]&&info[sh.set].ropes)||[];
  await p.evaluate(([sky,view,nr,only,fov])=>{const P=Preview.selected;
     P.canvas.style.background=`linear-gradient(${sky.join(',')})`; P.camera.fov=fov; P.camera.updateProjectionMatrix();
     try{ BarItems.view_mode.set(view||'textured'); BarItems.view_mode.onChange && BarItems.view_mode.onChange(); }catch(e){ try{Project.view_mode=view||'textured'; Canvas.updateAllFaces();}catch(e2){} }
     Cube.all.forEach(c=>{ let ok=!only, q=c.parent; while(q && typeof q==='object'){ if(q.name===only) ok=true; q=q.parent; } c.mesh.visible=ok; });
     Cube.all.filter(c=>c.name.startsWith('rope_')).forEach((c,i)=>{c.mesh.visible=i<nr;});
  },[sh.sky||['#6fbcf5','#d6f0ff'],sh.view,ropes.length,sh.only||null,sh.fov||(VERT?50:38)]);
  const dir=path.join(outDir,sh.name); fs.mkdirSync(dir,{recursive:true});
  const NF=Math.max(1,Math.round((sh.t1-sh.t0)*sh.fps));
  let G=null;   // 게임 카메라: cam 이 배열이 아니라 {type:...} 이면 모든 프레임 위치를 미리 계산
  if(!Array.isArray(sh.cam)){
   G=await p.evaluate(([c,t0,fps,n])=>{
     const V=THREE.Vector3; const grp=nm=>Group.all.find(g=>g.name===nm);
     const info=nm=>{const g=grp(nm); const v=new V(), q=new THREE.Quaternion(); if(g&&g.mesh){g.mesh.updateWorldMatrix(true,false); g.mesh.getWorldPosition(v); g.mesh.getWorldQuaternion(q);} 
        const f=new V(0,0,-1).applyQuaternion(q); f.y=0; if(f.length()<1e-6) f.set(0,0,-1); f.normalize(); return {p:v,f};};
     const sm=x=>x*x*(3-2*x), lerp=(a,b,u)=>a+(b-a)*u;
     const raw=[];
     for(let i=0;i<n;i++){ const t=t0+i/fps, u=n>1?i/(n-1):0; Timeline.setTime(t); Animator.preview();
       const T=c.target?info(c.target):{p:new V(...(c.center||[0,0,0])),f:new V(0,0,-1)};
       const Lk=c.lookAt?info(c.lookAt):null;
       let pos, tgt;
       if(c.type==='chase'||c.type==='shoulder'){        // 3인칭 추적 / 어깨 너머: 인물이 보는 방향 뒤·위·옆
         const f=T.f, r=new V(-f.z,0,f.x);               // 오른쪽
         const back=lerp(c.back[0]??c.back,c.back[1]??c.back,sm(u)), up=lerp(c.up[0]??c.up,c.up[1]??c.up,sm(u));
         pos=T.p.clone().addScaledVector(f,-back).addScaledVector(r,c.side||0); pos.y+=up;
         tgt=Lk?Lk.p.clone().add(new V(...(c.look||[0,0,0]))):T.p.clone().addScaledVector(f,c.ahead||10).add(new V(...(c.look||[0,8,0])));
       } else if(c.type==='orbit'){                       // 빙 돌기 (각도·반지름·높이를 시간에 따라)
         const a=(lerp(c.a[0],c.a[1],sm(u)))*Math.PI/180, R=lerp(c.r[0],c.r[1],sm(u)), h=lerp(c.h[0],c.h[1],sm(u));
         const C=T.p.clone(); pos=new V(C.x+Math.sin(a)*R, C.y+h, C.z-Math.cos(a)*R);
         tgt=(Lk?Lk.p.clone():C).add(new V(...(c.look||[0,8,0])));
       } else {                                           // track: 정한 자리에서 대상을 바라보며 따라감
         pos=new V(...c.pos); if(c.pos2){const q=new V(...c.pos2); pos.lerp(q,sm(u));}
         tgt=T.p.clone().add(new V(...(c.look||[0,0,0])));
       }
       raw.push([pos.x,pos.y,pos.z,tgt.x,tgt.y,tgt.z]); }
     // 부드럽게 늦게 따라오기 (lag 초) — 게임 카메라처럼 갑자기 꺾이지 않게
     const k=c.lag?1-Math.exp(-1/(fps*c.lag)):1; const out=[raw[0].slice()];
     for(let i=1;i<n;i++){ const pv=out[i-1], r=raw[i]; out.push(r.map((v,j)=>pv[j]+(v-pv[j])*(j<3?k:Math.min(1,k*1.6)))); }
     // 아주 작은 흔들림 (손에 든 카메라 느낌, sway 크기)
     if(c.sway){ for(let i=0;i<n;i++){ const t=i/fps; out[i][0]+=Math.sin(t*1.3)*c.sway; out[i][1]+=Math.sin(t*0.9+1)*c.sway*0.6; } }
     return out;
   },[sh.cam,sh.t0,sh.fps,NF]);
  }
  const n=Math.max(1,Math.round((sh.t1-sh.t0)*sh.fps));
  const idx=testFlag?[0,Math.floor(n/3),Math.floor(2*n/3),n-1]:[...Array(n).keys()];
  for(const i of idx){
   const fpath=path.join(dir,`f${String(i).padStart(5,'0')}.png`);
   if(!testFlag && fs.existsSync(fpath) && fs.statSync(fpath).size>1000) continue;   // 이미 찍은 장은 건너뜀 (멈춘 뒤 이어 찍기)
   const t=sh.t0+i/sh.fps, u=n>1?i/(n-1):0;
   await p.evaluate(([t,u,cam,follow,ropes,GP])=>{
     Timeline.setTime(t); Animator.preview();
     const V=THREE.Vector3; const grp=n=>Group.all.find(g=>g.name===n);
     const wp=n=>{const g=grp(n); const v=new V(); if(g&&g.mesh){g.mesh.updateWorldMatrix(true,false); g.mesh.getWorldPosition(v);} return v;};
     // 밧줄
     const rc=Cube.all.filter(c=>c.name.startsWith('rope_'));
     ropes.forEach(([a,bn],i)=>{const m=rc[i]&&rc[i].mesh; if(!m) return; const A=wp(a),B=wp(bn);
        m.parent.updateWorldMatrix(true,false); const inv=m.parent.matrixWorld.clone().invert();
        const Al=A.clone().applyMatrix4(inv), Bl=B.clone().applyMatrix4(inv);
        m.position.copy(Al); m.scale.set(1,1,Math.max(0.01,Al.distanceTo(Bl))); m.lookAt(B); m.updateMatrix();});
     // 카메라
     if(GP){ const P=Preview.selected; P.camera.position.set(GP[0],GP[1],GP[2]); P.controls.target.set(GP[3],GP[4],GP[5]); P.controls.update(); return; }
     const sm=x=>x*x*(3-2*x); let k=0; while(k<cam.length-2&&u>cam[k+1].u) k++;
     const c0=cam[k], c1=cam[Math.min(k+1,cam.length-1)]; const f=c1.u>c0.u?sm(Math.min(1,Math.max(0,(u-c0.u)/(c1.u-c0.u)))):0;
     const L=(a,b)=>a.map((v,j)=>v+(b[j]-v)*f); let pos=L(c0.pos,c1.pos), tgt=L(c0.tgt,c1.tgt);
     if(follow){const F=wp(follow); pos=[pos[0]+F.x,pos[1]+F.y,pos[2]+F.z]; tgt=[tgt[0]+F.x,tgt[1]+F.y,tgt[2]+F.z];}
     const P=Preview.selected; P.camera.position.set(...pos); P.controls.target.set(...tgt); P.controls.update();
   },[t,u,sh.cam,sh.follow||null,ropes,G?G[i]:null]);
   await p.screenshot({path:fpath,clip});
  }
  console.log('shot',sh.name,idx.length);
 }
 await b.close();
})();
