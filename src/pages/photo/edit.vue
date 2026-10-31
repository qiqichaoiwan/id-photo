<template>
  <view class="page">
    <view class="photo-wrapper">
      <view class="photo-container" :style="'background-color:' + IDPhotoForm.color + ';width:' + previewWidth + 'rpx;height:' + previewHeight + 'rpx'">
        <image class="photo" :src="currentPath" mode="aspectFit" />
      </view>
    </view>
    <view class="photo-meta"><view class="meta-name"><u-icon name="file-text" size="19" color="#666b73" /><text>{{ photoSize.name }}</text></view><text class="muted">{{ actualDimensions || '读取图片尺寸中' }}</text></view>

    <view class="section-card">
      <view class="section-title">背景颜色</view>
      <view class="color-grid">
        <view v-for="item in visibleColors" :key="item.color" class="color-option" @click="changeBackgroudColor(item.color)">
          <view class="color-circle" :class="{ selected: IDPhotoForm.color === item.color }" :style="'background-color:' + item.color"><text v-if="IDPhotoForm.color === item.color" class="check-icon" :class="{ dark: item.color === '#FFFFFF' }">✓</text></view>
          <text class="color-label">{{ item.name }}</text>
        </view>
        <view class="color-option" @click="toggleMoreColors"><view class="color-circle more-color">{{ showMoreColors ? '−' : '···' }}</view><text class="color-label">{{ showMoreColors ? '收起' : '更多' }}</text></view>
      </view>
    </view>

    <view class="section-card">
      <view class="section-title">输出方式</view>
      <view class="output-tabs"><view :class="{ active: outputMode === 'photo' }" @click="setOutputMode('photo')">电子照</view><view :class="{ active: outputMode === 'layout' }" @click="setOutputMode('layout')">打印排版</view></view>
      <view v-if="outputMode === 'layout'" class="setting-row"><text>冲印相纸</text><picker :range="papers" range-key="label" :value="paperIndex" @change="onPaperChange"><text class="muted">{{ papers[paperIndex].label }} ▾</text></picker></view>
      <view v-if="outputMode === 'layout'" class="setting-row"><text>显示裁剪线</text><switch :checked="cropLine" color="#cc3d35" @change="onCropLineChange" /></view>
    </view>
    <view class="section-card settings-card">
      <view class="settings-heading" @click="settingsExpanded = !settingsExpanded"><text>更多设置</text><u-icon :name="settingsExpanded ? 'arrow-up' : 'arrow-down'" size="16" color="#666b73" /></view>
      <view v-if="settingsExpanded" class="setting-row"><view><text class="setting-name">高清模式</text><text class="setting-hint">输出更高分辨率照片</text></view><switch :checked="isHd" color="#cc3d35" @change="onHdChange" /></view>
      <view v-if="settingsExpanded && outputMode === 'photo'" class="setting-row"><view><text class="setting-name">保存到电子照</text><text class="setting-hint">同时保存在本机，方便下次使用</text></view><switch :checked="saveToElectronic" color="#cc3d35" @change="onSaveToElectronicChange" /></view>
    </view>

    <view class="bottom-actions"><view class="save-hint">{{ accessHint }}</view><view class="primary-button" :class="{ disabled: busy }" @click="save">{{ busy ? '正在处理...' : saveButtonText }}</view></view>
    <LoadingOverlay :show="processing" :text="outputMode === 'layout' ? '正在生成排版照' : '正在处理照片'" tip="照片处理中，请稍候" />
    <button v-show="false" open-type="share" />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from 'vue-property-decorator';
import { Getter, Mutation } from 'vuex-class';
import { AddBackgroudColor, GenerateLayoutPhoto } from '@/api/photo';
import { PhotoSize } from '@/model/PhotoSize';
import { PhotoPath } from '@/model/Interfaces';
import { ElectronicPhotoManager } from '@/utils/electronic-photo';
import StorageManager from '@/utils/storage';
import { adManager } from '@/utils/ad-manager';
import { getMembershipStatus } from '@/api/membership';
import { writeTemporaryImage, removeTemporaryImage } from '@/utils/image-file';
import LoadingOverlay from '@/components/LoadingOverlay.vue';

const colors = [
  { name: '白色', color: '#FFFFFF' }, { name: '蓝色', color: '#438edb' }, { name: '红色', color: '#D9001B' },
  { name: '浅蓝', color: '#7ec8e8' }, { name: '灰色', color: '#b8b8b8' }, { name: '深红', color: '#a8000f' },
  { name: '深蓝', color: '#1a3a5c' }, { name: '粉色', color: '#ffb6c1' }
];

