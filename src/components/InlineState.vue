<template>
  <view class="state-panel" :class="kind" role="status" aria-live="polite">
    <view class="state-icon">
      <view v-if="kind === 'loading'" class="state-spinner"></view>
      <u-icon v-else :name="icon || (kind === 'error' ? 'info-circle' : 'photo')" size="27" :color="kind === 'error' ? '#cc3d35' : '#356caa'" />
    </view>
    <view class="state-title">{{ title }}</view>
    <view v-if="description" class="state-description">{{ description }}</view>
    <view v-if="actionText" class="state-action" role="button" @click="$emit('action')">{{ actionText }}</view>
  </view>
</template>
<script lang="ts">
import Vue from 'vue';
export default Vue.extend({
  props: {
    kind: { type: String, default: 'empty' },
    title: { type: String, required: true },
    description: { type: String, default: '' },
    actionText: { type: String, default: '' },
    icon: { type: String, default: '' }
  }
});
</script>
<style lang="scss" scoped>
@import '@/assets/design-tokens.scss';
.state-panel { @include card; padding: 44rpx 28rpx; display: flex; flex-direction: column; align-items: center; text-align: center; box-sizing: border-box; }
.state-icon { width: 88rpx; height: 88rpx; border-radius: 28rpx; display: flex; align-items: center; justify-content: center; background: $blue-soft; }.error .state-icon { background: $brand-soft; }
.state-spinner { width: 38rpx; height: 38rpx; border: 4rpx solid #cbdff6; border-top-color: $blue; border-radius: 50%; animation: state-spin 1s linear infinite; }
.state-title { margin-top: 20rpx; color: $ink; font-size: 29rpx; font-weight: 650; line-height: 1.5; }.state-description { margin-top: 8rpx; color: $muted; font-size: 24rpx; line-height: 1.6; }.state-action { margin-top: 22rpx; min-width: 180rpx; min-height: 80rpx; box-sizing: border-box; display: flex; align-items: center; justify-content: center; padding: 14rpx 24rpx; border-radius: 14rpx; background: $brand-soft; color: $brand; font-size: 25rpx; font-weight: 600; }
@keyframes state-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .state-spinner { animation: none; } }
</style>
