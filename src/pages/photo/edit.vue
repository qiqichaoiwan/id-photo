<template>
  <view class="page">
    <!-- 照片预览卡片 -->
    <view class="preview-card">
      <view class="photo-wrapper">
        <view 
          class="photo-container" 
          :style="'background-color:' + IDPhotoForm.color + ';width:' + previewWidth + 'rpx;height:' + previewHeight + 'rpx'"
        >
          <image class="photo" :src="isHd ? photoPath.base64HD : photoPath.base64" mode="aspectFit" />
        </view>
      </view>
      <view class="photo-meta">
        <view class="meta-item">
          <text class="label">规格</text>
          <text class="value">{{ photoSize.name }}</text>
        </view>
        <view class="divider"></view>
        <view class="meta-item">
          <text class="label">尺寸</text>
          <text class="value">{{ photoSize.pxWidth }}×{{ photoSize.pxHeight }}</text>
        </view>
        <view class="divider"></view>
        <view class="meta-item">
          <text class="label">质量</text>
          <text class="value-highlight">{{ isHd ? '高清' : '标清' }}</text>
        </view>
      </view>
    </view>

    <!-- 背景色选择 -->
    <view class="section-card">
      <view class="section-title">背景颜色</view>
      <view class="color-grid">
        <view 
          v-for="(item, index) in colorList" 
          :key="index"
          class="color-option"
          @click="changeBackgroudColor(item.color)"
        >
          <view 
            class="color-circle"
            :class="IDPhotoForm.color === item.color ? 'color-active' : (item.color === '#FFFFFF' ? 'color-white' : '')"
            :style="'background-color:' + item.color"
          >
            <text v-if="IDPhotoForm.color === item.color" class="check-icon">✓</text>
          </view>
          <text class="color-label" :class="IDPhotoForm.color === item.color ? 'label-active' : ''">{{ item.name }}</text>
        </view>
      </view>
    </view>

    <!-- 设置选项 -->
    <view class="section-card">
      <view class="section-title">输出设置</view>
      <view class="settings-list">
        <view class="setting-row">
          <view class="setting-left">
            <view class="icon-box-pink">
              <text class="icon-text">HD</text>
            </view>
            <view class="setting-text">
              <text class="main-text">高清模式</text>
              <text class="sub-text">输出更高分辨率的照片</text>
            </view>
          </view>
          <u-switch v-model="isHd" activeColor="#F77261" size="22" @change="onHdChange" />
        </view>
        <view class="setting-row">
          <view class="setting-left">
            <view class="icon-box-orange">
              <text class="icon-text">📁</text>
            </view>
            <view class="setting-text">
              <text class="main-text">保存到电子照</text>
              <text class="sub-text">方便下次快速使用</text>
            </view>
          </view>
          <u-switch v-model="saveToElectronic" activeColor="#F77261" size="22" @change="onSaveToElectronicChange" />
        </view>
      </view>
    </view>

    <!-- 底部操作 -->
    <view class="bottom-actions">
      <view class="btn-secondary" @click="generateLayoutPhoto">
        <text class="btn-icon">⊞</text>
        <text>排版冲印</text>
      </view>
      <view class="btn-primary" @click="generateIDPhoto">
        <text class="btn-icon">↓</text>
        <text>保存证件照</text>
      </view>
    </view>

    <button v-show="false" open-type="share" />
  </view>
</template>

<script lang="ts">
import Vue from 'vue';
import { Component } from "vue-property-decorator";
import { AddBackgroudColor, GenerateLayoutPhoto } from '@/api/photo'
import { Getter } from 'vuex-class';
import { PhotoSize } from '@/model/PhotoSize';
import { PhotoPath } from '@/model/Interfaces'
import { ElectronicPhotoManager } from '@/utils/electronic-photo'
import StorageManager from '@/utils/storage'
import { adConfig } from '@/config'

const prefix = 'data:image/png;base64,'

const colorConfig = [
  { name: '白色', color: '#FFFFFF' },
  { name: '蓝色', color: '#438edb' },
  { name: '红色', color: '#D9001B' },
  { name: '浅蓝', color: '#7ec8e8' },
  { name: '灰色', color: '#b8b8b8' },
  { name: '深红', color: '#a8000f' },
  { name: '深蓝', color: '#1a3a5c' },
  { name: '粉色', color: '#ffb6c1' },
]

@Component({})
export default class PhotoEdit extends Vue {
  colorList = colorConfig
  IDPhotoForm: any = { color: '#FFFFFF', kb: undefined, render: 0 }
  isHd: boolean = true
  saveToElectronic: boolean = false
  videoAd: any = null

  @Getter('photoConfig') photoSize!: PhotoSize
  @Getter('photoPath') photoPath!: PhotoPath

