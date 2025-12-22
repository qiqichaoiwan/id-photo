<template>
  <view v-if="show" class="loading-overlay" :class="{ 'fade-in': show }">
    <view class="loading-content">
      <!-- 主加载动画 -->
      <view class="loader-container">
        <view class="pulse-ring"></view>
        <view class="pulse-ring delay-1"></view>
        <view class="pulse-ring delay-2"></view>
        <view class="loader-icon">
          <text class="icon-camera">📷</text>
        </view>
      </view>
      
      <!-- 加载文字 -->
      <view class="loading-text-wrapper">
        <text class="loading-text">{{ text }}</text>
        <view class="dots">
          <text class="dot dot-1">.</text>
          <text class="dot dot-2">.</text>
          <text class="dot dot-3">.</text>
        </view>
      </view>
      
      <!-- 进度条（可选） -->
      <view v-if="showProgress" class="progress-wrapper">
        <view class="progress-bar">
          <view class="progress-fill" :style="'width:' + progress + '%'"></view>
        </view>
        <text class="progress-text">{{ progress }}%</text>
      </view>
      
      <!-- 提示文字 -->
      <text v-if="tip" class="tip-text">{{ tip }}</text>
    </view>
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component, Prop } from "vue-property-decorator";

@Component({})
export default class LoadingOverlay extends Vue {
  @Prop({ default: false }) show!: boolean;
  @Prop({ default: '处理中' }) text!: string;
  @Prop({ default: '' }) tip!: string;
  @Prop({ default: false }) showProgress!: boolean;
  @Prop({ default: 0 }) progress!: number;
}
</script>

<style lang="scss" scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.fade-in {
  opacity: 1;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx;
}

.loader-container {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40rpx;
}

.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 4rpx solid #F77261;
  opacity: 0;
  animation: pulse 2s ease-out infinite;
}

.delay-1 {
  animation-delay: 0.4s;
}

.delay-2 {
  animation-delay: 0.8s;
}

@keyframes pulse {
  0% {
    transform: scale(0.5);
    opacity: 0.8;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

.loader-icon {
  width: 80rpx;
  height: 80rpx;
  background: linear-gradient(135deg, #F77261 0%, #ff9a8b 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: bounce 1s ease-in-out infinite;
  box-shadow: 0 8rpx 24rpx rgba(247, 114, 97, 0.4);
}

@keyframes bounce {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.icon-camera {
  font-size: 36rpx;
}

.loading-text-wrapper {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.loading-text {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.dots {
  display: flex;
  margin-left: 4rpx;
}

.dot {
  font-size: 32rpx;
  font-weight: 600;
  color: #F77261;
  animation: dotBounce 1.4s ease-in-out infinite;
}

.dot-1 {
  animation-delay: 0s;
}

.dot-2 {
  animation-delay: 0.2s;
}

.dot-3 {
  animation-delay: 0.4s;
}

@keyframes dotBounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-8rpx);
    opacity: 1;
  }
}

.progress-wrapper {
  width: 400rpx;
  margin-top: 24rpx;
}

.progress-bar {
  width: 100%;
  height: 12rpx;
  background-color: #ffe0dc;
  border-radius: 6rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #F77261 0%, #ff9a8b 100%);
  border-radius: 6rpx;
  transition: width 0.3s ease;
}

.progress-text {
  display: block;
  text-align: center;
  font-size: 24rpx;
  color: #999;
  margin-top: 12rpx;
}

.tip-text {
  font-size: 24rpx;
  color: #999;
  margin-top: 16rpx;
}
</style>
