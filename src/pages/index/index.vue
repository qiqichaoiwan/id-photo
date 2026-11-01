<template>
  <view class="home">
    <view class="hero">
      <view class="hero-copy">
        <text class="hero-title">制作证件照</text>
        <text class="hero-subtitle">选择规格，轻松完成</text>
      </view>
      <view class="hero-art" aria-hidden="true">
        <view class="art-card art-card-back"></view>
        <view class="art-card art-card-front"><image src="/static/example.jpeg" mode="aspectFill" /></view>
      </view>
    </view>

    <view class="search-box">
      <u-icon name="search" size="20" color="#777d85" />
      <input v-model="searchText" confirm-type="search" placeholder="搜索尺寸或用途" placeholder-class="search-placeholder" />
      <view v-if="searchText" class="clear-search" @click="searchText = ''"><u-icon name="close-circle" size="18" color="#999" /></view>
    </view>
    <service-status-banner :state="serviceState" />
    <view class="scope-note"><u-icon name="lock" size="16" color="#287c70" /><text>仅提供个人图片制作与编辑，不提供公开发布或内容分发</text></view>

    <view v-if="!searchText" class="section">
      <view class="section-heading"><text>常用规格</text><view class="section-more" @click="showAllSizes"><text>更多</text><u-icon name="arrow-right" size="14" color="#737780" /></view></view>
      <view class="size-grid">
        <view v-for="(item, index) in commonSizes" :key="item.id" class="size-tile" @click="selectSize(item)">
          <view class="tile-icon" :class="'tone-' + index"><u-icon name="account-fill" size="23" :color="toneColors[index]" /></view>
          <text class="size-name">{{ item.name }}</text>
          <text class="size-detail">{{ item.mmWidth }}×{{ item.mmHeight }} mm</text>
          <text class="size-detail">{{ item.pxWidth }}×{{ item.pxHeight }} px</text>
        </view>
        <view class="size-tile" @click="customOpen = true">
          <view class="tile-icon tone-3"><u-icon name="plus-square-fill" size="23" color="#715a9b" /></view>
          <text class="size-name">自定义</text><text class="size-detail">输入像素尺寸</text>
        </view>
      </view>
    </view>

    <view v-if="!searchText" class="section">
      <view class="section-heading"><text>按用途选择</text><view class="section-more" @click="showAllSizes"><text>全部</text><u-icon name="arrow-right" size="14" color="#737780" /></view></view>
      <view class="category-grid">
        <view v-for="(group, index) in categories" :key="group.name" class="category-tile" @click="selectCategory(group.name)">
          <view class="tile-icon" :class="'tone-' + index"><u-icon :name="group.icon" size="23" :color="toneColors[index]" /></view><text>{{ group.name }}</text>
        </view>
      </view>
    </view>

    <view v-if="searchText || selectedCategory" class="section results">
      <view class="section-heading"><text>{{ searchText ? '搜索结果' : selectedCategory }}</text><text v-if="selectedCategory" class="section-more" @click="selectedCategory = ''">收起</text></view>
      <view v-if="filteredSizes.length" class="result-list">
        <view v-for="(item, index) in filteredSizes" :key="index" class="result-row" @click="selectSize(item)">
          <view><text class="result-name">{{ item.name }}</text><text class="result-size">{{ item.mmWidth }}×{{ item.mmHeight }} mm · {{ item.pxWidth }}×{{ item.pxHeight }} px</text></view>
          <u-icon name="arrow-right" size="15" color="#8b8f95" />
        </view>
      </view>
      <view v-else class="empty-result">没有找到匹配的规格，可以试试其他关键词或自定义尺寸。</view>
      <view v-if="hasMoreSizes" class="load-more" @click="resultLimit += 60">查看更多规格</view>
    </view>

    <view class="section">
      <view class="section-heading"><text>实用工具</text></view>
      <view class="tool-grid">
        <view class="tool-tile" @click="openTool('/pages/matting/index')"><view class="tile-icon tone-1"><u-icon name="cut" size="22" color="#356caa" /></view><text>人像抠图</text><u-icon name="arrow-right" size="14" color="#8b8f95" /></view>
        <view class="tool-tile" @click="openTool('/pages/watermark/index')"><view class="tile-icon tone-2"><u-icon name="photo" size="22" color="#287c70" /></view><text>图片加水印</text><u-icon name="arrow-right" size="14" color="#8b8f95" /></view>
        <view class="tool-tile" @click="openTool('/pages/convert/index')"><view class="tile-icon tone-3"><u-icon name="file-text" size="22" color="#715a9b" /></view><text>格式与压缩</text><u-icon name="arrow-right" size="14" color="#8b8f95" /></view>
      </view>
    </view>

    <u-popup :show="customOpen" mode="bottom" round="16" @close="customOpen = false">
      <view class="custom-form">
        <view class="custom-heading"><text>自定义尺寸</text><u-icon name="close" size="20" @click="customOpen = false" /></view>
        <view class="custom-row"><text>宽度</text><input v-model="customWidth" type="number" placeholder="80–1200" /><text>px</text></view>
        <view class="custom-row"><text>高度</text><input v-model="customHeight" type="number" placeholder="80–1200" /><text>px</text></view>
        <view class="custom-note">按 300 DPI 计算实际尺寸</view>
        <view class="primary-button" @click="applyCustomSize">开始制作</view>
      </view>
    </u-popup>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from 'vue-property-decorator';
