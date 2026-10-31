<template>
  <view class="page">
    <view class="page-heading">
      <view><view class="title">我的</view><view class="subtitle">照片与会员服务</view></view>
      <view class="heading-mark"><u-icon name="heart-fill" size="18" color="#cc3d35" /></view>
    </view>

    <view class="profile-card">
      <image class="avatar" src="/static/logo.png" mode="aspectFill" />
      <view class="profile-copy">
        <view class="profile-name">小七快照拍</view>
        <view class="profile-id"><text>会员编号：</text><text v-if="memberRef" selectable>{{ memberRef }}</text><text v-else>{{ profileError ? '暂不可用' : '查询中…' }}</text></view>
        <button v-if="memberRef" class="profile-id-action" @click="copyMemberRef">复制编号</button>
        <button v-else-if="profileError" class="profile-id-action" @click="loadProfile">重新查询</button>
      </view>
      <view class="profile-photo-count" @click="electronic">
        <text class="profile-photo-value">{{ electronicCount }}</text>
        <text class="profile-photo-label">张电子照</text>
      </view>
    </view>

    <view class="member-banner" role="button" @click="open('/pages/membership/index')">
      <view class="member-glow member-glow-one"></view><view class="member-glow member-glow-two"></view>
      <view class="member-top">
        <view class="member-icon"><u-icon name="gift-fill" size="25" color="#cc3d35" /></view>
        <view class="member-copy"><view class="member-title">{{ memberTitle }}</view><view class="member-description">{{ memberDescription }}</view></view>
        <u-icon name="arrow-right" size="16" color="#a2544c" />
      </view>
      <view class="member-footer"><text class="member-benefit">会员权益 · 免广告保存</text><text class="member-action">{{ memberStatus && memberStatus.active ? '查看会员' : '了解会员' }} ›</text></view>
    </view>

    <view class="section-heading"><text>照片与会员</text><text class="section-subtitle">常用服务</text></view>
    <view class="menu">
      <view v-for="item in personalItems" :key="item.key" class="menu-item" role="button" hover-class="menu-item-hover" @click="openItem(item)">
        <view class="menu-left"><view class="menu-icon" :class="item.tone"><u-icon :name="item.icon" size="20" :color="item.color" /></view><text class="menu-title">{{ item.label }}</text></view>
        <view class="menu-end"><text v-if="item.key === 'photos'">{{ electronicCount }} 张</text><u-icon name="arrow-right" size="15" color="#8b8f95" /></view>
      </view>
    </view>

    <view class="section-heading"><text>支持与设置</text></view>
    <view class="menu">
      <view v-for="item in supportItems" :key="item.key" class="menu-item" role="button" hover-class="menu-item-hover" @click="openItem(item)">
        <view class="menu-left"><view class="menu-icon" :class="item.tone"><u-icon :name="item.icon" size="20" :color="item.color" /></view><text class="menu-title">{{ item.label }}</text></view>
        <view class="menu-end"><u-icon name="arrow-right" size="15" color="#8b8f95" /></view>
      </view>
    </view>
    <view class="page-footer">小七快照拍 · 用心记录每一张照片</view>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from 'vue-property-decorator';
import StorageManager from '@/utils/storage';
import { ElectronicPhotoManager } from '@/utils/electronic-photo';
import { clearTemporaryImages } from '@/utils/image-file';
import { getMembershipProfile, getMembershipStatus, MembershipStatus, formatMemberDate } from '@/api/membership';

interface MenuItem { key: string; label: string; icon: string; color: string; tone: string; url?: string; }

