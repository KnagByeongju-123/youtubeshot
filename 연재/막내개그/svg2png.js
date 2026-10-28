const { chromium } = require('playwright'); const fs=require('fs'); const path=require('path');
(async()=>{ const b=await chromium.launch(); const p=await b.newPage({viewport:{width:256,height:256}});
 for (const f of process.argv.slice(2)) { const svg=fs.readFileSync(f,'utf8');
  await p.setContent(`<html><body style="margin:0;background:transparent">${svg.replace('<svg','<svg width="256" height="256"')}</body></html>`);
  await p.screenshot({path:f.replace(/\.svg$/,'.png'),omitBackground:true,clip:{x:0,y:0,width:256,height:256}}); }
 await b.close(); })();
