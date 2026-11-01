<template>
  <view class="matting-upload">
    <!-- 预览遮罩 -->
    <u-overlay :show="show" @click="show = false" :custom-style="{ backdropFilter: 'blur(20rpx)' }">
      <view class="preview-container" @click.stop>
        <view class="preview-header">
          <view class="preview-title">照片预览</view>
          <u-icon name="close" size="24" color="#fff" @click="show = false" />
        </view>
        <view class="preview-image-container">
          <u-image :src="imagePath" mode="aspectFit" height="800rpx" radius="20rpx" />
        </view>
        <view class="preview-actions">
          <u-button :plain="true" text="重新选择" :custom-style="secondaryButtonStyle" @click="show = false" />
          <u-button color="#cc3d35" text="确认选择" :custom-style="primaryButtonStyle" @click="confirmSelect" />
        </view>
      </view>
    </u-overlay>

    <!-- 主要内容区域 -->
    <view class="content-container">
      <!-- 功能介绍卡片 -->
      <view class="feature-card">
        <view class="feature-header">
          <u-icon name="cut" color="#cc3d35" size="20" />
          <text class="feature-title">人像抠图</text>
        </view>
        
        <view class="feature-list">
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="scan" size="18" color="#356caa" />
            </view>
            <view class="feature-content">
              <view class="feature-name">人像抠图</view>
              <view class="feature-desc">提取人物轮廓，去除照片背景</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#287c70" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="grid" size="18" color="#287c70" />
            </view>
            <view class="feature-content">
              <view class="feature-name">处理效果可选</view>
              <view class="feature-desc">支持高精度、标准和增强处理</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#287c70" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="checkmark-circle" size="18" color="#715a9b" />
            </view>
            <view class="feature-content">
              <view class="feature-name">透明背景</view>
              <view class="feature-desc">输出PNG格式，透明背景便于后续编辑</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#287c70" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="download" size="18" color="#956322" />
            </view>
            <view class="feature-content">
              <view class="feature-name">保留图片尺寸</view>
              <view class="feature-desc">输出结果保留原始像素尺寸</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#287c70" size="16" />
            </view>
          </view>
        </view>
      </view>

      <!-- 拍照建议卡片 -->
      <view class="tips-card">
        <view class="tips-header">
          <u-icon name="info-circle-fill" color="#956322" size="20" />
          <text class="tips-title">抠图建议</text>
        </view>
        
        <view class="tips-list">
          <view class="tip-item">
            <view class="tip-number">1</view>
            <text class="tip-text">选择背景简洁的照片，人物轮廓清晰</text>
          </view>
          <view class="tip-item">
            <view class="tip-number">2</view>
            <text class="tip-text">避免复杂背景，单一颜色效果更佳</text>
          </view>
          <view class="tip-item">
            <view class="tip-number">3</view>
            <text class="tip-text">光线充足，避免过暗或过曝的照片</text>
          </view>
          <view class="tip-item">
            <view class="tip-number">4</view>
            <text class="tip-text">建议人物占画面60%以上，便于提取人物轮廓</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部操作区域 -->
    <view class="action-container">
      <view class="action-tips">
        <u-icon name="info-circle-fill" color="#8C8C8C" size="14" />
        <text class="tips-text">请选择清晰的人像照片，效果更佳</text>
      </view>
      <view class="action-buttons">
        <u-button 
          :plain="true" 
          text="从相册选择" 
          :custom-style="secondaryButtonStyle" 
          @click="chooseImage('album')"
        />
        <u-button 
          color="#cc3d35"
          text="立即拍摄" 
          :custom-style="primaryButtonStyle" 
          @click="chooseImage('camera')"
        />
      </view>
    </view>

    <PhotoCamera v-if="showCamera" title="人像拍摄" preview-tip="检查人像完整、清晰且光线均匀"
      @close="showCamera = false" @select="onCameraSelect" />

    <!-- 原生分享按钮 - 使用open-type="share"直接触发分享 -->
    <button v-show="false" open-type="share" class="native-share-button" @getuserinfo="onShareSuccess">
      <u-icon name="share" size="20" color="white" />
    </button>

    <!-- 加载页面 -->
    <LoadingOverlay :show="loading" text="正在提取人像" tip="请稍候，正在为您处理照片" />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import LoadingOverlay from '@/components/LoadingOverlay.vue';