@Component({})
export default class Mine extends Vue {
  memberRef = '';
  profileError = false;
  profileSequence = 0;
  electronicCount = 0;
  memberStatus: MembershipStatus | null = null;
  membershipError = false;
  memberSequence = 0;
  personalItems: MenuItem[] = [
    { key: 'member', label: '会员中心', icon: 'heart', color: '#cc3d35', tone: 'rose', url: '/pages/membership/index' },
    { key: 'orders', label: '购买记录', icon: 'file-text', color: '#956322', tone: 'amber', url: '/pages/membership/orders' },
    { key: 'photos', label: '我的电子照', icon: 'photo', color: '#356caa', tone: 'blue' }
  ];
  supportItems: MenuItem[] = [
    { key: 'status', label: '服务状态', icon: 'wifi', color: '#287c70', tone: 'teal', url: '/pages/status/index' },
    { key: 'help', label: '使用帮助', icon: 'question-circle', color: '#356caa', tone: 'blue', url: '/pages/help/index' },
    { key: 'agreement', label: '用户协议', icon: 'file-text', color: '#715a9b', tone: 'violet', url: '/pages/user-agreement/index' },
    { key: 'privacy', label: '隐私政策', icon: 'lock', color: '#287c70', tone: 'teal', url: '/pages/privacy-policy/index' },
    { key: 'contact', label: '联系与反馈', icon: 'chat', color: '#356caa', tone: 'blue' },
    { key: 'clear', label: '清理本地照片', icon: 'trash', color: '#956322', tone: 'amber' }
  ];
  get memberTitle() {
    if (this.membershipError) return '会员状态暂不可用';
    if (!this.memberStatus) return '正在查询会员状态';
    return this.memberStatus.active ? '会员已开通' : this.memberStatus.status === 'expired' ? '会员已到期' : '会员免广告保存';
  }
  get memberDescription() {
    if (this.membershipError) return '进入会员中心可重试';
    if (!this.memberStatus) return '请稍候';
    return this.memberStatus.active ? '有效期至 ' + formatMemberDate(this.memberStatus.expires_at) : '保存照片时，无需观看广告';
  }
  onShow() { this.electronicCount = ElectronicPhotoManager.getAll().length; this.loadMembership(); this.loadProfile(); }
  onHide() { this.memberSequence++; this.profileSequence++; }
  async loadProfile() {
    const sequence = ++this.profileSequence;
    this.memberRef = ''; this.profileError = false;
    try {
      const profile = await getMembershipProfile();
      if (!profile || !/^[a-f0-9]{16}$/.test(profile.user_ref)) throw new Error('会员编号无效');
      if (sequence === this.profileSequence) this.memberRef = profile.user_ref;
    } catch (_) { if (sequence === this.profileSequence) this.profileError = true; }
  }
  copyMemberRef() {
    if (!this.memberRef) return;
    uni.setClipboardData({
      data: this.memberRef,
      success: () => uni.showToast({ title: '会员编号已复制', icon: 'success' }),
      fail: () => uni.showToast({ title: '复制失败，请重试', icon: 'none' })
    });
  }
  async loadMembership() {
    const sequence = ++this.memberSequence;
    this.memberStatus = null; this.membershipError = false;
    try { const status = await getMembershipStatus(); if (sequence === this.memberSequence) this.memberStatus = status; }
    catch (_) { if (sequence === this.memberSequence) this.membershipError = true; }
  }
  open(url: string) { uni.navigateTo({ url }); }
  openItem(item: MenuItem) {
    if (item.url) this.open(item.url);
    else if (item.key === 'photos') this.electronic();
    else if (item.key === 'contact') this.previewQrcode();
    else if (item.key === 'clear') this.clearCache();
  }
  electronic() { uni.switchTab({ url: '/pages/electronic/index' }); }
  previewQrcode() { uni.previewImage({ urls: ['/static/qrcode.jpg'], current: '/static/qrcode.jpg' }); }
  clearCache() {
    uni.showModal({ title: '确认清理', content: '将清理本地电子照、照片历史和临时图片，不影响手机相册。', success: async res => {
      if (!res.confirm) return;
      try {
        if (!ElectronicPhotoManager.clear()) throw new Error('电子照清理失败');
        StorageManager.clearPhotoHistory();
        uni.removeStorageSync('electronic_photo_history');
        await clearTemporaryImages();
        this.electronicCount = ElectronicPhotoManager.getAll().length;
        uni.showToast({ title: '清理成功', icon: 'success' });
      } catch (error: any) {
        this.electronicCount = ElectronicPhotoManager.getAll().length;
        uni.showModal({ title: '清理未完成', content: error.message || '请稍后重试', showCancel: false });
      }
    } });
  }
  onShareTimeline() { return { title: '小七快照拍 - 专业证件照制作', imageUrl: '/static/example.jpeg' }; }
  onShareAppMessage() { return { title: '小七快照拍 - 专业证件照制作', path: '/pages/index/index', imageUrl: '/static/example.jpeg' }; }
}
</script>

