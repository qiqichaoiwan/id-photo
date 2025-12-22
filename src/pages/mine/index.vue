<template>
  <view class="mine-page">
    <!-- 用户信息头部 -->
    <view class="user-header">
      <view class="header-bg"></view>
      <view class="user-info">
        <view class="avatar-section">
          <view class="avatar-wrapper">
            <u-image 
              :src="userAvatar" 
              class="user-avatar" 
              width="140rpx" 
              height="140rpx" 
              radius="70rpx"
              mode="aspectFill"
            />
            <view class="avatar-border"></view>
          </view>
          <view class="user-details">
            <text class="welcome-text">欢迎使用</text>
            <text class="app-name">小七快照拍</text>
            <view class="user-id">
              <text class="id-text">ID: {{ formatUserId(userId) }}</text>
            </view>
          </view>
        </view>
        
        <!-- 统计信息卡片 -->
        <view class="stats-cards">
          <view class="stat-card" @click="navigateToElectronic">
            <view class="stat-icon">
              <u-icon name="folder" size="28" color="#F77261" />
            </view>
            <view class="stat-info">
              <text class="stat-number">{{ electronicCount }}</text>
              <text class="stat-label">电子照</text>
            </view>
          </view>
          
          <view class="stat-card">
            <view class="stat-icon">
              <u-icon name="camera" size="28" color="#4CAF50" />
            </view>
            <view class="stat-info">
              <text class="stat-number">{{ statistics.totalPhotos }}</text>
              <text class="stat-label">累计制作</text>
            </view>
          </view>
          
          <view class="stat-card">
            <view class="stat-icon">
              <u-icon name="calendar" size="28" color="#2196F3" />
            </view>
            <view class="stat-info">
              <text class="stat-number">{{ statistics.usageDays }}</text>
              <text class="stat-label">使用天数</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 功能菜单 -->
    <view class="menu-section">
      <!-- 我的服务 -->
      <view class="menu-group">
        <view class="group-header">
          <text class="group-title">我的服务</text>
        </view>
        
        <view class="menu-item highlight" @click="navigateToElectronic">
          <view class="menu-left">
            <view class="menu-icon-wrapper electronic">
              <u-icon name="folder" size="24" color="#F77261" />
            </view>
            <text class="menu-text">我的电子照</text>
          </view>
          <view class="menu-right">
            <text class="menu-count">{{ electronicCount }}张</text>
            <u-icon name="arrow-right" size="16" color="#ccc" />
          </view>
        </view>
      </view>

      <!-- 帮助支持 -->
      <view class="menu-group">
        <view class="group-header">
          <text class="group-title">帮助支持</text>
        </view>
        
        <view class="menu-item" @click="navigateToUserAgreement">
          <view class="menu-left">
            <view class="menu-icon-wrapper agreement">
              <u-icon name="file-text" size="24" color="#FF9800" />
            </view>
            <text class="menu-text">用户协议</text>
          </view>
          <u-icon name="arrow-right" size="16" color="#ccc" />
        </view>

        <view class="menu-item" @click="navigateToPrivacyPolicy">
          <view class="menu-left">
            <view class="menu-icon-wrapper privacy">
              <u-icon name="lock" size="24" color="#9C27B0" />
            </view>
            <text class="menu-text">隐私政策</text>
          </view>
          <u-icon name="arrow-right" size="16" color="#ccc" />
        </view>

        <view class="menu-item" @click="navigateToHelp">
          <view class="menu-left">
            <view class="menu-icon-wrapper help">
              <u-icon name="question-circle" size="24" color="#2196F3" />
            </view>
            <text class="menu-text">使用帮助</text>
          </view>
          <u-icon name="arrow-right" size="16" color="#ccc" />
        </view>

        <view class="menu-item" @click="showFeedback">
          <view class="menu-left">
            <view class="menu-icon-wrapper feedback">
              <u-icon name="chat" size="24" color="#4CAF50" />
            </view>
            <text class="menu-text">意见反馈</text>
          </view>
          <u-icon name="arrow-right" size="16" color="#ccc" />
        </view>
      </view>

      <!-- 关于我们 -->
      <view class="menu-group">
        <view class="group-header">
          <text class="group-title">关于我们</text>
        </view>
        
        <view class="menu-item" @click="showAbout">
          <view class="menu-left">
            <view class="menu-icon-wrapper about">
              <u-icon name="info-circle" size="24" color="#607D8B" />
            </view>
            <text class="menu-text">关于应用</text>
          </view>
          <view class="menu-right">
            <text class="version-text">v1.0.0</text>
            <u-icon name="arrow-right" size="16" color="#ccc" />
          </view>
        </view>

        <view class="menu-item" @click="clearCache">
          <view class="menu-left">
            <view class="menu-icon-wrapper cache">
              <u-icon name="trash" size="24" color="#F44336" />
            </view>
            <text class="menu-text">清理缓存</text>
          </view>
          <view class="menu-right">
            <text class="menu-size">{{ cacheSize }}</text>
            <u-icon name="arrow-right" size="16" color="#ccc" />
          </view>
        </view>
      </view>
    </view>

    <!-- 公众号二维码区域 -->
    <view class="qrcode-section">
      <view class="qrcode-card">
        <view class="qrcode-header">
          <text class="qrcode-title">关注公众号</text>
          <text class="qrcode-subtitle">获取更多功能与支持</text>
        </view>
        <view class="qrcode-content">
          <u-image 
            src="/static/qrcode.jpg" 
            width="200rpx" 
            height="200rpx" 
            radius="16rpx"
            mode="aspectFit"
            @click="previewQrcode"
          />
        </view>
      </view>
    </view>

    <!-- 原生分享按钮 - 使用open-type="share"直接触发分享 -->
    <button v-show="false" open-type="share" class="native-share-button" @getuserinfo="onShareSuccess">
      <u-icon name="share" size="20" color="white" />
    </button>

    <!-- 关于弹窗 -->
    <u-popup :show="showAboutPopup" mode="center" round="20" @close="showAboutPopup = false">
      <view class="about-popup">
        <view class="popup-header">
          <text class="popup-title">关于应用</text>
          <u-icon name="close" size="20" @click="showAboutPopup = false" />
        </view>
        <view class="popup-content">
          <view class="app-info">
            <u-image src="/static/logo.png" width="120rpx" height="120rpx" radius="20rpx" />
            <text class="app-name">小七快照拍</text>
            <text class="app-version">版本 1.0.0</text>
          </view>
          
          <view class="app-description">
            <text class="description-text">
              小七快照拍是一款专业的证件照制作应用，采用先进的AI智能抠图技术，
              支持多种尺寸规格和背景色，帮助您快速制作符合各种要求的证件照。
            </text>
          </view>
          
          <view class="app-features">
            <text class="features-title">主要功能</text>
            <view class="features-grid">
              <view class="feature-item">
                <u-icon name="checkmark-circle" size="16" color="#4CAF50" />
                <text class="feature-text">AI智能抠图</text>
              </view>
              <view class="feature-item">
                <u-icon name="checkmark-circle" size="16" color="#4CAF50" />
                <text class="feature-text">多种背景色</text>
              </view>
              <view class="feature-item">
                <u-icon name="checkmark-circle" size="16" color="#4CAF50" />
                <text class="feature-text">高清输出</text>
              </view>
              <view class="feature-item">
                <u-icon name="checkmark-circle" size="16" color="#4CAF50" />
                <text class="feature-text">电子照管理</text>
              </view>
            </view>
          </view>
          
          <view class="copyright">
            <text class="copyright-text">© 2025 小七快照拍 版权所有</text>
          </view>
        </view>
      </view>
    </u-popup>

    <!-- 意见反馈弹窗 -->
    <u-popup :show="showFeedbackPopup" mode="center" round="20" @close="showFeedbackPopup = false">
      <view class="feedback-popup">
        <view class="popup-header">
          <text class="popup-title">意见反馈</text>
          <u-icon name="close" size="20" @click="showFeedbackPopup = false" />
        </view>
        <view class="popup-content">
          <view class="feedback-form">
            <text class="form-label">反馈类型</text>
            <u-tabs :list="feedbackTypes" v-model="feedbackType" line-width="60rpx" />
            
            <text class="form-label">反馈内容</text>
            <u-textarea 
              v-model="feedbackText" 
              placeholder="请详细描述您遇到的问题或建议..."
              :maxlength="500"
              count
              height="200rpx"
            />
            
            <text class="form-label">联系方式（选填）</text>
            <u-input 
              v-model="contactInfo" 
              placeholder="手机号或邮箱，方便我们联系您"
            />
          </view>
          
          <!-- 公众号二维码区域 -->
          <view class="feedback-qrcode-section">
            <view class="qrcode-info">
              <text class="qrcode-title">关注公众号反馈</text>
              <text class="qrcode-desc">请关注公众号【七七超i玩】，发送反馈截图和内容，我们会及时处理您的建议。</text>
            </view>
            <view class="qrcode-image">
              <u-image 
                src="/static/qrcode.jpg" 
                width="200rpx" 
                height="200rpx" 
                radius="16rpx"
                mode="aspectFit"
                @click="previewQrcode"
              />
            </view>
          </view>
          
          <view class="feedback-actions">
            <u-button 
              type="info" 
              :plain="true" 
              @click="showFeedbackPopup = false"
              :custom-style="{ width: '200rpx', borderRadius: '20rpx' }"
            >
              取消
            </u-button>
            <u-button 
              color="#F77261" 
              @click="submitFeedback"
              :custom-style="{ width: '200rpx', borderRadius: '20rpx' }"
            >
              我知道了
            </u-button>
          </view>
        </view>
      </view>
    </u-popup>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import StorageManager from '@/utils/storage';
