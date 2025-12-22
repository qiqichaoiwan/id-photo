<template>
  <view class="help-page">
    <view class="content-container">
      <view class="header-section">
        <view class="help-icon">
              <u-icon name="integral-fill" size="60" color="white" />
        </view>
        <text class="page-title">使用帮助</text>
        <text class="subtitle">快速上手，小七快照拍助您制作专业证件照</text>
      </view>

      <scroll-view class="content-scroll" scroll-y="true">
        <view class="content-section">
          <!-- 快速开始 -->
          <view class="help-section">
            <view class="section-header">
              <u-icon name="play-right" size="24" color="#2196F3" />
              <text class="section-title">快速开始</text>
            </view>
            <view class="step-list">
              <view class="step-item">
                <view class="step-number">1</view>
                <view class="step-content">
                  <text class="step-title">选择尺寸</text>
                  <text class="step-desc">在首页选择需要的证件照规格，如一寸、二寸、身份证等</text>
                </view>
              </view>
              <view class="step-item">
                <view class="step-number">2</view>
                <view class="step-content">
                  <text class="step-title">上传照片</text>
                  <text class="step-desc">拍摄新照片或从相册选择照片，建议选择正面、光线充足的照片</text>
                </view>
              </view>
              <view class="step-item">
                <view class="step-number">3</view>
                <view class="step-content">
                  <text class="step-title">编辑调整</text>
                  <text class="step-desc">调整背景色、照片效果，确保符合要求</text>
                </view>
              </view>
              <view class="step-item">
                <view class="step-number">4</view>
                <view class="step-content">
                  <text class="step-title">保存使用</text>
                  <text class="step-desc">保存到相册或电子照，随时查看和下载</text>
                </view>
              </view>
            </view>
          </view>

          <!-- 支持尺寸 -->
          <view class="help-section">
            <view class="section-header">
              <u-icon name="grid-fill" size="24" color="#4CAF50" />
              <text class="section-title">支持尺寸</text>
            </view>
            <view class="size-grid">
              <view class="size-item">
                <text class="size-name">一寸</text>
                <text class="size-desc">25×35mm</text>
              </view>
              <view class="size-item">
                <text class="size-name">二寸</text>
                <text class="size-desc">35×49mm</text>
              </view>
              <view class="size-item">
                <text class="size-name">小二寸</text>
                <text class="size-desc">35×45mm</text>
              </view>
              <view class="size-item">
                <text class="size-name">身份证</text>
                <text class="size-desc">26×32mm</text>
              </view>
              <view class="size-item">
                <text class="size-name">护照</text>
                <text class="size-desc">33×48mm</text>
              </view>
              <view class="size-item">
                <text class="size-name">驾照</text>
                <text class="size-desc">22×32mm</text>
              </view>
            </view>
            <view class="custom-size-tip">
              <u-icon name="info" size="16" color="#FF9800" />
              <text class="tip-text">还支持自定义尺寸，满足特殊需求</text>
            </view>
          </view>

          <!-- 背景色选择 -->
          <view class="help-section">
            <view class="section-header">
              <u-icon name="bookmark" size="24" color="#FF9800" />
              <text class="section-title">背景色选择</text>
            </view>
            <view class="color-list">
              <view class="color-item">
                <view class="color-preview" style="background-color: #FFFFFF;"></view>
                <text class="color-name">白色</text>
                <text class="color-usage">最常用，适用于多数证件</text>
              </view>
              <view class="color-item">
                <view class="color-preview" style="background-color: #FF0000;"></view>
                <text class="color-name">红色</text>
                <text class="color-usage">毕业证、身份证等</text>
              </view>
              <view class="color-item">
                <view class="color-preview" style="background-color: #4169E1;"></view>
                <text class="color-name">蓝色</text>
                <text class="color-usage">护照、签证等</text>
              </view>
              <view class="color-item">
                <view class="color-preview" style="background-color: #87CEEB;"></view>
                <text class="color-name">浅蓝色</text>
                <text class="color-usage">部分身份证件</text>
              </view>
            </view>
          </view>

          <!-- 照片要求 -->
          <view class="help-section">
            <view class="section-header">
              <u-icon name="camera" size="24" color="#9C27B0" />
              <text class="section-title">照片要求</text>
            </view>
            <view class="requirement-list">
              <view class="requirement-item">
                <u-icon name="checkmark-circle" size="20" color="#4CAF50" />
                <text class="requirement-text">正面照，面部清晰可见</text>
              </view>
              <view class="requirement-item">
                <u-icon name="checkmark-circle" size="20" color="#4CAF50" />
                <text class="requirement-text">光线充足，避免阴影</text>
              </view>
              <view class="requirement-item">
                <u-icon name="checkmark-circle" size="20" color="#4CAF50" />
                <text class="requirement-text">表情自然，嘴巴闭合</text>
              </view>
              <view class="requirement-item">
                <u-icon name="checkmark-circle" size="20" color="#4CAF50" />
                <text class="requirement-text">眼镜反光不超过眼睛50%</text>
              </view>
              <view class="requirement-item">
                <u-icon name="close-circle" size="20" color="#F44336" />
                <text class="requirement-text">避免戴帽子、墨镜等遮挡物</text>
              </view>
              <view class="requirement-item">
                <u-icon name="close-circle" size="20" color="#F44336" />
                <text class="requirement-text">避免过度美颜、滤镜处理</text>
              </view>
            </view>
          </view>

          <!-- 电子照功能 -->
          <view class="help-section">
            <view class="section-header">
              <u-icon name="folder" size="24" color="#F77261" />
              <text class="section-title">电子照功能</text>
            </view>
            <view class="feature-list">
              <view class="feature-item">
                <text class="feature-title">自动保存</text>
                <text class="feature-desc">编辑页面开启"保存到电子照"开关，制作的证件照会自动保存</text>
              </view>
              <view class="feature-item">
                <text class="feature-title">随时查看</text>
                <text class="feature-desc">在"我的电子照"页面查看所有保存的证件照</text>
              </view>
              <view class="feature-item">
                <text class="feature-title">便捷下载</text>
                <text class="feature-desc">点击下载按钮，直接保存到手机相册</text>
              </view>
              <view class="feature-item">
                <text class="feature-title">管理删除</text>
                <text class="feature-desc">长按照片可以删除不需要的证件照</text>
              </view>
            </view>
          </view>

          <!-- 常见问题 -->
          <view class="help-section">
            <view class="section-header">
              <u-icon name="question" size="24" color="#607D8B" />
              <text class="section-title">常见问题</text>
            </view>
            <view class="faq-list">
              <view class="faq-item" @click="toggleFaq(0)">
                <view class="faq-question">
                  <text class="question-text">为什么制作效果不理想？</text>
                  <u-icon :name="faqExpanded[0] ? 'arrow-up' : 'arrow-down'" size="16" color="#999" />
                </view>
                <view class="faq-answer" v-if="faqExpanded[0]">
                  <text class="answer-text">请确保：</text>
                  <text class="answer-text">1. 照片清晰，面部无遮挡</text>
                  <text class="answer-text">2. 光线充足，背景简洁</text>
                  <text class="answer-text">3. 选择正确的证件照规格</text>
                </view>
              </view>
              
              <view class="faq-item" @click="toggleFaq(1)">
                <view class="faq-question">
                  <text class="question-text">电子照保存在哪里？</text>
                  <u-icon :name="faqExpanded[1] ? 'arrow-up' : 'arrow-down'" size="16" color="#999" />
                </view>
                <view class="faq-answer" v-if="faqExpanded[1]">
                  <text class="answer-text">电子照保存在应用本地存储中：</text>
                  <text class="answer-text">1. 点击底部"电子照"标签页</text>
                  <text class="answer-text">2. 可以查看、下载或删除</text>
                  <text class="answer-text">3. 不会占用手机相册空间</text>
                </view>
              </view>
              
              <view class="faq-item" @click="toggleFaq(2)">
                <view class="faq-question">
                  <text class="question-text">支持哪些图片格式？</text>
                  <u-icon :name="faqExpanded[2] ? 'arrow-up' : 'arrow-down'" size="16" color="#999" />
                </view>
                <view class="faq-answer" v-if="faqExpanded[2]">
                  <text class="answer-text">支持常见图片格式：</text>
                  <text class="answer-text">1. JPG/JPEG - 推荐</text>
                  <text class="answer-text">2. PNG - 支持透明背景</text>
                  <text class="answer-text">3. 建议图片大小不超过10MB</text>
                </view>
              </view>
            </view>
          </view>

          <!-- 联系我们 -->
          <view class="help-section">
            <view class="section-header">
              <u-icon name="chat" size="24" color="#F44336" />
              <text class="section-title">联系我们</text>
            </view>
            <view class="contact-list">
              <view class="contact-item" @click="goToFeedback">
                <u-icon name="edit-pen" size="20" color="#F77261" />
                <text class="contact-text">意见反馈</text>
                <u-icon name="arrow-right" size="16" color="#ccc" />
              </view>
              <view class="contact-item">
                <u-icon name="email" size="20" color="#2196F3" />
                <text class="contact-text">客服邮箱</text>
                <text class="contact-email">761287561@qq.com</text>
              </view>
            </view>
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
export default class Help extends Vue {
  faqExpanded: boolean[] = [false, false, false];

