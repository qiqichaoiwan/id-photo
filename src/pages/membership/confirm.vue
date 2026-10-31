<template><view class="page"><InlineState v-if="loading" kind="loading" title="正在加载套餐" description="请稍候" /><InlineState v-else-if="!plan" kind="error" title="套餐暂不可用" description="请稍后重新加载" action-text="重新加载" @action="load" /><template v-else><view class="card"><view class="order-head"><text>{{ plan.name }}</text><text class="price">¥{{ price(plan.price_fen) }}</text></view><view class="row"><text>会员时长</text><text>{{ plan.months }}个月</text></view><view class="row"><text>会员权益</text><text>免广告保存</text></view><view class="row"><text>续费规则</text><text>按自然月叠加</text></view><view class="row"><text>购买方式</text><text>单次购买</text></view></view><view v-if="sandbox" class="note">沙箱模式：仅用于 Android 测试，不产生正式会员。</view><view class="note">ⓘ 不自动续费，到期后可手动续费</view><view v-if="plan.status !== 'active'" class="note">套餐正在准备，开放购买后可在此确认订单。</view><view v-else class="note">支付完成后请等待服务器确认会员权益。</view><view class="note link" @click="openRules">查看会员与退款说明 ›</view><view class="bottom"><view class="primary-button" :class="{ disabled: plan.status !== 'active' || buying }" @click="buy">{{ buying ? '正在创建订单...' : plan.status === 'active' ? '确认支付 ¥' + price(plan.price_fen) : '购买暂未开放' }}</view></view></template></view></template>
<script lang="ts">
import Vue from 'vue'; import { Component } from 'vue-property-decorator';
import InlineState from '@/components/InlineState.vue';
import { getMembershipPlans, createMembershipOrder, MembershipPlan, formatFen } from '@/api/membership';
declare const wx: any;
@Component({ components: { InlineState } }) export default class Confirm extends Vue {
  id = 0; plan: MembershipPlan | null = null; loading = true; buying = false;
  sandbox = process.env.VUE_APP_PAYMENT_SANDBOX === 'true';
  onLoad(options: any) { this.id = Number(options.id); this.load(); }
  async load() { this.loading = true; try { const plans = await getMembershipPlans(); this.plan = plans.find(item => item.id === this.id) || null; } catch (_) { this.plan = null; } finally { this.loading = false; } }
  price(value: number) { return formatFen(value); }
  openRules() { uni.navigateTo({ url: '/pages/membership/rules' }); }
  checkDevice(): boolean {
    // #ifdef MP-WEIXIN
    if (typeof wx.requestVirtualPayment !== 'function' || !wx.canIUse('requestVirtualPayment')) {
      uni.showModal({ title: '暂不支持支付', content: '请更新微信后重试。', showCancel: false }); return false;
    }
    const info = wx.getSystemInfoSync();
    if (info.platform === 'ios') {
      if (this.sandbox) { uni.showModal({ title: '沙箱暂不支持 iPhone', content: '请使用 Android 手机完成沙箱验证。', showCancel: false }); return false; }
      const version = String(info.version || '').split('.').map(Number), required = [8, 0, 68];
      let supported = true;
      for (let index = 0; index < required.length; index++) {
        if ((version[index] || 0) > required[index]) break;
        if ((version[index] || 0) < required[index]) { supported = false; break; }
      }
      if (!supported) { uni.showModal({ title: '请更新微信', content: 'iPhone 购买会员需要微信 8.0.68 或以上版本。', showCancel: false }); return false; }
    }
    return true;
    // #endif
    // #ifndef MP-WEIXIN
    uni.showToast({ title: '请在微信小程序内购买', icon: 'none' }); return false;
    // #endif
  }
  async buy() {
    if (this.buying || !this.plan || this.plan.status !== 'active' || !this.checkDevice()) return;
    this.buying = true;
    try {
      const code = await new Promise<string>((resolve, reject) => wx.login({ success: (res: any) => res.code ? resolve(res.code) : reject(new Error('微信登录失败')), fail: () => reject(new Error('微信登录失败')) }));
      const order = await createMembershipOrder(this.plan, code);
      const paymentError = await new Promise<any>((resolve) => {
        try { wx.requestVirtualPayment({ ...order.pay_data, success: () => resolve(null), fail: (error: any) => resolve(error || {}) }); }
        catch (_) { resolve({ errMsg: '无法调起微信支付' }); }
      });
      if (paymentError) {
        const raw = String(paymentError.errMsg || '支付未完成').slice(0, 160);
        const detail = raw.includes('COIN_OR_PRODUCT_ID_CREATED_IN_RECENTLY')
          ? '微信正在同步新建商品，请稍后重试。' : raw;
        await new Promise<void>((resolve) => uni.showModal({ title: '支付未完成', content: `${detail}\n最终结果以订单查询为准。`, showCancel: false, complete: () => resolve() }));
      }
      uni.redirectTo({ url: `/pages/membership/order?order_no=${encodeURIComponent(order.order_no)}` });
    } catch (error: any) {
      uni.showModal({ title: '暂无法发起支付', content: error.message || '请稍后重试', showCancel: false });
    } finally { this.buying = false; }
  }
}
</script>
<style lang="scss" scoped>
@import '@/assets/design-tokens.scss'; .page { min-height:100vh; padding:28rpx 30rpx calc(160rpx + env(safe-area-inset-bottom)); box-sizing:border-box; background:$page; color:$ink; }.card,.message { @include card; padding:28rpx 32rpx; }.message { color:$muted; font-size:27rpx; }.order-head,.row { display:flex; justify-content:space-between; align-items:center; min-height:90rpx; border-bottom:1rpx solid $border; }.order-head { font-size:34rpx; font-weight:700; }.price { color:$brand; }.row { font-size:28rpx; }.row text:first-child { color:$muted; }.row:last-child { border:0; }.note { color:$muted; font-size:25rpx; margin:24rpx 8rpx; line-height:1.5; }.bottom { position:fixed; left:0; right:0; bottom:0; padding:20rpx 32rpx calc(20rpx + env(safe-area-inset-bottom)); background:$page; }.primary-button { @include primary-button; }.disabled { opacity:.55; }.link { color:$brand; }
</style>
