<template>
  <view class="watermark-upload">
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
          <u-button color="#F77261" text="确认选择" :custom-style="primaryButtonStyle" @click="confirmSelect" />
        </view>
      </view>
    </u-overlay>

    <!-- 主要内容区域 -->
    <view class="content-container">
      <!-- 功能介绍卡片 -->
      <view class="feature-card">
        <view class="feature-header">
          <u-icon name="edit-pen" color="#F77261" size="20" />
          <text class="feature-title">图片加水印</text>
        </view>
        
        <view class="feature-list">
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="text" size="18" color="#F77261" />
            </view>
            <view class="feature-content">
              <view class="feature-name">文字水印</view>
              <view class="feature-desc">支持自定义文字内容，满足个性化需求</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#52C41A" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="more-circle" size="18" color="#F77261" />
            </view>
            <view class="feature-content">
              <view class="feature-name">样式丰富</view>
              <view class="feature-desc">支持字体大小、颜色、透明度、角度调节</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#52C41A" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="grid" size="18" color="#F77261" />
            </view>
            <view class="feature-content">
              <view class="feature-name">平铺水印</view>
              <view class="feature-desc">支持水印间距调节，均匀分布覆盖</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#52C41A" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="download" size="18" color="#F77261" />
            </view>
            <view class="feature-content">
              <view class="feature-name">高清输出</view>
              <view class="feature-desc">支持多种分辨率，满足不同使用场景</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#52C41A" size="16" />
            </view>
          </view>
        </view>
      </view>

      <!-- 拍照建议卡片 -->
      <view class="tips-card">
        <view class="tips-header">
          <u-icon name="info-circle-fill" color="#FFA940" size="20" />
          <text class="tips-title">水印建议</text>
        </view>
        
        <view class="tips-list">
          <view class="tip-item">
            <view class="tip-number">1</view>
            <text class="tip-text">选择清晰的照片，确保水印效果明显</text>
          </view>
          <view class="tip-item">
            <view class="tip-number">2</view>
            <text class="tip-text">背景简洁的照片，水印文字更易识别</text>
          </view>
          <view class="tip-item">
            <view class="tip-number">3</view>
            <text class="tip-text">适当调整透明度，既保护原图又不影响观感</text>
          </view>
          <view class="tip-item">
            <view class="tip-number">4</view>
            <text class="tip-text">建议文字简洁，避免过长影响美观</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部操作区域 -->
    <view class="action-container">
      <view class="action-tips">
        <u-icon name="info-circle-fill" color="#8C8C8C" size="14" />
        <text class="tips-text">请选择清晰的图片，添加个性水印</text>
      </view>
      <view class="action-buttons">
        <u-button 
          :plain="true" 
          text="从相册选择" 
          :custom-style="secondaryButtonStyle" 
          @click="chooseImage('album')"
        />
        <u-button 
          color="#F77261" 
          text="立即拍摄" 
          :custom-style="primaryButtonStyle" 
          @click="chooseImage('camera')"
        />
      </view>
    </view>

    <!-- 自定义相机遮罩 -->
    <view class="camera-overlay" v-if="showCamera" @click.stop>
      <camera 
        class="camera-view" 
        :device-position="cameraPosition"
        :flash="flashMode"
        @stop="onCameraStop"
        @error="onCameraError"
        @ready="onCameraReady"
      >
        <!-- 拍照指引 -->
        <view class="photo-guide">
          <svg class="photo-svg" viewBox="0 0 300 400" xmlns="http://www.w3.org/2000/svg">
            <!-- 取景框 -->
            <rect x="50" y="50" width="200" height="300" 
                  fill="none" stroke="#4CAF50" stroke-width="3" stroke-dasharray="8,4" opacity="0.9" rx="10"/>
            
            <!-- 四个角标 -->
            <path d="M50,70 L70,70 L70,50" fill="none" stroke="#4CAF50" stroke-width="4" opacity="0.9"/>
            <path d="M230,70 L250,70 L250,50" fill="none" stroke="#4CAF50" stroke-width="4" opacity="0.9"/>
            <path d="M50,330 L70,330 L70,350" fill="none" stroke="#4CAF50" stroke-width="4" opacity="0.9"/>
            <path d="M230,330 L250,330 L250,350" fill="none" stroke="#4CAF50" stroke-width="4" opacity="0.9"/>
          </svg>
        </view>
        
        <!-- 相机控制区域 -->
        <view class="camera-bottom-controls">
          <!-- 相册导入按钮 -->
          <view class="album-btn" @click="chooseFromAlbum">
            <u-icon name="photo" size="24" color="#fff" />
            <text class="album-text">相册</text>
          </view>
          
          <!-- 圆形拍照按钮 -->
          <view class="capture-btn-large" @click="capturePhoto">
            <view class="capture-ring"></view>
            <view class="capture-center"></view>
          </view>
          
          <!-- 切换摄像头按钮 -->
          <view class="switch-camera-btn" @click="switchCamera">
            <u-icon name="reload" size="24" color="#fff" />
          </view>
        </view>
      </camera>
    </view>

    <!-- 全屏拍照预览 -->
    <view class="full-screen-preview" v-if="showCapturePreview" @click.stop>
      <!-- 顶部控制栏 -->
      <view class="preview-top-bar">
        <view class="preview-back-btn" @click="retakePhoto">
          <u-icon name="arrow-left" size="24" color="#fff" />
          <text class="back-text">重新拍摄</text>
        </view>
        <view class="preview-confirm-btn" @click="confirmCapture">
          <text class="confirm-text">确认使用</text>
          <u-icon name="checkmark" size="24" color="#fff" />
        </view>
      </view>
      
      <!-- 全屏图片预览 -->
      <view class="preview-image-container">
        <image :src="capturedImagePath" mode="aspectFit" class="full-screen-image" />
      </view>
      
      <!-- 底部提示信息 -->
      <view class="preview-bottom-info">
        <view class="preview-tip">
          <u-icon name="info-circle" size="16" color="#fff" opacity="0.8" />
          <text class="tip-text">请确认照片清晰，适合添加水印</text>
        </view>
      </view>
    </view>

    <!-- 原生分享按钮 - 使用open-type="share"直接触发分享 -->
    <button v-show="false" open-type="share" class="native-share-button" @getuserinfo="onShareSuccess">
      <u-icon name="share" size="20" color="white" />
    </button>

    <!-- 加载页面 -->
    <LoadingOverlay :show="loading" text="AI智能处理中" tip="请稍候，正在为您处理照片" />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import LoadingOverlay from '@/components/LoadingOverlay.vue';