import { ElectronicPhotoManager } from '@/utils/electronic-photo';

// 声明微信小程序类型
declare const wx: any;

@Component({})
export default class Mine extends Vue {
  userId: string = '';
  statistics: any = {
    totalPhotos: 0,
    usageDays: 0
  };
  electronicCount: number = 0;
  cacheSize: string = '0MB';
  userAvatar: string = '/static/logo.png';
  
  showAboutPopup: boolean = false;
  showFeedbackPopup: boolean = false;
  
  feedbackText: string = '';
  feedbackType: number = 0;
  contactInfo: string = '';
  feedbackTypes = [
    { name: '功能建议' },
    { name: '问题反馈' },
    { name: '其他' }
  ];

  onLoad() {
    this.initUserInfo();
  }

  onShow() {
    this.loadUserData();
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
   * 初始化用户信息
   */
  initUserInfo() {
    this.userId = StorageManager.getUserId();
    this.loadUserData();
  }

  /**
   * 加载用户数据
   */
  loadUserData() {
    this.statistics = StorageManager.getUserStatistics();
    this.electronicCount = ElectronicPhotoManager.getAll().length;
    this.calculateCacheSize();
  }

  /**
   * 跳转到电子照
   */
  navigateToElectronic() {
    uni.switchTab({
      url: '/pages/electronic/index'
    });
  }

  /**
   * 格式化用户ID
   */
  formatUserId(userId: string): string {
    if (userId.length <= 8) return userId;
    return userId.substring(0, 4) + '***' + userId.substring(userId.length - 4);
  }

  /**
   * 计算缓存大小
   */
  calculateCacheSize() {
    const size = this.electronicCount * 0.5; // 假设每张电子照0.5MB
    if (size < 1) {
      this.cacheSize = Math.round(size * 1024) + 'KB';
    } else {
      this.cacheSize = size.toFixed(1) + 'MB';
    }
  }

  /**
   * 清理缓存
   */
  clearCache() {
    uni.showModal({
      title: '确认清理',
      content: '确定要清理所有缓存数据吗？这将清空电子照记录。',
      success: (res) => {
        if (res.confirm) {
          ElectronicPhotoManager.clear();
          this.loadUserData();
          uni.showToast({
            title: '清理成功',
            icon: 'success'
          });
        }
      }
    });
  }

  /**
   * 跳转到用户协议
   */
  navigateToUserAgreement() {
    uni.navigateTo({
      url: '/pages/user-agreement/index'
    });
  }

  /**
   * 跳转到隐私政策
   */
  navigateToPrivacyPolicy() {
    uni.navigateTo({
      url: '/pages/privacy-policy/index'
    });
  }

  /**
   * 跳转到使用帮助
   */
  navigateToHelp() {
    uni.navigateTo({
      url: '/pages/help/index'
    });
  }

  /**
   * 显示关于
   */
  showAbout() {
    this.showAboutPopup = true;
  }

  /**
   * 显示意见反馈
   */
  showFeedback() {
    this.showFeedbackPopup = true;
  }

  /**
   * 预览二维码
   */
  previewQrcode() {
    uni.previewImage({
      urls: ['/static/qrcode.jpg'],
      current: '/static/qrcode.jpg'
    });
  }

  /**
   * 提交意见反馈
   */
  submitFeedback() {
    if (!this.feedbackText.trim()) {
      uni.showToast({
        title: '请输入反馈内容',
        icon: 'none'
      });
      return;
    }

    this.resetForm();
    this.showFeedbackPopup = false;
    uni.showToast({
      title: '感谢您的反馈，我们会通过公众号及时处理',
      icon: 'success',
      duration: 3000
    });
  }

  /**
   * 重置表单
   */
  resetForm() {
    this.feedbackText = '';
    this.contactInfo = '';
    this.feedbackType = 0;
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
.mine-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
}

// 用户信息头部
.user-header {
  position: relative;
  padding: 0 40rpx 80rpx;
  
  .header-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 400rpx;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 0 0 50rpx 50rpx;
    z-index: 1;
  }
  
  .user-info {
    position: relative;
    z-index: 2;
    padding-top: calc(60rpx + env(safe-area-inset-top));
    
    .avatar-section {
      display: flex;
      align-items: center;
      margin-bottom: 40rpx;
      
      .avatar-wrapper {
        position: relative;
        margin-right: 30rpx;
        
        .user-avatar {
          border: 4rpx solid rgba(255, 255, 255, 0.9);
        }
        
        .avatar-border {
          position: absolute;
          top: -8rpx;
          left: -8rpx;
          right: -8rpx;
          bottom: -8rpx;
          border: 2rpx solid rgba(255, 255, 255, 0.3);
          border-radius: 78rpx;
          animation: rotate 20s linear infinite;
        }
      }
      
      .user-details {
        flex: 1;
        
        .welcome-text {
          display: block;
          font-size: 24rpx;
          color: rgba(255, 255, 255, 0.8);
          margin-bottom: 8rpx;
        }
        
        .app-name {
          display: block;
          font-size: 36rpx;
          font-weight: bold;
          color: white;
          margin-bottom: 12rpx;
        }
        
        .user-id {
          .id-text {
            font-size: 24rpx;
            color: rgba(255, 255, 255, 0.9);
            background: rgba(255, 255, 255, 0.2);
            padding: 6rpx 16rpx;
            border-radius: 16rpx;
            backdrop-filter: blur(10rpx);
          }
        }
      }
    }
    
    .stats-cards {
      display: flex;
      gap: 20rpx;
      
      .stat-card {
        flex: 1;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20rpx);
        border-radius: 20rpx;
        padding: 24rpx 20rpx;
        display: flex;
        flex-direction: column;
        align-items: center;
        transition: all 0.3s ease;
        
        &:active {
          transform: translateY(4rpx);
          background: rgba(255, 255, 255, 0.25);
        }
        
        .stat-icon {
          width: 56rpx;
          height: 56rpx;
          background: rgba(255, 255, 255, 0.9);
          border-radius: 28rpx;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 12rpx;
          box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
        }
        
        .stat-info {
          text-align: center;
          
          .stat-number {
            display: block;
            font-size: 32rpx;
            font-weight: bold;
            color: white;
            margin-bottom: 4rpx;
          }
          
          .stat-label {
            font-size: 22rpx;
            color: rgba(255, 255, 255, 0.8);
          }
        }
      }
    }
  }
}

