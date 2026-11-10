// 캐릭터 시트: 앞·옆·옆·뒤 4장을 흰 바탕으로 찍음.  node blockbench_시트촬영.js <폴더(.bbmodel 들)>  → <이름>_v0..3.png
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
const dir=process.argv[2];
(async()=>{
 const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});
 const p=await b.newPage({viewport:{width:1400,height:1400}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('https://web.blockbench.net/',{waitUntil:'load',timeout:120000});
 await p.waitForFunction(()=>window.Codecs&&window.Codecs.project,{timeout:120000});
 for(const f of fs.readdirSync(dir).filter(f=>f.endsWith('.bbmodel'))){
  const txt=fs.readFileSync(path.join(dir,f),'utf8');
  await p.evaluate((t)=>{ if(window.Project) try{Project.close(true)}catch(e){}; loadModelFile({content:t,path:'m.bbmodel',name:'m.bbmodel'});},txt);
  await p.waitForTimeout(2500);
  await p.evaluate(()=>{try{BarItems.toggle_sidebars.click()}catch(e){}});
  await p.waitForTimeout(800);
  await p.addStyleTag({content:'.preview_menu,.preview_view_mode_menu,.orbit_gizmo,.preview_options,.preview_tool_bar{display:none!important}'});
  const HH=await p.evaluate(()=>{try{three_grid.visible=false}catch(e){}; try{Transformer.visible=false;Transformer.detach()}catch(e){};
     Outliner.selected.length=0; try{unselectAllElements()}catch(e){}; try{updateSelection()}catch(e){};
     const P=Preview.selected; P.canvas.style.background='#ffffff';
     let top=0,wid=0; Outliner.elements.forEach(e=>{top=Math.max(top,e.to[1]); wid=Math.max(wid,Math.abs(e.from[0]),Math.abs(e.to[0]),Math.abs(e.from[2]),Math.abs(e.to[2]))}); return [Math.max(top,wid*2.1),top];});   // 키보다 옆으로 넓은 것(수레·괴물)도 잘리지 않게
  const rect=await p.evaluate(()=>{const c=Preview.selected.canvas.getBoundingClientRect();return {x:c.x,y:c.y,width:c.width,height:c.height};});
  const H=HH[0], cy=HH[1]/2, dist=H*4.2;
  const views=[[0,-1],[1,0],[-1,0],[0,1]];   // 앞(-z) 옆(+x) 옆(-x) 뒤(+z)
  for(let i=0;i<4;i++){
   await p.evaluate(([vx,vz,cy,dist])=>{const P=Preview.selected; P.camera.fov=14; P.camera.updateProjectionMatrix();
      P.camera.position.set(vx*dist,cy+dist*0.03,vz*dist); P.controls.target.set(0,cy,0); P.controls.update();},[views[i][0],views[i][1],cy,dist]);
   await p.waitForTimeout(300);
   await p.screenshot({path:path.join(dir,f.replace('.bbmodel',`_v${i}.png`)),clip:rect});
  }
  console.log('done',f);
 }
 await b.close();
})();
