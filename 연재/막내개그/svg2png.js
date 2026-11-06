// SVG → 투명 PNG (설치된 크로미움). 크기는 SIZE 환경변수 (기본 256): SIZE=1024 node svg2png.js a.svg b.svg
const { chromium } = require('playwright'); const fs=require('fs');
const S=parseInt(process.env.SIZE||'256');
(async()=>{ const b=await chromium.launch(); const p=await b.newPage({viewport:{width:S,height:S}});
 for (const f of process.argv.slice(2)) { const svg=fs.readFileSync(f,'utf8');
  await p.setContent(`<html><body style="margin:0;background:transparent">${svg.replace('<svg',`<svg width="${S}" height="${S}"`)}</body></html>`);
  await p.screenshot({path:f.replace(/\.svg$/,'.png'),omitBackground:true,clip:{x:0,y:0,width:S,height:S}}); }
 await b.close(); })();