import { Mutation } from 'vuex-class';
import { PhotoSize, photoSizes, allSize, getPhotoSize } from '@/model/PhotoSize';
import { fetchServiceStatus } from '@/api/service-status';
import ServiceStatusBanner from '@/components/ServiceStatusBanner.vue';

@Component({ components: { ServiceStatusBanner } })
export default class Index extends Vue {
  @Mutation('SET_PHOTO_SIZE') setPhotoSize!: (value: PhotoSize) => void;
  searchText = '';
  selectedCategory = '';
  customOpen = false;
  customWidth = '';
  customHeight = '';
  resultLimit = 60;
  toneColors = ['#cc3d35', '#356caa', '#287c70', '#715a9b'];
  serviceState: 'checking' | 'ok' | 'degraded' | 'offline' = 'checking';
  statusTimer: any = null;
  statusSequence = 0;
  categories = [
    { name: '考试报名', icon: 'file-text', ids: [1, 6, 7, 10] },
    { name: '证件办理', icon: 'bag', ids: [2, 9] },
    { name: '学习工作', icon: 'account', ids: [5, 8] },
    { name: '更多规格', icon: 'grid', ids: [] }
  ];

  get commonSizes(): PhotoSize[] {
    return [11, 12, 3].map(id => getPhotoSize(id)).filter((item): item is PhotoSize => !!item);
  }

  get matchingSizes(): PhotoSize[] {
    const query = this.searchText.trim().toLowerCase();
    if (query) return allSize.filter(item => `${item.name || ''} ${item.mmWidth} ${item.mmHeight} ${item.pxWidth} ${item.pxHeight}`.toLowerCase().indexOf(query) >= 0);
    const group = this.categories.find(item => item.name === this.selectedCategory);
    return !group || !group.ids.length ? allSize : photoSizes.filter(item => item.id !== undefined && group.ids.indexOf(item.id) >= 0);
  }

  get filteredSizes(): PhotoSize[] { return this.matchingSizes.slice(0, this.resultLimit); }
  get hasMoreSizes(): boolean { return this.matchingSizes.length > this.resultLimit; }

  onShow() { this.stopStatusUpdates(); this.refreshServiceStatus(); this.statusTimer = setInterval(() => this.refreshServiceStatus(), 60000); }
  onHide() { this.stopStatusUpdates(); }
  onUnload() { this.stopStatusUpdates(); }
  stopStatusUpdates() { if (this.statusTimer) clearInterval(this.statusTimer); this.statusTimer = null; this.statusSequence++; }
  async refreshServiceStatus() {
    const sequence = ++this.statusSequence;
    try { const status = await fetchServiceStatus(); if (sequence === this.statusSequence) this.serviceState = status.status; }
    catch (_) { if (sequence === this.statusSequence) this.serviceState = 'offline'; }
  }

  selectSize(size: PhotoSize) {
    this.setPhotoSize(size);
    uni.navigateTo({ url: '/pages/photo/index' });
  }
  showAllSizes() { this.resultLimit = 60; this.searchText = ''; this.selectedCategory = '全部规格'; }
  selectCategory(name: string) { this.resultLimit = 60; this.searchText = ''; this.selectedCategory = name; }
  openTool(url: string) { uni.navigateTo({ url }); }
  applyCustomSize() {
    const width = Number(this.customWidth), height = Number(this.customHeight);
    if (!Number.isInteger(width) || !Number.isInteger(height) || width < 80 || height < 80 || width > 1200 || height > 1200) {
      uni.showToast({ title: '宽高请输入 80–1200 的整数', icon: 'none' }); return;
    }
    this.customOpen = false;
    this.selectSize({ name: '自定义尺寸', pxWidth: width, pxHeight: height, dpi: 300,
      mmWidth: Math.round(width * 25.4 / 300), mmHeight: Math.round(height * 25.4 / 300) });
  }
  onShareAppMessage() { return { title: '小七快照拍 - 轻松制作证件照', path: '/pages/index/index', imageUrl: '/static/example.jpeg' }; }
}
</script>

