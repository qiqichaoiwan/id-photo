<template>
  <view class="content">
    <!-- 快速操作区域 -->
    <view class="quick-actions">
      <view class="section-title">
        <text class="title-text">智能工具</text>
        <text class="title-desc">AI驱动的图像处理工具</text>
      </view>
      
      <view class="action-cards">
        <!-- 一寸照卡片 -->
        <view class="action-card primary-card animated-card" @click="navigateToPhotoSelect(11)">
          <view class="card-content">
            <view class="card-image">
              <u-image 
                src="@/static/example.jpeg" 
                class="example-image" 
                width="120rpx" 
                height="168rpx" 
                radius="12rpx" 
              />
            </view>
            <view class="card-info">
              <text class="card-title">证件照制作</text>
              <text class="card-desc">专业规格 一键生成</text>
              <view class="card-tag">
                <u-tag text="热门" type="error" size="mini" class="unified-tag" />
              </view>
            </view>
          </view>
        </view>

        <!-- 新功能卡片 -->
        <view class="feature-cards">
          <view class="action-card feature-card matting-card" @click="navigateToMatting">
            <view class="card-content">
              <view class="card-icon">
                <u-icon name="cut" size="36" color="#FF6B6B" />
              </view>
              <view class="card-info">
                <text class="card-title">人像抠图</text>
                <text class="card-desc">AI智能识别</text>
                <view class="custom-tag ai-tag">AI</view>
              </view>
            </view>
          </view>

          <view class="action-card feature-card watermark-card" @click="navigateToWatermark">
            <view class="card-content">
              <view class="card-icon">
                <u-icon name="edit-pen" size="36" color="#4ECDC4" />
              </view>
              <view class="card-info">
                <text class="card-title">图片加水印</text>
                <text class="card-desc">个性定制</text>
                <view class="custom-tag practical-tag">实用</view>
              </view>
            </view>
          </view>
        </view>

        <!-- 传统功能 -->
        <view class="secondary-cards">
          <view class="action-card secondary-card" @click="navigateToPhotoSelect(12)">
            <view class="card-content">
              <view class="card-icon">
                <u-icon name="photo" size="32" color="#F77261" />
              </view>
              <view class="card-info">
                <text class="card-title">二寸照</text>
                <text class="card-desc">35mm × 49mm</text>
                <view class="custom-tag recommend-tag">推荐</view>
              </view>
            </view>
          </view>

          <view class="action-card secondary-card" @click="openCustomSize(true)">
            <view class="card-content">
              <view class="card-icon">
                <u-icon name="setting" size="32" color="#4CAF50" />
              </view>
              <view class="card-info">
                <text class="card-title">自定义尺寸</text>
                <text class="card-desc">任意规格</text>
                <view class="custom-tag new-tag">NEW</view>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 热门证件照类型 -->
    <view class="popular-types">
      <view class="section-title">
        <text class="title-text">热门证件照</text>
        <text class="title-desc">按需选择，专业规格</text>
      </view>
      
      <view class="type-grid">
        <view 
          :class="['type-item', 'rank' + index]" 
          v-for="(item, index) in popularList" 
          :key="index"
          @click="navigateToPhotoSelect(item.id)"
        >
          <view class="type-rank">{{ numberCase(index) }}</view>
          <view class="type-info">
            <text class="type-name">{{ item.name }}</text>
            <text class="type-size">{{ item.mmWidth }}×{{ item.mmHeight }}mm</text>
          </view>
          <view class="type-arrow">
            <u-icon name="arrow-right" size="16" color="#999" />
          </view>
        </view>
      </view>
    </view>

    <!-- 功能特色 -->
    <view class="features">
      <view class="section-title">
        <text class="title-text">功能特色</text>
        <text class="title-desc">智能AI，专业品质</text>
      </view>
      
      <view class="feature-grid">
        <view class="feature-item" v-for="(feature, index) in features" :key="index">
          <view class="feature-icon">
            <u-icon :name="feature.icon" size="32" :color="feature.color" />
          </view>
          <text class="feature-title">{{ feature.title }}</text>
          <text class="feature-desc">{{ feature.desc }}</text>
        </view>
      </view>
    </view>

    <!-- 使用统计 -->
    <view class="stats">
      <view class="stats-item">
        <text class="stats-number">{{ formatNumber(statistics.totalPhotos) }}</text>
        <text class="stats-label">累计制作</text>
      </view>
      <view class="stats-divider"></view>
      <view class="stats-item">
        <text class="stats-number">{{ statistics.usageDays }}</text>
        <text class="stats-label">使用天数</text>
      </view>
    </view>

    <!-- 自定义尺寸弹窗 -->
    <u-popup :show="customSize" mode="bottom" round="20" @close="openCustomSize(false)">
      <view class="size-form">
        <view class="form-header">
          <text class="form-title">自定义尺寸</text>
          <u-icon name="close" size="20" @click="openCustomSize(false)" />
        </view>
        
        <u-form label-width="120rpx" label-align="center" :model="customSizeForm" ref="sizeForm">
          <u-form-item label="宽度" prop="width">
            <u-input 
              type="number" 
              v-model="customSizeForm.width" 
              placeholder="80-1200"
              :custom-style="{ width: '300rpx' }"
            />
            <template slot="right">
              <text class="unit">px</text>
            </template>
          </u-form-item>
          
          <u-form-item label="高度" prop="height">
            <u-input 
              type="number" 
              v-model="customSizeForm.height" 
              placeholder="80-1200"
              :custom-style="{ width: '300rpx' }"
            />
            <template slot="right">
              <text class="unit">px</text>
            </template>
          </u-form-item>
          
          <u-form-item label="物理尺寸">
            <text class="size-info">{{ mmWidth && mmHeight ? `${mmWidth} × ${mmHeight}` : '-' }} mm</text>
          </u-form-item>
          
          <u-form-item label="分辨率">
            <text class="size-info">{{ customSizeForm.dpi }} DPI</text>
          </u-form-item>
        </u-form>

        <view class="form-actions">
          <u-button 
            type="info" 
            :plain="true" 
            @click="openCustomSize(false)"
            :custom-style="{ width: '240rpx', borderRadius: '20rpx' }"
          >
            取消
          </u-button>
          <u-button 
            color="#F77261" 
            @click="goToGenerate"
            :custom-style="{ width: '240rpx', borderRadius: '20rpx' }"
          >
            开始制作
          </u-button>
        </view>
      </view>
    </u-popup>

    <!-- 原生分享按钮 - 使用open-type="share"直接触发分享 -->
    <button open-type="share" class="native-share-button" @getuserinfo="onShareSuccess">
      <u-icon name="share" size="20" color="white" />
    </button>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component, Ref } from "vue-property-decorator";
