<template>
  <view class="electronic-page">
    <!-- 顶部导航栏 -->
    <view class="header-bar">
      <view class="header-title">
        <u-icon name="folder" size="24" color="#F77261" />
        <text class="title-text">我的电子照</text>
      </view>
      <view class="header-actions">
        <view class="stats-info">
          <text class="stats-text">{{ photos.length }}/{{ MAX_COUNT }}</text>
        </view>
      </view>
    </view>

    <!-- 主要内容区域 -->
    <scroll-view class="content-scroll" scroll-y="true">
      <!-- 统计信息卡片 -->
      <view class="stats-card" v-if="photos.length > 0">
        <view class="stats-grid">
          <view class="stats-item">
            <view class="stats-value">{{ stats.total }}</view>
            <view class="stats-label">总数量</view>
          </view>
          <view class="stats-divider"></view>
          <view class="stats-item">
            <view class="stats-value">{{ stats.size }}</view>
            <view class="stats-label">占用空间</view>
          </view>
          <view class="stats-divider"></view>
          <view class="stats-item">
            <view class="stats-value">{{ stats.oldestDate || '-' }}</view>
            <view class="stats-label">最早日期</view>
          </view>
        </view>
      </view>

      <!-- 空状态 -->
      <view class="empty-state" v-if="photos.length === 0">
        <view class="empty-icon">
          <u-icon name="folder" size="80" color="#D8D8D8" />
        </view>
        <view class="empty-title">暂无电子照</view>
        <view class="empty-desc">制作证件照后可以保存到电子照</view>
        <view class="empty-actions">
          <u-button 
            color="#F77261" 
            text="立即制作" 
            :custom-style="primaryButtonStyle" 
            @click="navigateToPhoto" 
          />
        </view>
      </view>

      <!-- 电子照列表 -->
      <view class="photo-list" v-else>
        <view 
          class="photo-item" 
          v-for="photo in photos" 
          :key="photo.id"
          @click="selectPhoto(photo)">
          <view class="photo-preview">
            <image 
              :src="photo.hdBase64" 
              mode="aspectFit" 
              class="photo-image"
            />
          </view>
          
          <view class="photo-info">
            <view class="photo-header">
              <text class="photo-name">{{ photo.name }}</text>
              <view class="photo-actions">
                <view class="action-btn" @click.stop="downloadPhoto(photo)">
                  <u-icon name="download" size="16" color="#F77261" />
                </view>
                <view class="action-btn delete" @click.stop="deletePhoto(photo.id)">
                  <u-icon name="trash" size="16" color="#FF4D4F" />
                </view>
              </view>
            </view>
            
            <view class="photo-details">
              <view class="detail-item">
                <text class="detail-label">创建:</text>
                <text class="detail-value">{{ formatDateString(photo.createdAt) }}</text>
              </view>
              <view class="detail-item">
                <text class="detail-label">颜色:</text>
                <view class="color-preview" :style="{ backgroundColor: photo.color }"></view>
                <text class="detail-value">{{ getColorName(photo.color) }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 底部占位区域 -->
      <view class="bottom-spacer"></view>
    </scroll-view>

    <!-- 底部操作栏 -->
    <view class="bottom-action-bar" v-if="photos.length > 0">
      <view class="action-container">
        <u-button 
          :plain="true" 
          text="清空全部" 
          :custom-style="secondaryButtonStyle" 
          @click="clearAll" 
        />
        <u-button 
          color="#F77261" 
          text="继续制作" 
          :custom-style="primaryButtonStyle" 
          @click="navigateToPhoto" 
        />
      </view>
    </view>

    <!-- 原生分享按钮 - 使用open-type="share"直接触发分享 -->
    <button v-show="false" open-type="share" class="native-share-button" @getuserinfo="onShareSuccess">
      <u-icon name="share" size="20" color="white" />
    </button>

    <!-- 加载页面 -->
    <LoadingOverlay :show="loading" text="处理中" />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import { ElectronicPhotoManager, ElectronicPhoto } from '@/utils/electronic-photo';
import { adConfig } from '@/config';
import LoadingOverlay from '@/components/LoadingOverlay.vue';

// 声明微信小程序类型
declare const wx: any;

@Component({ components: { LoadingOverlay } })
export default class ElectronicPage extends Vue {
  // 确保管理器在组件中可用
  electronicPhotoManager = ElectronicPhotoManager;
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
    borderColor: '#FF4D4F',
    color: '#FF4D4F'
  };

  photos: ElectronicPhoto[] = [];
  loading: boolean = false;
  MAX_COUNT = 2;
  //激励视频广告实例
  videoAd: any = null;

  mounted() {
    this.loadPhotos();
    
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

  onShow() {
    // 初始化激励视频广告
    this.initRewardedVideoAd()
    // 页面显示时重新加载数据
    this.loadPhotos();
  }

  /**
   * 初始化激励视频广告
   */
  initRewardedVideoAd() {
    // 在页面onLoad回调事件中创建激励视频广告实例
    if (wx.createRewardedVideoAd) {
      try {
        this.videoAd = wx.createRewardedVideoAd({
          adUnitId: adConfig.rewardedVideoAdUnitId
        })
        
        this.videoAd.onLoad(() => {
          console.log('激励视频广告加载成功')
        })
        
        this.videoAd.onError((err: any) => {
          console.error('激励视频广告加载失败', err)
        })
        
        this.videoAd.onClose((res: any) => {
          console.log('激励视频广告关闭', res)
        })
      } catch (error) {
        console.error('创建激励视频广告失败:', error)
      }
    } else {
      console.warn('当前环境不支持激励视频广告')
    }
  }

  /**
   * 显示激励视频广告并验证
   */
  async showRewardedVideoAd(): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.videoAd) {
        console.warn('激励视频广告实例不存在')
        resolve(false)
        return
      }

      try {
        this.videoAd.show().catch((err: any) => {
          console.error('激励视频广告显示失败:', err)
          // 失败重试
          if (this.videoAd) {
            this.videoAd.load()
              .then(() => {
                if (this.videoAd) {
                  this.videoAd.show()
                }
              })
              .catch((retryErr: any) => {
                console.error('激励视频广告重试失败:', retryErr)
                resolve(false)
              })
          } else {
            resolve(false)
          }
        })
        
        // 监听广告关闭事件
        const handleClose = (res: any) => {
          try {
            if (this.videoAd) {
              this.videoAd.offClose(handleClose)
            }
          } catch (e) {
            console.warn('移除广告关闭监听器失败:', e)
          }
          
          if (res && typeof res === 'object' && res.isEnded) {
            // 用户看完广告
            resolve(true)
          } else {
            // 用户没看完广告
            resolve(false)
          }
        }
        
        if (this.videoAd) {
          this.videoAd.onClose(handleClose)
        }
      } catch (error) {
        console.error('显示广告过程中发生错误:', error)
        resolve(false)
      }
    })
  }

  /**
   * 加载电子照列表
   */
  loadPhotos() {
    const photos = ElectronicPhotoManager.getAll();
    console.log('加载电子照列表:', photos);
    this.photos = photos;
  }

  /**
   * 获取统计信息
   */
  get stats() {
    return ElectronicPhotoManager.getStats();
  }

  /**
   * 选择照片
   */
  selectPhoto(photo: ElectronicPhoto) {
    // 可以添加预览功能
    console.log('选择照片:', photo);
  }

  /**
   * 下载照片
   */
  async downloadPhoto(photo: ElectronicPhoto) {
    // 显示激励视频广告
    const adVerified = await this.showRewardedVideoAd()
    if (!adVerified) {
      uni.showToast({
        title: '请看完广告后再继续操作',
        icon: 'none',
        duration: 2000
      })
      return
    }

    try {
      this.loading = true;
      
      // 选择高清还是标清
      const base64 = photo.hdBase64;
      const base64Data = base64.replace('data:image/png;base64,', '');
      
      // 使用用户数据目录保存临时文件
      const tempPath = `${wx.env.USER_DATA_PATH}/electronic_photo_${Date.now()}.png`;
      const fs = uni.getFileSystemManager();
      
      console.log('准备写入临时文件:', tempPath);
      
      fs.writeFile({
        filePath: tempPath,
        data: base64Data,
        encoding: 'base64',
        success: () => {
          console.log('临时文件写入成功，准备保存到相册:', tempPath);
          // 保存到相册
          uni.saveImageToPhotosAlbum({
            filePath: tempPath,
            success: () => {
              console.log('保存到相册成功');
              uni.showToast({
                title: '保存成功',
                icon: 'success'
              });
            },
            fail: (err) => {
              console.error('保存到相册失败:', err);
              uni.showToast({
                title: '保存失败',
                icon: 'none'
              });
            }
          });
        },
        fail: (err) => {
          console.error('写入临时文件失败:', err);
          uni.showToast({
            title: '保存失败',
            icon: 'none'
          });
        },
        complete: () => {
          this.loading = false;
        }
      });
    } catch (error) {
      console.error('下载照片失败:', error);
      this.loading = false;
      uni.showToast({
        title: '保存失败',
        icon: 'none'
      });
    }
  }

  /**
   * 删除照片
   */
  deletePhoto(id: string) {
    uni.showModal({
      title: '确认删除',
      content: '确定要删除这张电子照吗？删除后无法恢复。',
      success: (res) => {
        if (res.confirm) {
          if (ElectronicPhotoManager.delete(id)) {
            this.loadPhotos();
            uni.showToast({
              title: '删除成功',
              icon: 'success'
            });
          } else {
            uni.showToast({
              title: '删除失败',
              icon: 'none'
            });
          }
        }
      }
    });
  }

  /**
   * 清空全部
   */
  clearAll() {
    uni.showModal({
      title: '确认清空',
      content: '确定要清空所有电子照吗？清空后无法恢复。',
      success: (res) => {
        if (res.confirm) {
          if (ElectronicPhotoManager.clear()) {
            this.loadPhotos();
            uni.showToast({
              title: '清空成功',
              icon: 'success'
            });
          } else {
            uni.showToast({
              title: '清空失败',
              icon: 'none'
            });
          }
        }
      }
    });
  }

  /**
   * 获取颜色名称
   */
  getColorName(color: string): string {
    const colorNames: { [key: string]: string } = {
      '#FFFFFF': '白色',
      '#4A90E2': '蓝色',
      '#F5F5F5': '浅灰',
      '#E5E5E5': '灰色',
      '#D4E5F7': '淡蓝',
      '#FF6B6B': '红色',
      '#4ECDC4': '青色',
      '#45B7D1': '天蓝',
      '#96CEB4': '薄荷绿',
      '#FFEAA7': '浅黄',
      '#DDA0DD': '梅花红',
      '#F8B500': '橙色'
    };
    return colorNames[color] || color;
  }

  /**
   * 格式化日期为 YYYY-MM-dd
   */
  formatDateString(timestamp: number): string {
    return ElectronicPhotoManager.formatDateString(timestamp);
  }

  /**
   * 导航到首页选择尺寸
   */
  navigateToPhoto() {
    uni.switchTab({
      url: '/pages/index/index'
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
// 大师级设计变量
$primary-color: #F77261;
$primary-light: #FF9A8B;
$primary-dark: #E55A4A;
$success-color: #52C41A;
$warning-color: #FFA940;
$danger-color: #FF4D4F;
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
.electronic-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #FFFFFF 0%, #F8F9FA 100%);
  display: flex;
  flex-direction: column;
}

// 顶部导航栏
.header-bar {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20rpx);
  border-bottom: 2rpx solid $border-light;
  padding: 32rpx 40rpx;
  padding-top: calc(32rpx + env(safe-area-inset-top));
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
  
  .header-title {
    display: flex;
    align-items: center;
    gap: 16rpx;
    
    .title-text {
      font-size: 36rpx;
      font-weight: 700;
      color: $text-primary;
      letter-spacing: -0.3rpx;
    }
  }
  
  .header-actions {
    .stats-info {
      .stats-text {
        font-size: 24rpx;
        color: $primary-color;
        font-weight: 600;
        padding: 8rpx 16rpx;
        background: rgba(247, 114, 97, 0.1);
        border-radius: 16rpx;
      }
    }
  }
}

// 内容滚动区域
.content-scroll {
  flex: 1;
  padding: 32rpx 40rpx 200rpx;
  box-sizing: border-box;
}

// 统计信息卡片
.stats-card {
  background: $bg-white;
  border-radius: 24rpx;
  padding: 40rpx;
  margin-bottom: 32rpx;
  box-shadow: $shadow-light;
  border: 2rpx solid $border-light;
  
  .stats-grid {
    display: flex;
    align-items: center;
    justify-content: space-between;
    
    .stats-item {
      flex: 1;
      text-align: center;
      
      .stats-value {
        font-size: 32rpx;
        font-weight: 700;
        color: $primary-color;
        margin-bottom: 8rpx;
      }
      
      .stats-label {
        font-size: 24rpx;
        color: $text-tertiary;
      }
    }
    
    .stats-divider {
      width: 2rpx;
      height: 48rpx;
      background: $border-light;
    }
  }
}

// 空状态
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
  
  .empty-icon {
    margin-bottom: 32rpx;
  }
  
  .empty-title {
    font-size: 36rpx;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 16rpx;
  }
  
  .empty-desc {
    font-size: 28rpx;
    color: $text-secondary;
    margin-bottom: 48rpx;
    text-align: center;
    line-height: 1.5;
  }
  
  .empty-actions {
    ::v-deep .u-button {
      width: 280rpx;
      height: 88rpx;
      border-radius: 44rpx;
      font-size: 32rpx;
      font-weight: 700;
    }
  }
}

