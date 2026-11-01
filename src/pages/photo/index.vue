<template>
  <view class="selection-page">
    <view class="selection-content">
      <view class="selection-card">
        <view class="selection-title">已选规格</view>
        <view class="selected-size">
          <view class="selected-icon"><u-icon name="account" size="28" color="#8a8f95" /></view>
          <view class="selected-copy"><text class="selected-name">{{ photoSize.name }}</text><text class="selected-detail">{{ photoSize.mmWidth }}×{{ photoSize.mmHeight }} mm · {{ photoSize.pxWidth }}×{{ photoSize.pxHeight }} px</text></view>
          <text class="selected-change" @click="changeSize">更换 ›</text>
        </view>
      </view>

      <view class="selection-card">
        <view class="selection-title">拍摄建议</view>
        <view class="advice-content">
          <view class="advice-image"><image src="/static/example.jpeg" mode="aspectFill" /></view>
          <view class="advice-list">
            <view class="advice-row"><u-icon name="account" size="22" color="#20242a" /><view><text class="advice-name">正面平视</text><text class="advice-detail">保持头部居中，眼睛平视镜头</text></view></view>
            <view class="advice-row"><text class="advice-sun">☼</text><view><text class="advice-name">光线均匀</text><text class="advice-detail">避免强光、阴影或暗光</text></view></view>
            <view class="advice-row"><u-icon name="close-circle" size="22" color="#20242a" /><view><text class="advice-name">脸部无遮挡</text><text class="advice-detail">请勿佩戴遮挡脸部的物品</text></view></view>
          </view>
        </view>
      </view>

      <view class="selection-card advanced-card">
        <view class="advanced-heading" @click="settingsExpanded = !settingsExpanded"><view><u-icon name="setting" size="21" color="#20242a" /><text>高级设置</text></view><u-icon :name="settingsExpanded ? 'arrow-up' : 'arrow-down'" size="16" color="#858a91" /></view>
        <view v-if="settingsExpanded" class="advanced-content">
          <view class="advanced-row"><text>处理方式</text><picker :range="models" range-key="label" :value="modelIndex" @change="onModelChange"><text>{{ models[modelIndex].label }} ▾</text></picker></view>
          <view class="advanced-row"><text>人脸对齐</text><switch :checked="form.face_align" color="#cc3d35" @change="onFaceAlignChange" /></view>
          <view class="advanced-row"><text>水平翻转</text><switch :checked="form.horizontal_flip" color="#cc3d35" @change="onFlipChange" /></view>
          <view class="advanced-slider"><text>美白强度：{{ form.whitening_strength }}</text><slider :value="form.whitening_strength" :min="0" :max="15" :step="1" activeColor="#cc3d35" @change="onWhiteningChange" /></view>
        </view>
      </view>
    </view>
    <view class="selection-actions">
      <view class="selection-privacy"><u-icon name="lock" size="14" color="#777d85" /><text>照片将上传至服务器处理</text></view>
      <view class="selection-buttons"><view class="selection-secondary" @click="chooseImage('album')">从相册选择</view><view class="selection-primary" @click="chooseImage('camera')">拍摄照片</view></view>
    </view>

    <PhotoCamera v-if="showCamera" title="证件照拍摄" preview-tip="检查面部完整、清晰且光线均匀"
      @close="showCamera = false" @select="onCameraSelect" />

    <!-- 加载页面 -->
    <LoadingOverlay :show="loading" text="正在制作证件照" tip="请稍候，正在为您处理照片" />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import { GeneratePhoto } from '@/api/photo'
import { PhotoSize } from '@/model/PhotoSize'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import PhotoCamera from '@/components/PhotoCamera.vue'
import { Getter, Mutation } from 'vuex-class';
import { Colors } from '@/model/Colors'
import { PhotoPath } from "@/model/Interfaces";
import { writeTemporaryImage, removeTemporaryImage } from "@/utils/image-file";

// 声明微信小程序类型
declare const wx: any;

@Component({ components: { LoadingOverlay, PhotoCamera } })
export default class PhotoIndex extends Vue {
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