// 功能菜单
.menu-section {
  padding: 0 40rpx;
  margin-bottom: 40rpx;
}

.menu-group {
  background: white;
  border-radius: 24rpx;
  margin-bottom: 30rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.08);
}

.group-header {
  padding: 30rpx 30rpx 10rpx;
  border-bottom: 1rpx solid #f0f0f0;
  
  .group-title {
    font-size: 24rpx;
    color: #666;
    font-weight: 600;
    letter-spacing: 0.5rpx;
  }
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30rpx;
  border-bottom: 1rpx solid #f0f0f0;
  transition: all 0.3s ease;
  
  &:last-child {
    border-bottom: none;
  }
  
  &.highlight {
    background: linear-gradient(135deg, rgba(247, 114, 97, 0.1) 0%, rgba(247, 114, 97, 0.05) 100%);
    
    .menu-text {
      color: #F77261;
      font-weight: 600;
    }
  }
  
  &:active {
    background-color: #f8f9fa;
    transform: scale(0.98);
  }
  
  .menu-left {
    display: flex;
    align-items: center;
    
    .menu-icon-wrapper {
      width: 48rpx;
      height: 48rpx;
      border-radius: 24rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 20rpx;
      
      &.electronic {
        background: rgba(247, 114, 97, 0.1);
      }
      
      &.agreement {
        background: rgba(255, 152, 0, 0.1);
      }
      
      &.privacy {
        background: rgba(156, 39, 176, 0.1);
      }
      
      &.help {
        background: rgba(33, 150, 243, 0.1);
      }
      
      &.feedback {
        background: rgba(76, 175, 80, 0.1);
      }
      
      &.about {
        background: rgba(96, 125, 139, 0.1);
      }
      
      &.cache {
        background: rgba(244, 67, 54, 0.1);
      }
    }
    
    .menu-text {
      font-size: 28rpx;
      color: #333;
    }
  }
  
  .menu-right {
    display: flex;
    align-items: center;
    
    .menu-count, .menu-size, .version-text {
      font-size: 24rpx;
      color: #999;
      margin-right: 10rpx;
    }
  }
}

