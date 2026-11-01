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
    <view class="security-card">
      <view class="security-heading"><view><view class="security-title">内容安全检测</view><view class="security-subtitle">照片处理前先检查，审核演示会显示微信接口返回值</view></view><u-icon name="lock" size="25" color="#287c70" /></view>
      <view class="security-note">图片、文本和异步媒体检测均由后端调用微信内容安全接口；原始图片不写入审计日志，检测失败时不会继续处理。</view>

      <view class="security-demo">
        <view class="demo-heading"><text class="demo-index">1</text><view><view class="demo-title">图片检测</view><view class="demo-api">imgSecCheck</view></view></view>
      <view v-if="imageResult" class="security-result" :class="imageResultTone">
          <view class="result-title">{{ resultTitle(imageResult) }}</view>
          <view class="result-line">errcode：{{ imageResult.errcode }}　{{ imageResult.errmsg }}</view>
          <view v-if="imageResult.trace_id" class="result-line">trace_id：{{ imageResult.trace_id }}</view>
          <view class="result-line hash">文件摘要：{{ imageResult.sha256 }}</view>
        </view>
        <view class="security-action" :class="{ disabled: imageChecking }" @click="verifyImage">{{ imageChecking ? '正在检测…' : '上传照片并验证' }}</view>
      </view>

      <view class="security-demo">
        <view class="demo-heading"><text class="demo-index">2</text><view><view class="demo-title">文本检测</view><view class="demo-api">msgSecCheck</view></view></view>
        <textarea v-model="textContent" class="security-textarea" maxlength="2500" placeholder="输入要检测的文本" />
        <view v-if="textResult" class="security-result" :class="textResultTone">
          <view class="result-title">{{ resultTitle(textResult) }}</view>
          <view class="result-line">errcode：{{ textResult.errcode }}　{{ textResult.errmsg }}</view>
          <view v-if="textResult.trace_id" class="result-line">trace_id：{{ textResult.trace_id }}</view>
        </view>
        <view class="security-action" :class="{ disabled: textChecking }" @click="verifyText">{{ textChecking ? '正在检测…' : '检测这段文本' }}</view>
      </view>

      <view class="security-demo last-demo">
        <view class="demo-heading"><text class="demo-index">3</text><view><view class="demo-title">异步媒体检测</view><view class="demo-api">mediaCheckAsync</view></view></view>
        <view class="security-help">默认使用服务提供的固定演示图片，也可填写可公开访问的 HTTPS 图片地址。提交成功后，最终判定由微信消息推送回调返回。</view>
        <input v-model="mediaUrl" class="security-input" maxlength="2048" placeholder="https://…" />
        <view v-if="mediaResult" class="security-result" :class="mediaResultTone">
          <view class="result-title">{{ resultTitle(mediaResult, true) }}</view>
          <view class="result-line">errcode：{{ mediaResult.errcode }}　{{ mediaResult.errmsg }}</view>
          <view v-if="mediaResult.trace_id" class="result-line">trace_id：{{ mediaResult.trace_id }}</view>
        </view>
        <view class="security-action" :class="{ disabled: mediaChecking }" @click="verifyMedia">{{ mediaChecking ? '正在提交…' : '提交异步媒体检测' }}</view>
      </view>
    </view>
    <view class="refresh" role="button" @click="refresh">{{ refreshing ? '正在检查…' : '重新检查' }}</view>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from 'vue-property-decorator';
import { fetchServiceStatus, ServiceSnapshot, CheckState } from '@/api/service-status';
import { formatMemberDate } from '@/api/membership';
import { checkImageSecurity, checkMediaSecurity, checkTextSecurity, ContentSecurityResult } from '@/api/content-security';
import { baseUrl } from '@/config';