@Component({ components: { LoadingOverlay } })
export default class WatermarkUpload extends Vue {
  // 按钮样式
  primaryButtonStyle = {
    width: '280rpx',
    height: '88rpx',
    borderRadius: '44rpx',
    fontSize: '32rpx',
    fontWeight: 'bold',
    boxShadow: '0 8rpx 24rpx rgba(247, 114, 97, 0.3)'
  };
  
  secondaryButtonStyle = {
    width: '280rpx',
    height: '88rpx',
    borderRadius: '44rpx',
    fontSize: '32rpx',
    fontWeight: 'bold',
    borderColor: '#F77261',
    color: '#F77261'
  };

  // 本地文件地址
  imagePath: string = '';
  
  // 图片预览遮罩
  show: boolean = false;
  
  // 加载动画
  loading: boolean = false;
  
  // 相机相关状态
  showCamera: boolean = false;
  cameraPosition: 'front' | 'back' = 'front';
  flashMode: 'on' | 'off' = 'off';
  capturedImagePath: string = '';
  showCapturePreview: boolean = false;

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

  /**
   * 打开相机
   */
  openCamera() {
    this.showCamera = true;
  }

  /**
   * 关闭相机
   */
  closeCamera() {
    this.showCamera = false;
  }

  /**
   * 切换摄像头
   */
  switchCamera() {
    this.cameraPosition = this.cameraPosition === 'front' ? 'back' : 'front';
  }

  /**
   * 切换闪光灯
   */
  toggleFlash() {
    this.flashMode = this.flashMode === 'on' ? 'off' : 'on';
  }

  /**
   * 拍照
   */
  capturePhoto() {
    const cameraContext = uni.createCameraContext();
    cameraContext.takePhoto({
      quality: 'high',
      success: (res) => {
        this.capturedImagePath = res.tempImagePath;
        this.showCamera = false;
        this.showCapturePreview = true;
      },
      fail: (err) => {
        uni.showToast({
          title: '拍照失败',
          icon: 'none'
        });
      }
    });
  }

  /**
   * 重新拍摄
   */
  retakePhoto() {
    this.showCapturePreview = false;
    this.openCamera();
  }

  /**
   * 确认拍照
   */
  confirmCapture() {
    this.imagePath = this.capturedImagePath;
    this.showCapturePreview = false;
    this.show = true;
  }

  /**
   * 相机准备就绪
   */
  onCameraReady() {
    console.log('Camera ready');
  }

  /**
   * 相机停止
   */
  onCameraStop() {
    console.log('Camera stopped');
  }

