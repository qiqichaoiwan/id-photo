<template>
  <view class="matting-select">
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
          <u-icon name="checkmark-circle-fill" color="#cc3d35" size="20" />
          <text class="feature-title">功能特性</text>
        </view>
        
        <view class="feature-list">
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="coupon" size="18" color="#356caa" />
            </view>
            <view class="feature-content">
              <view class="feature-name">人像抠图</view>
              <view class="feature-desc">高精度提取人物轮廓</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#287c70" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="photo" size="18" color="#287c70" />
            </view>
            <view class="feature-content">
              <view class="feature-name">透明背景</view>
              <view class="feature-desc">制作 PNG 透明底图片</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#287c70" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="more-circle" size="18" color="#715a9b" />
            </view>
            <view class="feature-content">
              <view class="feature-name">多种处理方式</view>
              <view class="feature-desc">支持高精度、标准和增强处理</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#287c70" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="file-text" size="18" color="#956322" />
            </view>
            <view class="feature-content">
              <view class="feature-name">保留图片尺寸</view>
              <view class="feature-desc">输出结果保留原始像素尺寸</view>
            </view>
          </view>
        </view>
      </view>

      <!-- 设置选项卡片 -->
      <view class="settings-card">
        <view class="settings-header">
          <u-icon name="setting" color="#cc3d35" size="20" />
          <text class="settings-title">抠图设置</text>
        </view>
        
        <view class="settings-list">
          <view class="setting-item">
            <view class="setting-header-row">
              <view class="setting-icon">
                <u-icon name="coupon" size="20" color="#cc3d35" />
              </view>
              <view class="setting-content">
                <text class="setting-title">处理方式</text>
                <text class="setting-desc">选择人物轮廓处理效果</text>
              </view>
            </view>
            <view class="setting-options">
              <u-radio-group v-model="selectedModel" direction="row" wrap="true" active-color="#cc3d35">
                <u-radio 
                  v-for="(model, index) in mattingModels" 
                  :key="index"
                  :name="model.value"
                  :label="model.label"
                  :custom-style="{ marginRight: '20rpx', marginBottom: '16rpx' }"
                />
              </u-radio-group>
            </view>
          </view>
          
          <view class="setting-item">
            <view class="setting-header-row">
              <view class="setting-icon">
                <u-icon name="grid" size="20" color="#cc3d35" />
              </view>
              <view class="setting-content">
                <text class="setting-title">输出 DPI</text>
                <text class="setting-desc">用于打印尺寸标记，图片像素不变</text>
              </view>
            </view>
            <view class="setting-options">
              <u-radio-group v-model="dpi" direction="row" wrap="true" active-color="#cc3d35">
                <u-radio 
                  v-for="(item, index) in dpiOptions" 
                  :key="index"
                  :name="item.value"
                  :label="item.label"
                  :custom-style="{ marginRight: '20rpx', marginBottom: '16rpx' }"
                />
              </u-radio-group>
            </view>
          </view>
        </view>
      </view>

      <!-- 拍照建议卡片 -->
      <view class="tips-card">
        <view class="tips-header">
          <u-icon name="info-circle-fill" color="#956322" size="20" />
          <text class="tips-title">使用建议</text>
        </view>
        
        <view class="tips-list">
          <view class="tip-item">
            <view class="tip-number">1</view>
            <text class="tip-text">选择人脸清晰的照片，效果更佳</text>
          </view>
          <view class="tip-item">
            <view class="tip-number">2</view>
            <text class="tip-text">背景简单的图片，抠图更精准</text>
          </view>
          <view class="tip-item">
            <view class="tip-number">3</view>
            <text class="tip-text">避免复杂背景，提高处理成功率</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部操作区域 -->
    <view class="action-container">
      <view class="action-tips">
        <u-icon name="info-circle-fill" color="#8C8C8C" size="14" />
        <text class="tips-text">请选择清晰的人像照片</text>
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

    <!-- 加载页面 -->
    <LoadingOverlay :show="loading" text="正在提取人像" tip="请稍候，正在为您处理照片" />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import { humanMatting, MattingParams } from '@/api/matting';
import LoadingOverlay from '@/components/LoadingOverlay.vue';
import PhotoCamera from '@/components/PhotoCamera.vue';
import { writeTemporaryImage, removeTemporaryImage } from '@/utils/image-file';

// 声明微信小程序类型
declare const wx: any;

@Component({ components: { LoadingOverlay, PhotoCamera } })
export default class MattingPage extends Vue {
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
  
  // 抠图设置 - 默认选择 150 DPI 作为打印尺寸标记
  selectedModel: string = 'modnet_photographic_portrait_matting';
  dpi: number = 150;
  
