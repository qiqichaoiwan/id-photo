<template>
  <view class="page">
    <!-- 顶部标题区 -->
    <view class="header-section">
      <view class="success-icon">
        <u-icon name="checkmark" size="24" color="#287c70" />
      </view>
      <text class="header-title">水印添加成功</text>
      <text class="header-desc">图片已处理完成，可保存到相册</text>
    </view>

    <!-- 图片预览卡片 -->
    <view class="preview-card">
      <view class="card-header">
        <text class="card-title">效果预览</text>
        <view class="card-badge">
          <text class="badge-text">水印图</text>
        </view>
      </view>
      <view class="image-wrapper">
        <image 
          :src="imagePath" 
          mode="aspectFit" 
          class="preview-image"
        />
      </view>
    </view>

    <!-- 操作提示卡片 -->
    <view class="tips-card">
      <view class="tip-item">
        <view class="tip-icon"><u-icon name="checkmark-circle" size="19" color="#287c70" /></view>
        <text class="tip-text">水印已添加到图片中，原图不受影响</text>
      </view>
      <view class="tip-item">
        <view class="tip-icon"><u-icon name="photo" size="19" color="#356caa" /></view>
        <text class="tip-text">保存后可在相册中查看和分享</text>
      </view>
    </view>

    <!-- 底部操作区 -->
    <view class="bottom-actions">
      <view class="btn-secondary" @click="retake">
        <view class="btn-icon"><u-icon name="reload" size="19" color="#383e49" /></view>
        <text>重新添加</text>
      </view>
      <view class="btn-primary" @click="saveImage">
        <view class="btn-icon"><u-icon name="download" size="19" color="#ffffff" /></view>
        <text>保存图片</text>
      </view>
    </view>

    <!-- 隐藏分享按钮 -->
    <button v-show="false" open-type="share" />

    <!-- 加载页面 -->
    <LoadingOverlay :show="processing" text="正在保存照片" />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import { adManager } from '@/utils/ad-manager'
import { writeTemporaryImage, removeTemporaryImage } from '@/utils/image-file'
import LoadingOverlay from '@/components/LoadingOverlay.vue'

@Component({ components: { LoadingOverlay } })
export default class WatermarkResult extends Vue {
  imagePath: string = '';
  saving: boolean = false;
  processing: boolean = false;

  onLoad(options: any) {
    if (options.image) this.imagePath = decodeURIComponent(options.image);
  }

  onUnload() { removeTemporaryImage(this.imagePath); }
  retake() { uni.navigateBack(); }

  async saveImage() {
    if (this.saving) return;
    this.saving = true;
    let temporary = '';
    try {
      if (!this.imagePath) throw new Error('图片已失效，请重新制作');
      if (!await adManager.show()) return;
      this.processing = true;
      const path = this.imagePath.startsWith('data:image/')
        ? (temporary = await writeTemporaryImage(this.imagePath, 'watermark')) : this.imagePath;
      await new Promise<void>((resolve, reject) => uni.saveImageToPhotosAlbum({
        filePath: path, success: () => resolve(),
        fail: (err: any) => reject(new Error(err.errMsg && err.errMsg.indexOf('cancel') >= 0 ? '已取消保存' : '保存失败，请检查相册权限'))
      }));
      uni.showToast({ title: '保存成功', icon: 'success' });
    } catch (err: any) {
      uni.showModal({ title: '保存失败', content: err.message || '保存失败，请重试', showCancel: false });
    } finally { removeTemporaryImage(temporary); this.processing = false; this.saving = false; }
  }

  onShareTimeline() {
    return { title: '小七快照拍 - 专业证件照制作', imageUrl: '/static/example.jpeg' };
  }

  onShareAppMessage() {
    return { title: '小七快照拍 - 专业证件照制作', path: '/pages/index/index', imageUrl: '/static/example.jpeg' };
  }
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #faf8f8;
  padding: 24rpx;
  padding-bottom: 180rpx;
  box-sizing: border-box;
}

.header-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 0 32rpx;
}

.success-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
}

.icon-text {
  font-size: 40rpx;
  color: #fff;
  font-weight: bold;
}

.header-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #333;
  margin-bottom: 8rpx;
}

.header-desc {
  font-size: 26rpx;
  color: #999;
}

.preview-card {
  background-color: #fff;
  border-radius: 24rpx;
  padding: 28rpx;
  margin-bottom: 24rpx;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.card-badge {
  background-color: #fff5f4;
  padding: 8rpx 16rpx;
  border-radius: 20rpx;
}

.badge-text {
  font-size: 22rpx;
  color: #F77261;
  font-weight: 500;
}

.image-wrapper {
  position: relative;
  width: 100%;
  height: 400rpx;
  background-color: #f5f5f5;
  border-radius: 16rpx;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  width: 100%;
  height: 100%;
}

.tips-card {
  background-color: #fff;
  border-radius: 24rpx;
  padding: 24rpx 28rpx;
  margin-bottom: 24rpx;
}

.tip-item {
  display: flex;
  align-items: center;
  padding: 12rpx 0;
}

.tip-item:first-child {
  border-bottom: 1rpx solid #f5f5f5;
}

.tip-icon {
  font-size: 28rpx;
  margin-right: 16rpx;
}

.tip-text {
  font-size: 26rpx;
  color: #666;
}

.bottom-actions {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  padding: 20rpx 24rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background-color: #fff;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.05);
}

.btn-secondary {
  flex: 1;
  height: 88rpx;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #fff5f4;
  color: #F77261;
  font-size: 30rpx;
  font-weight: 600;
  margin-right: 20rpx;
  border: 2rpx solid #ffe0dc;
}

.btn-primary {
  flex: 1;
  height: 88rpx;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F77261;
  color: #fff;
  font-size: 30rpx;
  font-weight: 600;
}

.btn-icon {
  margin-right: 8rpx;
  font-size: 32rpx;
}

@import '@/assets/legacy-page-themes.scss';
@include result-page-theme;
</style>
