// three.js 애니 장면 촬영: 장면 html 의 window.renderFrame(i) 를 1/24초씩 불러 사진을 찍음 (그래픽카드 없이, 화면 없는 브라우저)
//   node 애니3D/촬영.js <장면.html> <프레임폴더> <장수> [시험할 장 번호: 0,24,48]
//   장면 html 약속: 준비되면 window.READY = true, window.renderFrame(i) 가 i 번째 장(i/24초)을 그림
//   저장소 폴더를 작은 웹 서버로 열어 씀(모델은 models/vrm/, 부품은 애니3D/node_modules/)
const {chromium}=require('playwright'); const fs=require('fs'); const path=require('path'); const http=require('http');
const [,,page,out,n,only]=process.argv; const ROOT=path.resolve(__dirname,'..');
const TYPES={'.html':'text/html; charset=utf-8','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.vrm':'application/octet-stream','.glb':'model/gltf-binary'};
const srv=http.createServer((q,r)=>{const p=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));
  if(!p.startsWith(ROOT)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){r.writeHead(404);return r.end();}
  r.writeHead(200,{'Content-Type':TYPES[path.extname(p)]||'application/octet-stream'}); fs.createReadStream(p).pipe(r);});
srv.listen(0,'127.0.0.1',async()=>{
 const url=`http://127.0.0.1:${srv.address().port}/${path.relative(ROOT,path.resolve(page)).split(path.sep).map(encodeURIComponent).join('/')}`;
 fs.mkdirSync(out,{recursive:true});
 const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});
 const p=await b.newPage({viewport:{width:1280,height:720}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto(url); await p.waitForFunction(()=>window.READY,{timeout:180000});
 const want=only?new Set(only.split(',').map(Number)):null;
 for(let i=0;i<+n;i++){ await p.evaluate(i=>window.renderFrame(i),i);
   if(!want||want.has(i)) await p.locator('canvas').screenshot({path:path.join(out,`f${String(i).padStart(4,'0')}.png`)}); }
 await b.close(); srv.close(); console.log('done',n);
});
