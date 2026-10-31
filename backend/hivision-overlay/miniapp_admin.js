'use strict';
const $ = id => document.getElementById(id);
if (!['127.0.0.1', 'localhost', '[::1]'].includes(location.hostname)) {
  $('access-mode').textContent = '安全远程访问';
  $('access-detail').textContent = '身份验证与加密连接';
  $('footer-label').textContent = '小七快照拍 · 运营后台';
}
const state = { view: 'overview', settings: { refresh_seconds: 30, page_size: 20 }, page: { users: 1, orders: 1, refunds: 1, events: 1, audit: 1 }, plans: [], service: null, timer: null };
const viewInfo = {
  overview: ['运营概览', '在这里查看会员、订单和服务运行情况。'],
  service: ['服务监控', '查看照片服务状态和接口运行统计。'],
  users: ['用户与会员', '查询会员状态、权益记录和订单。'],
  plans: ['会员套餐', '维护套餐与微信商品的关联。'],
  orders: ['订单与退款', '查询订单，并处理需要人工核对的事件。'],
  audit: ['操作日志', '查看管理员操作记录。'],
  settings: ['系统设置', '设置后台工作台并查看运行配置。']
};
const labels = {ok:'正常', degraded:'受影响', unavailable:'不可用', unknown:'待确认', disabled:'未开放', active:'生效中', expired:'已到期', none:'未开通', pending:'确认中', paid:'已发放', closed:'已关闭', draft:'草稿', archived:'已归档', manual_review:'待人工核对', refund_failed:'退款失败', unhandled:'待处理', resolved:'已处理'};
const routeNames = {'/idphoto':'证件照制作','/idphoto_crop':'证件照裁剪','/human_matting':'人像抠图','/convert_image':'格式转换','/add_background':'证件照换底','/generate_layout_photos':'照片排版','/watermark':'图片水印','/set_kb':'图片压缩','/auth/wechat':'微信登录','/membership/status':'会员状态','/membership/plans':'会员套餐'};
const actionNames = {create_plan:'创建套餐',edit_plan:'编辑套餐',activate_plan:'上架套餐',adjust_member:'调整会员',resolve_refund:'核对事件',update_refund_request:'处理退款申请',acknowledge_event:'核查事件',start_refund:'发起退款',review_refund:'核对退款',refresh_refund:'查询退款单',refresh_order:'微信查单',update_settings:'修改设置'};
const refundLabels = {submitted:'待处理', processing:'处理中', closed:'已处理'};
const refundStates = {dispatching:'提交中', accepted:'微信已受理', unknown:'结果待核对', notice_success:'微信通知成功 · 待核对', notice_failed:'微信通知失败 · 待核对', confirmed:'已人工核实退款', not_refunded:'已核实未退款'};
const refundReviewable = ['dispatching','accepted','unknown','notice_success','notice_failed'];
const wechatRefundStatus = {0:'初始化',1:'创建成功',2:'已支付待发货',3:'发货中',4:'已发货',5:'已经退款',6:'已关闭',7:'退款失败',8:'用户退款完成',9:'回收广告金完成',10:'分账回退完成'};
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const badge = value => `<span class="badge ${escapeHtml(value)}">${escapeHtml(labels[value] || value || '未知')}</span>`;
const serviceBadge = item => item?.id === 'payment' && item.state === 'unknown'
  ? '<span class="badge unknown">已开放 · 待验证</span>'
  : badge(item?.state || 'unknown');
