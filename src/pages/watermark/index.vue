<template>
  <view class="watermark-select">
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
              <u-icon name="file-text" size="18" color="#356caa" />
            </view>
            <view class="feature-content">
              <view class="feature-name">文字水印</view>
              <view class="feature-desc">支持自定义文字内容</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#287c70" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="more-circle" size="18" color="#287c70" />
            </view>
            <view class="feature-content">
              <view class="feature-name">样式丰富</view>
              <view class="feature-desc">字体大小、颜色、透明度调节</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#287c70" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="grid" size="18" color="#715a9b" />
            </view>
            <view class="feature-content">
              <view class="feature-name">平铺水印</view>
              <view class="feature-desc">支持水印间距调节</view>
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
          </view>
        </view>
      </view>

      <!-- 设置选项卡片 -->
      <view class="settings-card">
        <view class="settings-header">
          <u-icon name="setting" color="#cc3d35" size="20" />
          <text class="settings-title">水印设置</text>
        </view>
        
        <view class="settings-list">
          <view class="setting-item">
            <view class="setting-header-row">
              <view class="setting-icon">
                <u-icon name="file-text" size="20" color="#cc3d35" />
              </view>
              <view class="setting-content">
                <text class="setting-title">水印文字</text>
                <text class="setting-desc">输入要添加的水印文字</text>
              </view>
            </view>
            <view class="setting-options">
              <u--input 
                v-model="watermarkText" 
                placeholder="请输入水印文字" maxlength="100"
                :custom-style="inputCustomStyle"
              />
            </view>
          </view>
          
          <view class="setting-item">
            <view class="setting-header-row">
              <view class="setting-icon">
                <u-icon name="file-text" size="20" color="#cc3d35" />
              </view>
              <view class="setting-content">
                <text class="setting-title">字体大小</text>
                <text class="setting-desc">调整水印文字大小</text>
              </view>
            </view>
            <view class="setting-options">
              <view class="slider-container">
                <u-slider active-color="#cc3d35"
                  v-model="fontSize" 
                  :min="10" 
                  :max="100" 
                  :step="1"
                />
                <text class="slider-value">{{ fontSize }}px</text>
              </view>
            </view>
          </view>
          
          <view class="setting-item">
            <view class="setting-header-row">
              <view class="setting-icon">
                <u-icon name="eye" size="20" color="#cc3d35" />
              </view>
              <view class="setting-content">
                <text class="setting-title">透明度</text>
                <text class="setting-desc">控制水印的透明程度</text>
              </view>
            </view>
            <view class="setting-options">
              <view class="slider-container">
                <u-slider active-color="#cc3d35"
                  v-model="opacity" 
                  :min="0" 
                  :max="100" 
                  :step="1"
                />
                <text class="slider-value">{{ opacity }}%</text>
              </view>
            </view>
          </view>
          
          <view class="setting-item">
            <view class="setting-header-row">
              <view class="setting-icon">
                <u-icon name="reload" size="20" color="#cc3d35" />
              </view>
              <view class="setting-content">
                <text class="setting-title">旋转角度</text>
                <text class="setting-desc">调整水印文字的倾斜角度</text>
              </view>
            </view>
            <view class="setting-options">
              <view class="slider-container">
                <u-slider active-color="#cc3d35"
                  v-model="angle" 
                  :min="0" 
                  :max="360" 
                  :step="1"
                />
                <text class="slider-value">{{ angle }}°</text>
              </view>
            </view>
          </view>
          
          <view class="setting-item">
            <view class="setting-header-row">
              <view class="setting-icon">
                <u-icon name="more-circle" size="20" color="#cc3d35" />
              </view>
              <view class="setting-content">
                <text class="setting-title">水印颜色</text>
                <text class="setting-desc">选择水印文字的颜色</text>
              </view>
            </view>
            <view class="setting-options">
              <view class="color-picker">
                <view 
                  v-for="(color, index) in colorPresets" 
                  :key="index"
                  :class="['color-item', { 'color-selected': selectedColor === color.value }]"
                  :style="{ backgroundColor: color.value }"
                  @click="selectedColor = color.value" :aria-label="color.label + (selectedColor === color.value ? '，已选择' : '')" role="button"
                ><text v-if="selectedColor === color.value" class="color-check" :style="{ color: ['#FFFFFF', '#00FF00', '#FFFF00', '#00FFFF'].indexOf(color.value) >= 0 ? '#17191c' : '#ffffff' }">✓</text></view>
              </view>
            </view>
          </view>
          
          <view class="setting-item">
            <view class="setting-header-row">
              <view class="setting-icon">
                <u-icon name="grid" size="20" color="#cc3d35" />
              </view>
              <view class="setting-content">
                <text class="setting-title">水印间距</text>
                <text class="setting-desc">控制水印之间的距离</text>
              </view>
            </view>
            <view class="setting-options">
              <view class="slider-container">
                <u-slider active-color="#cc3d35"
                  v-model="space" 
                  :min="10" 
                  :max="100" 
                  :step="5"
                />
                <text class="slider-value">{{ space }}px</text>
              </view>
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

      <!-- 使用建议卡片 -->
      <view class="tips-card">
        <view class="tips-header">
          <u-icon name="info-circle-fill" color="#956322" size="20" />
          <text class="tips-title">使用建议</text>
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
        </view>
      </view>
    </view>

    <!-- 底部操作区域 -->
    <view class="action-container">
      <view v-if="preselectedImage" class="selected-image-action" @click="confirmSelect">已选择照片 · 开始添加水印 ›</view>
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
          color="#cc3d35"
          text="立即拍摄" 
          :custom-style="primaryButtonStyle" 
          @click="chooseImage('camera')"
        />
      </view>
    </view>

    <PhotoCamera v-if="showCamera" title="拍摄照片" preview-tip="检查照片清晰且内容完整" :guide-initially-enabled="false" initial-position="back"
      @close="showCamera = false" @select="onCameraSelect" />

    <!-- 原生分享按钮 - 使用open-type="share"直接触发分享 -->
    <button v-show="false" open-type="share" class="native-share-button" @getuserinfo="onShareSuccess">
      <u-icon name="share" size="20" color="white" />
    </button>

    <!-- 加载页面 -->
    <LoadingOverlay :show="loading" text="正在添加水印" tip="请稍候，正在为您处理照片" />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import { addWatermark, WatermarkParams } from '@/api/watermark';
