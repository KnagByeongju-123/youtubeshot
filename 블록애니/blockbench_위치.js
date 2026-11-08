// 묶음 위치 확인: node blockbench_위치.js <파일.bbmodel> <묶음이름,…> <시간,…>  → 그 시간의 world 위치
const {chromium}=require('playwright');const fs=require('fs');
const [,,file,names,times]=process.argv;
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage();
await p.goto('https://web.blockbench.net/',{waitUntil:'load',timeout:120000});await p.waitForFunction(()=>window.Codecs&&window.Codecs.project,{timeout:120000});
const txt=fs.readFileSync(file,'utf8');await p.evaluate(t=>loadModelFile({content:t,path:'m.bbmodel',name:'m.bbmodel'}),txt);await p.waitForTimeout(4000);
await p.evaluate(()=>{Modes.options.animate.select();Animation.all[0].select();});await p.waitForTimeout(800);
for(const t of times.split(',')){const r=await p.evaluate(([t,names])=>{Timeline.setTime(+t);Animator.preview();const V=THREE.Vector3;
 return names.split(',').map(n=>{const g=Group.all.find(g=>g.name===n);const v=new V();g.mesh.updateWorldMatrix(true,false);g.mesh.getWorldPosition(v);return n+':'+v.toArray().map(x=>x.toFixed(0)).join('/')}).join('  ')},[t,names]);console.log(t,r);}
await b.close();})();