  /**
   * 从相册选择
   */
  chooseFromAlbum() {
    // #ifdef H5
    uni.chooseImage({
      count: 1,
      sourceType: ['album'],
      success: (res) => {
        this.imagePath = res.tempFilePaths[0];
        this.showCamera = false;
        this.show = true;
      }
    });
    // #endif

    // #ifdef MP-WEIXIN
    uni.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album'],
      success: (res) => {
        this.imagePath = res.tempFiles[0].tempFilePath;
        this.showCamera = false;
        this.show = true;
      }
    });
    // #endif
  }

  /**
   * 相机错误
   */
  onCameraError(err: any) {
    console.error('Camera error:', err);
    uni.showToast({
      title: '相机打开失败',
      icon: 'none'
    });
    this.showCamera = false;
  }

  /**
   * 确认选择
   */
  confirmSelect() {
    // 跳转到水印处理页面，传递图片路径
    uni.navigateTo({
      url: `/pages/watermark/index?image=${encodeURIComponent(this.imagePath)}`
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
$primary-color: #F77261;
$primary-light: #FF9A8B;
$primary-dark: #E55A4A;
$success-color: #52C41A;
$warning-color: #FFA940;
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
.watermark-upload {
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

// 相机遮罩样式
.camera-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #000;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  
  .camera-view {
    flex: 1;
    width: 100%;
    position: relative;
  }
}

// 拍照指引
.photo-guide {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  width: 500rpx;
  height: 700rpx;
  
  .photo-svg {
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 0 8rpx rgba(76, 175, 80, 0.3));
    animation: photoPulse 3s infinite ease-in-out;
  }
}

// 拍照指引动画
@keyframes photoPulse {
  0% {
    opacity: 0.8;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.02);
  }
  100% {
    opacity: 0.8;
    transform: scale(1);
  }
}

// 相机底部控制区域
.camera-bottom-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.8) 30%, rgba(0, 0, 0, 0.95) 100%);
  padding: 40rpx 32rpx calc(40rpx + env(safe-area-inset-bottom));
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 20;
  
  .album-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8rpx;
    padding: 16rpx;
    border-radius: 16rpx;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10rpx);
    border: 1rpx solid rgba(255, 255, 255, 0.2);
    transition: all 0.3s ease;
    
    &:active {
      background: rgba(255, 255, 255, 0.2);
      transform: scale(0.95);
    }
    
    .album-text {
      color: white;
      font-size: 22rpx;
      font-weight: 500;
    }
  }
  
  .capture-btn-large {
    width: 120rpx;
    height: 120rpx;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 60rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    backdrop-filter: blur(10rpx);
    transition: all 0.3s ease;
    
    &:active {
      transform: scale(0.9);
      background: rgba(255, 255, 255, 1);
    }
    
    .capture-ring {
      width: 100rpx;
      height: 100rpx;
      border: 4rpx solid rgba(247, 114, 97, 0.8);
      border-radius: 50rpx;
      animation: capturePulse 2s infinite ease-in-out;
    }
    
    .capture-center {
      position: absolute;
      width: 80rpx;
      height: 80rpx;
      background: #F77261;
      border-radius: 40rpx;
      box-shadow: 0 8rpx 24rpx rgba(247, 114, 97, 0.4);
    }
  }
  
  .switch-camera-btn {
    width: 80rpx;
    height: 80rpx;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10rpx);
    border: 1rpx solid rgba(255, 255, 255, 0.2);
    border-radius: 40rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    
    &:active {
      background: rgba(255, 255, 255, 0.2);
      transform: scale(0.9);
    }
  }
}

// 拍照按钮动画
@keyframes capturePulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

// 全屏拍照预览样式
.full-screen-preview {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #000;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  
  .preview-top-bar {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    background: linear-gradient(180deg, rgba(0, 0, 0, 0.8) 0%, transparent 100%);
    padding: calc(env(safe-area-inset-top) + 32rpx) 32rpx 32rpx;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 10;
    
    .preview-back-btn {
      display: flex;
      align-items: center;
      gap: 12rpx;
      padding: 16rpx 24rpx;
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10rpx);
      border: 1rpx solid rgba(255, 255, 255, 0.2);
      border-radius: 32rpx;
      transition: all 0.3s ease;
      
      &:active {
        background: rgba(255, 255, 255, 0.2);
        transform: scale(0.95);
      }
      
      .back-text {
        color: #fff;
        font-size: 28rpx;
        font-weight: 600;
      }
    }
    
    .preview-confirm-btn {
      display: flex;
      align-items: center;
      gap: 12rpx;
      padding: 16rpx 24rpx;
      background: linear-gradient(135deg, #F77261 0%, #FF9A8B 100%);
      backdrop-filter: blur(10rpx);
      border: 1rpx solid rgba(247, 114, 97, 0.3);
      border-radius: 32rpx;
      transition: all 0.3s ease;
      box-shadow: 0 8rpx 24rpx rgba(247, 114, 97, 0.3);
      
      &:active {
        background: linear-gradient(135deg, #E55A4A 0%, #F77261 100%);
        transform: scale(0.95);
      }
      
      .confirm-text {
        color: #fff;
        font-size: 28rpx;
        font-weight: 600;
      }
    }
  }
  
  .preview-image-container {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 120rpx 32rpx 120rpx;
    
    .full-screen-image {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 20rpx;
    }
  }
  
  .preview-bottom-info {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(0deg, rgba(0, 0, 0, 0.8) 0%, transparent 100%);
    padding: 32rpx;
    padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
    display: flex;
    justify-content: center;
    z-index: 10;
    
    .preview-tip {
      display: flex;
      align-items: center;
      gap: 12rpx;
      padding: 16rpx 24rpx;
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10rpx);
      border: 1rpx solid rgba(255, 255, 255, 0.2);
      border-radius: 32rpx;
      
      .tip-text {
        color: rgba(255, 255, 255, 0.9);
        font-size: 24rpx;
        font-weight: 500;
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
</style>
