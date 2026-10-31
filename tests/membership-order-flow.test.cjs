const assert = require('assert');
const path = require('path');
const automator = require(process.env.WECHAT_AUTOMATOR_PATH || '/tmp/qingcun-wechat-tools/node_modules/miniprogram-automator');
const projectPath = process.env.WECHAT_PROJECT_PATH || path.resolve(__dirname, '../dist/build/mp-weixin');
const cliPath = process.env.WECHAT_CLI_PATH || '/Applications/wechatwebdevtools.app/Contents/MacOS/cli';
(async () => {
 const mini = await automator.launch({cliPath,projectPath,trustProject:true,timeout:60000});
 try {
  await mini.evaluate(() => {
   wx.__qaOriginal = { login:wx.login, request:wx.request, showModal:wx.showModal };
   wx.__qa = { refund:null, requests:[] };
   wx.login = options => options.success && options.success({code:'isolated-mock'});
   wx.showModal = options => options.success && options.success({confirm:true,cancel:false});
   wx.request = options => {
    const order = {order_no:'Mtest123',plan_name:'模拟会员',months:1,price_fen:1200,status:'paid',created_at:'2026-10-31T00:00:00+00:00',expires_at:'2026-11-30T00:00:00+00:00',review_needed:false};
    let statusCode=200, data;
    if (options.url.includes('/auth/wechat')) data={token:'mock-token',expires_in:3600};
    else if (options.url.endsWith('/membership/orders')) data=[order];
    else if (options.url.endsWith('/membership/orders/Mtest123/refund-requests')) {wx.__qa.refund={status:'submitted',response:'',created_at:'2026-10-31T00:00:00+00:00',updated_at:'2026-10-31T00:00:00+00:00'};data=wx.__qa.refund;}
    else if (options.url.endsWith('/membership/orders/Mtest123')) data={...order,refund_request:wx.__qa.refund};
    else {statusCode=404;data={detail:'订单不存在'};}
    wx.__qa.requests.push({path:options.url.replace(/^https?:\/\/[^/]+/,''),method:options.method});
    setTimeout(()=>{ options.success && options.success({statusCode,data}); options.complete && options.complete({statusCode,data}); },5);
    return {abort:()=>{}};
   };
  });
  const list=await mini.reLaunch('/pages/membership/orders');
  await list.waitFor(800);
  assert((await list.$('.order')), '订单列表未显示');
  await (await list.$('.order')).tap();
  await new Promise(resolve=>setTimeout(resolve,800));
  const detail=await mini.currentPage();
  let state=await mini.evaluate(()=>{const p=getCurrentPages().slice(-1)[0];return {route:p.route,orderNo:p.$vm.orderNo,status:p.$vm.order&&p.$vm.order.status};});
  assert.strictEqual(state.orderNo,'Mtest123'); assert.strictEqual(state.status,'paid');
  assert((await detail.$('.refund-card')), '退款入口未显示');
  await (await detail.$('.refund-button')).tap();
  await new Promise(resolve=>setTimeout(resolve,400));
  const input=await detail.$('textarea'); assert(input, '退款原因输入框未显示');
  await input.input('测试用申请');
  await (await detail.$('.submit-button')).tap();
  await new Promise(resolve=>setTimeout(resolve,600));
  state=await mini.evaluate(()=>{const p=getCurrentPages().slice(-1)[0];return {refund:p.$vm.order.refund_request.status,requests:wx.__qa.requests.filter(x=>x.path.endsWith('/refund-requests')).length};});
  assert.strictEqual(state.refund,'submitted');assert.strictEqual(state.requests,1);
  const missing=await mini.reLaunch('/pages/membership/order?order_no=Mmissing');
  await missing.waitFor(400);
  state=await mini.evaluate(()=>{const p=getCurrentPages().slice(-1)[0];return {order:p.$vm.order,error:p.$vm.error};});
  assert.strictEqual(state.order,null);assert(state.error.includes('未找到'));
  const invalid=await mini.reLaunch('/pages/membership/order?order_no=undefined');
  await invalid.waitFor(300);
  state=await mini.evaluate(()=>{const p=getCurrentPages().slice(-1)[0];return {invalid:p.$vm.invalidOrderNo,error:p.$vm.error};});
  assert.strictEqual(state.invalid,true);assert(state.error.includes('订单编号'));
  console.log('隔离模拟通过：列表跳转、订单展示、退款申请、无效订单提示');
 } finally {
  try {await mini.evaluate(()=>{if(wx.__qaOriginal){wx.login=wx.__qaOriginal.login;wx.request=wx.__qaOriginal.request;wx.showModal=wx.__qaOriginal.showModal;}delete wx.__qaOriginal;delete wx.__qa;});} catch(_) {}
  await mini.disconnect();
 }
})().catch(e=>{console.error('隔离模拟失败:',e.message);process.exitCode=1});
