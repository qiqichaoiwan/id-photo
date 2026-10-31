const path = require('path');
const fs = require('fs');
const root = path.resolve(__dirname, '..');
const automator = require(process.env.WECHAT_AUTOMATOR_PATH || '/tmp/qingcun-wechat-tools/node_modules/miniprogram-automator');
const projectPath = process.env.WECHAT_PROJECT_PATH || path.join(root, 'dist/ui-audit/mp-weixin');
const cliPath = process.env.WECHAT_CLI_PATH || '/Applications/wechatwebdevtools.app/Contents/MacOS/cli';
(async()=>{
 const mini=await automator.launch({cliPath,projectPath,trustProject:true,timeout:60000});
 try{
  for(const kind of ['matting','watermark']){
   const page=await mini.reLaunch('/pages/'+kind+'/upload');await page.waitFor(300);
   await mini.evaluate(()=>{const p=getCurrentPages().slice(-1)[0].$vm;p.imagePath='wxfile://tmp/100%20test sample.jpg';p.confirmSelect();return true});
   for(let i=0;i<20;i++){const current=await mini.currentPage();if(current.path==='pages/'+kind+'/index')break;await new Promise(r=>setTimeout(r,300))}
   const value=await mini.evaluate(()=>{const p=getCurrentPages().slice(-1)[0].$vm;return {path:p.imagePath,show:p.show,preselected:p.preselectedImage}});
   if(value.path!=='wxfile://tmp/100%20test sample.jpg')throw Error(kind+' path changed: '+value.path);
   if(!(kind==='matting'?value.show:value.preselected))throw Error(kind+' photo selection not shown');
   console.log('PASS '+kind+' legacy handoff '+JSON.stringify(value));
  }
 }finally{await mini.disconnect()}
})().catch(e=>{console.error('FAIL',e);process.exitCode=1});
