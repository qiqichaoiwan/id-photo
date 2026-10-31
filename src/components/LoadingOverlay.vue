<template>
  <view v-if="show" class="loading-overlay" role="alert" aria-live="polite" @touchmove.stop.prevent>
    <view class="loading-card">
      <view class="loading-art" aria-hidden="true">
        <view class="art-orbit"></view>
        <view class="art-tile"><u-icon name="photo" size="31" color="#cc3d35" /></view>
        <view class="art-spark art-spark-one"></view>
        <view class="art-spark art-spark-two"></view>
      </view>
      <view class="loading-title">{{ text }}</view>
      <view class="loading-tip">{{ tip || '请稍候，完成后将自动继续' }}</view>
      <view v-if="showProgress" class="progress-wrapper">
        <view class="progress-bar"><view class="progress-fill" :style="{ width: safeProgress + '%' }"></view></view>
        <text class="progress-text">{{ safeProgress }}%</text>
      </view>
      <view v-else class="loading-indicator" aria-hidden="true"><view></view><view></view><view></view></view>
    </view>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component, Prop } from 'vue-property-decorator';

@Component({})
export default class LoadingOverlay extends Vue {
  @Prop({ default: false }) show!: boolean;
  @Prop({ default: '正在处理' }) text!: string;
  @Prop({ default: '' }) tip!: string;
  @Prop({ default: false }) showProgress!: boolean;
  @Prop({ default: 0 }) progress!: number;

  get safeProgress(): number {
    return Number.isFinite(Number(this.progress)) ? Math.max(0, Math.min(100, Math.round(Number(this.progress)))) : 0;
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/design-tokens.scss';
.loading-overlay { position: fixed; top: 0; right: 0; bottom: 0; left: 0; z-index: 9999; display: flex; align-items: center; justify-content: center; padding: 32rpx; box-sizing: border-box; background: rgba(25, 30, 39, .32); }
.loading-card { width: 520rpx; max-width: 100%; box-sizing: border-box; padding: 46rpx 32rpx 40rpx; border-radius: 32rpx; background: $surface; box-shadow: 0 20rpx 80rpx rgba(27, 32, 42, .16); display: flex; flex-direction: column; align-items: center; text-align: center; }
.loading-art { position: relative; width: 132rpx; height: 132rpx; display: flex; align-items: center; justify-content: center; margin-bottom: 30rpx; }
.art-orbit { position: absolute; top: 0; right: 0; bottom: 0; left: 0; border: 4rpx solid #f6ded9; border-top-color: $brand; border-radius: 50%; animation: orbit 1.25s linear infinite; }
.art-tile { width: 88rpx; height: 88rpx; display: flex; align-items: center; justify-content: center; border-radius: 28rpx; background: $brand-soft; }
.art-spark { position: absolute; width: 12rpx; height: 12rpx; border-radius: 50%; background: #eab687; }
.art-spark-one { top: 6rpx; right: 8rpx; }.art-spark-two { left: 0; bottom: 18rpx; width: 8rpx; height: 8rpx; background: #8fc5ba; }
.loading-title { color: $ink; font-size: 32rpx; font-weight: 700; line-height: 1.4; }
.loading-tip { color: $muted; font-size: 24rpx; line-height: 1.6; margin-top: 12rpx; }
.loading-indicator { display: flex; gap: 10rpx; margin-top: 26rpx; }.loading-indicator view { width: 10rpx; height: 10rpx; border-radius: 50%; background: $brand; animation: dot 1.2s ease-in-out infinite; }.loading-indicator view:nth-child(2) { animation-delay: .15s; }.loading-indicator view:nth-child(3) { animation-delay: .3s; }
.progress-wrapper { width: 100%; margin-top: 24rpx; }.progress-bar { height: 8rpx; overflow: hidden; border-radius: 8rpx; background: $brand-soft; }.progress-fill { height: 100%; border-radius: 8rpx; background: $brand; transition: width .2s ease; }.progress-text { display: block; margin-top: 12rpx; color: $muted; font-size: 23rpx; }
@keyframes orbit { to { transform: rotate(360deg); } }
@keyframes dot { 0%, 60%, 100% { opacity: .3; transform: scale(.8); } 30% { opacity: 1; transform: scale(1); } }
@media (prefers-reduced-motion: reduce) { .art-orbit, .loading-indicator view { animation: none; } }
</style>