  // 根据证件照实际比例计算预览尺寸
  get previewWidth(): number {
    const maxWidth = 280
    const maxHeight = 400
    const ratio = this.photoSize.pxWidth / this.photoSize.pxHeight
    if (ratio > maxWidth / maxHeight) {
      return maxWidth
    }
    return Math.round(maxHeight * ratio)
  }

  get previewHeight(): number {
    const maxWidth = 280
    const maxHeight = 400
    const ratio = this.photoSize.pxWidth / this.photoSize.pxHeight
    if (ratio > maxWidth / maxHeight) {
      return Math.round(maxWidth / ratio)
    }
    return maxHeight
  }

  created() { this.initRewardedVideoAd() }

  initRewardedVideoAd() {
    if (wx.createRewardedVideoAd) {
      try {
        this.videoAd = wx.createRewardedVideoAd({ adUnitId: adConfig.rewardedVideoAdUnitId })
        this.videoAd.onLoad(() => console.log('广告加载成功'))
        this.videoAd.onError((err: any) => console.error('广告加载失败', err))
      } catch (e) { console.error('创建广告失败:', e) }
    }
  }

  async showRewardedVideoAd(): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.videoAd) { resolve(false); return }
      try {
        this.videoAd.show().catch(() => {
          this.videoAd?.load().then(() => this.videoAd?.show()).catch(() => resolve(false))
        })
        const handleClose = (res: any) => {
          this.videoAd?.offClose(handleClose)
          resolve(res?.isEnded || false)
        }
        this.videoAd.onClose(handleClose)
      } catch { resolve(false) }
    })
  }

  changeBackgroudColor(color: string) { 
    this.IDPhotoForm.color = color 
  }

  onHdChange(value: boolean) {
    this.isHd = value
  }

  onSaveToElectronicChange(value: boolean) {
    this.saveToElectronic = value
  }

  async generateIDPhoto() {
    const adVerified = await this.showRewardedVideoAd()
    if (!adVerified) { uni.showToast({ title: '请看完广告后再继续', icon: 'none' }); return }

    uni.showLoading({ title: '处理中...' })
    const { photoPath: photo, IDPhotoForm, isHd } = this
    const that = this
    
    // 只传递 add_background 接口需要的参数: color, kb, render, dpi
    const colorForm: any = {
      color: IDPhotoForm.color.replace('#', '')
    }
    // 可选参数
    if (IDPhotoForm.kb !== undefined) colorForm.kb = IDPhotoForm.kb
    if (IDPhotoForm.render !== undefined && IDPhotoForm.render !== 0) colorForm.render = IDPhotoForm.render
    
    // 根据是否高清选择对应的图片路径
    const imagePath = isHd ? photo.base64HDPath : photo.base64Path
    console.log('证件照 - 图片路径:', imagePath)
    console.log('证件照 - photoPath对象:', photo)
    
    // 检查路径是否有效
    if (!imagePath) {
      uni.hideLoading()
      uni.showModal({ title: '处理失败', content: '图片路径无效，请重新拍照', showCancel: false })
      return
    }
    
    try {
      console.log('证件照 - 开始添加背景色，参数:', colorForm)
      let res: any
      try {
        res = await AddBackgroudColor(colorForm, 'input_image', imagePath)
      } catch (apiErr) {
        console.error('证件照 - AddBackgroudColor API错误:', apiErr)
        throw apiErr
      }
      console.log('证件照 - 添加背景色返回:', JSON.stringify(res))
      
      // 检查 API 返回状态
      if (res?.status === false) {
        uni.hideLoading()
        const errMsg = res?.message || '添加背景色失败'
        console.error('证件照 - API返回失败:', errMsg)
        uni.showModal({ title: '处理失败', content: errMsg, showCancel: false })
        return
      }
      
      // 获取 base64 数据
      const colorBase64 = res?.image_base64
      if (!colorBase64) {
        uni.hideLoading()
        console.error('证件照 - 返回数据中没有image_base64:', res)
        uni.showModal({ title: '处理失败', content: '服务器返回数据异常', showCancel: false })
        return
      }
      
      const tempPath = `${wx.env.USER_DATA_PATH}/idphoto_${Date.now()}.png`
      await new Promise<void>((resolve, reject) => {
        uni.getFileSystemManager().writeFile({
          filePath: tempPath,
          data: colorBase64.replace(prefix, ''),
          encoding: 'base64',
          success: () => resolve(),
          fail: (err) => reject(err)
        })
      })
      
      uni.hideLoading()
      that.savePhotoToAlbum(tempPath, colorBase64)
      
    } catch (err) {
      console.error('生成证件照失败:', err)
      uni.hideLoading()
      uni.showModal({ title: '保存失败', content: '网络请求异常，请重试', showCancel: false })
    }
  }

  async generateLayoutPhoto() {
    const adVerified = await this.showRewardedVideoAd()
    if (!adVerified) { uni.showToast({ title: '请看完广告后再继续', icon: 'none' }); return }

    uni.showLoading({ title: '处理中...' })
    const that = this
    const { photoSize, IDPhotoForm, isHd, photoPath: photo } = this
    const layoutPhotoForm: any = { height: photoSize.pxHeight, width: photoSize.pxWidth }
    if (IDPhotoForm.kb !== undefined) layoutPhotoForm.kb = IDPhotoForm.kb
    
    // 只传递 add_background 接口需要的参数: color, kb, render, dpi
    const colorForm: any = {
      color: IDPhotoForm.color.replace('#', '')
    }
    // 可选参数
    if (IDPhotoForm.kb !== undefined) colorForm.kb = IDPhotoForm.kb
    if (IDPhotoForm.render !== undefined && IDPhotoForm.render !== 0) colorForm.render = IDPhotoForm.render
    
    // 选择图片路径 - 使用临时文件路径
    const imagePath = isHd ? photo.base64HDPath : photo.base64Path
    console.log('排版照 - 图片路径:', imagePath)
    console.log('排版照 - photoPath对象:', photo)
    
    // 检查路径是否有效
    if (!imagePath) {
      uni.hideLoading()
      uni.showModal({ title: '处理失败', content: '图片路径无效，请重新拍照', showCancel: false })
      return
    }
    
    try {
      // 第一步：添加背景色
      console.log('排版照 - 开始添加背景色，参数:', colorForm)
      let colorRes: any
      try {
        colorRes = await AddBackgroudColor(colorForm, 'input_image', imagePath)
      } catch (apiErr) {
        console.error('排版照 - AddBackgroudColor API错误:', apiErr)
        throw apiErr
      }
      console.log('排版照 - 添加背景色返回:', JSON.stringify(colorRes))
      
      // 检查 API 返回状态
      if (colorRes?.status === false) {
        uni.hideLoading()
        const errMsg = colorRes?.message || '添加背景色失败'
        console.error('排版照 - API返回失败:', errMsg)
        uni.showModal({ title: '处理失败', content: errMsg, showCancel: false })
        return
      }
      
      // 获取 base64 数据
      const colorBase64 = colorRes?.image_base64
      if (!colorBase64) {
        uni.hideLoading()
        console.error('排版照 - 返回数据中没有image_base64:', colorRes)
        uni.showModal({ title: '处理失败', content: '服务器返回数据异常', showCancel: false })
        return
      }
      
      // 第二步：写入临时文件
      const tempColorPath = `${wx.env.USER_DATA_PATH}/temp_color_${Date.now()}.png`
      await new Promise<void>((resolve, reject) => {
        uni.getFileSystemManager().writeFile({
          filePath: tempColorPath,
          data: colorBase64.replace(prefix, ''),
          encoding: 'base64',
          success: () => resolve(),
          fail: (err) => reject(err)
        })
      })
      
      // 第三步：生成排版照
      console.log('排版照 - 开始生成排版照，参数:', layoutPhotoForm)
      const layoutRes = await GenerateLayoutPhoto(layoutPhotoForm, 'input_image', tempColorPath)
      console.log('排版照 - 生成排版照返回:', JSON.stringify(layoutRes))
      
      // 检查 API 返回状态
      if (layoutRes?.status === false) {
        uni.hideLoading()
        const errMsg = layoutRes?.message || '生成排版照失败'
        console.error('排版照 - 生成排版照API返回失败:', errMsg)
        uni.showModal({ title: '处理失败', content: errMsg, showCancel: false })
        return
      }
      
      const layoutBase64 = layoutRes?.image_base64
      if (!layoutBase64) {
        uni.hideLoading()
        console.error('排版照 - 生成排版照返回数据中没有image_base64:', layoutRes)
        uni.showModal({ title: '处理失败', content: '生成排版照失败', showCancel: false })
        return
      }
      
      // 第四步：保存排版照到临时文件
      const tempPath = `${wx.env.USER_DATA_PATH}/layout_${Date.now()}.png`
      await new Promise<void>((resolve, reject) => {
        uni.getFileSystemManager().writeFile({
          filePath: tempPath,
          data: layoutBase64.replace(prefix, ''),
          encoding: 'base64',
          success: () => resolve(),
          fail: (err) => reject(err)
        })
      })
      
      uni.hideLoading()
      that.savePhotoToAlbum(tempPath)
      
    } catch (err) {
      console.error('生成排版照失败:', err)
      uni.hideLoading()
      uni.showModal({ title: '保存失败', content: '网络请求异常，请重试', showCancel: false })
    }
  }

  saveToElectronicPhoto(base64Data: string) {
    if (!ElectronicPhotoManager.canSaveMore()) {
      uni.showModal({ title: '保存失败', content: '电子照已达上限（2张），请先删除', showCancel: false,
        success: () => setTimeout(() => uni.switchTab({ url: '/pages/electronic/index' }), 1500) })
      return
    }
    const photoData = {
      name: `${this.photoSize.name}证件照`, size: `${this.photoSize.pxWidth}×${this.photoSize.pxHeight}`,
      color: this.IDPhotoForm.color, hdBase64: base64Data, sdBase64: this.isHd ? this.photoPath.base64 : base64Data
    }
    if (ElectronicPhotoManager.save(photoData)) {
      uni.showToast({ title: '已保存到电子照', icon: 'success' })
      setTimeout(() => uni.switchTab({ url: '/pages/electronic/index' }), 1500)
    } else { uni.showToast({ title: '保存失败', icon: 'none' }) }
  }

  savePhotoToAlbum(tempPath: string, base64Data?: string) {
    const self = this
    if (self.saveToElectronic && base64Data) self.saveToElectronicPhoto(base64Data)
    uni.saveImageToPhotosAlbum({
      filePath: tempPath,
      success() {
        try { StorageManager.savePhotoRecord({ originalImage: self.photoPath.base64,
          resultImages: { idPhoto: self.isHd ? self.photoPath.base64HD : self.photoPath.base64, layoutPhoto: '' },
          parameters: { size: self.photoSize, backgroundColor: self.IDPhotoForm.color, isHd: self.isHd } }) } catch {}
        uni.showToast({ title: '保存成功', icon: 'success' })
      },
      fail(err) {
        if (err.errMsg === 'saveImageToPhotosAlbum:fail cancel') uni.showToast({ title: '已取消保存', icon: 'none' })
        else uni.showModal({ title: '保存失败', content: '请授权相册权限', showCancel: false })
      }
    })
  }

  onShareTimeline() { return { title: '小七快照拍 - 专业证件照制作', imageUrl: '/static/example.jpeg' } }
  onShareAppMessage() { return { title: '小七快照拍 - 专业证件照制作', path: '/pages/index/index', imageUrl: '/static/example.jpeg' } }
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #faf8f8;
  padding: 24rpx;
  padding-bottom: 180rpx;
  box-sizing: border-box;
}

