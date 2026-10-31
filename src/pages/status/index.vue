<template>
  <view class="page">
    <view class="intro">
      <view class="intro-icon"><u-icon name="wifi" size="27" color="#287c70" /></view>
      <view><view class="title">服务状态</view><view class="subtitle">查看照片服务的连接和基础检查</view></view>
    </view>
    <view class="summary" :class="displayState">
      <view class="summary-top"><view class="dot"></view><text>{{ summaryTitle }}</text></view>
      <view class="summary-detail">{{ summaryDetail }}</view>
      <view v-if="snapshot" class="time">最近检查：{{ checkedAt }}</view>
    </view>
    <view v-if="snapshot && connection === 'online'" class="check-list">
      <view v-for="item in snapshot.checks" :key="item.id" class="check-row">
        <view class="check-copy"><view class="check-name">{{ item.name }}</view><view class="check-detail">{{ item.detail }}</view></view>
        <text class="check-state" :class="item.state">{{ stateLabel(item.state) }}</text>
      </view>
    </view>
    <view class="explanation">{{ snapshot && connection === 'online' ? snapshot.note : connection === 'offline' ? '无法连接可能与手机网络、服务繁忙或服务器离线有关。请检查网络后重试。' : '正在获取最新的服务状态。' }}</view>
    <view class="refresh" role="button" @click="refresh">{{ refreshing ? '正在检查…' : '重新检查' }}</view>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from 'vue-property-decorator';
import { fetchServiceStatus, ServiceSnapshot, CheckState } from '@/api/service-status';
import { formatMemberDate } from '@/api/membership';

@Component({})
export default class StatusPage extends Vue {
  snapshot: ServiceSnapshot | null = null;
  connection: 'checking' | 'online' | 'offline' = 'checking';
  refreshing = false;
  sequence = 0;
  timer: any = null;
  get displayState() { return this.connection === 'online' && this.snapshot ? this.snapshot.status : this.connection; }
  get summaryTitle() { return ({ checking:'正在检查服务', ok:'服务连接正常', degraded:'部分服务可能受影响', offline:'暂时无法连接服务' } as any)[this.displayState]; }
  get summaryDetail() { return ({ checking:'正在获取最新状态', ok:'基础检查已完成', degraded:'请查看下方具体状态，稍后可再次检查', offline:'请检查网络或稍后重试' } as any)[this.displayState]; }
  get checkedAt() { return this.snapshot ? formatMemberDate(this.snapshot.checked_at) : ''; }
  stateLabel(state: CheckState) { return ({ok:'未见异常',degraded:'近期异常',unavailable:'暂不可用',disabled:'暂未开放',unknown:'未验证'} as any)[state]; }
  onShow() { this.stop(); this.refresh(); this.timer = setInterval(() => this.refresh(), 60000); }
  onHide() { this.stop(); }
  onUnload() { this.stop(); }
  stop() { if (this.timer) clearInterval(this.timer); this.timer = null; this.sequence++; this.refreshing = false; }
  async refresh() {
    if (this.refreshing) return;
    const sequence = ++this.sequence; this.refreshing = true;
    try { const result = await fetchServiceStatus(); if (sequence === this.sequence) { this.snapshot = result; this.connection = 'online'; } }
    catch (_) { if (sequence === this.sequence) { this.snapshot = null; this.connection = 'offline'; } }
    finally { if (sequence === this.sequence) this.refreshing = false; }
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/design-tokens.scss';
.page { min-height:100vh; box-sizing:border-box; padding:32rpx 32rpx calc(48rpx + env(safe-area-inset-bottom)); background:$page; color:$ink; }
.intro { display:flex; align-items:center; gap:20rpx; margin:12rpx 0 32rpx; }.intro-icon { width:84rpx; height:84rpx; border-radius:22rpx; display:flex; align-items:center; justify-content:center; background:$teal-soft; }.title { font-size:42rpx; font-weight:700; }.subtitle { color:$muted; font-size:25rpx; margin-top:8rpx; }
.summary { padding:28rpx; border-radius:24rpx; background:$teal-soft; }.summary.degraded { background:$amber-soft; }.summary.offline { background:$brand-soft; }.summary.checking { background:$blue-soft; }.summary-top { display:flex; align-items:center; gap:14rpx; font-size:31rpx; font-weight:650; }.dot { width:16rpx; height:16rpx; border-radius:50%; background:$teal; }.degraded .dot { background:$amber; }.offline .dot { background:$brand; }.checking .dot { background:$blue; }.summary-detail,.time { color:$muted; font-size:24rpx; margin-top:12rpx; line-height:1.5; }
.check-list { @include card; margin-top:24rpx; padding:0 28rpx; }.check-row { display:flex; justify-content:space-between; align-items:center; gap:20rpx; padding:26rpx 0; border-bottom:1rpx solid $border; }.check-row:last-child { border:0; }.check-copy { flex:1; min-width:0; }.check-name { font-size:28rpx; font-weight:600; }.check-detail { font-size:23rpx; line-height:1.5; color:$muted; margin-top:7rpx; }.check-state { flex-shrink:0; font-size:22rpx; color:$teal; }.check-state.degraded { color:$amber; }.check-state.unavailable { color:$brand; }.check-state.disabled,.check-state.unknown { color:$muted; }
.explanation { color:$muted; font-size:23rpx; line-height:1.7; margin:24rpx 6rpx; }.refresh { @include primary-button; margin-top:26rpx; }
</style>
