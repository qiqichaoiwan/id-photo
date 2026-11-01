<template>
  <view class="privacy-page">
    <view class="content-container">
      <view class="header-section">
        <view class="privacy-icon">
          <u-icon name="lock" size="28" color="#287c70" />
        </view>
        <text class="page-title">隐私政策</text>
        <text class="update-date">更新日期：2026年10月</text>
      </view>

      <scroll-view class="content-scroll" scroll-y="true">
        <view class="content-section">
          <view class="section-block">
            <text class="section-title">照片处理</text>
            <text class="section-content">选择或拍摄照片后，照片会通过网络发送至证件照处理服务，以完成人像抠图、证件照制作或水印处理。处理结果会返回您的设备。</text>
          </view>
          <view class="section-block">
            <text class="section-title">内容安全识别</text>
            <text class="section-content">为遵守平台内容安全要求，上传的照片会在处理前调用微信公众平台内容安全接口进行识别。原始照片只用于本次检查和照片处理，服务端不保存原图；仅保留检测时间、文件摘要、错误码和检测编号等必要的审计信息。</text>
          </view>
          <view class="section-block">
            <text class="section-title">本地保存</text>
            <text class="section-content">处理过程中会在小程序本地生成临时图片。您选择保存到电子照时，照片会保存在本设备的小程序存储中；保存到相册需要您的授权。</text>
            <text class="section-content">您可以在“我的 → 清理本地照片”删除小程序内的电子照、历史记录和临时图片。已保存到手机相册的照片请在相册中删除。</text>
          </view>
          <view class="section-block">
            <text class="section-title">微信服务与广告</text>
            <text class="section-content">本应用使用微信登录能力验证访问，并使用微信激励视频广告。微信及广告服务可能按照其规则处理相关数据，具体请参阅微信的隐私说明。</text>
          </view>
          <view class="section-block">
            <text class="section-title">联系我们</text>
            <text class="section-content">有关照片和隐私的问题，可通过 761287561@qq.com 联系我们。</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- 原生分享按钮 - 使用open-type="share"直接触发分享 -->
    <button v-show="false" open-type="share" class="native-share-button" @getuserinfo="onShareSuccess">
      <u-icon name="share" size="20" color="white" />
    </button>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";

// 声明微信小程序类型
declare const wx: any;

@Component({})
export default class PrivacyPolicy extends Vue {
  onLoad() {
    uni.setNavigationBarTitle({
      title: '隐私政策'
    });

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
.privacy-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
}

.content-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header-section {
  background: linear-gradient(135deg, #9C27B0 0%, #673AB7 100%);
  padding: 60rpx 40rpx 40rpx;
  text-align: center;
  padding-top: calc(60rpx + env(safe-area-inset-top));
  
  .privacy-icon {
    width: 120rpx;
    height: 120rpx;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 60rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24rpx;
    backdrop-filter: blur(10rpx);
  }
  
  .page-title {
    display: block;
    font-size: 32rpx;
    font-weight: bold;
    color: white;
    margin-bottom: 12rpx;
  }
  
  .update-date {
    font-size: 24rpx;
    color: rgba(255, 255, 255, 0.8);
  }
}

.content-scroll {
  flex: 1;
  padding: 40rpx;
  box-sizing: border-box;
}

.content-section {
  background: white;
  border-radius: 24rpx;
  padding: 40rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.08);
}

.section-block {
  margin-bottom: 40rpx;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  .section-title {
    display: block;
    font-size: 32rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 24rpx;
    position: relative;
    
    &::before {
      content: '';
      position: absolute;
      left: -16rpx;
      top: 50%;
      transform: translateY(-50%);
      width: 6rpx;
      height: 32rpx;
      background: linear-gradient(135deg, #9C27B0 0%, #673AB7 100%);
      border-radius: 3rpx;
    }
  }
  
  .section-content {
    display: block;
    font-size: 28rpx;
    color: #666;
    line-height: 1.8;
    margin-bottom: 16rpx;
    text-align: justify;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .section-list {
    display: block;
    font-size: 28rpx;
    color: #666;
    line-height: 1.8;
    margin-bottom: 12rpx;
    padding-left: 32rpx;
    position: relative;
    
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 16rpx;
      width: 8rpx;
      height: 8rpx;
      background: #9C27B0;
      border-radius: 50%;
    }
  }
}

.footer-section {
  margin-top: 60rpx;
  padding-top: 30rpx;
  border-top: 2rpx solid #f0f0f0;
  text-align: center;
  
  .footer-text {
    display: block;
    font-size: 24rpx;
    color: #999;
    margin-bottom: 8rpx;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
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

@import '@/assets/legacy-page-themes.scss';
@include document-page-theme;
</style>
