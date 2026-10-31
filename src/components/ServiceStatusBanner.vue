<template>
  <view class="status-banner" :class="state" role="button" aria-label="查看服务状态" @click="openStatus">
    <view class="status-dot"></view>
    <view class="status-copy">
      <text class="status-title">{{ title }}</text>
      <text class="status-description">{{ description }}</text>
    </view>
    <text class="status-action">查看 ›</text>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
export default Vue.extend({
  props: { state: { type: String, default: 'checking' } },
  computed: {
    title(): string {
      return ({ checking: '正在检查服务', ok: '服务连接正常', degraded: '部分服务可能受影响', offline: '暂时无法连接服务' } as any)[this.state] || '服务状态待检查';
    },
    description(): string {
      return ({ checking: '请稍候', ok: '基础检查通过', degraded: '可查看受影响的功能', offline: '请检查网络，或稍后重试' } as any)[this.state] || '';
    }
  },
  methods: { openStatus() { uni.navigateTo({ url: '/pages/status/index' }); } }
});
</script>

<style lang="scss" scoped>
@import '@/assets/design-tokens.scss';
.status-banner { display:flex; align-items:center; gap:16rpx; margin-top:24rpx; padding:18rpx 22rpx; min-height:88rpx; box-sizing:border-box; border-radius:20rpx; background:$teal-soft; }
.status-banner.degraded { background:$amber-soft; }.status-banner.offline { background:$brand-soft; }.status-banner.checking { background:$blue-soft; }
.status-dot { width:14rpx; height:14rpx; border-radius:50%; background:$teal; flex-shrink:0; }.degraded .status-dot { background:$amber; }.offline .status-dot { background:$brand; }.checking .status-dot { background:$blue; }
.status-copy { flex:1; min-width:0; display:flex; flex-wrap:wrap; align-items:baseline; gap:6rpx 16rpx; }.status-title { color:$ink; font-size:25rpx; font-weight:600; }.status-description { color:$muted; font-size:22rpx; }.status-action { color:$muted; font-size:23rpx; flex-shrink:0; }
</style>