import LoadingOverlay from '@/components/LoadingOverlay.vue';
import PhotoCamera from '@/components/PhotoCamera.vue';
import { writeTemporaryImage, removeTemporaryImage } from '@/utils/image-file';

// 声明微信小程序类型
declare const wx: any;

@Component({ components: { LoadingOverlay, PhotoCamera } })
export default class WatermarkPage extends Vue {
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
  preselectedImage: boolean = false;
  
  // 图片预览遮罩
  show: boolean = false;
  
  // 加载动画
  loading: boolean = false;
  
  showCamera: boolean = false;
  
  // 水印设置 - 默认使用 150 DPI 作为打印尺寸标记
  watermarkText: string = '';
  fontSize: number = 20;
  opacity: number = 50;
  angle: number = 30;
  selectedColor: string = '#000000';
  space: number = 25;
  dpi: number = 150;
  
  // 预设颜色
  colorPresets = [
    { label: '黑色', value: '#000000' },
    { label: '白色', value: '#FFFFFF' },
    { label: '红色', value: '#FF0000' },
    { label: '蓝色', value: '#0000FF' },
    { label: '绿色', value: '#00FF00' },
    { label: '黄色', value: '#FFFF00' },
    { label: '紫色', value: '#FF00FF' },
    { label: '青色', value: '#00FFFF' }
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
    this.preselectedImage = !!this.imagePath;
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
   * 输入框自定义样式
   */
  get inputCustomStyle() {
    return this.loading 
      ? { width: '100%', visibility: 'hidden' } 
      : { width: '100%' };
  }

  /**
   * 选择图片
   */
  chooseImage(type: 'album' | 'camera') {
    // 先校验是否输入了水印文字
    if (!this.watermarkText.trim()) {
      uni.showToast({
        title: '请先输入水印文字',
        icon: 'none',
        duration: 2000
      });
      return;
    }

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
    this.preselectedImage = !!path;
    this.confirmSelect();
  }

  /**
   * 确认选择
   */
  async confirmSelect() {
    if (this.loading) return;
    if (!this.imagePath) { uni.showToast({ title: '请先选择图片', icon: 'none' }); return; }
    if (!this.watermarkText.trim()) {
      uni.showToast({ title: '请输入水印文字', icon: 'none' }); return;
    }
    this.loading = true;
    let resultPath = '';
    try {
      const params: WatermarkParams = { text: this.watermarkText, size: this.fontSize, opacity: this.opacity / 100,
        angle: this.angle, color: this.selectedColor, space: this.space, dpi: this.dpi };
      const data = await addWatermark(params, 'input_image', this.imagePath);
      resultPath = await writeTemporaryImage(data.image_base64, 'watermark');
      await new Promise<void>((resolve, reject) => uni.navigateTo({
        url: `/pages/watermark/result?image=${encodeURIComponent(resultPath)}`,
        success: () => resolve(), fail: () => reject(new Error('打开结果页面失败，请重试'))
      }));
    } catch (err: any) {
      removeTemporaryImage(resultPath);
      uni.showModal({ title: '处理失败', content: err.message || '图片处理失败，请重试', showCancel: false });
    } finally { this.loading = false; }
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
.watermark-select {
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
        padding-right: 20rpx;
        width: calc(100% - 96rpx);

        .slider-container {
          display: flex;
          align-items: center;
          gap: 16rpx;
          width: 100%;

          .slider-value {
            font-size: 24rpx;
            color: $text-secondary;
            font-weight: 600;
            min-width: 80rpx;
            text-align: right;
            flex-shrink: 0;
          }

          ::v-deep .u-slider {
            flex: 1;
            min-width: 200rpx;
          }
        }

        .color-picker {
          display: flex;
          gap: 12rpx;
          flex-wrap: wrap;
          max-width: 100%;

          .color-item {
            width: 48rpx;
            height: 48rpx;
            border-radius: 12rpx;
            border: 3rpx solid transparent;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

            &.color-selected {
              border-color: $primary-color;
              transform: scale(1.1);
              box-shadow: 0 4rpx 12rpx rgba(247, 114, 97, 0.3);
            }

            &:active {
              transform: scale(0.9);
            }
          }
        }

        ::v-deep .u-radio-group {
          display: flex;
          flex-wrap: wrap;
          gap: 16rpx;
        }
        
        ::v-deep .u-radio {
          margin-bottom: 8rpx;
        }

        ::v-deep .u--input {
          width: 100% !important;
        }
        
        
        
      }
    }
  }
}