@Component({})
export default class StatusPage extends Vue {
  snapshot: ServiceSnapshot | null = null;
  connection: 'checking' | 'online' | 'offline' = 'checking';
  refreshing = false;
  sequence = 0;
  timer: any = null;
  imageChecking = false;
  textChecking = false;
  mediaChecking = false;
  imageResult: ContentSecurityResult | null = null;
  textResult: ContentSecurityResult | null = null;
  mediaResult: ContentSecurityResult | null = null;
  textContent = '小七快照拍内容安全能力演示';
  mediaUrl = `${baseUrl}/content-security/demo-media`;
  get displayState() { return this.connection === 'online' && this.snapshot ? this.snapshot.status : this.connection; }
  get summaryTitle() { return ({ checking:'正在检查服务', ok:'服务连接正常', degraded:'部分服务可能受影响', offline:'暂时无法连接服务' } as any)[this.displayState]; }
  get summaryDetail() { return ({ checking:'正在获取最新状态', ok:'基础检查已完成', degraded:'请查看下方具体状态，稍后可再次检查', offline:'请检查网络或稍后重试' } as any)[this.displayState]; }
  get checkedAt() { return this.snapshot ? formatMemberDate(this.snapshot.checked_at) : ''; }
  get imageResultTone() { return this.imageResult ? this.resultTone(this.imageResult) : ''; }
  get textResultTone() { return this.textResult ? this.resultTone(this.textResult) : ''; }
  get mediaResultTone() { return this.mediaResult ? this.resultTone(this.mediaResult, true) : ''; }
  stateLabel(state: CheckState) { return ({ok:'未见异常',degraded:'近期异常',unavailable:'暂不可用',disabled:'暂未开放',unknown:'未验证'} as any)[state]; }
  resultTone(result: ContentSecurityResult, asynchronous = false) {
    if (asynchronous && result.accepted) return 'pending';
    return result.safe === true ? 'pass' : result.available ? 'risk' : 'unavailable';
  }
  resultTitle(result: ContentSecurityResult, asynchronous = false) {
    if (asynchronous && result.accepted) return '已提交，等待微信异步回调';
    return result.safe === true ? '检测通过' : result.available ? '检测未通过' : '检测服务暂不可用';
  }
  onShow() { this.stop(); this.refresh(); this.timer = setInterval(() => this.refresh(), 60000); }
  onHide() { this.stop(); }
  onUnload() { this.stop(); }
  stop() { if (this.timer) clearInterval(this.timer); this.timer = null; this.sequence++; this.refreshing = false; }
  verifyImage() {
    if (this.imageChecking) return;
    uni.chooseImage({ count: 1, sizeType: ['compressed', 'original'], sourceType: ['album', 'camera'], success: async (result: any) => {
      const path = result.tempFilePaths && result.tempFilePaths[0];
      if (!path) return;
      this.imageChecking = true;
      uni.showLoading({ title: '检测中…', mask: true });
      try {
        this.imageResult = await checkImageSecurity(path);
        uni.showToast({ title: this.imageResult.safe === true ? '检测通过' : this.imageResult.available ? '检测未通过' : '服务暂不可用', icon: this.imageResult.safe === true ? 'success' : 'none' });
      } catch (error: any) {
        uni.showModal({ title: '检测失败', content: error.message || '内容安全服务暂不可用，请稍后重试', showCancel: false });
      } finally {
        uni.hideLoading();
        this.imageChecking = false;
      }
    } });
  }
  async verifyText() {
    if (this.textChecking) return;
    const content = this.textContent.trim();
    if (!content) { uni.showToast({ title: '请输入要检测的文本', icon: 'none' }); return; }
    this.textChecking = true;
    uni.showLoading({ title: '检测中…', mask: true });
    try {
      this.textResult = await checkTextSecurity({ content, scene: 2, title: '内容安全能力演示' });
      uni.showToast({ title: this.textResult.safe === true ? '检测通过' : '检测未通过', icon: this.textResult.safe === true ? 'success' : 'none' });
    } catch (error: any) {
      uni.showModal({ title: '检测失败', content: error.message || '文本内容安全服务暂不可用，请稍后重试', showCancel: false });
    } finally {
      uni.hideLoading();
      this.textChecking = false;
    }
  }
  async verifyMedia() {
    if (this.mediaChecking) return;
    const mediaUrl = this.mediaUrl.trim();
    if (!/^https:\/\//i.test(mediaUrl)) { uni.showToast({ title: '请输入 HTTPS 媒体地址', icon: 'none' }); return; }
    this.mediaChecking = true;
    uni.showLoading({ title: '提交中…', mask: true });
    try {
      this.mediaResult = await checkMediaSecurity({ media_url: mediaUrl, media_type: 2, scene: 4 });
      uni.showToast({ title: this.mediaResult.accepted ? '已提交异步检测' : '提交失败', icon: this.mediaResult.accepted ? 'success' : 'none' });
    } catch (error: any) {
      uni.showModal({ title: '提交失败', content: error.message || '媒体内容安全服务暂不可用，请稍后重试', showCancel: false });
    } finally {
      uni.hideLoading();
      this.mediaChecking = false;
    }
  }
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
.security-card { @include card; margin-top:24rpx; padding:28rpx; }.security-heading { display:flex; align-items:center; justify-content:space-between; gap:18rpx; }.security-title { font-size:29rpx; font-weight:650; }.security-subtitle { color:$muted; font-size:22rpx; margin-top:8rpx; }.security-note,.security-help { color:$muted; font-size:22rpx; line-height:1.65; }.security-note { margin-top:18rpx; padding:18rpx; border-radius:14rpx; background:$blue-soft; }.security-demo { margin-top:28rpx; padding-top:26rpx; border-top:1rpx solid $border; }.security-demo.last-demo { padding-bottom:2rpx; }.demo-heading { display:flex; align-items:center; gap:14rpx; }.demo-index { width:40rpx; height:40rpx; border-radius:50%; display:flex; align-items:center; justify-content:center; background:$teal-soft; color:$teal; font-size:22rpx; font-weight:700; }.demo-title { font-size:27rpx; font-weight:650; }.demo-api { color:$muted; font-size:20rpx; margin-top:3rpx; }.security-result { margin-top:20rpx; padding:20rpx; border-radius:16rpx; background:$teal-soft; }.security-result.risk { background:$brand-soft; }.security-result.unavailable { background:$amber-soft; }.security-result.pending { background:$blue-soft; }.result-title { font-size:26rpx; font-weight:650; }.result-line { color:$muted; font-size:21rpx; line-height:1.6; margin-top:6rpx; word-break:break-all; }.hash { color:#8b9399; }.security-textarea,.security-input { width:100%; box-sizing:border-box; margin-top:18rpx; padding:18rpx; border:1rpx solid $border; border-radius:14rpx; background:$page; color:$ink; font-size:24rpx; }.security-textarea { min-height:132rpx; }.security-input { height:76rpx; }.security-help { margin-top:16rpx; }.security-action { @include secondary-button; margin-top:20rpx; text-align:center; }.security-action.disabled { opacity:.55; }
</style>