@Component({ components: { LoadingOverlay } })
export default class PhotoEdit extends Vue {
  @Getter('photoConfig') photoSize!: PhotoSize;
  @Getter('photoPath') photoPath!: PhotoPath;
  @Mutation('SET_PHOTO_PATH') setPhotoPath!: (data: PhotoPath) => void;
  IDPhotoForm: any = { color: '#FFFFFF', kb: undefined, render: 0 };
  isHd = true; saveToElectronic = false; busy = false; processing = false; cropLine = false;
  outputMode = 'photo'; showMoreColors = false; settingsExpanded = false; paperIndex = 0;
  actualDimensions = ''; memberState: 'member' | 'ordinary' | 'unknown' = 'unknown';
  rewardedKey = '';
  papers = [{ label: '六寸 (4R)', value: '4r' }, { label: '五寸 (3R)', value: '3r' }, { label: 'A4', value: 'a4' }];
  get visibleColors() { return this.showMoreColors ? colors : colors.slice(0, 3); }
  get currentPath() { if (!this.photoPath) return ''; return this.isHd && this.photoPath.base64HDPath ? this.photoPath.base64HDPath : this.photoPath.base64Path; }
  get previewWidth(): number { const ratio = this.photoSize.pxWidth / this.photoSize.pxHeight; return Math.round(Math.min(560, 650 * ratio)); }
  get previewHeight(): number { const ratio = this.photoSize.pxWidth / this.photoSize.pxHeight; return Math.round(Math.min(650, 560 / ratio)); }
  get accessHint() { return this.memberState === 'member' ? '会员免广告保存' : this.memberState === 'ordinary' ? '观看完整广告后保存' : '保存前将确认会员状态'; }
  get saveButtonText() { return (this.memberState === 'member' ? '直接保存' : '保存') + (this.outputMode === 'layout' ? '排版照' : '电子照'); }
  get saveKey() { return JSON.stringify([this.currentPath, this.IDPhotoForm.color, this.outputMode, this.paperIndex, this.cropLine]); }
  onShow() { this.refreshDimensions(); this.refreshMembership(); }
  onUnload() {
    if (this.photoPath) { removeTemporaryImage(this.photoPath.base64Path); removeTemporaryImage(this.photoPath.base64HDPath); }
    this.setPhotoPath({ base64: '', base64HD: '', base64Path: '', base64HDPath: '' });
  }
  async refreshMembership() { try { this.memberState = (await getMembershipStatus()).active ? 'member' : 'ordinary'; } catch (_) { this.memberState = 'unknown'; } }
  refreshDimensions() { const path = this.currentPath; this.actualDimensions = ''; if (!path) return; uni.getImageInfo({ src: path, success: (info: any) => { if (path === this.currentPath) this.actualDimensions = `${info.width}×${info.height} px`; } }); }
  changeBackgroudColor(color: string) { if (!this.busy) this.IDPhotoForm.color = color; }
  toggleMoreColors() { if (!this.busy) this.showMoreColors = !this.showMoreColors; }
  setOutputMode(mode: string) { if (!this.busy) this.outputMode = mode; }
  onPaperChange(event: any) { if (!this.busy) this.paperIndex = Number(event.detail.value); }
  onCropLineChange(event: any) { if (!this.busy) this.cropLine = event.detail.value; }
  onHdChange(event: any) { if (!this.busy) { this.isHd = event.detail.value; this.refreshDimensions(); } }
  onSaveToElectronicChange(event: any) { if (!this.busy) this.saveToElectronic = event.detail.value; }
  async save() {
    if (this.busy) return;
    this.busy = true;
    const layout = this.outputMode === 'layout';
    const key = this.saveKey;
    let colorPath = ''; let resultPath = '';
    try {
      const imagePath = this.currentPath;
      if (!imagePath) throw new Error('图片路径无效，请重新制作');
      if (this.rewardedKey !== key) {
        const access = await adManager.authorize();
        if (!access) return;
        this.memberState = access === 'member' ? 'member' : 'ordinary';
        if (access === 'ad') this.rewardedKey = key;
      }
      this.processing = true;
      const dpi = this.photoSize.dpi || 300;
      const colorForm: any = { color: this.IDPhotoForm.color.replace('#', ''), dpi };
      if (this.IDPhotoForm.kb !== undefined) colorForm.kb = this.IDPhotoForm.kb;
      if (this.IDPhotoForm.render) colorForm.render = this.IDPhotoForm.render;
      const color = await AddBackgroudColor(colorForm, 'input_image', imagePath);
      if (!color.image_base64) throw new Error('服务器未返回照片');
      colorPath = await writeTemporaryImage(color.image_base64, 'color');
      let output = color.image_base64;
      if (layout) {
        const result = await GenerateLayoutPhoto({ height: this.photoSize.pxHeight, width: this.photoSize.pxWidth, dpi, paper_size: this.papers[this.paperIndex].value, crop_line: this.cropLine }, 'input_image', colorPath);
        if (!result.image_base64) throw new Error('服务器未返回排版照');
        output = result.image_base64; resultPath = await writeTemporaryImage(output, 'layout');
      } else resultPath = colorPath;
      this.processing = false;
      await new Promise<void>((resolve, reject) => uni.saveImageToPhotosAlbum({ filePath: resultPath, success: () => resolve(), fail: (err: any) => reject(new Error(err.errMsg && err.errMsg.indexOf('cancel') >= 0 ? '已取消保存' : '保存失败，请检查相册权限')) }));
      this.rewardedKey = '';
      try { StorageManager.recordPhotoCreated(); } catch (_) { /* statistics are optional */ }
      if (!layout && this.saveToElectronic) this.saveToElectronicPhoto(output);
      else uni.showToast({ title: '保存成功', icon: 'success' });
    } catch (err: any) { uni.showModal({ title: '处理失败', content: err.message || '操作失败，请重试', showCancel: false }); }
    finally { this.processing = false; removeTemporaryImage(colorPath); if (resultPath !== colorPath) removeTemporaryImage(resultPath); this.busy = false; }
  }
  saveToElectronicPhoto(base64Data: string) {
    if (!ElectronicPhotoManager.canSaveMore()) { uni.showModal({ title: '已保存到相册', content: '电子照已达上限（2张），请先删除后再保存到电子照', showCancel: false }); return; }
    const photoData = { name: `${this.photoSize.name}证件照`, size: this.actualDimensions || `${this.photoSize.pxWidth}×${this.photoSize.pxHeight}`, color: this.IDPhotoForm.color, hdBase64: base64Data, sdBase64: base64Data };
    if (ElectronicPhotoManager.save(photoData)) { uni.showToast({ title: '已保存到电子照', icon: 'success' }); }
    else uni.showModal({ title: '已保存到相册', content: '保存到电子照失败，请检查设备存储空间', showCancel: false });
  }
  onShareTimeline() { return { title: '小七快照拍 - 专业证件照制作', imageUrl: '/static/example.jpeg' }; }
  onShareAppMessage() { return { title: '小七快照拍 - 专业证件照制作', path: '/pages/index/index', imageUrl: '/static/example.jpeg' }; }
}
</script>