  // 抠图处理方式选项
  mattingModels = [
    { label: '高精度', value: 'modnet_photographic_portrait_matting' },
    { label: '标准版', value: 'hivision_modnet' },
    { label: '增强版', value: 'birefnet-v1-lite' }
  ];
  
  // DPI选项
  dpiOptions = [
    { label: '150 DPI', value: 150 },
    { label: '300 DPI', value: 300 },
    { label: '600 DPI', value: 600 }
  ];

  onLoad(options: any) {
    if (!options || !options.image) return;
    try { this.imagePath = decodeURIComponent(options.image); }
    catch (_) { this.imagePath = options.image; }
    this.show = !!this.imagePath;
  }

  mounted() {
    // 显示分享菜单，包括分享到朋友圈
    // #ifdef MP-WEIXIN
    wx.showShareMenu({
      menus: ['shareAppMessage', 'shareTimeline'],
      success: (res: any) => {
        console.log('显示分享菜单成功', res);
      },
      fail: (err: any) => {
        console.log('显示分享菜单失败', err);
      }
    });
    // #endif
  }

  /**
   * 选择图片
   */
  chooseImage(type: 'album' | 'camera') {
    if (type === 'camera') {
      this.openCamera();
      return;
    }

    // 从相册选择，直接处理，不显示预览弹窗
    // #ifdef H5
    uni.chooseImage({
      count: 1,
      sourceType: [type],
      success: (res) => {
        const path = res.tempFilePaths[0];
        this.imagePath = path;
        // 直接进行处理，不显示预览弹窗
        this.confirmSelect();
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
        // 直接进行处理，不显示预览弹窗
        this.confirmSelect();
      }
    });
    // #endif
  }

  openCamera() { this.showCamera = true; }
  onCameraSelect(path: string) {
    this.showCamera = false;
    this.imagePath = path;
    this.confirmSelect();
  }

  /**
   * 确认选择
   */
  async confirmSelect() {
    if (this.loading) return;
    if (!this.imagePath) { uni.showToast({ title: '请先选择图片', icon: 'none' }); return; }
    this.loading = true;
    let resultPath = '';
    try {
      const params: MattingParams = { human_matting_model: this.selectedModel, dpi: this.dpi };
      const data = await humanMatting(params, 'input_image', this.imagePath);
      resultPath = await writeTemporaryImage(data.image_base64, 'matting');
      await new Promise<void>((resolve, reject) => uni.navigateTo({
        url: `/pages/matting/result?image=${encodeURIComponent(resultPath)}`,
        success: () => resolve(), fail: () => reject(new Error('打开结果页面失败，请重试'))
      }));
    } catch (err: any) {
      removeTemporaryImage(resultPath);
      uni.showModal({ title: '处理失败', content: err.message || '图片处理失败，请重试', showCancel: false });
    } finally { this.loading = false; }
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
.matting-select {
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

// 设置选项卡片
.settings-card {
  background: $bg-white;
  border-radius: 24rpx;
  padding: 40rpx;
  margin-bottom: 32rpx;
  box-shadow: $shadow-light;
  border: 2rpx solid $border-light;

  .settings-header {
    display: flex;
    align-items: center;
    margin-bottom: 32rpx;

    .settings-title {
      font-size: 36rpx;
      font-weight: 700;
      color: $text-primary;
      margin-left: 16rpx;
      letter-spacing: -0.3rpx;
    }
  }

  .settings-list {
    .setting-item {
      display: flex;
      flex-direction: column;
      padding: 24rpx 0;
      border-bottom: 2rpx solid $border-light;

      &:last-child {
        border-bottom: none;
      }

      .setting-header-row {
        display: flex;
        align-items: center;
        gap: 20rpx;
        margin-bottom: 20rpx;

        .setting-icon {
          width: 56rpx;
          height: 56rpx;
          background: linear-gradient(135deg, rgba(247, 114, 97, 0.1) 0%, rgba(255, 154, 139, 0.1) 100%);
          border-radius: 16rpx;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .setting-content {
          .setting-title {
            font-size: 30rpx;
            font-weight: 600;
            color: $text-primary;
            margin-bottom: 4rpx;
          }

          .setting-desc {
            font-size: 24rpx;
            color: $text-tertiary;
            line-height: 1.4;
          }
        }
      }

      .setting-options {
        padding-left: 76rpx;
        
        ::v-deep .u-radio-group {
          display: flex;
          flex-wrap: wrap;
          gap: 16rpx;
        }
        
        ::v-deep .u-radio {
          margin-bottom: 8rpx;
        }
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
.content-container > *:nth-child(3) { animation-delay: 0.3s; }

@import '@/assets/legacy-page-themes.scss';
@include tool-page-theme;
</style>