<style lang="scss" scoped>
@import '@/assets/design-tokens.scss';
.home { min-height: 100vh; background: $page; padding: 0 32rpx 48rpx; box-sizing: border-box; color: $ink; }
.hero { display: flex; justify-content: space-between; align-items: center; height: 250rpx; margin: 0 -32rpx; padding: 12rpx 36rpx 0; background: linear-gradient(110deg, #fff 30%, #fff1ee 100%); overflow: hidden; }
.hero-copy { display: flex; flex-direction: column; z-index: 1; }
.hero-title { font-size: 52rpx; font-weight: 700; letter-spacing: 1rpx; }
.hero-subtitle { margin-top: 12rpx; font-size: 28rpx; color: $muted; }
.hero-art { position: relative; width: 220rpx; height: 190rpx; }
.art-card { position: absolute; width: 144rpx; height: 168rpx; border-radius: 14rpx; }
.art-card-back { top: 17rpx; left: 0; background: #ffd8d1; transform: rotate(-11deg); }
.art-card-front { top: 4rpx; left: 58rpx; padding: 8rpx; box-sizing: border-box; background: #fff; box-shadow: 0 8rpx 24rpx rgba(142, 79, 70, .15); transform: rotate(8deg); overflow: hidden; }
.art-card-front image { width: 100%; height: 100%; border-radius: 8rpx; }
.search-box { display: flex; align-items: center; gap: 16rpx; height: 88rpx; padding: 0 28rpx; margin-top: -16rpx; position: relative; background: #fff; border-radius: 48rpx; box-shadow: 0 6rpx 24rpx rgba(0, 0, 0, .05); }
.search-box input { flex: 1; font-size: 28rpx; min-width: 0; }.search-placeholder { color: #8b8f95; }.clear-search { padding: 10rpx; }
.scope-note { display: flex; align-items: center; gap: 10rpx; margin-top: 18rpx; color: #536a68; font-size: 22rpx; line-height: 1.5; }
.section { margin-top: 44rpx; }.section-heading { display: flex; justify-content: space-between; align-items: center; font-size: 32rpx; font-weight: 650; margin-bottom: 22rpx; }.section-more { display: flex; align-items: center; flex-shrink: 0; gap: 4rpx; white-space: nowrap; color: $muted; font-size: 24rpx; font-weight: 400; }
.size-grid, .category-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12rpx; }
.size-tile, .category-tile { @include card; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 1rpx solid $border; text-align: center; box-sizing: border-box; }
.tile-icon { width: 60rpx; height: 60rpx; border-radius: 18rpx; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }.tone-0 { background: $brand-soft; }.tone-1 { background: $blue-soft; }.tone-2 { background: $teal-soft; }.tone-3 { background: $violet-soft; }
.size-tile { min-height: 210rpx; padding: 18rpx 5rpx; }.size-name { font-size: 26rpx; margin: 12rpx 0 8rpx; font-weight: 600; }.size-detail { color: $muted; font-size: 19rpx; line-height: 1.5; }
.category-tile { min-height: 144rpx; font-size: 23rpx; gap: 14rpx; }
.tool-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12rpx; }.tool-tile { @include card; display: flex; align-items: center; gap: 14rpx; min-height: 112rpx; padding: 0 22rpx; border: 1rpx solid $border; font-size: 27rpx; box-sizing: border-box; }.tool-tile text { flex: 1; }
.result-list { @include card; overflow: hidden; }.result-row { display: flex; align-items: center; justify-content: space-between; min-height: 104rpx; padding: 16rpx 24rpx; border-bottom: 1rpx solid $border; box-sizing: border-box; }.result-row:last-child { border-bottom: 0; }.result-name, .result-size { display: block; }.result-name { font-size: 28rpx; }.result-size { color: $muted; font-size: 23rpx; margin-top: 7rpx; }.empty-result { @include card; padding: 28rpx; color: $muted; font-size: 26rpx; line-height: 1.6; }
.load-more { text-align: center; padding: 24rpx; color: $brand; font-size: 26rpx; }
.custom-form { padding: 36rpx 32rpx calc(32rpx + env(safe-area-inset-bottom)); }.custom-heading { display: flex; justify-content: space-between; align-items: center; font-size: 34rpx; font-weight: 600; margin-bottom: 28rpx; }.custom-row { display: flex; align-items: center; gap: 18rpx; min-height: 92rpx; border-bottom: 1rpx solid $border; font-size: 28rpx; }.custom-row input { flex: 1; text-align: right; }.custom-note { font-size: 24rpx; color: $muted; margin: 20rpx 0 30rpx; }.primary-button { @include primary-button; }
</style>
