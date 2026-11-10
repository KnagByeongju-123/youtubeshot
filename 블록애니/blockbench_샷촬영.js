// 샷 촬영: node blockbench_샷촬영.js <샷목록.json> <모형폴더> <출력폴더> [샷이름,...] [--test]
// 샷 = {name,set,t0,t1,fps,sky:[색,...],ropes:bool,view:'textured'|'wireframe', cam:[{u,pos:[x,y,z],tgt:[x,y,z],shake?,fov?,roll?}], follow:'묶음이름'(있으면 pos·tgt 는 그 묶음 위치 기준), shake:흔들림 크기}
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
const [,,shotFile,modelDir,outDir,only,testFlag]=process.argv;
const all=JSON.parse(fs.readFileSync(shotFile,'utf8'));
const info=JSON.parse(fs.readFileSync(path.join(modelDir,'세트정보.json'),'utf8'));
const want=(only&&only!=='all')?only.split(','):null;
const shots=all.shots.filter(s=>!want||want.includes(s.name));
(async()=>{
 const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});
 const VERT=!!process.env.VERT;      // VERT=1 → 세로(9:16, 쇼츠)로 찍음
 const p=await b.newPage({viewport:VERT?{width:1500,height:2200}:{width:1600,height:1100}});
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
   let w=rect.width,h=Math.round(w*9/16); if(h>rect.height){h=rect.height;w=Math.round(h*16/9);}
   if(VERT){ h=rect.height; w=Math.round(h*9/16); if(w>rect.width){w=rect.width;h=Math.round(w*16/9);} }
   clip={x:Math.round(rect.x+(rect.width-w)/2),y:Math.round(rect.y+(rect.height-h)/2),width:w,height:h};
   loaded=sh.set; console.log('set',sh.set,JSON.stringify(clip));
  }
  const ropes=(sh.ropes===false)?[]:(info[sh.set]&&info[sh.set].ropes)||[];
  await p.evaluate(([sky,view,nr,only])=>{const P=Preview.selected;
     P.canvas.style.background=`linear-gradient(${sky.join(',')})`; P.camera.fov=38; P.camera.updateProjectionMatrix();
     try{ BarItems.view_mode.set(view||'textured'); BarItems.view_mode.onChange && BarItems.view_mode.onChange(); }catch(e){ try{Project.view_mode=view||'textured'; Canvas.updateAllFaces();}catch(e2){} }
     Cube.all.forEach(c=>{ let ok=!only, q=c.parent; while(q && typeof q==='object'){ if(q.name===only) ok=true; q=q.parent; } c.mesh.visible=ok; });
     Cube.all.filter(c=>c.name.startsWith('rope_')).forEach((c,i)=>{c.mesh.visible=i<nr;});
  },[sh.sky||['#6fbcf5','#d6f0ff'],sh.view,ropes.length,sh.only||null]);
  const dir=path.join(outDir,sh.name); fs.mkdirSync(dir,{recursive:true});
  const n=Math.max(1,Math.round((sh.t1-sh.t0)*sh.fps));
  const idx=testFlag?[0,Math.floor(n/3),Math.floor(2*n/3),n-1]:[...Array(n).keys()];
  for(const i of idx){
   const fpath=path.join(dir,`f${String(i).padStart(5,'0')}.png`);
   if(!testFlag && fs.existsSync(fpath) && fs.statSync(fpath).size>1000) continue;   // 이미 찍은 장은 건너뜀 (멈춘 뒤 이어 찍기)
   const t=sh.t0+i/sh.fps, u=n>1?i/(n-1):0;
   await p.evaluate(([t,u,cam,follow,ropes,shake,vert])=>{
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
     const sm=x=>x*x*(3-2*x); let k=0; while(k<cam.length-2&&u>cam[k+1].u) k++;
     const c0=cam[k], c1=cam[Math.min(k+1,cam.length-1)]; const f=c1.u>c0.u?sm(Math.min(1,Math.max(0,(u-c0.u)/(c1.u-c0.u)))):0;
     const L=(a,b)=>a.map((v,j)=>v+(b[j]-v)*f); let pos=L(c0.pos,c1.pos), tgt=L(c0.tgt,c1.tgt);
     if(follow){const F=wp(follow); pos=[pos[0]+F.x,pos[1]+F.y,pos[2]+F.z]; tgt=[tgt[0]+F.x,tgt[1]+F.y,tgt[2]+F.z];}
     if(shake){const w=(c0.shake!==undefined?c0.shake:1)*(1-f)+(c1.shake!==undefined?c1.shake:1)*f, q=shake*w;   // 흔들림 (추락·싸움): 키마다 shake 배율(0~1)을 줄 수 있음
       pos=[pos[0]+q*Math.sin(t*31.7),pos[1]+q*Math.sin(t*23.3+1.3),pos[2]+q*0.6*Math.sin(t*17.9+2.1)]; tgt=[tgt[0]+q*0.7*Math.sin(t*27.1+0.5),tgt[1]+q*0.7*Math.sin(t*19.7+2.9),tgt[2]];}
     const P=Preview.selected;
     const num=(k,dv)=>{const a=(c0[k]!==undefined?c0[k]:dv), b=(c1[k]!==undefined?c1[k]:dv); return a+(b-a)*f;};
     let fov=num('fov',38); const roll=num('roll',0)*Math.PI/180;
     if(vert) fov=Math.min(104,2*Math.atan(Math.tan(fov*Math.PI/360)*2.1)*180/Math.PI);      // 세로 화면은 좌우가 좁아짐 → 시야각을 넓혀 맞춤      // 순간 확대(시야각)·화면 기울이기 (게임 같은 카메라)
     if(Math.abs(P.camera.fov-fov)>0.01){P.camera.fov=fov; P.camera.updateProjectionMatrix();}
     P.camera.up.set(Math.sin(roll),Math.cos(roll),0);
     P.camera.position.set(...pos); P.controls.target.set(...tgt); P.controls.update();
   },[t,u,sh.cam,sh.follow||null,ropes,sh.shake||0,VERT]);
   await p.screenshot({path:fpath,clip});
  }
  console.log('shot',sh.name,idx.length);
 }
 await b.close();
})();
