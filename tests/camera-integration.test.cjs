const path = require('path');
const fs = require('fs');
const root = path.resolve(__dirname, '..');
const automator = require(process.env.WECHAT_AUTOMATOR_PATH || '/tmp/qingcun-wechat-tools/node_modules/miniprogram-automator');
const projectPath = process.env.WECHAT_PROJECT_PATH || path.join(root, 'dist/ui-audit/mp-weixin');
const cliPath = process.env.WECHAT_CLI_PATH || '/Applications/wechatwebdevtools.app/Contents/MacOS/cli';
const assert=(condition,message)=>{if(!condition)throw Error(message)};
async function waitUntil(mini, predicate, label){
 for(let i=0;i<120;i++){const value=await mini.evaluate(predicate);if(value)return value;await new Promise(resolve=>setTimeout(resolve,500));}
 throw Error('timeout: '+label);
}
(async()=>{
 const mini=await automator.launch({cliPath,projectPath,trustProject:true,timeout:60000});
 mini.on('exception',e=>console.log('EXCEPTION',JSON.stringify(e)));
 try {
  for(const scene of [
   {id:'photo',path:'/pages/photo/index',target:'pages/photo/edit'},
   {id:'matting',path:'/pages/matting/index',target:'pages/matting/result'},
   {id:'watermark',path:'/pages/watermark/index',target:'pages/watermark/result'},
   {id:'convert',path:'/pages/convert/index',target:''}
  ]) {
   console.log('START '+scene.id);
   const page=await mini.reLaunch(scene.path);await page.waitFor(300);
   await mini.evaluate(id=>{
    const p=getCurrentPages().slice(-1)[0].$vm;
    if(id==='watermark')p.watermarkText='测试水印';
    if(id==='convert')p.showCamera=true;else p.chooseImage('camera');
    const fs=wx.getFileSystemManager();
    fs.copyFileSync('/static/example.jpeg',wx.env.USER_DATA_PATH+'/idphoto-camera-integration.jpg');
    wx.__integrationCamera=wx.createCameraContext;
    wx.createCameraContext=()=>({takePhoto(o){o.success({tempImagePath:wx.env.USER_DATA_PATH+'/idphoto-camera-integration.jpg'})}});
    return true;
   },scene.id);
   await page.waitFor(650);
   await mini.evaluate(()=>{
    const c=getCurrentPages().slice(-1)[0].$vm.$children.find(v=>typeof v.toggleGuide==='function');
    if(!c)throw Error('component missing');c.onCameraError=function(){};c.retryCamera();c.cameraReady=true;c.capturePhoto();c.confirmCapture();return true;
   });
   if(scene.target){
    const target=scene.target;
    await waitUntil(mini,()=>{const p=getCurrentPages().slice(-1)[0];return p&&p.route},scene.id+' route update');
    for(let i=0;i<120;i++){
     const current=await mini.currentPage();
     if(current.path===target)break;
     if(i===119)throw Error(scene.id+' did not reach '+target+', current '+current.path);
     await new Promise(resolve=>setTimeout(resolve,500));
    }
    console.log('PASS '+scene.id+' 模拟拍摄确认后，真实后端处理并进入 '+target);
   } else {
    const selected=await mini.evaluate(()=>getCurrentPages().slice(-1)[0].$vm.sourcePath);
    assert(selected&&selected.includes('idphoto-camera-integration.jpg'),'convert source handoff failed');
    await mini.evaluate(()=>{getCurrentPages().slice(-1)[0].$vm.onAction();return true});
    await waitUntil(mini,()=>getCurrentPages().slice(-1)[0].$vm.resultPath,'convert result');
    const result=await mini.evaluate(()=>{const p=getCurrentPages().slice(-1)[0].$vm;return {result:!!p.resultPath,width:p.width,height:p.height}});
    assert(result.result&&result.width>0&&result.height>0,'conversion result incomplete');
    console.log('PASS convert 模拟拍摄确认后，真实后端完成格式转换');
   }
   await mini.evaluate(()=>{if(wx.__integrationCamera)wx.createCameraContext=wx.__integrationCamera;delete wx.__integrationCamera;return true});
  }
 }finally {
  try{await mini.evaluate(()=>{if(wx.__integrationCamera)wx.createCameraContext=wx.__integrationCamera;delete wx.__integrationCamera;try{wx.getFileSystemManager().unlinkSync(wx.env.USER_DATA_PATH+'/idphoto-camera-integration.jpg')}catch(e){}return true})}catch(e){console.error('CLEANUP',String(e));process.exitCode=1}
  await mini.disconnect();
 }
})().catch(e=>{console.error('FAIL',e);process.exitCode=1});
