const {chromium}=require('playwright');const fs=require('fs');
const [,,file,outdir,mode]=process.argv; // mode: test | full
(async()=>{
 const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});
 const p=await b.newPage({viewport:{width:2000,height:1200}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('https://web.blockbench.net/',{waitUntil:'load',timeout:120000});
 await p.waitForFunction(()=>window.Codecs&&window.Codecs.project,{timeout:120000});
 const txt=fs.readFileSync(file,'utf8');
 console.log(await p.evaluate((t)=>{loadModelFile({content:t,path:'s.bbmodel',name:'s.bbmodel'});return Outliner.elements.length;},txt));
 await p.waitForTimeout(4000);
 await p.evaluate(()=>{Modes.options.animate.select();});
 await p.waitForTimeout(1500);
 await p.evaluate(()=>{try{BarItems.toggle_sidebars.click()}catch(e){console.log(e)}});
 await p.waitForTimeout(1500);
 await p.addStyleTag({content:'.preview_menu,.preview_view_mode_menu,.orbit_gizmo,.preview_options,#preview_options,.preview_tool_bar{display:none!important} canvas.preview{background:linear-gradient(#6fbcf5,#cfeeff)!important}'});
 await p.evaluate(()=>{try{three_grid.visible=false}catch(e){}; try{Transformer.visible=false;Transformer.detach()}catch(e){};
   Animation.all[0].select(); Preview.selected.canvas.classList.add('preview');
   Preview.selected.canvas.style.background='linear-gradient(#6fbcf5,#cfeeff)'; Preview.selected.camera.fov=40; Preview.selected.camera.updateProjectionMatrix();});
 let rect=await p.evaluate(()=>{const c=Preview.selected.canvas.getBoundingClientRect();return {x:c.x,y:c.y,width:c.width,height:c.height};});
 // 16:9 centred crop
 let w=rect.width,h=Math.round(w*9/16); if(h>rect.height){h=rect.height;w=Math.round(h*16/9);}
 const clip={x:rect.x+(rect.width-w)/2,y:rect.y+(rect.height-h)/2,width:w,height:h};
 console.log(JSON.stringify(rect),JSON.stringify(clip));
 fs.mkdirSync(outdir,{recursive:true});
 const L=12, times = mode==='test'?[0,3,5.8,7,9,10.5]:[...Array(L*24).keys()].map(i=>i/24);
 let n=0;
 for(const t of times){
  await p.evaluate((t)=>{
   const lerp=(a,b,u)=>a+(b-a)*u, ease=u=>u*u*(3-2*u);
   // camera: follow kid during walk, then settle between both, closer
   const kx= t<6? -150+130*(t/6) : -20;
   let u=Math.min(1,Math.max(0,(t-5)/3)); u=ease(u);
   const tx=lerp(-kx-10,-8,u), dist=lerp(230,150,u), ty=lerp(30,22,u);
   const P=Preview.selected;
   P.camera.position.set(tx+40*(1-u)+20, ty+lerp(60,35,u), -24-dist);
   P.controls.target.set(tx,ty,-24); P.controls.update();
   Timeline.setTime(t); Animator.preview();
  },t);
  await p.screenshot({path:`${outdir}/f${String(n++).padStart(4,'0')}.png`,clip});
 }
 await b.close();
})();