import PhotoCamera from '@/components/PhotoCamera.vue';

@Component({ components: { LoadingOverlay, PhotoCamera } })
export default class MattingUpload extends Vue {
  // 按钮样式
  primaryButtonStyle = {
    width: '280rpx',
    height: '88rpx',
    borderRadius: '20rpx',
    fontSize: '30rpx',
    fontWeight: '600',
    boxShadow: 'none'
  };
  
  secondaryButtonStyle = {
    width: '280rpx',
    height: '88rpx',
    borderRadius: '20rpx',
    fontSize: '30rpx',
    fontWeight: '600',
    borderColor: '#cc3d35',
    color: '#cc3d35'
  };

  // 本地文件地址
  imagePath: string = '';
  
  // 图片预览遮罩
  show: boolean = false;
  
  // 加载动画
  loading: boolean = false;
  
  showCamera: boolean = false;

  mounted() {
  }

  /**
   * 选择图片
   */
  chooseImage(type: 'album' | 'camera') {
    if (type === 'camera') {
      this.openCamera();
      return;
    }

    // 从相册选择
    // #ifdef H5
    uni.chooseImage({
      count: 1,
      sourceType: [type],
      success: (res) => {
        const path = res.tempFilePaths[0];
        this.imagePath = path;
        this.show = true;
      }
    });
    // #endif

    // #ifdef MP-WEIXIN
    uni.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: [type],
      success: (res) => {
        const path = res.tempFiles[0].tempFilePath;
        this.imagePath = path;
        this.show = true;
      }
    });
    // #endif
  }

  openCamera() { this.showCamera = true; }
  onCameraSelect(path: string) {
    this.showCamera = false;
    this.imagePath = path;
    this.show = true;
  }

  /**
   * 确认选择
   */
  confirmSelect() {
    // 跳转到抠图处理页面，传递图片路径
    uni.navigateTo({
      url: `/pages/matting/index?image=${encodeURIComponent(this.imagePath)}`
    });
  }

  /**
   * 分享成功回调 - 原生分享按钮使用
   */
  onShareSuccess() {
    console.log('分享成功回调');
    uni.showToast({
      title: '分享成功',
      icon: 'success',
      duration: 2000
    });
  }

  /**
   * 分享到朋友圈方法 - 供微信小程序调用
   */
  onShareTimeline() {
    return {
      title: '小七快照拍 - 专业证件照制作',
      query: '',
      imageUrl: '/static/example.jpeg'
    };
  }

  /**
   * 页面分享方法 - 供微信小程序调用
   */
  onShareAppMessage() {
    return {
      title: '小七快照拍 - 专业证件照制作',
      path: '/pages/index/index',
      imageUrl: '/static/example.jpeg'
    };
  }
}
</script>

<style lang="scss" scoped>
// 大师级设计变量
$primary-color: #cc3d35;
$primary-light: #FF9A8B;
$primary-dark: #E55A4A;
$success-color: #287c70;
$warning-color: #956322;
$text-primary: #1A1A1A;
$text-secondary: #595959;
$text-tertiary: #8C8C8C;
$border-light: #F0F0F0;
$border-base: #E8E8E8;
$bg-light: #FAFAFA;
$bg-white: #FFFFFF;
$shadow-light: 0 4rpx 24rpx rgba(0, 0, 0, 0.06);
$shadow-medium: 0 8rpx 32rpx rgba(0, 0, 0, 0.08);
$shadow-heavy: 0 16rpx 48rpx rgba(0, 0, 0, 0.12);

// 主容器
.matting-upload {
  min-height: 100vh;
  background: linear-gradient(180deg, #FFFFFF 0%, #F8F9FA 100%);
  display: flex;
  flex-direction: column;
}

// 预览弹窗样式
.preview-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 680rpx;
  background: $bg-white;
  border-radius: 32rpx;
  overflow: hidden;
  box-shadow: $shadow-heavy;

  .preview-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 32rpx 40rpx;
    background: linear-gradient(135deg, $primary-color 0%, $primary-light 100%);

    .preview-title {
      font-size: 36rpx;
      font-weight: 600;
      color: $bg-white;
    }
  }

  .preview-image-container {
    padding: 40rpx;
    display: flex;
    justify-content: center;
    align-items: center;
    background: $bg-light;
  }

  .preview-actions {
    display: flex;
    gap: 24rpx;
    padding: 32rpx 40rpx;
    background: $bg-white;
    border-top: 2rpx solid $border-light;
  }
}

