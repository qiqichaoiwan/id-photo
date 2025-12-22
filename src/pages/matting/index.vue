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
          <u-button color="#F77261" text="确认选择" :custom-style="primaryButtonStyle" @click="confirmSelect" />
        </view>
      </view>
    </u-overlay>

    <!-- 主要内容区域 -->
    <view class="content-container">
      <!-- 功能介绍卡片 -->
      <view class="feature-card">
        <view class="feature-header">
          <u-icon name="checkmark-circle-fill" color="#F77261" size="20" />
          <text class="feature-title">功能特性</text>
        </view>
        
        <view class="feature-list">
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="coupon" size="18" color="#F77261" />
            </view>
            <view class="feature-content">
              <view class="feature-name">智能抠图</view>
              <view class="feature-desc">AI高精度人像识别</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#52C41A" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="photo" size="18" color="#F77261" />
            </view>
            <view class="feature-content">
              <view class="feature-name">透明背景</view>
              <view class="feature-desc">一键生成PNG透明图</view>
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
              <view class="feature-name">多种模型</view>
              <view class="feature-desc">支持高精度、标准、轻量版</view>
            </view>
            <view class="feature-check">
              <u-icon name="checkmark-circle-fill" color="#52C41A" size="16" />
            </view>
          </view>
          
          <view class="feature-item">
            <view class="feature-icon">
              <u-icon name="file-text" size="18" color="#F77261" />
            </view>
            <view class="feature-content">
              <view class="feature-name">高清输出</view>
              <view class="feature-desc">支持多种分辨率选择</view>
            </view>
          </view>
        </view>
      </view>

      <!-- 设置选项卡片 -->
      <view class="settings-card">
        <view class="settings-header">
          <u-icon name="setting" color="#F77261" size="20" />
          <text class="settings-title">抠图设置</text>
        </view>
        
        <view class="settings-list">
          <view class="setting-item">
            <view class="setting-header-row">
              <view class="setting-icon">
                <u-icon name="coupon" size="20" color="#F77261" />
              </view>
              <view class="setting-content">
                <text class="setting-title">抠图模型</text>
                <text class="setting-desc">选择AI处理模型</text>
              </view>
            </view>
            <view class="setting-options">
              <u-radio-group v-model="selectedModel" direction="row" wrap="true">
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
                <u-icon name="level" size="20" color="#F77261" />
              </view>
              <view class="setting-content">
                <text class="setting-title">输出分辨率</text>
                <text class="setting-desc">选择图片输出质量</text>
              </view>
            </view>
            <view class="setting-options">
              <u-radio-group v-model="dpi" direction="row" wrap="true">
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
          <u-icon name="info-circle-fill" color="#FFA940" size="20" />
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
        <!-- 人像轮廓指引 -->
        <view class="portrait-guide">
          <svg class="portrait-svg" viewBox="0 0 300 400" xmlns="http://www.w3.org/2000/svg">
            <!-- 人脸轮廓 -->
            <ellipse cx="150" cy="120" rx="70" ry="85" 
                     fill="none" stroke="#4CAF50" stroke-width="3" stroke-dasharray="8,4" opacity="0.9"/>
            
            <!-- 肩膀轮廓 -->
            <path d="M80,200 Q150,170 220,200" 
                  fill="none" stroke="#4CAF50" stroke-width="3" stroke-dasharray="8,4" opacity="0.9"/>
            
            <!-- 左肩膀 -->
            <path d="M80,200 Q60,210 50,200" 
                  fill="none" stroke="#4CAF50" stroke-width="3" stroke-dasharray="8,4" opacity="0.9"/>
            
            <!-- 右肩膀 -->
            <path d="M220,200 Q240,210 250,200" 
                  fill="none" stroke="#4CAF50" stroke-width="3" stroke-dasharray="8,4" opacity="0.9"/>
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
          <text class="tip-text">请确认照片清晰，人像完整</text>
        </view>
      </view>
    </view>

    <!-- 加载页面 -->
    <LoadingOverlay :show="loading" text="AI智能处理中" tip="请稍候，正在为您处理照片" />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import { humanMatting, MattingParams } from '@/api/matting';
import LoadingOverlay from '@/components/LoadingOverlay.vue';

// 声明微信小程序类型
declare const wx: any;

@Component({ components: { LoadingOverlay } })
export default class MattingPage extends Vue {
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
  
  // 抠图设置 - 默认选择150 DPI以减少文件大小
  selectedModel: string = 'modnet_photographic_portrait_matting';
  dpi: number = 150;
  
  // 抠图模型选项
  mattingModels = [
    { label: '高精度', value: 'modnet_photographic_portrait_matting' },
    { label: '标准版', value: 'hivision_modnet' },
    { label: '轻量版', value: 'rmbg-1.4' },
    { label: '增强版', value: 'birefnet-v1-lite' }
  ];
  