import { photoSizes, PhotoSize, getPhotoSize } from '@/model/PhotoSize'
import { Mutation } from 'vuex-class';
import StorageManager from '@/utils/storage';

// 声明微信小程序类型
declare const wx: any;

@Component({})
export default class Index extends Vue {
  // 热门照片尺寸
  popularList = photoSizes.slice(0, 8);
  
  // 功能特色
  features = [
    {
      icon: 'checkmark-circle',
      color: '#4CAF50',
      title: 'AI智能抠图',
      desc: '精准识别人像轮廓'
    },
    {
      icon: 'more-circle',
      color: '#2196F3',
      title: '多色背景',
      desc: '支持多种背景色'
    },
    {
      icon: 'level',
      color: '#FF9800',
      title: '高清输出',
      desc: '支持高清图片生成'
    },
    {
      icon: 'grid',
      color: '#9C27B0',
      title: '批量排版',
      desc: '智能排版打印'
    }
  ];

  // 自定义尺寸弹窗
  customSize: boolean = false;

  customSizeForm: {
    height?: number;
    width?: number;
    dpi: number;
  } = {
    height: undefined,
    width: undefined,
    dpi: 300
  };

  // 用户统计
  statistics: any = {
    totalPhotos: 0,
    usageDays: 0
  };

  @Ref('sizeForm') readonly sizeForm!: HTMLFormElement;

  // 设置vuex
  @Mutation('SET_PHOTO_SIZE') setPhotoSize!: (data: PhotoSize) => void;

  // 300DPI时的换算系数
  readonly DPICoefficient = 25.4;