.preview-card {
  background-color: #fff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.photo-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 28rpx;
}

.photo-container {
  border-radius: 12rpx;
  overflow: hidden;
  position: relative;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.photo {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.photo-meta {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 20rpx 0;
  background-color: #fff5f4;
  border-radius: 16rpx;
}

.meta-item {
  text-align: center;
}

.label {
  display: block;
  font-size: 22rpx;
  color: #999;
  margin-bottom: 8rpx;
}

.value {
  display: block;
  font-size: 26rpx;
  color: #333;
  font-weight: 600;
}

.value-highlight {
  display: block;
  font-size: 26rpx;
  color: #F77261;
  font-weight: 600;
}

.divider {
  width: 1rpx;
  height: 48rpx;
  background-color: #ffe0dc;
}

.section-card {
  background-color: #fff;
  border-radius: 24rpx;
  padding: 28rpx 32rpx;
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 24rpx;
}

.color-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
}

.color-option {
  width: 25%;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24rpx;
}

.color-circle {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.color-white {
  border: 2rpx solid #e0e0e0;
}

.color-active {
  border: 4rpx solid #F77261;
  transform: scale(1.1);
}

.check-icon {
  font-size: 28rpx;
  color: #F77261;
  font-weight: bold;
}

.color-label {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #888;
}

.label-active {
  color: #F77261;
  font-weight: 600;
}

.settings-list {
  padding: 0;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #fff0ee;
}

.setting-row:last-child {
  border-bottom: none;
}

.setting-left {
  display: flex;
  align-items: center;
}

.icon-box-pink {
  width: 56rpx;
  height: 56rpx;
  border-radius: 14rpx;
  background-color: #F77261;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
}

.icon-box-orange {
  width: 56rpx;
  height: 56rpx;
  border-radius: 14rpx;
  background-color: #ff9a8b;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
}

.icon-text {
  font-size: 24rpx;
  color: #fff;
  font-weight: bold;
}

.setting-text {
  display: flex;
  flex-direction: column;
}

.main-text {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.sub-text {
  font-size: 22rpx;
  color: #999;
  margin-top: 4rpx;
}

.bottom-actions {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  padding: 20rpx 24rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background-color: #fff;
}

.btn-secondary {
  flex: 1;
  height: 88rpx;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #fff5f4;
  color: #F77261;
  font-size: 30rpx;
  font-weight: 600;
  margin-right: 20rpx;
  border: 2rpx solid #ffe0dc;
}

.btn-primary {
  flex: 1;
  height: 88rpx;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F77261;
  color: #fff;
  font-size: 30rpx;
  font-weight: 600;
}

.btn-icon {
  margin-right: 8rpx;
  font-size: 32rpx;
}
</style>
