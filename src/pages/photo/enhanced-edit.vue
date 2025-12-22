<template>
  <view class="photo-edit">
    <!-- 顶部导航 -->
    <view class="navbar">
      <u-icon name="arrow-left" size="24" @click="goBack" />
      <text class="navbar-title">编辑证件照</text>
      <view class="navbar-actions">
        <u-icon name="more-dot-fill" size="20" @click="showMoreActions" />
      </view>
    </view>

    <!-- 预览区域 -->
    <view class="preview-section">
      <view class="preview-container">
        <view 
          class="photo-preview" 
          :style="{ 
            'height': imageHeight, 
            'width': imageWidth, 
            'backgroundColor': currentBackgroundColor 
          }"
        >
          <u-image 
            class="preview-image" 
            :src="currentImage" 
            mode="aspectFit" 
            :width="imageWidth"
            :height="imageHeight" 
          />
        </view>
        
        <!-- 对比模式 -->
        <view v-if="showCompare" class="compare-container">
          <view class="compare-item">
            <text class="compare-label">原图</text>
            <u-image :src="originalImage" width="100%" height="200rpx" mode="aspectFit" />
          </view>
          <view class="compare-item">
            <text class="compare-label">效果图</text>
            <u-image :src="currentImage" width="100%" height="200rpx" mode="aspectFit" />
          </view>
        </view>
      </view>
    </view>

    <!-- 编辑工具栏 -->
    <view class="tools-section">
      <!-- 背景色选择 -->
      <view class="tool-group">
        <view class="tool-header">
          <text class="tool-title">背景颜色</text>
          <u-icon 
            :name="showColorPicker ? 'arrow-up' : 'arrow-down'" 
            size="16" 
            @click="showColorPicker = !showColorPicker"
          />
        </view>
        <view v-show="showColorPicker" class="color-picker">
          <view 
            class="color-item" 
            v-for="color in colors" 
            :key="color"
            :class="{ 'color-active': currentBackgroundColor === color }"
            :style="{ backgroundColor: color }"
            @click="changeBackgroundColor(color)"
          ></view>
          <view class="color-item custom-color" @click="showCustomColorDialog">
            <u-icon name="plus" size="16" color="#999" />
          </view>
        </view>
      </view>

      <!-- 图片质量 -->
      <view class="tool-group">
        <view class="tool-header">
          <text class="tool-title">图片质量</text>
        </view>
        <view class="quality-selector">
          <view 
            class="quality-item"
            :class="{ 'quality-active': !isHd }"
            @click="toggleQuality(false)"
          >
            <text class="quality-text">标准</text>
            <text class="quality-desc">快速生成</text>
          </view>
          <view 
            class="quality-item"
            :class="{ 'quality-active': isHd }"
            @click="toggleQuality(true)"
          >
            <text class="quality-text">高清</text>
            <text class="quality-desc">品质更佳</text>
          </view>
        </view>
      </view>

      <!-- 图像增强 -->
      <view class="tool-group">
        <view class="tool-header">
          <text class="tool-title">图像增强</text>
          <u-icon 
            :name="showEnhancement ? 'arrow-up' : 'arrow-down'" 
            size="16" 
            @click="showEnhancement = !showEnhancement"
          />
        </view>
        <view v-show="showEnhancement" class="enhancement-controls">
          <view class="slider-control">
            <text class="slider-label">亮度</text>
            <u-slider 
              v-model="enhancementParams.brightness_strength"
              :min="-50"
              :max="50"
              :step="1"
              @change="onEnhancementChange"
            />
            <text class="slider-value">{{ enhancementParams.brightness_strength }}</text>
          </view>
          <view class="slider-control">
            <text class="slider-label">对比度</text>
            <u-slider 
              v-model="enhancementParams.contrast_strength"
              :min="-50"
              :max="50"
              :step="1"
              @change="onEnhancementChange"
            />
            <text class="slider-value">{{ enhancementParams.contrast_strength }}</text>
          </view>
          <view class="slider-control">
            <text class="slider-label">锐度</text>
            <u-slider 
              v-model="enhancementParams.sharpen_strength"
              :min="0"
              :max="100"
              :step="1"
              @change="onEnhancementChange"
            />
            <text class="slider-value">{{ enhancementParams.sharpen_strength }}</text>
          </view>
          <view class="slider-control">
            <text class="slider-label">饱和度</text>
            <u-slider 
              v-model="enhancementParams.saturation_strength"
              :min="-50"
              :max="50"
              :step="1"
              @change="onEnhancementChange"
            />
            <text class="slider-value">{{ enhancementParams.saturation_strength }}</text>
          </view>
          <view class="enhancement-actions">
            <u-button size="mini" type="info" plain @click="resetEnhancement">重置</u-button>
            <u-button size="mini" color="#F77261" @click="applyEnhancement">应用</u-button>
          </view>
        </view>
      </view>

      <!-- 水印设置 -->
      <view class="tool-group">
        <view class="tool-header">
          <text class="tool-title">水印设置</text>
          <u-switch v-model="watermarkEnabled" @change="onWatermarkToggle" />
        </view>
        <view v-show="watermarkEnabled" class="watermark-controls">
          <u-form-item label="水印文字">
            <u-input v-model="watermarkParams.text" placeholder="请输入水印文字" />
          </u-form-item>
          <view class="slider-control">
            <text class="slider-label">大小</text>
            <u-slider 
              v-model="watermarkParams.size"
              :min="10"
              :max="50"
              :step="1"
            />
            <text class="slider-value">{{ watermarkParams.size }}</text>
          </view>
          <view class="slider-control">
            <text class="slider-label">透明度</text>
            <u-slider 
              v-model="watermarkParams.opacity"
              :min="0"
              :max="100"
              :step="1"
            />
            <text class="slider-value">{{ watermarkParams.opacity }}%</text>
          </view>
        </view>
      </view>

      <!-- 更多操作 -->
      <view class="tool-group">
        <view class="tool-header">
          <text class="tool-title">更多操作</text>
        </view>
        <view class="action-buttons">
          <u-button size="mini" type="info" plain @click="toggleCompare">
            {{ showCompare ? '隐藏对比' : '显示对比' }}
          </u-button>
          <u-button size="mini" type="info" plain @click="cropPhoto">智能裁剪</u-button>
          <u-button size="mini" type="info" plain @click="adjustSize">调整大小</u-button>
        </view>
      </view>
    </view>

    <!-- 底部操作栏 -->
    <view class="bottom-actions">
      <view class="action-left">
        <u-button 
          type="info" 
          plain 
          :custom-style="{ width: '200rpx', borderRadius: '20rpx' }"
          @click="generateLayoutPhoto"
        >
          保存排版照
        </u-button>
      </view>
      <view class="action-right">
        <u-button 
          color="#F77261" 
          :custom-style="{ width: '200rpx', borderRadius: '20rpx' }"
          @click="saveCurrentPhoto"
          :loading="saving"
        >
          保存证件照
        </u-button>
      </view>
    </view>

    <!-- 更多操作菜单 -->
    <u-action-sheet 
      :show="showActions" 
      :actions="actionList" 
      @close="showActions = false"
      @select="onActionSelect"
    />

    <!-- 自定义颜色弹窗 -->
    <u-popup :show="showCustomColor" mode="center" round="20" @close="showCustomColor = false">
      <view class="color-dialog">
        <view class="dialog-header">
          <text class="dialog-title">选择颜色</text>
          <u-icon name="close" size="20" @click="showCustomColor = false" />
        </view>
        <view class="color-input">
          <u-input v-model="customColorValue" placeholder="输入颜色代码，如：#FF0000" />
        </view>
        <view class="dialog-actions">
          <u-button type="info" plain @click="showCustomColor = false">取消</u-button>
          <u-button color="#F77261" @click="applyCustomColor">确定</u-button>
        </view>
      </view>
    </u-popup>

    <!-- 调整大小弹窗 -->
    <u-popup :show="showSizeAdjust" mode="center" round="20" @close="showSizeAdjust = false">
      <view class="size-dialog">
        <view class="dialog-header">
          <text class="dialog-title">调整文件大小</text>
          <u-icon name="close" size="20" @click="showSizeAdjust = false" />
        </view>
        <view class="size-input">
          <u-input 
            v-model="targetKb" 
            type="number" 
            placeholder="输入目标文件大小(KB)"
          />
        </view>
        <view class="dialog-actions">
          <u-button type="info" plain @click="showSizeAdjust = false">取消</u-button>
          <u-button color="#F77261" @click="applySizeAdjust">确定</u-button>
        </view>
      </view>
    </u-popup>
    
    <!-- 原生分享按钮 - 使用open-type="share"直接触发分享 -->
    <button v-show="false" open-type="share" class="native-share-button" @getuserinfo="onShareSuccess">
      <u-icon name="share" size="20" color="white" />
    </button>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component, Watch } from "vue-property-decorator";