// 内容容器
.content-container {
  flex: 1;
  padding: 40rpx 32rpx 200rpx;
  overflow-y: auto;
  margin-bottom: 80rpx;
}

// 功能特性卡片
.feature-card {
  background: $bg-white;
  border-radius: 24rpx;
  padding: 40rpx;
  margin-bottom: 32rpx;
  box-shadow: $shadow-light;
  border: 2rpx solid $border-light;

  .feature-header {
    display: flex;
    align-items: center;
    margin-bottom: 32rpx;

    .feature-title {
      font-size: 36rpx;
      font-weight: 700;
      color: $text-primary;
      margin-left: 16rpx;
      letter-spacing: -0.3rpx;
    }
  }

  .feature-list {
    .feature-item {
      display: flex;
      align-items: center;
      padding: 24rpx 0;
      border-bottom: 2rpx solid $border-light;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

      &:last-child {
        border-bottom: none;
      }

      &:active {
        background: $bg-light;
        margin: 0 -40rpx;
        padding: 24rpx 40rpx;
      }

      .feature-icon {
        width: 64rpx;
        height: 64rpx;
        background: linear-gradient(135deg, rgba(247, 114, 97, 0.1) 0%, rgba(255, 154, 139, 0.1) 100%);
        border-radius: 20rpx;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 24rpx;
      }

      .feature-content {
        flex: 1;

        .feature-name {
          font-size: 30rpx;
          font-weight: 600;
          color: $text-primary;
          margin-bottom: 4rpx;
        }

        .feature-desc {
          font-size: 24rpx;
          color: $text-tertiary;
          line-height: 1.4;
        }
      }

      .feature-check {
        margin-left: 16rpx;
      }
    }
  }
}

// 拍照建议卡片
.tips-card {
  background: linear-gradient(135deg, rgba(255, 169, 64, 0.08) 0%, rgba(255, 193, 7, 0.05) 100%);
  border-radius: 24rpx;
  padding: 40rpx;
  margin-bottom: 32rpx;
  border: 2rpx solid rgba(255, 169, 64, 0.2);

  .tips-header {
    display: flex;
    align-items: center;
    margin-bottom: 32rpx;

    .tips-title {
      font-size: 36rpx;
      font-weight: 700;
      color: $text-primary;
      margin-left: 16rpx;
      letter-spacing: -0.3rpx;
    }
  }

  .tips-list {
    .tip-item {
      display: flex;
      align-items: flex-start;
      margin-bottom: 24rpx;

      &:last-child {
        margin-bottom: 0;
      }

      .tip-number {
        width: 48rpx;
        height: 48rpx;
        background: linear-gradient(135deg, $warning-color 0%, #FFC107 100%);
        color: $bg-white;
        border-radius: 24rpx;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24rpx;
        font-weight: 700;
        margin-right: 20rpx;
        flex-shrink: 0;
      }

      .tip-text {
        font-size: 28rpx;
        color: $text-secondary;
        line-height: 1.5;
        flex: 1;
        padding-top: 8rpx;
      }
    }
  }
}

// 底部操作区域
.action-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20rpx);
  border-top: 2rpx solid $border-light;
  padding: 32rpx;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -8rpx 32rpx rgba(0, 0, 0, 0.08);

  .action-tips {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24rpx;

    .tips-text {
      font-size: 24rpx;
      color: $text-tertiary;
      margin-left: 8rpx;
    }
  }

  .action-buttons {
    display: flex;
    gap: 24rpx;

    ::v-deep .u-button {
      flex: 1;
      height: 96rpx;
      border-radius: 48rpx;
      font-size: 32rpx;
      font-weight: 700;
      letter-spacing: 0.5rpx;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

      &:active {
        transform: translateY(2rpx);
      }
    }
  }
}

// 动画效果
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(40rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.content-container > * {
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

.content-container > *:nth-child(1) { animation-delay: 0.1s; }
.content-container > *:nth-child(2) { animation-delay: 0.2s; }

@import '@/assets/legacy-page-themes.scss';
@include tool-page-theme;
</style>