  onLoad() {
    uni.setNavigationBarTitle({
      title: '使用帮助'
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
   * 切换FAQ展开状态
   */
  toggleFaq(index: number) {
    this.$set(this.faqExpanded, index, !this.faqExpanded[index]);
  }

  /**
   * 跳转到意见反馈
   */
  goToFeedback() {
    uni.navigateBack({
      delta: 2
    });
    
    // 延迟触发反馈弹窗
    setTimeout(() => {
      uni.switchTab({
        url: '/pages/mine/index'
      });
    }, 100);
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
.help-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
}

.content-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header-section {
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  padding: 60rpx 40rpx 40rpx;
  text-align: center;
  padding-top: calc(60rpx + env(safe-area-inset-top));
  
  .help-icon {
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
    margin-bottom: 8rpx;
  }
  
  .subtitle {
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

.help-section {
  margin-bottom: 40rpx;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  .section-header {
    display: flex;
    align-items: center;
    margin-bottom: 24rpx;
    
    .section-title {
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
      margin-left: 12rpx;
    }
  }
}

// 快速开始步骤
.step-list {
  .step-item {
    display: flex;
    align-items: flex-start;
    margin-bottom: 24rpx;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .step-number {
      width: 56rpx;
      height: 56rpx;
      background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
      border-radius: 28rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 24rpx;
      font-weight: bold;
      margin-right: 20rpx;
      flex-shrink: 0;
    }
    
    .step-content {
      flex: 1;
      padding-top: 8rpx;
      
      .step-title {
        display: block;
        font-size: 28rpx;
        font-weight: 600;
        color: #333;
        margin-bottom: 8rpx;
      }
      
      .step-desc {
        font-size: 24rpx;
        color: #666;
        line-height: 1.6;
      }
    }
  }
}

// 尺寸网格
.size-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20rpx;
  margin-bottom: 20rpx;
  
  .size-item {
    background: #f8f9fa;
    border-radius: 16rpx;
    padding: 20rpx;
    text-align: center;
    
    .size-name {
      display: block;
      font-size: 26rpx;
      font-weight: 600;
      color: #333;
      margin-bottom: 8rpx;
    }
    
    .size-desc {
      font-size: 22rpx;
      color: #666;
    }
  }
}

.custom-size-tip {
  display: flex;
  align-items: center;
  background: rgba(255, 152, 0, 0.1);
  border-radius: 12rpx;
  padding: 16rpx;
  
  .tip-text {
    font-size: 24rpx;
    color: #FF9800;
    margin-left: 8rpx;
  }
}

// 背景色列表
.color-list {
  .color-item {
    display: flex;
    align-items: center;
    margin-bottom: 20rpx;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .color-preview {
      width: 48rpx;
      height: 48rpx;
      border-radius: 24rpx;
      border: 2rpx solid #f0f0f0;
      margin-right: 16rpx;
      flex-shrink: 0;
    }
    
    .color-name {
      font-size: 26rpx;
      font-weight: 600;
      color: #333;
      margin-right: 12rpx;
      width: 80rpx;
    }
    
    .color-usage {
      flex: 1;
      font-size: 24rpx;
      color: #666;
    }
  }
}

// 要求列表
.requirement-list {
  .requirement-item {
    display: flex;
    align-items: center;
    margin-bottom: 16rpx;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .requirement-text {
      font-size: 26rpx;
      color: #666;
      margin-left: 12rpx;
      line-height: 1.6;
    }
  }
}

// 功能列表
.feature-list {
  .feature-item {
    margin-bottom: 20rpx;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .feature-title {
      display: block;
      font-size: 26rpx;
      font-weight: 600;
      color: #333;
      margin-bottom: 8rpx;
    }
    
    .feature-desc {
      font-size: 24rpx;
      color: #666;
      line-height: 1.6;
    }
  }
}

// FAQ列表
.faq-list {
  .faq-item {
    border-bottom: 1rpx solid #f0f0f0;
    padding: 20rpx 0;
    
    &:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }
    
    .faq-question {
      display: flex;
      align-items: center;
      justify-content: space-between;
      
      .question-text {
        font-size: 26rpx;
        font-weight: 600;
        color: #333;
        flex: 1;
      }
    }
    
    .faq-answer {
      margin-top: 16rpx;
      padding-left: 12rpx;
      
      .answer-text {
        display: block;
        font-size: 24rpx;
        color: #666;
        line-height: 1.6;
        margin-bottom: 8rpx;
        
        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }
}

// 联系方式
.contact-list {
  .contact-item {
    display: flex;
    align-items: center;
    padding: 20rpx 0;
    border-bottom: 1rpx solid #f0f0f0;
    
    &:last-child {
      border-bottom: none;
    }
    
    .contact-text {
      flex: 1;
      font-size: 26rpx;
      color: #333;
      margin-left: 12rpx;
    }
    
    .contact-email {
      font-size: 24rpx;
      color: #2196F3;
      margin-left: 12rpx;
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
</style>
