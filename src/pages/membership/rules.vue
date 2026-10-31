<template>
  <view class="page">
    <view class="card">
      <view class="title">会员与退款说明</view>
      <view class="section"><view class="heading">会员权益</view><view>会员有效期内保存照片无需观看激励广告。权益以会员中心显示的状态为准。</view></view>
      <view class="section"><view class="heading">购买与续费</view><view>会员为单次购买，不会自动续费或自动扣款。有效期内续费会从当前到期时间起叠加所购买的自然月数；过期后购买从权益生效时起计算。</view><view>目标月份没有对应日期时，到期日取该月最后一天。例如 1 月 31 日购买 1 个月，到期为 2 月末的对应时刻。</view></view>
      <view class="section"><view class="heading">订单与退款</view><view>支付后请等待服务器确认会员权益。可在“我的 → 购买记录”查看订单。</view><view>iPhone 用户可通过 App Store 申请退款，最终结果由 Apple 决定。其他支付渠道的退款请通过“我的 → 联系与反馈”联系处理。退款成功后，会员权益由管理员核对处理。</view></view>
      <view class="section link" @click="agreement">查看用户协议 ›</view>
    </view>
  </view>
</template>
<script lang="ts">
import Vue from 'vue';
import { Component } from 'vue-property-decorator';
@Component({}) export default class MembershipRules extends Vue {
  agreement() { uni.navigateTo({ url: '/pages/user-agreement/index' }); }
}
</script>
<style lang="scss" scoped>
@import '@/assets/design-tokens.scss';
.page { min-height: 100vh; padding: 28rpx; box-sizing: border-box; background: $page; }
.card { @include card; padding: 32rpx; color: $muted; font-size: 26rpx; line-height: 1.8; }
.title { color: $ink; font-size: 36rpx; font-weight: 700; }
.section { margin-top: 30rpx; }
.section view + view { margin-top: 12rpx; }
.heading { color: $ink; font-size: 30rpx; font-weight: 600; }
.link { color: $brand; }
</style>