  form: any = {
    height: 0,
    width: 0,
    human_matting_model: "birefnet-v1-lite",
    face_detect_model: "mtcnn",
    face_align: false,
    horizontal_flip: false,
    whitening_strength: 0
  }
  models = [
    { label: '增强版', value: 'birefnet-v1-lite' },
    { label: '标准版', value: 'hivision_modnet' },
    { label: '人像版', value: 'modnet_photographic_portrait_matting' }
  ]
  settingsExpanded: boolean = false
  changeSize() { uni.navigateBack(); }
  modelIndex: number = 0
  onModelChange(event: any) { this.modelIndex = Number(event.detail.value); this.form.human_matting_model = this.models[this.modelIndex].value }
  onFaceAlignChange(event: any) { this.form.face_align = event.detail.value }
  onFlipChange(event: any) { this.form.horizontal_flip = event.detail.value }
  onWhiteningChange(event: any) { this.form.whitening_strength = Number(event.detail.value) }
  colors = Colors.slice(0, 5)
  //本地文件地址
  imagePath: string = ''
  //图片预览遮罩
  show: boolean = false
  //加载动画
  loading: boolean = false
  showCamera: boolean = false
  //获取图片配置
  @Getter('photoConfig') photoSize!: PhotoSize
  //设置图片base64地址
  @Mutation('SET_PHOTO_PATH') setPhotoPath!: (data: PhotoPath) => void

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
        this.imagePath = path
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
        const path = res.tempFiles[0].tempFilePath
        this.imagePath = path
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
   * 提交表单
   */
  submit() {

  }
  /**
   * 确认选择
   */
  async confirmSelect() {
    if (this.loading) return;
    if (!this.imagePath || !this.photoSize || !this.photoSize.pxWidth || !this.photoSize.pxHeight) {
      uni.showToast({ title: '请选择照片和有效规格', icon: 'none' });
      return;
    }
    this.loading = true;
    let standardPath = '';
    let hdPath = '';
    try {
      const form = { ...this.form, height: this.photoSize.pxHeight, width: this.photoSize.pxWidth, dpi: this.photoSize.dpi || 300, hd: true };
      const data = await GeneratePhoto(form, 'input_image', this.imagePath);
      if (!data.image_base64_standard || !data.image_base64_hd) throw new Error('服务器未返回完整照片，请重试');
      standardPath = await writeTemporaryImage(data.image_base64_standard, 'standard');
      hdPath = await writeTemporaryImage(data.image_base64_hd, 'hd');
      const photoPath: PhotoPath = {
        base64: data.image_base64_standard, base64HD: data.image_base64_hd,
        base64Path: standardPath, base64HDPath: hdPath
      };
      this.setPhotoPath(photoPath);
      await new Promise<void>((resolve, reject) => uni.navigateTo({
        url: '/pages/photo/edit', success: () => resolve(), fail: () => reject(new Error('打开编辑页面失败，请重试'))
      }));
    } catch (err: any) {
      removeTemporaryImage(standardPath);
      removeTemporaryImage(hdPath);
      this.setPhotoPath({ base64: '', base64HD: '', base64Path: '', base64HDPath: '' });
      uni.showModal({ title: '制作失败', content: err.message || '照片处理失败，请重试', showCancel: false });
    } finally { this.loading = false; }
  }
  skipTo() {
    uni.navigateTo({
      url: '/pages/photo/index'
    })
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
.photo-select {
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

// 尺寸信息卡片
.size-card {
  background: $bg-white;
  border-radius: 24rpx;
  padding: 40rpx;
  margin-bottom: 32rpx;
  box-shadow: $shadow-light;
  border: 2rpx solid $border-light;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 8rpx;
    background: linear-gradient(90deg, $primary-color 0%, $primary-light 100%);
  }

  .size-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 40rpx;

    .size-title {
      font-size: 48rpx;
      font-weight: 700;
      color: $text-primary;
      letter-spacing: -0.5rpx;
    }

    .size-badge {
      background: linear-gradient(135deg, $primary-color 0%, $primary-light 100%);
      color: $bg-white;
      font-size: 22rpx;
      font-weight: 600;
      padding: 12rpx 20rpx;
      border-radius: 20rpx;
      box-shadow: 0 4rpx 12rpx rgba(247, 114, 97, 0.3);
    }
  }

  .size-specs {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .spec-item {
      flex: 1;
      text-align: center;

      .spec-value {
        font-size: 32rpx;
        font-weight: 700;
        color: $text-primary;
        margin-bottom: 8rpx;
        letter-spacing: -0.3rpx;
      }

      .spec-label {
        font-size: 24rpx;
        color: $text-tertiary;
        font-weight: 500;
      }
    }

    .spec-divider {
      width: 2rpx;
      height: 60rpx;
      background: $border-light;
    }
  }
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

      .feature-colors {
        margin-left: 16rpx;
        display: flex;
        gap: 12rpx;

        .color-dot {
          width: 36rpx;
          height: 36rpx;
          border-radius: 18rpx;
          border: 3rpx solid $bg-white;
          box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
          transition: transform 0.2s ease;

          &:active {
            transform: scale(1.1);
          }
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

/* 证件照选择页面 */
.selection-page { min-height: 100vh; background: #f6f6f6; color: #17191c; box-sizing: border-box; padding: 24rpx 32rpx 250rpx; }
.selection-card { background: #fff; border-radius: 24rpx; padding: 28rpx; margin-bottom: 22rpx; }
.selection-title { font-size: 30rpx; font-weight: 650; margin-bottom: 22rpx; }
.selected-size { display: flex; align-items: center; gap: 20rpx; }
.selected-icon { width: 84rpx; height: 84rpx; background: #f4f5f6; border-radius: 12rpx; display: flex; align-items: center; justify-content: center; }
.selected-copy { flex: 1; min-width: 0; }.selected-name, .selected-detail { display: block; }.selected-name { font-size: 30rpx; font-weight: 600; }.selected-detail { color: #666b73; font-size: 22rpx; margin-top: 8rpx; }.selected-change { color: #cc3d35; font-size: 26rpx; }
.advice-content { display: flex; gap: 24rpx; align-items: center; }.advice-image { width: 238rpx; height: 304rpx; border-radius: 12rpx; overflow: hidden; background: #f5f5f5; flex-shrink: 0; }.advice-image image { width: 100%; height: 100%; }.advice-list { flex: 1; display: flex; flex-direction: column; gap: 28rpx; }.advice-row { display: flex; gap: 16rpx; align-items: flex-start; }.advice-sun { font-size: 44rpx; line-height: 1; color: #20242a; width: 44rpx; text-align: center; flex-shrink: 0; }.advice-name, .advice-detail { display: block; }.advice-name { font-size: 27rpx; font-weight: 600; }.advice-detail { margin-top: 5rpx; color: #666b73; font-size: 23rpx; line-height: 1.4; }
.advanced-heading, .advanced-heading > view { display: flex; align-items: center; }.advanced-heading { justify-content: space-between; min-height: 50rpx; font-size: 29rpx; font-weight: 600; }.advanced-heading > view { gap: 16rpx; }.advanced-content { padding-top: 18rpx; }.advanced-row { display: flex; justify-content: space-between; align-items: center; min-height: 88rpx; border-top: 1rpx solid #e8eaed; font-size: 27rpx; }.advanced-slider { border-top: 1rpx solid #e8eaed; padding-top: 20rpx; font-size: 27rpx; }
.selection-actions { position: fixed; z-index: 10; left: 0; right: 0; bottom: 0; background: #f6f6f6; padding: 18rpx 32rpx calc(24rpx + env(safe-area-inset-bottom)); }.selection-privacy { display: flex; align-items: center; justify-content: center; gap: 8rpx; color: #666b73; font-size: 23rpx; margin-bottom: 22rpx; }.selection-buttons { display: flex; gap: 16rpx; }.selection-secondary, .selection-primary { flex: 1; min-height: 96rpx; border-radius: 20rpx; display: flex; justify-content: center; align-items: center; font-size: 30rpx; font-weight: 600; }.selection-secondary { background: white; color: #17191c; }.selection-primary { background: #cc3d35; color: white; }
</style>
