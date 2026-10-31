<template>
  <view class="page">
    <InlineState v-if="loading && !order" kind="loading" title="正在查询订单" description="请稍候" />
    <view v-else-if="!order">
      <InlineState kind="error" title="订单暂不可用" :description="error" :action-text="invalidOrderNo ? '查看购买记录' : '重新查询'" @action="retry" />
      <view v-if="!invalidOrderNo" class="link" @click="goOrders">返回购买记录</view>
    </view>
    <template v-else>
      <view class="card">
        <view class="title">{{ statusText(order.status) }}</view>
        <view class="row"><text>套餐</text><text>{{ order.plan_name }}</text></view>
        <view class="row"><text>金额</text><text>¥{{ price(order.price_fen) }}</text></view>
        <view class="row"><text>订单编号</text><text>{{ order.order_no }}</text></view>
        <view class="row"><text>创建时间</text><text>{{ date(order.created_at) }}</text></view>
        <view v-if="order.expires_at" class="row"><text>本单发放后的有效期</text><text>{{ date(order.expires_at) }}</text></view>
        <view v-if="order.status === 'pending'" class="note">支付结果确认中，请勿重复付款。微信支付已取消时也需要先查询订单状态。</view>
        <view v-if="order.review_needed" class="note">订单信息正在人工核对。</view>
        <view class="link" @click="refresh(false)">{{ loading ? '正在查询…' : '向微信查询订单状态' }}</view>
      </view>
      <view v-if="order.status === 'paid' || order.refund_request" class="card refund-card">
        <view class="section-title">退款与售后</view>
        <view v-if="order.refund_request" class="refund-status">
          <view class="status-heading">{{ refundStatus(order.refund_request.status) }}</view>
          <view v-if="order.refund_request.response">{{ order.refund_request.response }}</view>
          <view v-else>商家会核实支付渠道并处理，请稍后回来查看进度。</view>
          <view class="status-hint">提交申请不代表退款已完成。</view>
          <view class="action-link" @click="load">刷新申请进度 ›</view>
        </view>
        <view class="help-heading">在小程序内申请退款</view>
        <view class="note">所有支付渠道均可在此提交申请，由商家核实处理。提交申请不代表退款已完成，也不会自动调整会员权益。</view>
        <view v-if="order.status === 'paid' && (!order.refund_request || order.refund_request.status === 'closed')">
          <view v-if="!showRefundForm" class="refund-button" @click="showRefundForm = true">{{ order.refund_request ? '再次申请售后' : '申请退款' }}</view>
          <view v-else class="refund-form">
            <view class="form-label">退款原因</view>
            <textarea v-model="reason" maxlength="200" placeholder="请简要说明原因，请勿填写身份证号等敏感信息" />
            <view class="form-hint">{{ reason.length }}/200</view>
            <view class="form-actions"><view class="cancel-button" @click="cancelRefund">取消</view><view class="refund-button submit-button" :class="{ disabled: submitting }" @click="submitRefund">{{ submitting ? '提交中…' : '提交申请' }}</view></view>
          </view>
        </view>
        <view class="help-heading">Apple 内购退款说明</view>
        <view class="note">如通过 Apple 内购支付，您可在此提交申请，由商家协助核实；也可通过 Apple“报告问题”申请，退款结果由 Apple 决定。</view>
        <view class="action-link" @click="copyAppleLink">复制 Apple 退款网址 ›</view>
      </view>
    </template>
  </view>
</template>
<script lang="ts">
import Vue from 'vue';
import { Component } from 'vue-property-decorator';
import InlineState from '@/components/InlineState.vue';
import { getMembershipOrder, refreshMembershipOrder, requestMembershipRefund, MembershipOrder, formatFen, formatMemberDate } from '@/api/membership';

@Component({ components: { InlineState } })
export default class Order extends Vue {
  orderNo = '';
  order: MembershipOrder | null = null;
  loading = true;
  error = '';
  showRefundForm = false;
  submitting = false;
  reason = '';

