<template>
  <view class="history-page">
    <!-- 历史记录列表 -->
    <view class="history-content">
      <view v-if="historyList.length === 0" class="empty-state">
        <u-icon name="photo" size="80" color="#ccc" />
        <text class="empty-text">暂无历史记录</text>
        <text class="empty-desc">开始制作您的第一张证件照吧</text>
        <u-button color="#F77261" @click="goToCreate">开始制作</u-button>
      </view>

      <view v-else class="history-list">
        <view 
          class="history-item" 
          v-for="(item, index) in historyList" 
          :key="item.id"
          @click="viewHistory(item)"
        >
          <view class="item-image">
            <u-image 
              :src="item.resultImages.idPhoto" 
              width="120rpx" 
              height="160rpx" 
              radius="8rpx"
              mode="aspectFill"
            />
          </view>
          <view class="item-info">
            <view class="item-header">
              <text class="item-title">{{ item.parameters.size.name || '自定义尺寸' }}</text>
              <text class="item-time">{{ formatTime(item.timestamp) }}</text>
            </view>
            <view class="item-details">
              <text class="item-size">{{ item.parameters.size.pxWidth }}×{{ item.parameters.size.pxHeight }}px</text>
              <view class="item-tags">
                <u-tag 
                  v-if="item.parameters.isHd" 
                  text="高清" 
                  type="primary" 
                  size="mini"
                />
                <u-tag 
                  :text="item.parameters.backgroundColor" 
                  type="warning" 
                  size="mini"
                />
              </view>
            </view>
          </view>
          <view class="item-actions">
            <u-icon name="more-dot-fill" size="20" @click.stop="showActionSheet(item)" />
          </view>
        </view>
      </view>
    </view>

    <!-- 操作菜单 -->
    <u-action-sheet 
      :show="showActions" 
      :actions="actionList" 
      @close="showActions = false"
      @select="onActionSelect"
    />

    <!-- 清空确认弹窗 -->
    <u-modal 
      :show="showClearModal" 
      title="确认清空"
      content="确定要清空所有历史记录吗？此操作不可恢复。"
      @cancel="showClearModal = false"
      @confirm="clearAllHistory"
    />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import StorageManager, { PhotoRecord } from '@/utils/storage';

// 声明微信小程序类型
declare const wx: any;

@Component({})
export default class History extends Vue {
  historyList: PhotoRecord[] = [];
  showActions: boolean = false;
  showClearModal: boolean = false;
  selectedItem: PhotoRecord | null = null;

  actionList = [
    {
      name: '查看详情',
      id: 'view'
    },
    {
      name: '重新编辑',
      id: 'edit'
    },
    {
      name: '删除',
      id: 'delete',
      color: '#f56c6c'
    }
  ];

  onLoad() {
    this.loadHistory();
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
    this.loadHistory();
  }

  /**
   * 加载历史记录
   */
  loadHistory() {
    this.historyList = StorageManager.getPhotoHistory();
  }

  /**
   * 返回上一页
   */
  goBack() {
    uni.navigateBack();
  }

  /**
   * 跳转到创建页面
   */
  goToCreate() {
    uni.switchTab({
      url: '/pages/index/index'
    });
  }

  /**
   * 查看历史记录详情
   */
  viewHistory(item: PhotoRecord) {
    // 跳转到编辑页面，传入历史数据
    uni.navigateTo({
      url: '/pages/photo/edit?history=' + encodeURIComponent(JSON.stringify(item))
    });
  }

  /**
   * 清空所有历史记录
   */
  clearAllHistory() {
    StorageManager.clearPhotoHistory();
    this.historyList = [];
    this.showClearModal = false;
    uni.showToast({
      title: '已清空历史记录',
      icon: 'success'
    });
  }

  /**
   * 显示操作菜单
   */
  showActionSheet(item: PhotoRecord) {
    this.selectedItem = item;
    this.showActions = true;
  }

  /**
   * 处理操作选择
   */
  onActionSelect(action: any) {
    if (!this.selectedItem) return;

    switch (action.id) {
      case 'view':
        this.viewHistory(this.selectedItem);
        break;
      case 'edit':
        this.editHistory(this.selectedItem);
        break;
      case 'delete':
        this.deleteHistory(this.selectedItem);
        break;
    }
    
    this.showActions = false;
    this.selectedItem = null;
  }

  /**
   * 编辑历史记录
   */
  editHistory(item: PhotoRecord) {
    uni.navigateTo({
      url: '/pages/photo/index?edit=' + encodeURIComponent(JSON.stringify(item))
    });
  }

  /**
   * 删除历史记录
   */
  deleteHistory(item: PhotoRecord) {
    uni.showModal({
      title: '确认删除',
      content: '确定要删除这条记录吗？',
      success: (res) => {
        if (res.confirm) {
          StorageManager.deletePhotoRecord(item.id);
          this.loadHistory();
          uni.showToast({
            title: '删除成功',
            icon: 'success'
          });
        }
      }
    });
  }

  /**
   * 格式化时间
   */
  formatTime(timestamp: number): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) { // 1分钟内
      return '刚刚';
    } else if (diff < 3600000) { // 1小时内
      return Math.floor(diff / 60000) + '分钟前';
    } else if (diff < 86400000) { // 1天内
      return Math.floor(diff / 3600000) + '小时前';
    } else if (diff < 604800000) { // 1周内
      return Math.floor(diff / 86400000) + '天前';
    } else {
      return date.toLocaleDateString();
    }
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
.history-page {
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
  
  .clear-btn {
    font-size: 28rpx;
    color: #f56c6c;
  }
}

.history-content {
  padding: 20rpx;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
  
  .empty-text {
    font-size: 32rpx;
    color: #333;
    margin: 40rpx 0 20rpx;
    font-weight: bold;
  }
  
  .empty-desc {
    font-size: 26rpx;
    color: #999;
    margin-bottom: 60rpx;
  }
}

.history-list {
  .history-item {
    display: flex;
    align-items: center;
    padding: 30rpx;
    margin-bottom: 20rpx;
    background: white;
    border-radius: 16rpx;
    box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    
    &:active {
      transform: scale(0.98);
      background: #f8f9fa;
    }
    
    .item-image {
      margin-right: 30rpx;
      border-radius: 8rpx;
      overflow: hidden;
    }
    
    .item-info {
      flex: 1;
      
      .item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12rpx;
        
        .item-title {
          font-size: 28rpx;
          font-weight: bold;
          color: #333;
        }
        
        .item-time {
          font-size: 22rpx;
          color: #999;
        }
      }
      
      .item-details {
        display: flex;
        align-items: center;
        gap: 20rpx;
        
        .item-size {
          font-size: 24rpx;
          color: #666;
        }
        
        .item-tags {
          display: flex;
          gap: 10rpx;
        }
      }
    }
    
    .item-actions {
      padding: 10rpx;
      color: #999;
    }
  }
}
</style>
