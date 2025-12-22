<template>
  <view class="page">
    <!-- 顶部标题区 -->
    <view class="header-section">
      <view class="success-icon">
        <text class="icon-text">✓</text>
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
        <text class="tip-icon">💡</text>
        <text class="tip-text">水印已添加到图片中，原图不受影响</text>
      </view>
      <view class="tip-item">
        <text class="tip-icon">📱</text>
        <text class="tip-text">保存后可在相册中查看和分享</text>
      </view>
    </view>

    <!-- 底部操作区 -->
    <view class="bottom-actions">
      <view class="btn-secondary" @click="retake">
        <text class="btn-icon">↺</text>
        <text>重新添加</text>
      </view>
      <view class="btn-primary" @click="saveImage">
        <text class="btn-icon">↓</text>
        <text>保存图片</text>
      </view>
    </view>

    <!-- 隐藏分享按钮 -->
    <button v-show="false" open-type="share" />

    <!-- 加载页面 -->
    <LoadingOverlay :show="saving" text="保存中" />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import StorageManager from '@/utils/storage'
import { adConfig } from '@/config'
import LoadingOverlay from '@/components/LoadingOverlay.vue'

@Component({ components: { LoadingOverlay } })
export default class WatermarkResult extends Vue {
  imagePath: string = '';
  base64Data: string = '';
  saving: boolean = false;
  videoAd: any = null;
  prefix = 'data:image/png;base64,';

  onLoad(options: any) {
    this.initRewardedVideoAd();
    if (options.image) {
      const imageData = decodeURIComponent(options.image);
      if (imageData.startsWith('data:image/')) {
        this.imagePath = imageData;
        this.base64Data = imageData;
      } else {
        this.imagePath = imageData;
      }
    }
  }

  initRewardedVideoAd() {
    if (wx.createRewardedVideoAd) {
      try {
        this.videoAd = wx.createRewardedVideoAd({ adUnitId: adConfig.rewardedVideoAdUnitId });
        this.videoAd.onLoad(() => console.log('广告加载成功'));
        this.videoAd.onError((err: any) => console.error('广告加载失败', err));
      } catch (e) { console.error('创建广告失败:', e); }
    }
  }

  async showRewardedVideoAd(): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.videoAd) { resolve(false); return; }
      try {
        this.videoAd.show().catch(() => {
          this.videoAd?.load().then(() => this.videoAd?.show()).catch(() => resolve(false));
        });
        const handleClose = (res: any) => {
          this.videoAd?.offClose(handleClose);
          resolve(res?.isEnded || false);
        };
        this.videoAd.onClose(handleClose);
      } catch { resolve(false); }
    });
  }

  retake() {
    uni.navigateBack();
  }

  async saveImage() {
    const adVerified = await this.showRewardedVideoAd();
    if (!adVerified) {
      uni.showToast({ title: '请看完广告后再继续', icon: 'none' });
      return;
    }

    this.saving = true;
    const that = this;

    if (this.base64Data) {
      const saveData = this.base64Data.replace(this.prefix, '');
      const tempPath = `${wx.env.USER_DATA_PATH}/watermark_${Date.now()}.png`;
      
      uni.getFileSystemManager().writeFile({
        filePath: tempPath,
        data: saveData,
        encoding: 'base64',
        success() { that.savePhotoToAlbum(tempPath); },
        fail() {
          that.saving = false;
          uni.showModal({ title: '保存失败', content: '保存发生异常', showCancel: false });
        }
      });
    } else {
      this.savePhotoToAlbum(this.imagePath);
    }
  }

  savePhotoToAlbum(tempPath: string) {
    const self = this;
    uni.saveImageToPhotosAlbum({
      filePath: tempPath,
      success() {
        try {
          StorageManager.savePhotoRecord({
            originalImage: self.base64Data,
            resultImages: { idPhoto: '', layoutPhoto: '', watermarkPhoto: self.base64Data },
            parameters: { size: null, backgroundColor: '', isHd: false }
          });
        } catch {}
        uni.showToast({ title: '保存成功', icon: 'success' });
      },
      fail(err) {
        if (err.errMsg === 'saveImageToPhotosAlbum:fail cancel') {
          uni.showToast({ title: '已取消保存', icon: 'none' });
        } else {
          uni.showModal({ title: '保存失败', content: '请授权相册权限', showCancel: false });
        }
      },
      complete() {
        self.saving = false;
        self.cleanupTempFile(tempPath);
      }
    });
  }

  cleanupTempFile(tempPath: string) {
    try {
      uni.getFileSystemManager().unlink({ filePath: tempPath, success() {}, fail() {} });
    } catch {}
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
</style>