  mounted() {
    this.loadUserStatistics();
    this.initFormRules();
    
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
   * 加载用户统计
   */
  loadUserStatistics() {
    this.statistics = StorageManager.getUserStatistics();
  }

  /**
   * 初始化表单验证规则
   */
  initFormRules() {
    const rules = {
      height: [
        { required: true, message: "请输入高度", trigger: ['change', 'blur'] },
        { type: 'integer', message: "请输入整数", trigger: ['change', 'blur'] },
        {
          validator: (rule: any, value: any, callback: any) => {
            if (Number(value) >= 80 && Number(value) <= 1200) callback();
            else callback(new Error("高度应该在80-1200px之间"));
          },
          trigger: ['change', 'blur']
        }
      ],
      width: [
        { required: true, message: "请输入宽度", trigger: ['change', 'blur'] },
        { type: 'integer', message: "请输入整数", trigger: ['change', 'blur'] },
        {
          validator: (rule: any, value: any, callback: any) => {
            if (Number(value) >= 80 && Number(value) <= 1200) callback();
            else callback(new Error("宽度应该在80-1200px之间"));
          },
          trigger: ['change', 'blur']
        }
      ]
    };
    this.$nextTick(() => {
      this.sizeForm.setRules(rules);
    });
  }

  /**
   * 数字转换
   */
  numberCase(index: number): string {
    const num = index + 1;
    return num >= 10 ? num.toString() : '0' + num;
  }

  /**
   * 格式化数字
   */
  formatNumber(num: number): string {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + 'w';
    }
    return num.toString();
  }

  get mmWidth(): number {
    const { customSizeForm } = this;
    return Math.round((customSizeForm.width || 0) * this.DPICoefficient / customSizeForm.dpi);
  }

  get mmHeight(): number {
    const { customSizeForm } = this;
    return Math.round((customSizeForm.height || 0) * this.DPICoefficient / customSizeForm.dpi);
  }

  /**
   * 打开自定义尺寸弹窗
   */
  openCustomSize(flag: boolean) {
    this.customSize = flag;
  }

  /**
   * 跳转到生成页面
   */
  goToGenerate() {
    const { mmHeight, mmWidth, customSizeForm: { height, width, dpi }, setPhotoSize } = this;

    this.sizeForm.validate().then(() => {
      if (height && width) {
        const photoSize: PhotoSize = {
          name: "自定义尺寸",
          pxHeight: height,
          pxWidth: width,
          mmHeight: mmHeight,
          mmWidth: mmWidth,
          dpi: dpi
        };
        
        uni.navigateTo({
          url: '/pages/photo/index',
          success() {
            setPhotoSize(photoSize);
          }
        });
      }
    }).catch((error: any) => {
      uni.showToast({
        title: error[0]?.message || '请按照规则填写宽度和高度',
        icon: 'none'
      });
    });
  }

  /**
   * 跳转到图片选择页
   */
  navigateToPhotoSelect(id: number) {
    const { setPhotoSize } = this;
    const photoSize = getPhotoSize(id);
    if (photoSize) {
      uni.navigateTo({
        url: '/pages/photo/index?id=' + id,
        success() {
          setPhotoSize(photoSize);
        }
      });
    }
  }

  /**
   * 跳转到历史记录
   */
  navigateToHistory() {
    uni.navigateTo({
      url: '/pages/history/index'
    });
  }

  /**
   * 跳转到人像抠图
   */
  navigateToMatting() {
    uni.navigateTo({
      url: '/pages/matting/index'
    });
  }