import { AddBackgroudColor, GenerateLayoutPhoto } from '@/api/photo'
import { AddWatermark, SetKb, IdphotoCrop, ImageEnhancementParams, WatermarkParams } from '@/api/photo-enhanced'
import { Colors } from '@/model/Colors'
import { Getter, Mutation } from 'vuex-class';
import { PhotoSize } from '@/model/PhotoSize';
import { cloneDeep } from 'lodash'
import { PhotoPath } from '@/model/Interfaces'
import StorageManager from '@/utils/storage';

@Component({})
export default class EnhancedEdit extends Vue {
  colors = { ...Colors };
  
  // 当前状态
  currentBackgroundColor: string = Colors[0];
  isHd: boolean = true;
  currentImage: string = '';
  originalImage: string = '';
  
  // 控制显示
  showColorPicker: boolean = true;
  showEnhancement: boolean = false;
  showCompare: boolean = false;
  watermarkEnabled: boolean = false;
  showActions: boolean = false;
  showCustomColor: boolean = false;
  showSizeAdjust: boolean = false;
  saving: boolean = false;
  
  // 参数设置
  enhancementParams: ImageEnhancementParams = {
    brightness_strength: 0,
    contrast_strength: 0,
    sharpen_strength: 0,
    saturation_strength: 0
  };
  
