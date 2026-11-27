// 정사영 정면(얼굴격자 비교·맞추기용, 애니3D 폴더를 http 로 열고): node 정사영촬영.js <glb이름> <출력.png> [cy] [os]
const {chromium}=require('playwright');
const [g,out,cy,os]=[process.argv[2],process.argv[3],process.argv[4]||'1.6',process.argv[5]||'0.16'];
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});
const q=await b.newPage({viewport:{width:1000,height:1000}});
await q.goto(`http://localhost:8765/_정사영보기.html?w=1000&h=1000&cy=${cy}&os=${os}&g=${g}.glb`);await q.waitForFunction('window.READY',{timeout:120000});
await q.evaluate(`render(0,0,null,0,10)`);await q.screenshot({path:out});
await b.close();})();
