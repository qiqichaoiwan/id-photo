// Admin UI test with mocked responses. No real payment or refund is sent.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {JSDOM} = require('jsdom');
const dir = path.resolve(__dirname, '../backend/hivision-overlay');
const dom = new JSDOM(fs.readFileSync(path.join(dir, 'miniapp_admin.html'), 'utf8'), {url:'http://127.0.0.1:8091/', runScripts:'outside-only'});
const {window} = dom;
Object.defineProperty(window, 'crypto', {value:require('crypto').webcrypto});
let channel = 'wechat', submitted = null;
window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
window.HTMLDialogElement.prototype.close = function () { this.open = false; };
window.confirm = () => true;
window.fetch = async (request, options = {}) => {
  let data;
  if (request === '/api/settings') data = {refresh_seconds:0,page_size:20};
  else if (request === '/api/overview') data = {users:1,active_members:1,paid_orders:1,review_events:0,refund_requests:0,pending_orders:0};
  else if (request === '/api/service') data = {reachable:false,checks:[]};
  else if (request.startsWith('/api/orders?')) data = {orders:[],total:0,page:1,page_size:20};
  else if (request.startsWith('/api/refund-requests?')) data = {requests:[],total:0,page:1,page_size:20};
  else if (request.startsWith('/api/review-events?')) data = {events:[],total:0,page:1,page_size:20};
  else if (request === '/api/orders/test-order') data = {order:{order_no:'test-order',user_ref:'1234567890abcdef',plan_name:'测试',months:1,price_fen:1200,status:'paid',product_id:'test'},events:[],grant:null,refunds:[]};
  else if (request === '/api/orders/test-order/refund-quote') data = channel === 'ios'
    ? {channel:'ios',eligible:false,message:'此订单为 Apple 内购，请引导用户向 Apple 申请退款'}
    : {channel:'wechat',eligible:true,paid_fen:1200,left_fee:1200};
  else if (request === '/api/orders/test-order/refund') { submitted = JSON.parse(options.body); data = {state:'accepted'}; }
  else throw Error('Unexpected request: ' + request);
  return {ok:true,json:async () => data};
};
window.eval(fs.readFileSync(path.join(dir, 'miniapp_admin.js'), 'utf8') + '\nwindow.__showOrder = showOrder;');
const wait = () => new Promise(resolve => setTimeout(resolve, 60));

(async () => {
  await wait();
  await window.__showOrder('test-order');
  window.document.getElementById('prepare-refund').click();
  await wait();
  assert.strictEqual(window.document.getElementById('modal-title').textContent, '申请微信退款', window.document.getElementById('modal-error').textContent);
  window.document.getElementById('direct-refund-amount').value = '6.00';
  window.document.getElementById('direct-refund-note').value = '客服工单测试';
  window.document.getElementById('direct-refund-form').dispatchEvent(new window.Event('submit', {bubbles:true,cancelable:true}));
  await wait();
  assert.strictEqual(submitted.amount_fen, 600);
  assert.strictEqual(submitted.expected_left_fen, 1200);
  assert.match(submitted.request_key, /^[a-f0-9]{32}$/);
  assert.strictEqual(window.document.getElementById('modal-title').textContent, '订单详情');
  channel = 'ios';
  window.document.getElementById('prepare-refund').click();
  await wait();
  assert(window.document.getElementById('modal-body').textContent.includes('Apple'));
  assert(!window.document.getElementById('direct-refund-form'));
  console.log('隔离模拟通过：退款金额提交、订单跳转和 Apple 渠道提示');
  dom.window.close();
})().catch(error => { console.error(error); dom.window.close(); process.exitCode = 1; });