  watermarkParams: WatermarkParams = {
    text: 'AI证件照',
    size: 20,
    opacity: 50,
    angle: 30,
    color: '#000000',
    space: 25
  };
  
  customColorValue: string = '';
  targetKb: string = '';
  
  // 操作列表
  actionList = [
    {
      name: '保存到历史记录',
      id: 'save_history'
    },
    {
      name: '分享图片',
      id: 'share'
    },
    {
      name: '重新制作',
      id: 'remake'
    }
  ];

  // vuex中的图片大小信息
  @Getter('photoConfig') photoSize!: PhotoSize;
  @Getter('photoPath') photoPath!: PhotoPath;
  
  // 设置图片base64地址
  @Mutation('SET_PHOTO_PATH') setPhotoPath!: (data: PhotoPath) => void;

  // 标准宽度
  readonly standard_width = 700;

  onLoad(options: any) {
    this.initFromOptions(options);
  }

  @Watch('photoPath', { immediate: true })
  onPhotoPathChange() {
    if (this.photoPath) {
      this.currentImage = this.isHd ? this.photoPath.base64HD : this.photoPath.base64;
      this.originalImage = this.photoPath.base64;
    }
  }

  /**
   * 从路由参数初始化
   */
  initFromOptions(options: any) {
    if (options.history) {
      // 从历史记录恢复
      const history = JSON.parse(decodeURIComponent(options.history));
      this.currentBackgroundColor = history.parameters.backgroundColor;
      this.isHd = history.parameters.isHd;
      if (history.parameters.enhancement) {
        this.enhancementParams = { ...history.parameters.enhancement };
      }
      if (history.parameters.watermark) {
        this.watermarkParams = { ...history.parameters.watermark };
        this.watermarkEnabled = true;
      }
    }
  }

  get imageHeight() {
    const { pxHeight, pxWidth } = this.photoSize;
    if (Number(pxHeight) > Number(pxWidth)) {
      return this.standard_width + 'rpx';
    } else {
      return (this.standard_width / pxWidth * pxHeight) + 'rpx';
    }
  }

  get imageWidth() {
    const { pxHeight, pxWidth } = this.photoSize;
    if (Number(pxWidth) > Number(pxHeight)) {
      return this.standard_width + 'rpx';
    } else {
      return (this.standard_width / pxHeight * pxWidth) + 'rpx';
    }
  }

  /**
   * 返回上一页
   */
  goBack() {
    uni.navigateBack();
  }

  /**
   * 显示更多操作
   */
  showMoreActions() {
    this.showActions = true;
  }

