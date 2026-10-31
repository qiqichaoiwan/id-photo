const path = require('path');
const fs = require('fs');
const root = path.resolve(__dirname, '..');
const automator = require(process.env.WECHAT_AUTOMATOR_PATH || '/tmp/qingcun-wechat-tools/node_modules/miniprogram-automator');
const projectPath = process.env.WECHAT_PROJECT_PATH || path.join(root, 'dist/ui-audit/mp-weixin');
const cliPath = process.env.WECHAT_CLI_PATH || '/Applications/wechatwebdevtools.app/Contents/MacOS/cli';
const outputPath = process.env.CAMERA_AUDIT_OUTPUT || path.join(root, 'dist/ui-audit/camera');
fs.mkdirSync(outputPath, { recursive: true });
const assert=(condition,message)=>{if(!condition)throw Error(message)};
(async()=>{
 const mini=await automator.launch({cliPath,projectPath,trustProject:true,timeout:60000});
 try {
  for(const scenario of [
   {path:'/pages/photo/index',guide:true,position:'front',id:'photo'},
   {path:'/pages/matting/index',guide:true,position:'front',id:'matting'},
   {path:'/pages/matting/upload',guide:true,position:'front',id:'matting-upload'},
   {path:'/pages/watermark/index',guide:false,position:'back',id:'watermark'},
   {path:'/pages/watermark/upload',guide:false,position:'back',id:'watermark-upload'},
   {path:'/pages/convert/index',guide:false,position:'back',id:'convert'}
  ]) {
   const page=await mini.reLaunch(scenario.path); await page.waitFor(300);
   await mini.evaluate((id)=>{const p=getCurrentPages().slice(-1)[0].$vm;if(id==='watermark')p.watermarkText='测试水印';if(id==='convert')p.showCamera=true;else p.chooseImage('camera');return true},scenario.id);
   await page.waitFor(700);
   const initial=await mini.evaluate(()=>{const p=getCurrentPages().slice(-1)[0].$vm;const c=p.$children.find(v=>typeof v.toggleGuide==='function');if(!c)return null;return {guide:c.guideEnabled,position:c.cameraPosition,error:c.cameraError,title:c.title}});
   assert(initial,scenario.id+' camera component missing');
   assert(initial.guide===scenario.guide,scenario.id+' wrong default guide');
   assert(initial.position===scenario.position,scenario.id+' wrong initial camera');
   await mini.evaluate(()=>{const p=getCurrentPages().slice(-1)[0].$vm;const c=p.$children.find(v=>typeof v.toggleGuide==='function');c.onCameraError=function(){};c.retryCamera();c.cameraReady=true;return true});
   await page.waitFor(650);
   if(scenario.id==='photo')await mini.screenshot({path:path.join(outputPath, 'shared-guide-on.png')});
   await mini.evaluate(()=>{const c=getCurrentPages().slice(-1)[0].$vm.$children.find(v=>typeof v.toggleGuide==='function');c.toggleGuide();return true});
   await page.waitFor(250);
   const toggled=await mini.evaluate(()=>getCurrentPages().slice(-1)[0].$vm.$children.find(v=>typeof v.toggleGuide==='function').guideEnabled);
   assert(toggled===!scenario.guide,scenario.id+' toggle failed');
   if(scenario.id==='photo')await mini.screenshot({path:path.join(outputPath, 'shared-guide-off.png')});
   if(scenario.id==='watermark')await mini.screenshot({path:path.join(outputPath, 'shared-watermark.png')});
   await mini.evaluate(()=>{const c=getCurrentPages().slice(-1)[0].$vm.$children.find(v=>typeof v.toggleGuide==='function');c.toggleGuide();c.switchCamera();return true});
   const flipped=await mini.evaluate(()=>getCurrentPages().slice(-1)[0].$vm.$children.find(v=>typeof v.toggleGuide==='function').cameraPosition);
   assert(flipped!==scenario.position,scenario.id+' flip failed');
   await mini.evaluate(()=>{wx.__auditCamera=wx.createCameraContext;wx.createCameraContext=()=>({takePhoto(o){o.success({tempImagePath:'/static/example.jpeg'})}});const c=getCurrentPages().slice(-1)[0].$vm.$children.find(v=>typeof v.toggleGuide==='function');c.cameraReady=true;c.capturePhoto();return true});
   await page.waitFor(300);
   const preview=await mini.evaluate(()=>{const c=getCurrentPages().slice(-1)[0].$vm.$children.find(v=>typeof v.toggleGuide==='function');return {preview:c.showCapturePreview,path:c.capturedImagePath}});
   assert(preview.preview&&preview.path,scenario.id+' capture preview failed');
   if(scenario.id==='photo')await mini.screenshot({path:path.join(outputPath, 'shared-preview.png')});
   await mini.evaluate(()=>{const c=getCurrentPages().slice(-1)[0].$vm.$children.find(v=>typeof v.toggleGuide==='function');c.retakePhoto();c.cameraReady=true;c.capturePhoto();return true});
   await page.waitFor(250);
   if(scenario.id==='matting-upload'||scenario.id==='watermark-upload'||scenario.id==='convert') {
    await mini.evaluate(()=>{const c=getCurrentPages().slice(-1)[0].$vm.$children.find(v=>typeof v.toggleGuide==='function');c.confirmCapture();return true});await page.waitFor(300);
    const result=await mini.evaluate(()=>{const p=getCurrentPages().slice(-1)[0].$vm;return {open:p.showCamera,path:p.imagePath||p.sourcePath,show:p.show}});
    assert(!result.open&&result.path==='/static/example.jpeg',scenario.id+' photo handoff failed');
    if(scenario.id.endsWith('upload'))assert(result.show,scenario.id+' selection preview missing');
   } else {
    await mini.evaluate(()=>{const c=getCurrentPages().slice(-1)[0].$vm.$children.find(v=>typeof v.toggleGuide==='function');c.closeCamera();return true});await page.waitFor(250);
    assert(!await mini.evaluate(()=>getCurrentPages().slice(-1)[0].$vm.showCamera),scenario.id+' close failed');
   }
   await mini.evaluate(()=>{if(wx.__auditCamera)wx.createCameraContext=wx.__auditCamera;delete wx.__auditCamera;return true});
   console.log('PASS '+scenario.id+' camera defaults, guide toggle, flip, capture preview, retake and '+(scenario.id.endsWith('upload')||scenario.id==='convert'?'handoff':'close'));
  }
 } finally {
  try{await mini.evaluate(()=>{if(wx.__auditCamera)wx.createCameraContext=wx.__auditCamera;delete wx.__auditCamera;return true})}catch(e){console.error('CLEANUP',String(e));process.exitCode=1}
  await mini.disconnect();
 }
})().catch(e=>{console.error('FAIL',e);process.exitCode=1});