  /**
   * 跳转到图片加水印
   */
  navigateToWatermark() {
    uni.navigateTo({
      url: '/pages/watermark/index'
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
.content {
  width: 100%;
  min-height: 100vh;
  background: #f8f9fa;
}

// 主内容区域
.main-content {
  background: white;
  border-radius: 40rpx 40rpx 0 0;
  margin-top: -20rpx;
  padding-top: 40rpx;
  min-height: calc(100vh - 200rpx);
}

// 轮播图
.banner-section {
  padding: 0 40rpx;
  margin-bottom: 40rpx;
  
  .banner {
    border-radius: 20rpx;
    overflow: hidden;
  }
}

// 通用标题样式
.section-title {
  padding: 0 40rpx 30rpx;
  
  .title-text {
    font-size: 36rpx;
    font-weight: bold;
    color: #333;
    display: block;
    margin-bottom: 8rpx;
  }
  
  .title-desc {
    font-size: 24rpx;
    color: #999;
  }
}

// 快速操作区域
.quick-actions {
  background: white;
  border-radius: 40rpx 40rpx 0 0;
  margin-top: -20rpx;
  padding: 40rpx 0;
}

.action-cards {
  padding: 0 40rpx;
}

.primary-card {
  background: linear-gradient(135deg, #F77261 0%, #FF9A8B 100%);
  border-radius: 24rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 8rpx 24rpx rgba(247, 114, 97, 0.3);
  
  .card-content {
    display: flex;
    align-items: center;
    gap: 30rpx;
  }
  
  .card-info {
    flex: 1;
    
    .card-title {
      color: white;
      font-size: 32rpx;
      font-weight: bold;
      display: block;
      margin-bottom: 8rpx;
    }
    
    .card-desc {
      color: rgba(255, 255, 255, 0.8);
      font-size: 24rpx;
      display: block;
      margin-bottom: 16rpx;
    }
  }
}

.feature-cards {
  display: flex;
  gap: 20rpx;
  margin-bottom: 30rpx;
}

.feature-card {
  flex: 1;
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.05) 0%, rgba(78, 205, 196, 0.05) 100%);
  border-radius: 20rpx;
  padding: 30rpx;
  border: 2rpx solid #E9ECEF;
  
  .card-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .card-icon {
    margin-bottom: 20rpx;
  }
  
  .card-info {
    .card-title {
      font-size: 28rpx;
      font-weight: bold;
      color: #333;
      display: block;
      margin-bottom: 8rpx;
    }
    
    .card-desc {
      font-size: 22rpx;
      color: #666;
      display: block;
    }
  }
}

.secondary-cards {
  display: flex;
  gap: 20rpx;
}

.secondary-card {
  flex: 1;
  background: #F8F9FA;
  border-radius: 20rpx;
  padding: 30rpx;
  border: 2rpx solid #E9ECEF;
  
  .card-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .card-icon {
    margin-bottom: 20rpx;
  }
  
  .card-info {
    .card-title {
      font-size: 28rpx;
      font-weight: bold;
      color: #333;
      display: block;
      margin-bottom: 8rpx;
    }
    
    .card-desc {
      font-size: 22rpx;
      color: #666;
      display: block;
      margin-bottom: 12rpx;
    }
  }
}

// 热门证件照类型
.popular-types {
  background: white;
  padding: 40rpx 0;
  margin-top: 20rpx;
}

.type-grid {
  padding: 0 40rpx;
}

.type-item {
  display: flex;
  align-items: center;
  padding: 30rpx;
  margin-bottom: 20rpx;
  background: #F8F9FA;
  border-radius: 16rpx;
  border-left: 6rpx solid #F77261;
  transition: all 0.3s ease;
  
  &:active {
    transform: scale(0.98);
    background: #E9ECEF;
  }
  
  .type-rank {
    font-size: 28rpx;
    font-weight: bold;
    color: #F77261;
    margin-right: 20rpx;
    min-width: 60rpx;
  }
  
  .type-info {
    flex: 1;
    
    .type-name {
      font-size: 28rpx;
      font-weight: bold;
      color: #333;
      display: block;
      margin-bottom: 4rpx;
    }
    
    .type-size {
      font-size: 22rpx;
      color: #666;
    }
  }
  
  .type-arrow {
    color: #999;
  }
}

.rank0 .type-rank { color: #FF4757; }
.rank1 .type-rank { color: #FF6348; }
.rank2 .type-rank { color: #FFA502; }

// 功能特色
.features {
  background: white;
  padding: 40rpx 0;
}

.feature-grid {
  padding: 0 40rpx;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30rpx;
}

.feature-item {
  text-align: center;
  padding: 30rpx 20rpx;
  background: #F8F9FA;
  border-radius: 16rpx;
  
  .feature-icon {
    display: flex;
    justify-content: center;
    margin-bottom: 20rpx;
  }
  
  .feature-title {
    font-size: 26rpx;
    font-weight: bold;
    color: #333;
    display: block;
    margin-bottom: 8rpx;
  }
  
  .feature-desc {
    font-size: 22rpx;
    color: #666;
  }
}

// 使用统计
.stats {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  margin-top: 20rpx;
  
  .stats-item {
    flex: 1;
    text-align: center;
    
    .stats-number {
      font-size: 48rpx;
      font-weight: bold;
      color: white;
      display: block;
      margin-bottom: 8rpx;
    }
    
    .stats-label {
      font-size: 24rpx;
      color: rgba(255, 255, 255, 0.8);
    }
  }
  
  .stats-divider {
    width: 2rpx;
    height: 60rpx;
    background: rgba(255, 255, 255, 0.3);
  }
}

// AI智能工具区域
.ai-tools {
  background: white;
  padding: 40rpx 0;
  margin-top: 20rpx;
}

.tool-cards {
  padding: 0 40rpx;
}

.tool-card {
  display: flex;
  align-items: center;
  padding: 40rpx;
  margin-bottom: 20rpx;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-radius: 20rpx;
  border: 2rpx solid #e9ecef;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
    transition: left 0.6s ease;
  }
  
  &:active {
    transform: scale(0.98);
    box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
    
    &::before {
      left: 100%;
    }
  }
  
  .tool-icon {
    margin-right: 30rpx;
    width: 96rpx;
    height: 96rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, rgba(255, 107, 107, 0.05) 100%);
    border-radius: 24rpx;
  }
  
  .tool-info {
    flex: 1;
    
    .tool-title {
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
      display: block;
      margin-bottom: 8rpx;
    }
    
    .tool-desc {
      font-size: 24rpx;
      color: #666;
      display: block;
      margin-bottom: 12rpx;
    }
  }
  
  .tool-arrow {
    color: #999;
  }
}

.watermark-tool .tool-icon {
  background: linear-gradient(135deg, rgba(78, 205, 196, 0.1) 0%, rgba(78, 205, 196, 0.05) 100%);
}

// 动效卡片
.animated-card {
  animation: slideInUp 0.6s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// 自定义尺寸弹窗
.size-form {
  padding: 40rpx;
  background: white;
  border-radius: 20rpx 20rpx 0 0;
  
  .form-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 40rpx;
    
    .form-title {
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
    }
  }
  
  .size-info {
    color: #666;
    font-size: 28rpx;
  }
  
  .unit {
    color: #999;
    font-size: 24rpx;
  }
  
  .form-actions {
    display: flex;
    gap: 30rpx;
    margin-top: 40rpx;
    justify-content: center;
  }
}

// 统一标签样式
::v-deep .unified-tag {
  min-width: 60rpx !important;
  max-width: 80rpx !important;
  text-align: center !important;
  justify-content: center !important;
  display: inline-flex !important;
  align-items: center !important;
  padding: 4rpx 12rpx !important;
  box-sizing: border-box !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

// 针对小程序的额外样式
/* #ifdef MP-WEIXIN */
::v-deep .u-tag {
  min-width: 60rpx !important;
  max-width: 80rpx !important;
  text-align: center !important;
  justify-content: center !important;
  display: inline-flex !important;
  align-items: center !important;
  padding: 4rpx 12rpx !important;
  box-sizing: border-box !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  
  .u-tag__text {
    text-align: center !important;
    justify-content: center !important;
    display: inline-block !important;
    width: 100% !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
  }
}

// 强制居中样式 - 覆盖uView默认样式
::v-deep .u-tag-wrapper {
  display: inline-flex !important;
  justify-content: center !important;
  align-items: center !important;
  min-width: 60rpx !important;
  max-width: 80rpx !important;
}

::v-deep .u-tag {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  width: 100% !important;
  min-width: 60rpx !important;
  max-width: 80rpx !important;
}

::v-deep .u-tag__text {
  display: block !important;
  width: 100% !important;
  text-align: center !important;
  justify-content: center !important;
  align-items: center !important;
  word-break: keep-all !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

// 针对mini标签的特殊处理
::v-deep .u-tag--mini {
  min-width: 60rpx !important;
  max-width: 80rpx !important;
  padding: 2rpx 8rpx !important;
  justify-content: center !important;
  align-items: center !important;
  display: flex !important;
}

::v-deep .u-tag--mini .u-tag__text {
  font-size: 20rpx !important;
  line-height: 1.2 !important;
  text-align: center !important;
  display: block !important;
  width: 100% !important;
}
/* #endif */

// 自定义标签样式
.custom-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 60rpx;
  max-width: 80rpx;
  height: 32rpx;
  padding: 4rpx 12rpx;
  border-radius: 16rpx;
  font-size: 20rpx;
  font-weight: 600;
  line-height: 1;
  text-align: center;
  box-sizing: border-box;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 12rpx;
}

.ai-tag {
  background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
  color: white;
  border: none;
}

.practical-tag {
  background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
  color: white;
  border: none;
}

.recommend-tag {
  background: linear-gradient(135deg, #FFA726 0%, #FF7043 100%);
  color: white;
  border: none;
}

.new-tag {
  background: linear-gradient(135deg, #66BB6A 0%, #43A047 100%);
  color: white;
  border: none;
}

// 原生分享按钮 - 使用open-type="share"直接触发
.native-share-button {
  position: fixed;
  right: 40rpx;
  top: 70%;
  transform: translateY(-50%);
  z-index: 999;
  width: 100rpx;
  height: 100rpx;
  background: linear-gradient(135deg, #F77261 0%, #FF9A8B 100%);
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
</style>
