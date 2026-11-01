<template>
  <view class="share-button-wrapper">
    <!-- 三个点的分享按钮 -->
    <view class="share-button" @click="showShareMenu">
      <u-icon name="more-dot-fill" size="24" color="#666" />
    </view>

    <!-- 分享菜单弹窗 -->
    <u-popup :show="showSharePopup" mode="bottom" round="20" @close="closeShareMenu">
      <view class="share-menu">
        <view class="share-header">
          <text class="share-title">分享到</text>
          <u-icon name="close" size="20" color="#999" @click="closeShareMenu" />
        </view>
        
        <view class="share-options">
          <!-- 分享到朋友圈 -->
          <view class="share-option" @click="shareToMoments">
            <view class="share-icon moments">
              <u-icon name="moments" size="32" color="#00D084" />
            </view>
            <text class="share-label">朋友圈</text>
          </view>
          
          <!-- 分享给朋友 -->
          <view class="share-option" @click="shareToFriend">
            <view class="share-icon friend">
              <u-icon name="chat" size="32" color="#1AAD19" />
            </view>
            <text class="share-label">微信好友</text>
          </view>
          
          <!-- 复制链接 -->
          <view class="share-option" @click="copyLink">
            <view class="share-icon link">
              <u-icon name="attach" size="32" color="#576B95" />
            </view>
            <text class="share-label">复制链接</text>
          </view>
        </view>
        
        <view class="share-cancel">
          <u-button 
            :plain="true" 
            text="取消" 
            :custom-style="cancelButtonStyle" 
            @click="closeShareMenu" 
          />
        </view>
      </view>
    </u-popup>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component, Prop } from "vue-property-decorator";

// 声明微信小程序类型
declare const wx: any;

@Component({})
export default class ShareButton extends Vue {
  @Prop({ type: String, default: '/pages/index/index' }) sharePath!: string;
  @Prop({ type: String, default: '小七快照拍 - 图片制作与证件照编辑' }) shareTitle!: string;
  @Prop({ type: String, default: '/static/example.jpeg' }) shareImage!: string;
  
  showSharePopup: boolean = false;
  
  cancelButtonStyle = {
    width: '100%',
    height: '96rpx',
    borderRadius: '48rpx',
    fontSize: '32rpx',
    fontWeight: 'bold',
    borderColor: '#E8E8E8',
    color: '#666'
  };

  /**
   * 显示分享菜单
   */
  showShareMenu() {
    this.showSharePopup = true;
  }

  /**
   * 关闭分享菜单
   */
  closeShareMenu() {
    this.showSharePopup = false;
  }

  /**
   * 分享到朋友圈
   */
  shareToMoments() {
    this.closeShareMenu();
    
    // 检查是否支持分享到朋友圈
    if (wx.updateShareMenu) {
      wx.updateShareMenu({
        withShareTicket: true,
        success: () => {
          // 触发分享
          uni.showShareMenu({
            withShareTicket: true,
            menus: ['shareAppMessage', 'shareTimeline'],
            success: () => {
              console.log('分享菜单显示成功');
              uni.showToast({
                title: '请点击右上角分享到朋友圈',
                icon: 'none',
                duration: 2000
              });
            },
            fail: (err: any) => {
              console.error('分享菜单显示失败:', err);
              this.fallbackShare();
            }
          });
        },
        fail: () => {
          this.fallbackShare();
        }
      });
    } else {
      this.fallbackShare();
    }
  }

  /**
   * 分享给朋友
   */
  shareToFriend() {
    this.closeShareMenu();
    
    // 检查是否支持分享功能
    if (uni.share) {
      uni.share({
        provider: 'weixin',
        scene: 'WXSceneSession',
        type: 0,
        href: this.getShareUrl(),
        title: this.shareTitle,
        summary: '图片制作与证件照编辑，支持常用规格与背景处理',
        imageUrl: this.getAbsoluteImageUrl(),
        success: () => {
          uni.showToast({
            title: '分享成功',
            icon: 'success'
          });
        },
        fail: (err: any) => {
          console.error('分享失败:', err);
          this.fallbackShare();
        }
      });
    } else {
      this.fallbackShare();
    }
  }

  /**
   * 复制链接
   */
  copyLink() {
    this.closeShareMenu();
    
    const shareUrl = this.getShareUrl();
    
    uni.setClipboardData({
      data: shareUrl,
      success: () => {
        uni.showToast({
          title: '链接已复制',
          icon: 'success'
        });
      },
      fail: () => {
        uni.showToast({
          title: '复制失败',
          icon: 'none'
        });
      }
    });
  }

  /**
   * 获取分享链接
   */
  getShareUrl(): string {
    // 构建完整的分享链接
    const baseUrl = 'https://your-domain.com'; // 替换为实际域名
    return `${baseUrl}${this.sharePath}`;
  }

  /**
   * 获取绝对路径图片URL
   */
  getAbsoluteImageUrl(): string {
    // 如果是本地路径，需要转换为可访问的URL
    if (this.shareImage.startsWith('/static/')) {
      const baseUrl = 'https://your-domain.com'; // 替换为实际域名
      return `${baseUrl}${this.shareImage}`;
    }
    return this.shareImage;
  }

  /**
   * 降级分享方案
   */
  fallbackShare() {
    // 使用原生分享功能
    uni.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline'],
      success: () => {
        uni.showToast({
          title: '请点击右上角分享',
          icon: 'none',
          duration: 2000
        });
      },
      fail: () => {
        uni.showToast({
          title: '当前环境不支持分享',
          icon: 'none'
        });
      }
    });
  }
}
</script>

<style lang="scss" scoped>
.share-button-wrapper {
  position: relative;
  display: inline-block;
}

.share-button {
  width: 60rpx;
  height: 60rpx;
  border-radius: 30rpx;
  background: rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  
  &:active {
    transform: scale(0.9);
    background: rgba(0, 0, 0, 0.1);
  }
}

.share-menu {
  background: white;
  border-radius: 20rpx 20rpx 0 0;
  padding: 40rpx;
  
  .share-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 40rpx;
    
    .share-title {
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
    }
  }
  
  .share-options {
    display: flex;
    justify-content: space-around;
    margin-bottom: 40rpx;
    
    .share-option {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20rpx;
      border-radius: 16rpx;
      transition: all 0.3s ease;
      
      &:active {
        background: #f8f9fa;
        transform: scale(0.95);
      }
      
      .share-icon {
        width: 96rpx;
        height: 96rpx;
        border-radius: 48rpx;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16rpx;
        
        &.moments {
          background: rgba(0, 208, 132, 0.1);
        }
        
        &.friend {
          background: rgba(26, 173, 25, 0.1);
        }
        
        &.link {
          background: rgba(87, 107, 149, 0.1);
        }
      }
      
      .share-label {
        font-size: 24rpx;
        color: #333;
      }
    }
  }
  
  .share-cancel {
    ::v-deep .u-button {
      margin-top: 20rpx;
    }
  }
}
</style>