  // DPI选项
  dpiOptions = [
    { label: '150 DPI', value: 150 },
    { label: '300 DPI', value: 300 },
    { label: '600 DPI', value: 600 }
  ];

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
    // 直接进行处理，不显示预览弹窗
    this.confirmSelect();
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
        // 直接进行处理，不显示预览弹窗
        this.confirmSelect();
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
        // 直接进行处理，不显示预览弹窗
        this.confirmSelect();
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
  async confirmSelect() {
    if (!this.imagePath) {
      uni.showToast({
        title: '请先选择图片',
        icon: 'none'
      });
      return;
    }

    this.loading = true;
    const prefix = 'data:image/png;base64,'
    let imageBase64 = ''
    let imagePath = ''
    //提交后台服务器  获取base64
    const params: MattingParams = {
      human_matting_model: this.selectedModel,
      dpi: this.dpi
    };
    
    try {
      const data = await humanMatting(params, 'input_image', this.imagePath);
      console.log('API返回数据:', data);
      
      imageBase64 = data['image_base64'];
      console.log('获取到base64数据，长度:', imageBase64.length);
      
      const fs = uni.getFileSystemManager();
      // #ifdef MP-WEIXIN
      imagePath = `${wx.env.USER_DATA_PATH}/matting_result.png`;
      // #endif
      
      // 保存到电子照历史记录
      this.saveToElectronicPhoto(imageBase64, '人像抠图');
      
      console.log('准备跳转到结果页面');
      
      // 直接传递base64数据，避免文件存储超限问题
      uni.navigateTo({
        url: `/pages/matting/result?image=${encodeURIComponent(imageBase64)}`,
        success: () => {
          console.log('跳转成功');
          this.loading = false;
        },
        fail: (err) => {
          console.error('跳转失败:', err);
          this.loading = false;
        }
      });
    } catch (err) {
      console.error('抠图处理失败:', err);
      uni.showToast({
        title: '抠图处理失败，请重试',
        icon: 'none'
      });
      this.loading = false;
    }
  }

  /**
   * 保存到电子照历史记录
   */
  saveToElectronicPhoto(base64Image: string, type: string) {
    try {
      const historyData = uni.getStorageSync('electronic_photo_history') || [];
      const newRecord = {
        id: Date.now(),
        type: type,
        image: base64Image,
        timestamp: new Date().toISOString()
      };
      historyData.unshift(newRecord);
      // 只保留最近20条记录
      if (historyData.length > 20) {
        historyData.splice(20);
      }
      uni.setStorageSync('electronic_photo_history', historyData);
      console.log('已保存到电子照历史记录');
    } catch (err) {
      console.error('保存到电子照历史记录失败:', err);
    }
  }

  /**
   * 处理存储空间超限错误
   */
  handleStorageLimitError(imageBase64: string) {
    try {
      // 清理旧的临时文件
      const fs = uni.getFileSystemManager();
      const userDataPath = wx.env.USER_DATA_PATH;
      
      // 读取用户数据目录下的文件
      fs.readdir({
        dirPath: userDataPath,
        success: (res) => {
          const files = res.files || [];
          const mattingFiles = files.filter((file: string) => 
            file.startsWith('matting_') && file.endsWith('.png')
          );
          
          // 删除旧的抠图文件，只保留最新的3个
          if (mattingFiles.length > 3) {
            const filesToDelete = mattingFiles.slice(3);
            filesToDelete.forEach((file: string) => {
              fs.unlink({
                filePath: `${userDataPath}/${file}`,
                success: () => {
                  console.log(`已删除旧文件: ${file}`);
                },
                fail: (err) => {
                  console.error(`删除文件失败: ${file}`, err);
                }
              });
            });
          }
          
          // 重新尝试保存新文件
          setTimeout(() => {
            this.retrySaveWithNewName(imageBase64);
          }, 1000);
        },
        fail: (err) => {
          console.error('读取目录失败:', err);
          this.showStorageError();
        }
      });
    } catch (err) {
      console.error('处理存储错误失败:', err);
      this.showStorageError();
    }
  }

  /**
   * 使用新文件名重新保存
   */
  retrySaveWithNewName(imageBase64: string) {
    const prefix = 'data:image/png;base64,';
    const fs = uni.getFileSystemManager();
    const timestamp = Date.now();
    const tempImagePath = `${wx.env.USER_DATA_PATH}/matting_${timestamp}.png`;
    
    fs.writeFile({
      filePath: tempImagePath,
      data: imageBase64.replace(prefix, ''),
      encoding: 'base64',
      success: (res) => {
        console.log(res, "重新写入本地成功");
        this.saveToElectronicPhoto(imageBase64, '人像抠图');
        
        uni.navigateTo({
          url: `/pages/matting/result?image=${encodeURIComponent(tempImagePath)}`,
          success: () => {
            this.loading = false;
          }
        });
      },
      fail: (err) => {
        console.error("重新写入失败:", err);
        this.showStorageError();
        this.loading = false;
      }
    });
  }

  /**
   * 显示存储错误提示
   */
  showStorageError() {
    uni.showModal({
      title: '存储空间不足',
      content: '设备存储空间不足，请清理微信缓存或重启应用后重试。',
      showCancel: false,
      confirmText: '我知道了',
      success: () => {
        this.loading = false;
      }
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

// 人像轮廓指引
.portrait-guide {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  width: 500rpx;
  height: 700rpx;
  
  .portrait-svg {
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 0 8rpx rgba(76, 175, 80, 0.3));
    animation: portraitPulse 3s infinite ease-in-out;
  }
}

// 人像轮廓动画
@keyframes portraitPulse {
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
</style>