<style lang="scss" scoped>
@import '@/assets/design-tokens.scss';
.page { min-height: 100vh; box-sizing: border-box; padding: 32rpx 32rpx 50rpx; background: $page; color: $ink; }
.page-heading { display: flex; justify-content: space-between; align-items: center; margin: 4rpx 0 26rpx; }.title { font-size: 46rpx; font-weight: 700; line-height: 1.25; }.subtitle { margin-top: 8rpx; color: $muted; font-size: 24rpx; }.heading-mark { display: flex; align-items: center; justify-content: center; width: 58rpx; height: 58rpx; border-radius: 19rpx; background: $brand-soft; }
.profile-card { @include card; display: flex; align-items: center; padding: 26rpx; gap: 20rpx; }.avatar { width: 96rpx; height: 96rpx; flex-shrink: 0; border-radius: 24rpx; background: #f4f5f6; }.profile-copy { flex: 1; min-width: 0; }.profile-name { font-size: 31rpx; font-weight: 700; }.profile-id { color: $muted; font-size: 22rpx; margin-top: 9rpx; line-height: 1.5; word-break: break-all; }.profile-id-action { display: inline-block; margin: 4rpx 0 0; padding: 0; min-height: 44rpx; line-height: 44rpx; background: transparent; color: $brand; font-size: 22rpx; text-align: left; }.profile-id-action::after { border: 0; }.profile-photo-count { display: flex; flex-direction: column; align-items: center; flex-shrink: 0; padding: 8rpx 8rpx 8rpx 20rpx; border-left: 1rpx solid $border; }.profile-photo-value { font-size: 29rpx; font-weight: 700; color: $ink; }.profile-photo-label { color: $muted; font-size: 21rpx; margin-top: 5rpx; }
.member-banner { position: relative; overflow: hidden; margin-top: 20rpx; padding: 28rpx; border-radius: 24rpx; background: linear-gradient(115deg, #fff3f0, #fbe2dd); }.member-glow { position: absolute; border-radius: 50%; background: rgba(255,255,255,.45); }.member-glow-one { width: 150rpx; height: 150rpx; right: -36rpx; top: -60rpx; }.member-glow-two { width: 70rpx; height: 70rpx; right: 84rpx; bottom: -35rpx; }.member-top { position: relative; display: flex; align-items: center; gap: 18rpx; }.member-icon { display: flex; align-items: center; justify-content: center; width: 76rpx; height: 76rpx; flex-shrink: 0; border-radius: 22rpx; background: rgba(255,255,255,.72); }.member-copy { flex: 1; min-width: 0; }.member-title { font-weight: 700; font-size: 30rpx; }.member-description { color: #725c59; font-size: 23rpx; margin-top: 7rpx; line-height: 1.5; }.member-footer { position: relative; display: flex; justify-content: space-between; align-items: center; gap: 12rpx; border-top: 1rpx solid rgba(204,61,53,.12); margin-top: 22rpx; padding-top: 18rpx; font-size: 22rpx; }.member-benefit { color: #84534d; }.member-action { color: #a73730; font-weight: 600; }
.section-heading { display: flex; justify-content: space-between; align-items: center; margin: 36rpx 4rpx 18rpx; font-size: 29rpx; font-weight: 700; }.section-subtitle { color: $muted; font-size: 22rpx; font-weight: 400; }.menu { @include card; overflow: hidden; }.menu-item { display: flex; justify-content: space-between; align-items: center; min-height: 100rpx; padding: 0 24rpx; box-sizing: border-box; }.menu-item + .menu-item { border-top: 1rpx solid $border; }.menu-item-hover { background: #f9f8f7; }.menu-left, .menu-end { display: flex; align-items: center; gap: 18rpx; }.menu-title { font-size: 27rpx; }.menu-end { color: $muted; font-size: 23rpx; }.menu-icon { width: 58rpx; height: 58rpx; border-radius: 18rpx; display: flex; align-items: center; justify-content: center; }.menu-icon.rose { background: $brand-soft; }.menu-icon.blue { background: $blue-soft; }.menu-icon.teal { background: $teal-soft; }.menu-icon.violet { background: $violet-soft; }.menu-icon.amber { background: $amber-soft; }
.page-footer { padding: 38rpx 0 8rpx; color: #8b8f95; text-align: center; font-size: 22rpx; }
</style>