// 使用建议卡片
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

// 原生分享按钮 - 使用open-type="share"直接触发
.native-share-button {
  position: fixed;
  right: 40rpx;
  top: 70%;
  transform: translateY(-50%);
  z-index: 999;
  width: 100rpx;
  height: 100rpx;
  background: linear-gradient(135deg, #cc3d35 0%, #FF9A8B 100%);
  border-radius: 50rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(247, 114, 97, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: pulse 2s infinite;
  
  &:active {
    transform: scale(0.9);
    box-shadow: 0 4rpx 12rpx rgba(247, 114, 97, 0.3);
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 8rpx 24rpx rgba(247, 114, 97, 0.4);
  }
  50% {
    box-shadow: 0 8rpx 24rpx rgba(247, 114, 97, 0.6), 0 0 0 10rpx rgba(247, 114, 97, 0.1);
  }
  100% {
    box-shadow: 0 8rpx 24rpx rgba(247, 114, 97, 0.4);
  }
}

.selected-image-action { margin-bottom: 16rpx; padding: 18rpx 24rpx; border-radius: 16rpx; background: #fff0ed; color: #a32e28; font-size: 26rpx; font-weight: 600; text-align: center; }

@import '@/assets/legacy-page-themes.scss';
@include tool-page-theme;
</style>