  /**
   * 处理操作选择
   */
  onActionSelect(action: any) {
    switch (action.id) {
      case 'save_history':
        this.saveToHistory();
        break;
      case 'share':
        this.shareImage();
        break;
      case 'remake':
        this.remakePhoto();
        break;
    }
    this.showActions = false;
  }

  /**
   * 修改背景色
   */
  changeBackgroundColor(color: string) {
    this.currentBackgroundColor = color;
    this.applyBackgroundColor();
  }

  /**
   * 应用背景色
   */
  async applyBackgroundColor() {
    try {
      uni.showLoading({ title: '处理中...' });
      
      const targetImage = this.isHd ? this.photoPath.base64HDPath : this.photoPath.base64Path;
      const form = {
        color: this.currentBackgroundColor.replace('#', ''),
        dpi: 300
      };
      
      const res = await AddBackgroudColor(form, 'input_image', targetImage);
      const colorBase64 = res['image_base64'];
      
      if (colorBase64) {
        this.currentImage = 'data:image/png;base64,' + colorBase64;
      }
    } catch (error) {
      uni.showToast({ title: '处理失败', icon: 'none' });
    } finally {
      uni.hideLoading();
    }
  }

  /**
   * 切换图片质量
   */
  toggleQuality(hd: boolean) {
    this.isHd = hd;
    this.currentImage = hd ? this.photoPath.base64HD : this.photoPath.base64;
  }

  /**
   * 图像增强参数变化
   */
  onEnhancementChange() {
    // 实时预览增强效果（可选）
  }

  /**
   * 应用图像增强
   */
  async applyEnhancement() {
    try {
      uni.showLoading({ title: '增强中...' });
      
      // 调用完整的图像处理流程，包含增强参数
      await this.regenerateWithEnhancement();
      
      uni.showToast({ title: '增强成功', icon: 'success' });
    } catch (error) {
      uni.showToast({ title: '增强失败', icon: 'none' });
    } finally {
      uni.hideLoading();
    }
  }

  /**
   * 重新生成包含增强参数的图片
   */
  async regenerateWithEnhancement() {
    // 构建包含增强参数的处理参数
    const form = {
      height: this.photoSize.pxHeight,
      width: this.photoSize.pxWidth,
      hd: this.isHd,
      dpi: 300,
      // 添加增强参数
      brightness_strength: this.enhancementParams.brightness_strength,
      contrast_strength: this.enhancementParams.contrast_strength,
      sharpen_strength: this.enhancementParams.sharpen_strength,
      saturation_strength: this.enhancementParams.saturation_strength
    };
    
    // 先应用背景色
    await this.applyBackgroundColor();
    
    // 如果有水印，再应用水印
    if (this.watermarkEnabled) {
      await this.applyWatermark();
    }
  }

  /**
   * 重置增强参数
   */
  resetEnhancement() {
    this.enhancementParams = {
      brightness_strength: 0,
      contrast_strength: 0,
      sharpen_strength: 0,
      saturation_strength: 0
    };
  }

  /**
   * 水印开关变化
   */
  onWatermarkToggle(enabled: boolean) {
    if (enabled) {
      this.applyWatermark();
    } else {
      this.currentImage = this.isHd ? this.photoPath.base64HD : this.photoPath.base64;
    }
  }

  /**
   * 应用水印
   */
  async applyWatermark() {
    try {
      uni.showLoading({ title: '添加水印...' });
      
      const form = { ...this.watermarkParams };
      const targetImage = this.currentImage;
      
      const res = await AddWatermark(form, 'input_image', targetImage);
      const watermarkBase64 = res['image_base64'];
      
      if (watermarkBase64) {
        this.currentImage = 'data:image/png;base64,' + watermarkBase64;
      }
    } catch (error) {
      uni.showToast({ title: '水印添加失败', icon: 'none' });
    } finally {
      uni.hideLoading();
    }
  }

  /**
   * 切换对比显示
   */
  toggleCompare() {
    this.showCompare = !this.showCompare;
  }