  get invalidOrderNo() { return !this.orderNo || this.orderNo === 'undefined' || this.orderNo === 'null'; }
  onLoad(options: any) { this.orderNo = typeof options.order_no === 'string' ? options.order_no : ''; this.load(); }
  onShow() { if (this.order && !this.loading) this.load(); }
  async load() {
    if (this.invalidOrderNo) { this.error = '订单编号缺失，请从购买记录重新打开。'; this.loading = false; return; }
    this.loading = true;
    this.error = '';
    try {
      this.order = await getMembershipOrder(this.orderNo);
      if (!this.order || this.order.order_no !== this.orderNo) throw new Error('订单数据无法读取，请重新查询');
    } catch (error: any) {
      this.order = null;
      this.error = error.statusCode === 404 ? '未找到该订单，请返回购买记录重新打开。' : (error.message || '请检查网络后重新查询');
    } finally { this.loading = false; }
    if (this.order && this.order.status === 'pending') this.refresh(true);
  }
  retry() { if (this.invalidOrderNo) this.goOrders(); else this.load(); }
  goOrders() { uni.redirectTo({ url: '/pages/membership/orders' }); }
  async refresh(silent = false) {
    if (this.invalidOrderNo || this.loading) return;
    this.loading = true;
    try {
      await refreshMembershipOrder(this.orderNo);
      this.order = await getMembershipOrder(this.orderNo);
      if (!silent) uni.showToast({ title: '已更新订单状态', icon: 'none' });
    } catch (error: any) {
      if (!silent) uni.showToast({ title: error.message || '订单确认中，请稍后重试', icon: 'none' });
    } finally { this.loading = false; }
  }
  cancelRefund() { if (!this.submitting) { this.showRefundForm = false; this.reason = ''; } }
  async submitRefund() {
    const reason = this.reason.trim();
    if (this.submitting || !this.order) return;
    if (reason.length < 2) { uni.showToast({ title: '请填写退款原因', icon: 'none' }); return; }
    this.submitting = true;
    try {
      const refund = await requestMembershipRefund(this.orderNo, reason);
      if (this.order) this.order = { ...this.order, refund_request: refund };
      this.reason = '';
      this.showRefundForm = false;
      uni.showModal({ title: '申请已提交', content: '商家会核实并处理。申请提交不代表退款已完成，请在此查看进度。', showCancel: false });
    } catch (error: any) {
      uni.showModal({ title: '暂无法提交申请', content: error.message || '请稍后重试', showCancel: false });
    } finally { this.submitting = false; }
  }
  copyAppleLink() { uni.setClipboardData({ data: 'https://reportaproblem.apple.com' }); }
  price(value: number) { return formatFen(value); }
  date(value: string) { return formatMemberDate(value); }
  refundStatus(value: string) { return ({ submitted: '申请已提交', processing: '申请处理中', closed: '申请已处理' } as any)[value] || '申请处理中'; }
  statusText(value: string) { return ({ paid: '订单已完成', pending: '订单确认中', cancelled: '订单已取消', closed: '订单已关闭', failed: '订单未完成', refunded: '订单已退款' } as any)[value] || '订单处理中'; }
}
</script>
<style lang="scss" scoped>
@import '@/assets/design-tokens.scss';
.page { min-height: 100vh; background: $page; padding: 28rpx; box-sizing: border-box; }
.card { @include card; padding: 32rpx; color: $muted; font-size: 26rpx; }
.title { font-size: 36rpx; font-weight: 700; color: $ink; margin: 12rpx 0 25rpx; }
.row { display: flex; justify-content: space-between; gap: 20rpx; border-top: 1rpx solid $border; padding: 24rpx 0; }
.row text:last-child { color: $ink; text-align: right; word-break: break-all; }
.note { line-height: 1.7; }
.link { color: $brand; margin-top: 24rpx; text-align: center; padding: 20rpx; }
.refund-card { margin-top: 20rpx; }
.section-title { font-size: 31rpx; color: $ink; font-weight: 700; }
.help-heading { margin: 28rpx 0 10rpx; color: $ink; font-weight: 600; }
.action-link { display: inline-block; color: $brand; padding: 16rpx 0 2rpx; }
.refund-status { margin-top: 22rpx; padding: 22rpx; border-radius: 16rpx; background: #fff6eb; line-height: 1.6; color: #805d3e; }
.status-heading { font-weight: 700; color: #8a552e; margin-bottom: 6rpx; }
.status-hint { margin-top: 8rpx; font-size: 23rpx; }
.refund-button { margin-top: 24rpx; text-align: center; border: 1rpx solid $brand; border-radius: 42rpx; color: $brand; padding: 18rpx; font-weight: 600; }
.refund-form { margin-top: 24rpx; }
.form-label { color: $ink; font-weight: 600; margin-bottom: 12rpx; }
textarea { box-sizing: border-box; width: 100%; height: 150rpx; padding: 20rpx; background: #f8f8f8; border-radius: 14rpx; font-size: 25rpx; }
.form-hint { text-align: right; color: $muted; font-size: 22rpx; margin-top: 8rpx; }
.form-actions { display: flex; align-items: center; gap: 20rpx; }
.cancel-button, .submit-button { flex: 1; text-align: center; }
.cancel-button { margin-top: 24rpx; padding: 18rpx; }
.submit-button { background: $brand; color: #fff; }
.disabled { opacity: .55; }
</style>
