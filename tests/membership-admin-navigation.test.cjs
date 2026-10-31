// Exercise the admin order-to-user navigation with isolated mocked data.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {JSDOM} = require('jsdom');
const dir = path.resolve(__dirname, '../backend/hivision-overlay');
const dom = new JSDOM(fs.readFileSync(path.join(dir, 'miniapp_admin.html'), 'utf8'), {url:'http://127.0.0.1:8091/', runScripts:'outside-only'});
const {window} = dom;
const calls = [];
window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
window.HTMLDialogElement.prototype.close = function () { this.open = false; };
window.fetch = async request => {
  calls.push(request);
  let data;
  if (request === '/api/settings') data = {refresh_seconds:0, page_size:20};
  else if (request === '/api/overview') data = {users:1, active_members:0, paid_orders:1, review_events:0, refund_requests:0, pending_orders:0};
  else if (request === '/api/service') data = {reachable:false, checks:[]};
  else if (request === '/api/orders/test-order') data = {order:{order_no:'test-order',user_ref:'1234567890abcdef',plan_name:'测试',months:1,price_fen:1200,status:'paid'}, events:[], grant:null};
  else if (request === '/api/users/1234567890abcdef') data = {user_ref:'1234567890abcdef',created_at:null,expires_at:null,orders:[],grants:[],adjustments:[]};
  else throw Error('Unexpected request: ' + request);
  return {ok:true, json:async () => data};
};
window.eval(fs.readFileSync(path.join(dir, 'miniapp_admin.js'), 'utf8') + '\nwindow.__showOrder = showOrder;');

(async () => {
  await new Promise(resolve => setTimeout(resolve, 30));
  await window.__showOrder('test-order');
  assert.strictEqual(window.document.getElementById('modal-title').textContent, '订单详情');
  window.document.getElementById('order-user').click();
  await new Promise(resolve => setTimeout(resolve, 30));
  assert.strictEqual(window.document.getElementById('modal-title').textContent, '用户详情');
  assert(window.document.getElementById('modal-subtitle').textContent.includes('1234567890abcdef'));
  assert(calls.includes('/api/users/1234567890abcdef'));
  console.log('隔离模拟通过：订单详情跳转至对应用户');
  dom.window.close();
})().catch(error => { console.error(error); dom.window.close(); process.exitCode = 1; });