  /**
   * 智能裁剪
   */
  async cropPhoto() {
    try {
      uni.showLoading({ title: '裁剪中...' });
      
      const form = {
        height: this.photoSize.pxHeight,
        width: this.photoSize.pxWidth,
        hd: this.isHd,
        dpi: 300
      };
      
      const targetImage = this.isHd ? this.photoPath.base64HDPath : this.photoPath.base64Path;
      const res = await IdphotoCrop(form, 'input_image', targetImage);
      const cropBase64 = res['image_base64'];
      
      if (cropBase64) {
        this.currentImage = 'data:image/png;base64,' + cropBase64;
        uni.showToast({ title: '裁剪成功', icon: 'success' });
      }
    } catch (error) {
      uni.showToast({ title: '裁剪失败', icon: 'none' });
    } finally {
      uni.hideLoading();
    }
  }

  /**
   * 调整大小
   */
  adjustSize() {
    this.showSizeAdjust = true;
  }

  /**
   * 应用大小调整
   */
  async applySizeAdjust() {
    if (!this.targetKb) {
      uni.showToast({ title: '请输入文件大小', icon: 'none' });
      return;
    }
    
    try {
      uni.showLoading({ title: '调整中...' });
      
      const form = {
        kb: parseInt(this.targetKb),
        dpi: 300
      };
      
      const targetImage = this.currentImage;
      const res = await SetKb(form, 'input_image', targetImage);
      const kbBase64 = res['image_base64'];
      
      if (kbBase64) {
        this.currentImage = 'data:image/png;base64,' + kbBase64;
        uni.showToast({ title: '调整成功', icon: 'success' });
        this.showSizeAdjust = false;
      }
    } catch (error) {
      uni.showToast({ title: '调整失败', icon: 'none' });
    } finally {
      uni.hideLoading();
    }
  }

  /**
   * 显示自定义颜色对话框
   */
  showCustomColorDialog() {
    this.showCustomColor = true;
  }

  /**
   * 应用自定义颜色
   */
  applyCustomColor() {
    if (this.customColorValue) {
      this.changeBackgroundColor(this.customColorValue);
      this.showCustomColor = false;
    }
  }

  /**
   * 保存当前照片
   */
  async saveCurrentPhoto() {
    this.saving = true;
    try {
      const tempPath = await this.saveImageToLocal(this.currentImage);
      await this.saveToAlbum(tempPath);
      
      // 保存到历史记录
      await this.saveToHistory();
      
      uni.showToast({ title: '保存成功', icon: 'success' });
    } catch (error) {
      uni.showToast({ title: '保存失败', icon: 'none' });
    } finally {
      this.saving = false;
    }
  }

  /**
   * 生成排版照
   */
  async generateLayoutPhoto() {
    try {
      uni.showLoading({ title: '生成排版照...' });
      
      const form = {
        height: this.photoSize.pxHeight,
        width: this.photoSize.pxWidth
      };
      
      // 先生成带背景色的图片
      await this.applyBackgroundColor();
      
      const res = await GenerateLayoutPhoto(form, 'input_image', this.currentImage);
      const layoutBase64 = res['image_base64'];
      
      if (layoutBase64) {
        const tempPath = await this.saveImageToLocal('data:image/png;base64,' + layoutBase64);
        await this.saveToAlbum(tempPath);
        uni.showToast({ title: '排版照保存成功', icon: 'success' });
      }
    } catch (error) {
      uni.showToast({ title: '生成失败', icon: 'none' });
    } finally {
      uni.hideLoading();
    }
  }

  /**
   * 保存图片到本地
   */
  async saveImageToLocal(base64: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const tempPath = `${wx.env.USER_DATA_PATH}/photo_${Date.now()}.png`;
      const fs = uni.getFileSystemManager();
      
      fs.writeFile({
        filePath: tempPath,
        data: base64.replace('data:image/png;base64,', ''),
        encoding: 'base64',
        success: () => resolve(tempPath),
        fail: reject
      });
    });
  }

  /**
   * 保存到相册
   */
  async saveToAlbum(tempPath: string) {
    return new Promise((resolve, reject) => {
      uni.saveImageToPhotosAlbum({
        filePath: tempPath,
        success: resolve,
        fail: reject
      });
    });
  }

  /**
   * 保存到历史记录
   */
  async saveToHistory() {
    const record = {
      originalImage: this.originalImage,
      resultImages: {
        idPhoto: this.currentImage
      },
      parameters: {
        size: this.photoSize,
        backgroundColor: this.currentBackgroundColor,
        isHd: this.isHd,
        enhancement: this.enhancementParams,
        watermark: this.watermarkEnabled ? this.watermarkParams : undefined
      }
    };
    
    StorageManager.savePhotoRecord(record);
  }

  /**
   * 分享图片
   */
  shareImage() {
    uni.share({
      provider: 'weixin',
      scene: 'WXSceneSession',
      type: 0,
      imageUrl: this.currentImage,
      success: () => {
        uni.showToast({ title: '分享成功', icon: 'success' });
      },
      fail: () => {
        uni.showToast({ title: '分享失败', icon: 'none' });
      }
    });
  }

  /**
   * 重新制作
   */
  remakePhoto() {
    uni.navigateBack();
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
.photo-edit {
  min-height: 100vh;
  background: #f8f9fa;
}

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 40rpx;
  background: white;
  border-bottom: 1rpx solid #e9ecef;
  
  .navbar-title {
    font-size: 32rpx;
    font-weight: bold;
    color: #333;
  }
}