const money = value => '¥' + (Number(value) / 100).toFixed(2);
function dateTime(value) {
  if (!value) return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '时间异常';
  return new Intl.DateTimeFormat('zh-CN', {timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(parsed);
}
async function api(path, options = {}) {
  const response = await fetch(path, {cache:'no-store', ...options, headers: {'Accept':'application/json', 'X-Admin-Request':'1', ...(options.body ? {'Content-Type':'application/json'} : {}), ...options.headers}});
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `请求失败（${response.status}）`);
  return data;
}
function showError(error) { $('app-alert').textContent = error.message || '请求失败，请稍后重试'; $('app-alert').hidden = false; }
function clearError() { $('app-alert').hidden = true; }
function toast(message) { $('toast').textContent = message; $('toast').hidden = false; clearTimeout(toast.timer); toast.timer = setTimeout(() => $('toast').hidden = true, 3000); }
function openModal(title, subtitle, body) { $('modal-title').textContent = title; $('modal-subtitle').textContent = subtitle; $('modal-body').innerHTML = body; if (!$('modal').open) $('modal').showModal(); }
function modalError(error) { const node = $('modal-error'); if (node) node.textContent = error.message; else showError(error); }
$('modal-close').addEventListener('click', () => $('modal').close());
$('modal').addEventListener('click', e => { if (e.target === $('modal')) $('modal').close(); });
function paginate(id, key, data, reload) {
  const totalPages = Math.max(1, Math.ceil(data.total / data.page_size));
  $(id).innerHTML = `<span>共 ${data.total} 条 · ${data.page} / ${totalPages} 页</span><button class="button secondary" data-page="prev" ${data.page <= 1 ? 'disabled' : ''}>上一页</button><button class="button secondary" data-page="next" ${data.page >= totalPages ? 'disabled' : ''}>下一页</button>`;
  $(id).querySelectorAll('button').forEach(button => button.addEventListener('click', () => { state.page[key] += button.dataset.page === 'prev' ? -1 : 1; run(reload); }));
}
function showRows(rowsId, emptyId, rows, markup, empty = '暂无数据') {
  $(rowsId).innerHTML = rows.map(markup).join('');
  $(emptyId).hidden = rows.length > 0;
  $(emptyId).textContent = empty;
}
function params(values) { const query = new URLSearchParams(); Object.entries(values).forEach(([k,v]) => { if (v !== '' && v !== null && v !== false) query.set(k, String(v)); }); return query.toString(); }
function run(fn) { Promise.resolve().then(fn).catch(showError); }
function navigate(view) {
  if (!viewInfo[view]) return;
  state.view = view;
  document.querySelectorAll('.view').forEach(node => node.hidden = node.id !== 'view-' + view);
  document.querySelectorAll('[data-nav]').forEach(node => { const active = node.dataset.nav === view; node.classList.toggle('active', active); if (active) node.setAttribute('aria-current','page'); else node.removeAttribute('aria-current'); });
  $('page-title').textContent = viewInfo[view][0]; $('page-description').textContent = viewInfo[view][1]; clearError();
  run(loadCurrent);
}
document.addEventListener('click', event => { const target = event.target.closest('[data-nav], [data-go]'); if (target) navigate(target.dataset.nav || target.dataset.go); });
$('refresh-page').addEventListener('click', () => run(loadCurrent));
function updated() { $('last-updated').textContent = '更新于 ' + dateTime(new Date().toISOString()); }
function updateReviewCount(count) { $('nav-review').hidden = !count; $('nav-review').textContent = count > 99 ? '99+' : count; }
async function loadCurrent() {
  clearError();
  const loaders = {overview:loadOverview, service:loadServicePage, users:loadUsers, plans:loadPlans, orders:loadOrdersPage, audit:loadAudit, settings:loadSettingsPage};
  await loaders[state.view](); updated();
}
function renderOverviewService(service) {
  if (!service.reachable) return '<div class="status-row"><span class="status-label"><span class="dot unavailable"></span>本机照片服务未响应</span>' + badge('unavailable') + '</div>';
  const publicState = service.public?.reachable ? service.public.status : 'unavailable';
  return `<div class="status-row"><span class="status-label"><span class="dot ${escapeHtml(publicState)}"></span>公网连接</span>${badge(publicState)}</div>` + service.checks.filter(item => ['photo','matting','membership','payment','push'].includes(item.id)).map(item => `<div class="status-row"><span class="status-label"><span class="dot ${escapeHtml(item.state)}"></span>${escapeHtml(item.name)}</span>${serviceBadge(item)}</div>`).join('');
}
async function loadOverview() {
  const [data, service] = await Promise.all([api('/api/overview'), api('/api/service')]); state.service = service;
  const pendingWork = data.review_events + data.refund_requests;
  const stats = [['累计用户',data.users,'登录过或有业务记录','♙','blue'],['有效会员',data.active_members,'当前未到期','◇','rose'],['已发放订单',data.paid_orders,'本地记录，非结算收入','✓','green'],['待处理事项',pendingWork,'申请和支付事件需人工处理','!','gold']];
  $('overview-stats').innerHTML = stats.map(item => `<article class="stat-card"><div class="stat-top"><span>${item[0]}</span><span class="stat-icon ${item[4]}">${item[3]}</span></div><div class="stat-value">${item[1]}</div><div class="stat-hint">${item[2]}</div></article>`).join('');
  $('overview-service').innerHTML = renderOverviewService(service); $('overview-service').classList.remove('loading');
  $('overview-tasks').innerHTML = `<div class="task-row"><div class="task-copy"><strong>${pendingWork ? '有 ' + pendingWork + ' 条待处理事项' : '暂无待处理事项'}</strong><small>${data.refund_requests} 条用户申请 · ${data.review_events} 条支付事件</small></div><button class="text-button" data-go="orders">查看 →</button></div><div class="task-row"><div class="task-copy"><strong>${data.pending_orders} 笔订单确认中</strong><small>可在订单页查询微信状态</small></div><button class="text-button" data-go="orders">查看 →</button></div><div class="task-row"><div class="task-copy"><strong>会员套餐管理</strong><small>创建、编辑并核对商品</small></div><button class="text-button" data-go="plans">前往 →</button></div>`; $('overview-tasks').classList.remove('loading');
  updateReviewCount(pendingWork);
}
async function loadServicePage() {
  const [service, metrics] = await Promise.all([api('/api/service'), api('/api/metrics?days=7')]); state.service = service;
  $('service-time').textContent = '检查时间：' + dateTime(service.checked_at) + '（北京时间）'; $('service-overall').innerHTML = badge(service.reachable ? service.status : 'unavailable');
  const publicState = service.public?.reachable ? service.public.status : 'unavailable';
  const publicDetail = service.public?.reachable ? '本机已通过公网域名连接；不代表所有地区网络均正常。' : (service.public?.note || '公网连接暂不可用');
  const publicCard = `<div class="check-item"><div class="check-item-header"><span class="status-label"><span class="dot ${escapeHtml(publicState)}"></span>公网连接</span>${badge(publicState)}</div><p>${escapeHtml(publicDetail)}</p></div>`;
  $('service-checks').classList.remove('loading'); $('service-checks').innerHTML = publicCard + (service.reachable ? service.checks.map(item => `<div class="check-item"><div class="check-item-header"><span class="status-label"><span class="dot ${escapeHtml(item.state)}"></span>${escapeHtml(item.name)}</span>${serviceBadge(item)}</div><p>${escapeHtml(item.detail)}</p></div>`).join('') : '<div class="check-item"><div class="check-item-header">本机照片服务 ' + badge('unavailable') + '</div><p>本机服务未响应，请检查服务和网络。</p></div>');
  $('service-note').textContent = service.note || '';
  const grouped = new Map(); metrics.rows.forEach(row => { const item = grouped.get(row.route) || {route:row.route,total:0,success:0,client:0,server:0,duration:0,max:0}; item.total += row.count; item.duration += row.duration_ms; item.max = Math.max(item.max,row.max_ms); if(row.status_class === 2)item.success += row.count; if(row.status_class === 4)item.client += row.count; if(row.status_class === 5)item.server += row.count; grouped.set(row.route,item); });
  showRows('metric-rows','metric-empty',[...grouped.values()], item => `<tr><td>${escapeHtml(routeNames[item.route] || item.route)}</td><td>${item.total}</td><td>${item.success}</td><td>${item.client}</td><td>${item.server}</td><td>${Math.round(item.duration/item.total)} ms</td><td>${item.max} ms</td></tr>`, metrics.available ? '暂无监控数据，调用接口后会开始记录。' : '监控数据暂不可读取。');
  $('metric-note').textContent = (metrics.first_observed_at ? '最早保留记录：' + dateTime(metrics.first_observed_at) + '（北京时间）。' : '') + ' 统计为尽力记录，服务停止或繁忙时少量记录可能丢失。';
}
async function loadUsers() {
  const data = await api('/api/users?' + params({page:state.page.users,page_size:state.settings.page_size,search:$('user-search').value.trim(),status:$('user-status').value}));
  showRows('user-rows','user-empty',data.users, u => `<tr><td class="mono">${escapeHtml(u.user_ref)}</td><td>${escapeHtml(dateTime(u.created_at))}</td><td>${badge(u.member_status)}</td><td>${escapeHtml(dateTime(u.expires_at))}</td><td>${u.order_count}</td><td>${u.review_count || '—'}</td><td><button class="text-button" data-user="${escapeHtml(u.user_ref)}">查看详情</button></td></tr>`, '没有符合条件的用户');
  $('user-rows').querySelectorAll('[data-user]').forEach(b => b.onclick = () => run(() => showUser(b.dataset.user)));
  paginate('user-pagination','users',data,loadUsers);
}
$('user-filter').addEventListener('submit', e => { e.preventDefault(); state.page.users = 1; run(loadUsers); });
$('user-filter').addEventListener('reset', () => { state.page.users = 1; setTimeout(() => run(loadUsers), 0); });
async function showUser(ref) {
  const user = await api('/api/users/' + encodeURIComponent(ref));
  const orders = user.orders.map(o => `<div class="history-item"><strong>${escapeHtml(o.plan_name)} · ${money(o.price_fen)} · ${escapeHtml(labels[o.status] || o.status)}</strong><br>${escapeHtml(o.order_no)} · ${escapeHtml(dateTime(o.created_at))}${o.review_needed ? ' · 待核对' : ''}</div>`).join('') || '<p class="muted">暂无订单</p>';
  const grants = user.grants.map(g => `<div class="history-item"><strong>订单发放 · ${escapeHtml(g.order_no)}</strong><br>${escapeHtml(dateTime(g.start_at))} 至 ${escapeHtml(dateTime(g.expires_at))}</div>`).join('');
  const changes = user.adjustments.map(a => `<div class="history-item"><strong>${a.source === 'refund_review' ? '退款核对调整' : '管理员调整'} · ${escapeHtml(dateTime(a.created_at))}</strong><br>${escapeHtml(dateTime(a.previous_expires_at))} → ${escapeHtml(dateTime(a.new_expires_at))}<br>原因：${escapeHtml(a.reason)}</div>`).join('');
  openModal('用户详情', '匿名编号 ' + ref + ' · 时间为北京时间', `<div class="modal-content"><div class="detail-grid"><div><small>首次登录</small><strong>${escapeHtml(dateTime(user.created_at))}</strong></div><div><small>会员到期时间</small><strong>${escapeHtml(dateTime(user.expires_at))}</strong></div></div><section class="modal-section"><h3>人工调整会员</h3><p class="footnote">调整会立即生效并记录原因，不会创建支付订单。延长从当前有效期或现在开始，按自然月计算。</p><form id="adjust-form"><div class="form-grid"><label>调整方式<select id="adjust-mode"><option value="extend">延长自然月</option><option value="set">指定到期时间</option></select></label><label id="adjust-month-label">延长月数<input id="adjust-months" type="number" min="1" max="120" value="1"></label><label id="adjust-date-label" hidden>新到期时间（北京时间）<input id="adjust-date" type="datetime-local"></label><label class="full">调整原因<input id="adjust-reason" maxlength="200" minlength="2" required placeholder="例如：客服补发及工单编号"></label></div><p id="modal-error" class="modal-error" role="alert"></p><div class="modal-actions"><button type="submit" class="button primary">保存会员调整</button></div></form></section><section class="modal-section"><h3>权益流水（最近 100 条）</h3>${grants || changes ? grants + changes : '<p class="muted">暂无记录</p>'}</section><section class="modal-section"><h3>关联订单（最近 100 条）</h3>${orders}</section></div>`);
  $('adjust-mode').onchange = () => { const byDate = $('adjust-mode').value === 'set'; $('adjust-month-label').hidden = byDate; $('adjust-date-label').hidden = !byDate; };
  $('adjust-form').onsubmit = async e => { e.preventDefault(); const mode = $('adjust-mode').value, local = $('adjust-date').value; if(mode === 'set' && !local) { modalError(Error('请选择到期时间')); return; } const body = {mode, months:mode === 'extend' ? Number($('adjust-months').value) : null, new_expires_at:mode === 'set' ? local + ':00+08:00' : null, expected_expires_at:user.expires_at, reason:$('adjust-reason').value.trim()}; if (!confirm('确认调整该用户会员到期时间？此操作会立即生效并记录原因。')) return; try { await api('/api/users/'+encodeURIComponent(ref)+'/adjust',{method:'POST',body:JSON.stringify(body)}); toast('会员时间已调整'); await showUser(ref); await loadUsers(); } catch(error) { modalError(error); } };
}
async function loadPlans() {
  state.plans = await api('/api/plans');
  showRows('plan-rows','plan-empty',state.plans,p => `<tr><td><strong>${escapeHtml(p.name)}</strong><br><span class="muted">${escapeHtml(p.description || '会员免广告保存')}</span></td><td>${p.months} 个月</td><td>${money(p.price_fen)}</td><td class="mono">${escapeHtml(p.wechat_product_id || '未填写')}</td><td>${p.sort_order}</td><td>${badge(p.status)}</td><td><button class="text-button" data-edit="${p.id}">编辑</button>${p.status === 'draft' && p.wechat_product_id ? `　<button class="text-button" data-activate="${p.id}">核对并上架</button>` : ''}</td></tr>`, '暂无套餐');
  $('plan-rows').querySelectorAll('[data-edit]').forEach(b => b.onclick = () => editPlan(state.plans.find(p => p.id === Number(b.dataset.edit))));
  $('plan-rows').querySelectorAll('[data-activate]').forEach(b => b.onclick = () => run(() => activatePlan(state.plans.find(p => p.id === Number(b.dataset.activate)))));
}
$('add-plan').onclick = () => editPlan(null);
function editPlan(plan) {
  openModal(plan ? '编辑套餐' : '新增套餐', '保存为草稿或归档；已上架套餐编辑后将退回草稿。', `<div class="modal-content"><form id="plan-form"><div class="form-grid"><label>套餐名称<input id="plan-name" maxlength="40" required value="${escapeHtml(plan?.name || '')}"></label><label>时长（自然月）<input id="plan-months" type="number" min="1" max="120" required value="${plan?.months || 1}"></label><label>价格（元）<input id="plan-price" inputmode="decimal" required value="${plan ? (plan.price_fen/100).toFixed(2) : ''}" placeholder="例如 12.00"></label><label>微信商品 ID<input id="plan-product" maxlength="64" value="${escapeHtml(plan?.wechat_product_id || '')}" placeholder="可稍后填写"></label><label>套餐说明<input id="plan-description" maxlength="100" value="${escapeHtml(plan?.description || '会员免广告保存')}"></label><label>排序<input id="plan-sort" type="number" min="0" max="10000" value="${plan?.sort_order || 0}"></label><label>状态<select id="plan-status"><option value="draft">草稿</option><option value="archived" ${plan?.status === 'archived' ? 'selected' : ''}>归档</option></select></label></div><p id="modal-error" class="modal-error" role="alert"></p><div class="modal-actions"><button type="button" class="button secondary" id="cancel-plan">取消</button><button class="button primary" type="submit">保存套餐</button></div></form></div>`);
  $('cancel-plan').onclick = () => $('modal').close();
  $('plan-form').onsubmit = async e => { e.preventDefault(); const price = $('plan-price').value.trim(); if (!/^\d{1,6}(\.\d{1,2})?$/.test(price)) { modalError(Error('请输入有效价格，最多两位小数')); return; } const [whole, decimal=''] = price.split('.'); const body = {name:$('plan-name').value,months:Number($('plan-months').value),price_fen:Number(whole)*100+Number(decimal.padEnd(2,'0')),wechat_product_id:$('plan-product').value.trim(),description:$('plan-description').value,sort_order:Number($('plan-sort').value),status:$('plan-status').value}; try { await api(plan ? '/api/plans/'+plan.id : '/api/plans',{method:plan ? 'PUT':'POST',body:JSON.stringify(body)}); $('modal').close(); toast('套餐已保存'); await loadPlans(); } catch(error) { modalError(error); } };
}
async function activatePlan(plan) { if (!confirm(`请确认微信后台商品 ${plan.wechat_product_id} 已发布，价格为 ${money(plan.price_fen)}。支付总开关开启后用户可购买。`)) return; await api('/api/plans/'+plan.id+'/activate',{method:'POST',body:JSON.stringify({product_id:plan.wechat_product_id,price_fen:plan.price_fen,published:true})}); toast('套餐已上架'); await loadPlans(); }
async function loadOrdersPage() { const [, , , overview] = await Promise.all([loadOrders(), loadRefundRequests(), loadEvents(), api('/api/overview')]); updateReviewCount(overview.review_events + overview.refund_requests); }
async function loadOrders() {
  const data = await api('/api/orders?' + params({page:state.page.orders,page_size:state.settings.page_size,order_no:$('order-search').value.trim(),status:$('order-status').value,date_from:$('order-from').value,date_to:$('order-to').value,review:$('order-review').checked}));
  showRows('order-rows','order-empty',data.orders,o => `<tr><td class="mono">${escapeHtml(o.order_no)}</td><td>${escapeHtml(o.plan_name)}</td><td>${money(o.price_fen)}</td><td>${badge(o.status)}</td><td>${escapeHtml(dateTime(o.created_at))}</td><td>${o.review_needed ? badge('manual_review') : '—'}</td><td><button class="text-button" data-order="${escapeHtml(o.order_no)}">详情</button></td></tr>`, '没有符合条件的订单');
  $('order-rows').querySelectorAll('[data-order]').forEach(b => b.onclick = () => run(() => showOrder(b.dataset.order)));
  paginate('order-pagination','orders',data,loadOrders);
}
$('order-filter').addEventListener('submit', e => { e.preventDefault(); state.page.orders=1; run(loadOrders); });
$('order-filter').addEventListener('reset', () => { state.page.orders=1; setTimeout(() => run(loadOrders),0); });
async function showOrder(number) {
  const data = await api('/api/orders/'+encodeURIComponent(number)), o = data.order;
  const events = data.events.map(e => `<div class="history-item"><strong>${escapeHtml(e.event_type)} · ${escapeHtml(labels[e.state] || e.state)}</strong><br>${escapeHtml(dateTime(e.created_at))} · ${escapeHtml(e.details || '无补充说明')}</div>`).join('') || '<p class="muted">暂无支付事件</p>';
  const refunds = (data.refunds || []).map(r => `<div class="history-item"><strong>${escapeHtml(refundStates[r.state] || r.state)} · ${money(r.amount_fen)}</strong><br>退款单：<span class="mono">${escapeHtml(r.refund_id)}</span>${r.wx_refund_id ? '<br>微信退款号：<span class="mono">' + escapeHtml(r.wx_refund_id) + '</span>' : ''}<br>${escapeHtml(r.detail || '正在提交')} · ${escapeHtml(dateTime(r.updated_at))}${r.query_status !== null && r.query_status !== undefined ? '<br>微信退款单状态：' + escapeHtml(wechatRefundStatus[r.query_status] || String(r.query_status)) + ' · ' + escapeHtml(dateTime(r.query_checked_at)) : ''}${refundReviewable.includes(r.state) ? `<br><button class="text-button" data-refund-refresh="${escapeHtml(r.refund_id)}">向微信查退款单</button>　<button class="text-button" data-refund-review="${escapeHtml(r.refund_id)}">登记核对结果 →</button>` : ''}</div>`).join('') || '<p class="muted">暂无后台发起的退款</p>';
  openModal('订单详情','订单金额为本地快照，实际结算以微信账单为准。',`<div class="modal-content"><div class="detail-grid"><div><small>订单号</small><strong class="mono">${escapeHtml(o.order_no)}</strong></div><div><small>用户编号</small><strong class="mono">${escapeHtml(o.user_ref)}</strong></div><div><small>套餐</small><strong>${escapeHtml(o.plan_name)} · ${o.months} 个月</strong></div><div><small>金额 / 状态</small><strong>${money(o.price_fen)} · ${escapeHtml(labels[o.status] || o.status)}</strong></div><div><small>微信商品 ID</small><strong>${escapeHtml(o.product_id || '未关联')}</strong></div><div><small>微信订单号</small><strong class="mono">${escapeHtml(o.platform_order_id || '未记录')}</strong></div><div><small>创建时间</small><strong>${escapeHtml(dateTime(o.created_at))}</strong></div><div><small>权益到期时间</small><strong>${escapeHtml(dateTime(o.expires_at))}</strong></div></div><section class="modal-section"><h3>权益发放</h3><p class="muted">${data.grant ? escapeHtml(dateTime(data.grant.start_at)) + ' 至 ' + escapeHtml(dateTime(data.grant.expires_at)) : '暂无权益发放记录'}</p></section><section class="modal-section"><h3>后台退款记录</h3>${refunds}</section><section class="modal-section"><h3>关联支付事件</h3>${events}</section><p id="modal-error" class="modal-error" role="alert"></p><div class="modal-actions"><button id="prepare-refund" class="button danger" ${o.status === 'paid' && o.product_id ? '' : 'disabled'}>申请退款</button><button id="order-user" class="button secondary">查看该用户</button><button id="query-order" class="button secondary" ${o.product_id ? '' : 'disabled'}>向微信查单</button><button id="close-order" class="button primary">完成</button></div></div>`);
  $('close-order').onclick = () => $('modal').close();
  $('prepare-refund').onclick = async () => { const button = $('prepare-refund'); button.disabled = true; try { await showRefundForm(number); } catch(error) { modalError(error); button.disabled = false; } };
  $('modal-body').querySelectorAll('[data-refund-review]').forEach(button => button.onclick = () => showRefundReview((data.refunds || []).find(item => item.refund_id === button.dataset.refundReview)));
  $('modal-body').querySelectorAll('[data-refund-refresh]').forEach(button => button.onclick = async () => { button.disabled = true; try { await api('/api/refunds/' + encodeURIComponent(button.dataset.refundRefresh) + '/refresh', {method:'POST'}); await showOrder(number); } catch(error) { modalError(error); button.disabled = false; } });
  $('order-user').onclick = async () => {
    const button = $('order-user');
    button.disabled = true;
    try { await showUser(o.user_ref); }
    catch(error) { modalError(error); button.disabled = false; }
  };
  $('query-order').onclick = async () => { if (!confirm('将向微信查询订单并按现有规则核验及补发权益，是否继续？')) return; $('query-order').disabled = true; try { await api('/api/orders/'+encodeURIComponent(number)+'/refresh',{method:'POST'}); toast('已完成查单'); await showOrder(number); await loadOrders(); } catch(error) { modalError(error); $('query-order').disabled = false; } };
}
async function showRefundForm(number) {
  const quote = await api('/api/orders/' + encodeURIComponent(number) + '/refund-quote');
  if (!quote.eligible) {
    const apple = quote.channel === 'ios' ? '<p class="footnote">请让用户在 App Store 的购买记录中申请，或访问 Apple 的问题报告页面。退款结果由 Apple 决定。</p>' : '';
    openModal('核对退款', '微信订单核对结果', `<div class="modal-content"><p>${escapeHtml(quote.message || '当前无法发起退款')}</p>${apple}<p id="modal-error" class="modal-error" role="alert"></p><div class="modal-actions"><button id="refund-back" class="button secondary">返回订单</button></div></div>`);
    $('refund-back').onclick = () => run(() => showOrder(number));
    return;
  }
  const bytes = new Uint8Array(16);
  window.crypto.getRandomValues(bytes);
  const requestKey = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
  openModal('申请微信退款', '请核对订单、金额和原因。微信受理不代表退款完成。', `<div class="modal-content"><div class="detail-grid"><div><small>订单号</small><strong class="mono">${escapeHtml(number)}</strong></div><div><small>原支付金额</small><strong>${money(quote.paid_fen)}</strong></div><div><small>微信当前可退</small><strong>${money(quote.left_fee)}</strong></div><div><small>渠道</small><strong>普通虚拟支付</strong></div></div><p class="footnote">提交后请在退款记录中核对结果；会员到期时间不会自动改变。若结果不明，先去微信后台核对，避免重复退款。</p><form id="direct-refund-form"><div class="form-grid"><label>退款金额（元）<input id="direct-refund-amount" inputmode="decimal" value="${(quote.left_fee / 100).toFixed(2)}" required></label><label>退款原因<select id="direct-refund-reason"><option value="3">用户主动退款</option><option value="1">产品问题</option><option value="2">售后问题</option><option value="4">价格问题</option><option value="5">其他原因</option></select></label><label class="full">内部说明<input id="direct-refund-note" minlength="2" maxlength="200" placeholder="例如：客服工单编号及核对情况" required></label></div><p id="modal-error" class="modal-error" role="alert"></p><div class="modal-actions"><button type="button" id="refund-back" class="button secondary">返回订单</button><button type="submit" id="refund-submit" class="button danger">确认发起退款</button></div></form></div>`);
  $('refund-back').onclick = () => run(() => showOrder(number));
  $('direct-refund-form').onsubmit = async event => {
    event.preventDefault();
    const value = $('direct-refund-amount').value.trim(), note = $('direct-refund-note').value.trim();
    if (!/^\d{1,6}(\.\d{1,2})?$/.test(value) || note.length < 2) { modalError(Error('请输入有效退款金额和内部说明')); return; }
    const [whole, decimal=''] = value.split('.');
    const amount = Number(whole) * 100 + Number(decimal.padEnd(2, '0'));
    if (amount <= 0 || amount > quote.left_fee) { modalError(Error('退款金额须大于零且不超过当前可退金额')); return; }
    if (!confirm(`确认对订单 ${number} 发起 ${money(amount)} 的真实退款？请确认订单和金额。`)) return;
    const button = $('refund-submit'); button.disabled = true;
    try {
      const result = await api('/api/orders/' + encodeURIComponent(number) + '/refund', {method:'POST',body:JSON.stringify({request_key:requestKey,amount_fen:amount,expected_left_fen:quote.left_fee,reason_code:$('direct-refund-reason').value,note})});
      toast(refundStates[result.state] || '退款请求已记录');
      await showOrder(number);
      await loadOrdersPage();
    } catch(error) {
      modalError(Error((error.message || '请求失败') + '。请返回订单查看退款记录并重新核对，避免重复提交。'));
    }
  };
}
function showRefundReview(refund) {
  if (!refund) return;
  openModal('登记退款核对结果', '请先在微信公众平台核实这笔退款单的最终结果。', `<div class="modal-content"><p>订单：<span class="mono">${escapeHtml(refund.order_no)}</span><br>退款单：<span class="mono">${escapeHtml(refund.refund_id)}</span><br>金额：${money(refund.amount_fen)}<br>当前状态：${escapeHtml(refundStates[refund.state] || refund.state)}</p><p class="footnote">此处只登记你在微信平台核实的结果，不会发起或撤销退款，也不会自动调整会员。核实未退款后才可重新发起；结果不明时请保持待核对。</p><form id="direct-review-form"><label>微信平台最终结果<select id="direct-review-outcome"><option value="">请选择</option><option value="confirmed">已确认退款完成</option><option value="not_refunded">已确认未退款</option></select></label><label>核对记录<textarea id="direct-review-note" minlength="2" maxlength="200" required placeholder="记录微信平台状态及核对依据"></textarea></label><p id="modal-error" class="modal-error" role="alert"></p><div class="modal-actions"><button type="button" id="direct-review-back" class="button secondary">返回订单</button><button type="submit" id="direct-review-submit" class="button primary">保存核对结果</button></div></form></div>`);
  $('direct-review-back').onclick = () => run(() => showOrder(refund.order_no));
  $('direct-review-form').onsubmit = async event => {
    event.preventDefault();
    const outcome = $('direct-review-outcome').value, note = $('direct-review-note').value.trim();
    if (!outcome || note.length < 2) { modalError(Error('请选择平台最终结果并填写核对记录')); return; }
    if (!confirm(outcome === 'not_refunded' ? '确认已在微信平台核实此退款未发生？登记后可重新发起退款。' : '确认已在微信平台核实此退款完成？会员权益仍需人工处理。')) return;
    const button = $('direct-review-submit'); button.disabled = true;
    try { await api('/api/refunds/' + encodeURIComponent(refund.refund_id) + '/review',{method:'POST',body:JSON.stringify({outcome,note})}); toast('退款核对结果已保存'); await showOrder(refund.order_no); await loadOrdersPage(); }
    catch(error) { modalError(error); button.disabled = false; }
  };
}
async function loadEvents() {
  const data = await api('/api/review-events?' + params({page:state.page.events,page_size:state.settings.page_size,state:$('event-state').value}));
  $('event-list').classList.remove('loading'); $('event-list').innerHTML = data.events.map(e => `<div class="event-card"><div class="event-head"><strong>${escapeHtml(e.order_no || '未匹配订单')}</strong>${badge(e.state)}</div><p>${escapeHtml(e.event_type)} · ${escapeHtml(dateTime(e.created_at))}</p><p>${escapeHtml(e.details || '无补充说明')}</p>${(e.state === 'manual_review' && ['xpay_refund_notify','order_verification','xpay_goods_deliver_notify'].includes(e.event_type)) || ['refund_failed','unhandled'].includes(e.state) ? `<div class="event-actions"><button class="text-button" data-event="${escapeHtml(e.event_key)}">记录人工处理 →</button></div>` : ''}</div>`).join('') || '<div class="empty">暂无符合条件的事件</div>';
  $('event-list').querySelectorAll('[data-event]').forEach(b => b.onclick = () => reviewEvent(data.events.find(e => e.event_key === b.dataset.event)));
  paginate('event-pagination','events',data,loadEvents);
}
$('refund-state').onchange = () => { state.page.refunds=1; run(loadRefundRequests); };
async function loadRefundRequests() {
  const data = await api('/api/refund-requests?' + params({page:state.page.refunds,page_size:state.settings.page_size,state:$('refund-state').value}));
  $('refund-list').classList.remove('loading');
  $('refund-list').innerHTML = data.requests.map(r => `<div class="event-card"><div class="event-head"><strong>${escapeHtml(r.order_no)}</strong><span class="badge ${r.status === 'closed' ? 'closed' : 'manual_review'}">${escapeHtml(refundLabels[r.status] || r.status)}</span></div><p>${escapeHtml(r.plan_name)} · ${money(r.price_fen)} · 申请于 ${escapeHtml(dateTime(r.created_at))}</p><p>用户原因：${escapeHtml(r.reason)}</p>${r.response ? `<p>给用户的说明：${escapeHtml(r.response)}</p>` : ''}${r.status !== 'closed' ? `<div class="event-actions"><button class="text-button" data-refund="${r.id}">处理申请 →</button></div>` : ''}</div>`).join('') || '<div class="empty">暂无符合条件的退款申请</div>';
  $('refund-list').querySelectorAll('[data-refund]').forEach(b => b.onclick = () => reviewRefundRequest(data.requests.find(r => String(r.id) === b.dataset.refund)));
  paginate('refund-pagination','refunds',data,loadRefundRequests);
}
function reviewRefundRequest(request) {
  openModal('处理用户退款申请', '可查看订单并核对退款；下方表单只记录申请进度。', `<div class="modal-content"><p>订单：<span class="mono">${escapeHtml(request.order_no)}</span><br>用户原因：${escapeHtml(request.reason)}</p><p class="footnote">所有渠道都可在小程序内提交申请。Apple 内购请协助用户核实并说明 Apple 退款方式，退款结果由 Apple 决定；普通虚拟支付可进入订单详情核对并申请退款。退款完成后的会员权益按支付事件人工核对。</p><form id="refund-form"><div class="form-grid"><label class="full">申请状态<select id="refund-update-status"><option value="processing">处理中</option><option value="closed">已处理</option></select></label><label class="full">给用户的处理说明（结束申请时必填）<textarea id="refund-response" maxlength="200">${escapeHtml(request.response || '')}</textarea></label><label class="full">内部处理记录（不会显示给用户）<textarea id="refund-note" minlength="2" maxlength="200" required></textarea></label></div><p id="modal-error" class="modal-error" role="alert"></p><div class="modal-actions"><button type="button" id="refund-view-order" class="button secondary">查看订单并申请退款</button><button type="submit" class="button primary">保存处理记录</button></div></form></div>`);
  $('refund-view-order').onclick = () => run(() => showOrder(request.order_no));
  $('refund-form').onsubmit = async e => { e.preventDefault(); const body = {status:$('refund-update-status').value,response:$('refund-response').value.trim(),note:$('refund-note').value.trim()}; if (body.status === 'closed' && body.response.length < 2) { modalError(Error('结束申请时请填写给用户的处理说明')); return; } try { await api('/api/refund-requests/'+request.id+'/update',{method:'POST',body:JSON.stringify(body)}); $('modal').close(); toast('处理记录已保存'); await loadOrdersPage(); } catch(error) { modalError(error); } };
}
$('event-state').onchange = () => { state.page.events=1; run(loadEvents); };
function reviewEvent(event) {
  if (['refund_failed','unhandled'].includes(event.state)) {
    openModal('记录事件核查', '请先核对微信平台记录。此操作只记录处理结果，不会更改支付或会员。', `<div class="modal-content"><form id="ack-form"><label>核查结论<textarea id="ack-note" minlength="2" maxlength="200" required></textarea></label><p id="modal-error" class="modal-error" role="alert"></p><div class="modal-actions"><button type="submit" class="button primary">保存核查记录</button></div></form></div>`);
    $('ack-form').onsubmit = async e => { e.preventDefault(); const note = $('ack-note').value.trim(); if (!confirm('确认记录此事件已核查？')) return; try { await api('/api/review-events/'+encodeURIComponent(event.event_key)+'/acknowledge',{method:'POST',body:JSON.stringify({note})}); $('modal').close(); toast('核查记录已保存'); await loadOrdersPage(); } catch(error) { modalError(error); } };
    return;
  }
  openModal('记录人工核对','请先与微信平台订单、退款记录核对。填写新到期时间时会同步调整会员。',`<div class="modal-content"><form id="review-form"><div class="form-grid"><label class="full">本地订单号<input id="review-order" maxlength="128" required value="${escapeHtml(event.order_no || '')}"></label><label class="full">核对结论与处理记录<textarea id="review-note" maxlength="200" required></textarea></label><label class="full">新的会员到期时间（北京时间，留空表示不调整）<input id="review-date" type="datetime-local"></label><div class="full"><button type="button" class="button secondary" id="review-load">读取当前会员时间</button><p class="footnote" id="review-member">如需调整到期时间，请先读取并核对当前会员时间。</p></div></div><p id="modal-error" class="modal-error" role="alert"></p><div class="modal-actions"><button type="submit" class="button primary">保存核对记录</button></div></form></div>`);
  let snapshot = null;
  $('review-order').oninput = () => { snapshot = null; $('review-member').textContent = '订单号已变化，请重新读取会员时间。'; };
  $('review-load').onclick = async () => { const number = $('review-order').value.trim(); if (!number) { modalError(Error('请先填写订单号')); return; } try { const order = await api('/api/orders/'+encodeURIComponent(number)); const user = await api('/api/users/'+encodeURIComponent(order.order.user_ref)); if ($('review-order').value.trim() !== number) return; if (!user.expires_at) throw Error('该用户没有可调整的会员记录'); snapshot = {number, expiry:user.expires_at}; $('review-member').textContent = '当前会员到期：' + dateTime(user.expires_at) + '（北京时间）'; $('modal-error').textContent = ''; } catch(error) { snapshot = null; modalError(error); } };
  $('review-form').onsubmit = async e => { e.preventDefault(); const local = $('review-date').value, number = $('review-order').value.trim(); if (local && (!snapshot || snapshot.number !== number)) { modalError(Error('调整会员时间前，请先读取并核对当前会员时间')); return; } const body = {order_no:number,note:$('review-note').value.trim(),new_expires_at:local ? local+':00+08:00' : null, expected_expires_at:local ? snapshot.expiry : null}; if (!confirm('确认保存核对结论及填写的会员时间调整？')) return; try { await api('/api/refund-events/'+encodeURIComponent(event.event_key)+'/resolve',{method:'POST',body:JSON.stringify(body)}); $('modal').close(); toast('核对记录已保存'); await loadOrdersPage(); } catch(error) { if (error.message.includes('会员到期时间已变化')) { snapshot = null; $('review-member').textContent = '会员时间已变化，请重新读取。'; } modalError(error); } };
}
async function loadAudit() {
  const data = await api('/api/audit?' + params({page:state.page.audit,page_size:state.settings.page_size}));
  showRows('audit-rows','audit-empty',data.records,a => `<tr><td>${escapeHtml(dateTime(a.created_at))}</td><td>${escapeHtml(actionNames[a.action] || a.action)}</td><td class="mono">${escapeHtml(a.target)}</td><td>${escapeHtml(a.details)}</td></tr>`, '暂无管理员操作记录');
  paginate('audit-pagination','audit',data,loadAudit);
}
async function loadSettingsPage() { const [settings, service] = await Promise.all([api('/api/settings'),api('/api/service')]); state.settings = settings; state.service = service; $('settings-refresh').value = String(settings.refresh_seconds); $('settings-page-size').value = String(settings.page_size); const payment = service.checks.find(item => item.id === 'payment'); $('settings-runtime').classList.remove('loading'); $('settings-runtime').innerHTML = `<span>会员购买</span>${serviceBadge(payment)}`; }
$('settings-form').onsubmit = async e => { e.preventDefault(); try { state.settings = await api('/api/settings',{method:'PUT',body:JSON.stringify({refresh_seconds:Number($('settings-refresh').value),page_size:Number($('settings-page-size').value)})}); Object.keys(state.page).forEach(key => state.page[key]=1); scheduleRefresh(); toast('设置已保存并生效'); } catch(error) { showError(error); } };
function scheduleRefresh() { clearInterval(state.timer); if (state.settings.refresh_seconds) state.timer = setInterval(() => { if (!document.hidden && !$('modal').open && ['overview','service'].includes(state.view)) run(loadCurrent); }, state.settings.refresh_seconds*1000); }
(async function init() { try { state.settings = await api('/api/settings'); scheduleRefresh(); navigate('overview'); } catch(error) { showError(error); } })();