<style lang="scss" scoped>
@import '@/assets/design-tokens.scss';
.page { min-height: 100vh; padding: 24rpx 28rpx calc(210rpx + env(safe-area-inset-bottom)); box-sizing: border-box; background: $page; color: $ink; }
.photo-wrapper { display: flex; justify-content: center; margin-bottom: 12rpx; }.photo-container { position: relative; overflow: hidden; border-radius: 14rpx; box-shadow: 0 4rpx 20rpx rgba(0,0,0,.05); }.photo { width: 100%; height: 100%; }
.photo-meta { @include card; display: flex; justify-content: space-between; align-items: center; padding: 20rpx 24rpx; font-size: 27rpx; margin-bottom: 20rpx; }.meta-name { display: flex; align-items: center; gap: 14rpx; font-weight: 600; }.muted { color: $muted; font-size: 25rpx; }
.section-card { @include card; padding: 26rpx 28rpx; margin-bottom: 20rpx; }.section-title { font-weight: 600; font-size: 30rpx; margin-bottom: 22rpx; }.color-grid { display: flex; flex-wrap: wrap; }.color-option { display: flex; flex-direction: column; align-items: center; width: 25%; padding-bottom: 8rpx; }.color-circle { width: 72rpx; height: 72rpx; border-radius: 50%; border: 2rpx solid $border; box-sizing: border-box; display: flex; align-items: center; justify-content: center; }.color-circle.selected { box-shadow: 0 0 0 4rpx #fff, 0 0 0 7rpx $brand; }.check-icon { color: #fff; font-size: 29rpx; font-weight: 700; }.check-icon.dark { color: $brand; }.color-label { margin-top: 12rpx; color: $muted; font-size: 24rpx; }.more-color { background: #edeef0; color: $muted; font-weight: 700; }
.output-tabs { display: flex; background: #f6f6f6; border: 1rpx solid #d5d7db; border-radius: 14rpx; overflow: hidden; }.output-tabs view { flex: 1; text-align: center; padding: 19rpx 0; font-size: 28rpx; }.output-tabs .active { color: $brand; background: #fff5f3; box-shadow: inset 0 0 0 2rpx $brand; border-radius: 14rpx; font-weight: 600; }
.settings-card { padding: 0 28rpx; }.settings-heading, .setting-row { display: flex; align-items: center; justify-content: space-between; min-height: 92rpx; font-size: 27rpx; }.settings-heading { font-weight: 600; }.setting-row { border-top: 1rpx solid $border; }.setting-name, .setting-hint { display: block; }.setting-hint { font-size: 23rpx; color: $muted; margin-top: 6rpx; }
.bottom-actions { position: fixed; left: 0; right: 0; bottom: 0; padding: 12rpx 28rpx calc(20rpx + env(safe-area-inset-bottom)); background: $page; }.save-hint { text-align: center; color: $muted; font-size: 24rpx; margin-bottom: 14rpx; }.primary-button { @include primary-button; }.disabled { opacity: .6; }
</style>
