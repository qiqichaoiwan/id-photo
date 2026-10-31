<template>
  <view class="page">
    <view class="heading">会员中心</view><view class="subheading">开通会员，享受更好的体验</view>
    <view class="hero"><view><view class="hero-title">会员免广告保存</view><view class="hero-subtitle">保存照片，无需观看广告</view></view><view class="hero-badge"><u-icon name="gift-fill" size="30" color="#cc3d35" /></view></view>
    <view v-if="memberStatus && memberStatus.active" class="status-card"><view><text class="status-title">会员已开通</text><text class="status-desc">有效期至 {{ date(memberStatus.expires_at) }}</text></view></view>
    <view v-else-if="memberStatus && memberStatus.status === 'expired'" class="status-card"><view><text class="status-title">会员已到期</text><text class="status-desc">到期时间 {{ date(memberStatus.expires_at) }}</text></view></view>
    <view class="section-title">选择会员套餐</view>
    <InlineState v-if="loading" kind="loading" title="正在加载套餐" description="请稍候" />
    <InlineState v-else-if="error" kind="error" title="套餐暂时无法加载" description="请检查网络后重试" action-text="重新加载" @action="load" />
    <InlineState v-else-if="!plans.length" title="套餐准备中" description="请稍后再来" icon="gift" />
    <view v-else class="plan-grid"><view v-for="plan in plans" :key="plan.id" class="plan" :class="{ selected: selectedId === plan.id }" @click="selectedId = plan.id"><text class="plan-name">{{ plan.months }}个月</text><text class="plan-price"><text class="currency">¥</text>{{ price(plan.price_fen) }}</text><text v-if="plan.status !== 'active'" class="plan-state">准备中</text></view></view>
    <view class="benefit"><text>会员权益</text><text class="benefit-value">免广告保存</text></view>
    <view class="notes"><view>ⓘ 单次购买，不自动续费</view><view>ⓘ 按自然月计算，续费时长叠加</view><view>ⓘ 套餐和价格以购买时页面为准</view></view>
    <view class="bottom"><view class="primary-button" :class="{ disabled: !selectedPlan }" @click="openDetails">{{ selectedPlan && selectedPlan.status === 'active' ? '开通会员 ¥' + price(selectedPlan.price_fen) : selectedPlan ? '查看套餐详情' : '套餐准备中' }}</view></view>
  </view>
</template>
<script lang="ts">
import Vue from 'vue';
import { Component } from 'vue-property-decorator';
import { getMembershipPlans, getMembershipStatus, MembershipPlan, MembershipStatus, formatFen, formatMemberDate } from '@/api/membership';
import InlineState from '@/components/InlineState.vue';
@Component({ components: { InlineState } })
export default class Membership extends Vue {
  plans: MembershipPlan[] = []; memberStatus: MembershipStatus | null = null; selectedId: number | null = null; loading = true; error = false;
  get selectedPlan(): MembershipPlan | undefined { return this.plans.find(item => item.id === this.selectedId); }
  onShow() { this.load(); }
  async load() {
    this.loading = true; this.error = false;
    try { this.plans = await getMembershipPlans(); if (!this.plans.some(item => item.id === this.selectedId)) this.selectedId = this.plans.length ? this.plans[0].id : null; }
    catch (_) { this.error = true; this.plans = []; this.selectedId = null; }
    finally { this.loading = false; }
    try { this.memberStatus = await getMembershipStatus(); } catch (_) { this.memberStatus = null; }
  }
  price(value: number) { return formatFen(value).replace(/\.00$/, ''); }
  date(value: string | null) { return formatMemberDate(value); }
  openDetails() { if (this.selectedPlan) uni.navigateTo({ url: `/pages/membership/confirm?id=${this.selectedPlan.id}` }); }
}
</script>
<style lang="scss" scoped>
@import '@/assets/design-tokens.scss';
.page { min-height: 100vh; box-sizing: border-box; padding: 32rpx 32rpx calc(190rpx + env(safe-area-inset-bottom)); background: $page; color: $ink; }.heading { font-size: 48rpx; font-weight: 700; }.subheading { font-size: 26rpx; color: $muted; margin: 8rpx 0 30rpx; }.hero { display: flex; justify-content: space-between; align-items: center; min-height: 210rpx; padding: 28rpx 32rpx; border-radius: 24rpx; background: linear-gradient(120deg,#fff7f5,#fde9e5); box-sizing: border-box; }.hero-title { font-size: 37rpx; font-weight: 700; }.hero-subtitle { color: $muted; font-size: 26rpx; margin-top: 12rpx; }.hero-badge { width: 106rpx; height: 106rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #fff; }.status-card { @include card; padding: 24rpx; margin-top: 20rpx; }.status-title,.status-desc { display: block; }.status-title { font-size: 28rpx; font-weight: 600; }.status-desc { color: $muted; margin-top: 8rpx; font-size: 24rpx; }.section-title { font-size: 32rpx; font-weight: 650; margin: 44rpx 0 22rpx; }.plan-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 16rpx; }.plan { @include card; border: 2rpx solid $border; min-height: 190rpx; display: flex; flex-direction: column; align-items: center; justify-content: center; box-sizing: border-box; }.plan.selected { border-color: $brand; background: #fff6f5; }.plan-name { font-size: 28rpx; }.plan-price { font-size: 40rpx; font-weight: 700; margin-top: 14rpx; }.selected .plan-price { color: $brand; }.currency { font-size: 24rpx; }.plan-state { color: $muted; font-size: 21rpx; margin-top: 8rpx; }.message-card { @include card; padding: 32rpx; color: $muted; font-size: 27rpx; }.benefit { @include card; display: flex; justify-content: space-between; padding: 28rpx; margin-top: 30rpx; font-size: 28rpx; font-weight: 600; }.benefit-value { font-weight: 400; color: $muted; }.notes { color: $muted; font-size: 24rpx; line-height: 2.2; margin: 28rpx 8rpx; }.bottom { position: fixed; left: 0; right: 0; bottom: 0; background: $page; padding: 18rpx 32rpx calc(20rpx + env(safe-area-inset-bottom)); }.primary-button { @include primary-button; }.disabled { opacity: .55; }
</style>