// 公众号二维码区域
.qrcode-section {
  padding: 0 40rpx 40rpx;
  
  .qrcode-card {
    background: white;
    border-radius: 24rpx;
    padding: 40rpx;
    box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.08);
    
    .qrcode-header {
      text-align: center;
      margin-bottom: 30rpx;
      
      .qrcode-title {
        display: block;
        font-size: 32rpx;
        font-weight: bold;
        color: #333;
        margin-bottom: 8rpx;
      }
      
      .qrcode-subtitle {
        font-size: 24rpx;
        color: #666;
      }
    }
    
    .qrcode-content {
      display: flex;
      justify-content: center;
      
      .qrcode-placeholder {
        width: 200rpx;
        height: 200rpx;
        background: #f8f9fa;
        border: 2rpx dashed #ddd;
        border-radius: 16rpx;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        
        .qrcode-placeholder-text {
          font-size: 24rpx;
          color: #999;
          margin-top: 16rpx;
        }
      }
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

// 弹窗样式
.agreement-popup, .privacy-popup, .help-popup, .about-popup, .feedback-popup {
  width: 680rpx;
  max-height: 80vh;
  background: white;
  border-radius: 24rpx;
  overflow: hidden;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30rpx;
  border-bottom: 1rpx solid #f0f0f0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  
  .popup-title {
    font-size: 32rpx;
    font-weight: bold;
    color: white;
  }
}

.popup-content {
  padding: 30rpx;
  max-height: 60vh;
}

.content-section {
  .section-title {
    display: block;
    font-size: 28rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 16rpx;
    margin-top: 24rpx;
    
    &:first-child {
      margin-top: 0;
    }
  }
  
  .content-text {
    display: block;
    font-size: 26rpx;
    color: #666;
    line-height: 1.8;
    margin-bottom: 12rpx;
  }
}

.help-section {
  margin-bottom: 30rpx;
  
  .help-title {
    display: block;
    font-size: 28rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 16rpx;
  }
  
  .help-text {
    display: block;
    font-size: 26rpx;
    color: #666;
    line-height: 1.6;
    margin-bottom: 8rpx;
  }
}

.about-popup {
  .app-info {
    text-align: center;
    margin-bottom: 30rpx;
    
    .app-name {
      display: block;
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
      margin: 20rpx 0 8rpx;
    }
    
    .app-version {
      font-size: 24rpx;
      color: #999;
    }
  }
  
  .app-description {
    margin-bottom: 30rpx;
    
    .description-text {
      font-size: 26rpx;
      color: #666;
      line-height: 1.8;
    }
  }
  
  .app-features {
    margin-bottom: 30rpx;
    
    .features-title {
      display: block;
      font-size: 26rpx;
      font-weight: bold;
      color: #333;
      margin-bottom: 16rpx;
    }
    
    .features-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12rpx;
      
      .feature-item {
        display: flex;
        align-items: center;
        
        .feature-text {
          font-size: 24rpx;
          color: #666;
          margin-left: 8rpx;
        }
      }
    }
  }
  
  .copyright {
    text-align: center;
    padding-top: 20rpx;
    border-top: 1rpx solid #f0f0f0;
    
    .copyright-text {
      font-size: 22rpx;
      color: #999;
    }
  }
}

.feedback-popup {
  .feedback-form {
    margin-bottom: 30rpx;
    
    .form-label {
      display: block;
      font-size: 26rpx;
      color: #333;
      font-weight: 600;
      margin-bottom: 16rpx;
      margin-top: 24rpx;
      
      &:first-child {
        margin-top: 0;
      }
    }
  }
  
  .feedback-qrcode-section {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 30rpx;
    padding: 20rpx;
    background: #f8f9fa;
    border-radius: 16rpx;
    
    .qrcode-info {
      flex: 1;
      margin-right: 20rpx;
      
      .qrcode-title {
        display: block;
        font-size: 28rpx;
        font-weight: bold;
        color: #333;
        margin-bottom: 8rpx;
      }
      
      .qrcode-desc {
        display: block;
        font-size: 24rpx;
        color: #666;
        line-height: 1.5;
      }
    }
    
    .qrcode-image {
      flex-shrink: 0;
    }
  }
  
  .feedback-actions {
    display: flex;
    gap: 20rpx;
    justify-content: center;
  }
}

// 动画效果
@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