.preview-section {
  padding: 40rpx;
  background: white;
  margin-bottom: 20rpx;
  
  .preview-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    
    .photo-preview {
      display: flex;
      justify-content: center;
      align-items: center;
      border-radius: 12rpx;
      overflow: hidden;
      margin-bottom: 30rpx;
      box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.1);
    }
    
    .compare-container {
      width: 100%;
      display: flex;
      gap: 20rpx;
      
      .compare-item {
        flex: 1;
        
        .compare-label {
          display: block;
          text-align: center;
          font-size: 24rpx;
          color: #666;
          margin-bottom: 10rpx;
        }
      }
    }
  }
}

.tools-section {
  padding: 0 40rpx;
}

.tool-group {
  background: white;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  
  .tool-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20rpx;
    
    .tool-title {
      font-size: 28rpx;
      font-weight: bold;
      color: #333;
    }
  }
}

.color-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
  
  .color-item {
    width: 60rpx;
    height: 60rpx;
    border-radius: 12rpx;
    border: 2rpx solid #e9ecef;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &.color-active {
      border-color: #F77261;
      transform: scale(1.1);
    }
    
    &.custom-color {
      border-style: dashed;
      background: #f8f9fa;
    }
  }
}

.quality-selector {
  display: flex;
  gap: 20rpx;
  
  .quality-item {
    flex: 1;
    padding: 30rpx 20rpx;
    border-radius: 12rpx;
    border: 2rpx solid #e9ecef;
    text-align: center;
    transition: all 0.3s ease;
    
    &.quality-active {
      border-color: #F77261;
      background: rgba(247, 114, 97, 0.1);
    }
    
    .quality-text {
      display: block;
      font-size: 28rpx;
      font-weight: bold;
      color: #333;
      margin-bottom: 8rpx;
    }
    
    .quality-desc {
      font-size: 22rpx;
      color: #666;
    }
  }
}

.enhancement-controls {
  .slider-control {
    display: flex;
    align-items: center;
    margin-bottom: 30rpx;
    
    .slider-label {
      width: 120rpx;
      font-size: 26rpx;
      color: #333;
    }
    
    .slider-value {
      width: 80rpx;
      text-align: center;
      font-size: 24rpx;
      color: #666;
    }
  }
  
  .enhancement-actions {
    display: flex;
    gap: 20rpx;
    justify-content: center;
  }
}

.watermark-controls {
  .u-form-item {
    margin-bottom: 20rpx;
  }
  
  .slider-control {
    display: flex;
    align-items: center;
    margin-bottom: 20rpx;
    
    .slider-label {
      width: 120rpx;
      font-size: 26rpx;
      color: #333;
    }
    
    .slider-value {
      width: 80rpx;
      text-align: center;
      font-size: 24rpx;
      color: #666;
    }
  }
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}

.bottom-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  padding: 30rpx 40rpx;
  background: white;
  border-top: 1rpx solid #e9ecef;
  box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.1);
}

// 弹窗样式
.color-dialog, .size-dialog {
  width: 500rpx;
  padding: 40rpx;
  background: white;
  border-radius: 20rpx;
  
  .dialog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 30rpx;
    
    .dialog-title {
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
    }
  }
  
  .color-input, .size-input {
    margin-bottom: 30rpx;
  }
  
  .dialog-actions {
    display: flex;
    gap: 20rpx;
    justify-content: center;
  }
}
</style>