// 照片列表
.photo-list {
  .photo-item {
    background: $bg-white;
    border-radius: 24rpx;
    padding: 32rpx;
    margin-bottom: 24rpx;
    box-shadow: $shadow-light;
    border: 2rpx solid $border-light;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    &:active {
      transform: translateY(4rpx);
      box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08);
    }
    
    .photo-preview {
      position: relative;
      width: 100%;
      height: 400rpx;
      background: $bg-light;
      border-radius: 16rpx;
      overflow: hidden;
      margin-bottom: 24rpx;
      
      .photo-image {
        width: 100%;
        height: 100%;
        border-radius: 16rpx;
      }
      
      .photo-overlay {
        position: absolute;
        top: 16rpx;
        right: 16rpx;
        background: rgba(255, 77, 79, 0.9);
        backdrop-filter: blur(10rpx);
        border-radius: 12rpx;
        padding: 6rpx 12rpx;
        
        .expire-badge {
          font-size: 20rpx;
          color: $bg-white;
          font-weight: 600;
        }
      }
    }
    
    .photo-info {
      .photo-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20rpx;
        
        .photo-name {
          font-size: 32rpx;
          font-weight: 600;
          color: $text-primary;
          flex: 1;
        }
        
        .photo-actions {
          display: flex;
          gap: 16rpx;
          
          .action-btn {
            width: 56rpx;
            height: 56rpx;
            background: $bg-light;
            border-radius: 28rpx;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            
            &:active {
              transform: scale(0.9);
              background: $border-light;
            }
            
            &.delete {
              background: rgba(255, 77, 79, 0.1);
              
              &:active {
                background: rgba(255, 77, 79, 0.2);
              }
            }
          }
        }
      }
      
      .photo-details {
        .detail-item {
          display: flex;
          align-items: center;
          margin-bottom: 12rpx;
          
          .detail-label {
            font-size: 24rpx;
            color: $text-tertiary;
            width: 80rpx;
            flex-shrink: 0;
          }
          
          .detail-value {
            font-size: 24rpx;
            color: $text-secondary;
            margin-left: 16rpx;
            
            &.expire {
              color: $text-tertiary;
              
              &.expiring {
                color: $danger-color;
                font-weight: 600;
              }
            }
          }
          
          .color-preview {
            width: 24rpx;
            height: 24rpx;
            border-radius: 12rpx;
            margin-left: 8rpx;
            border: 2rpx solid $border-light;
          }
        }
      }
    }
  }
}

// 底部占位区域
.bottom-spacer {
  height: 200rpx;
}

// 底部操作栏
.bottom-action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20rpx);
  border-top: 2rpx solid $border-light;
  padding: 32rpx 40rpx;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -8rpx 32rpx rgba(0, 0, 0, 0.08);
  z-index: 100;
  
  .action-container {
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

.stats-card,
.photo-item {
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

.photo-item {
  animation-delay: 0.1s;
}

.stats-card { animation-delay: 0.2s; }
</style>
