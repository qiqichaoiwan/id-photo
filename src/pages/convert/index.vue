<template>
  <view class="page">
    <view class="preview" :class="{ 'has-image': displayPath }" @click="choosePhoto">
      <image v-if="displayPath" :src="displayPath" mode="aspectFit" />
      <view v-else class="placeholder">
        <view class="preview-icon"><u-icon name="photo" size="30" color="#356caa" /></view>
        <text class="placeholder-title">选择需要转换的照片</text>
        <text class="placeholder-hint">支持从相册选择或拍摄</text>
        <view class="choose-button"><u-icon name="plus" size="15" color="#cc3d35" /><text>选择照片</text></view>
      </view>
    </view>
    <view v-if="displayPath" class="change-photo" @click="choosePhoto">重新选择照片</view>
    <view class="card"><view class="title">图片格式</view><view class="tabs"><view :class="{ active: outputFormat === 'jpg' }" @click="setFormat('jpg')">JPG</view><view :class="{ active: outputFormat === 'png' }" @click="setFormat('png')">PNG</view></view><view class="hint">{{ outputFormat === 'png' ? 'PNG 保留透明背景，文件大小取决于图片内容。' : 'JPG 会将透明背景转换为白色。' }}</view></view>
    <view class="card"><view class="title">目标大小</view><picker :range="targetLabels" :value="targetIndex" @change="onTargetChange"><view class="picker"><text>{{ targetLabels[targetIndex] }}</text><u-icon name="arrow-down" size="16" color="#666b73" /></view></picker><view v-if="targetIndex" class="hint">转换时尽量控制在目标大小内，实际结果可能受图片内容影响。</view></view>
    <view v-if="resultPath" class="card"><view class="title">转换结果</view><view class="result-row"><text>图片大小</text><text>{{ sizeText }}</text></view><view class="result-row"><text>图片尺寸</text><text>{{ width }}×{{ height }} px</text></view><view v-if="!targetMet" class="warning">当前图片无法达到目标大小，可尝试调整目标或更换格式。</view></view>
    <view class="bottom"><view v-if="resultPath" class="save-hint">{{ memberState === 'member' ? '会员免广告保存' : memberState === 'ordinary' ? '观看完整广告后保存' : '保存前将确认会员状态' }}</view><view class="primary-button" :class="{ disabled: busy || !sourcePath }" @click="onAction">{{ busy ? '正在处理...' : resultPath ? '保存到相册' : '开始转换' }}</view></view>
    <PhotoCamera v-if="showCamera" title="拍摄照片" :guide-initially-enabled="false" initial-position="back"
      @close="showCamera = false" @select="onCameraSelect" />
    <LoadingOverlay :show="processing" :text="saving ? '正在保存图片' : '正在转换图片'" :tip="saving ? '请稍候，正在保存到相册' : '正在处理图片格式与大小，请稍候'" />
  </view>
</template>
<script lang="ts">
import Vue from 'vue'; import { Component } from 'vue-property-decorator';
import { uploadFile } from '@/utils/request'; import { writeTemporaryImage, removeTemporaryImage } from '@/utils/image-file'; import { adManager } from '@/utils/ad-manager'; import { getMembershipStatus } from '@/api/membership';
import LoadingOverlay from '@/components/LoadingOverlay.vue';
import PhotoCamera from '@/components/PhotoCamera.vue';
@Component({ components: { LoadingOverlay, PhotoCamera } }) export default class Convert extends Vue {
  showCamera=false; sourcePath=''; resultPath=''; outputFormat='jpg'; targetIndex=0; busy=false; processing=false; saving=false; rewarded=false;
  targetValues=[0,50,100,200,500,1000,2000]; targetLabels=['不限制','50 KB','100 KB','200 KB','500 KB','1 MB','2 MB'];
  width=0; height=0; sizeBytes=0; targetMet=true; memberState:'member'|'ordinary'|'unknown'='unknown';
  get displayPath(){ return this.resultPath || this.sourcePath; }
  get sizeText(){ return this.sizeBytes >= 1024*1024 ? (this.sizeBytes/1024/1024).toFixed(2)+' MB' : (this.sizeBytes/1024).toFixed(1)+' KB'; }
  onShow(){ this.refreshMembership(); }
  onUnload(){ removeTemporaryImage(this.resultPath); }
  async refreshMembership(){ try{this.memberState=(await getMembershipStatus()).active?'member':'ordinary';}catch(_){this.memberState='unknown';} }
  clearResult(){ removeTemporaryImage(this.resultPath); this.resultPath=''; this.rewarded=false; }
  choosePhoto(){
    if(this.busy)return;
    uni.showActionSheet({itemList:['拍摄照片','从相册选择'],success:result=>{
      if(result.tapIndex===0){this.showCamera=true;return;}
      if(result.tapIndex===1)uni.chooseImage({count:1,sizeType:['original'],sourceType:['album'],success:selection=>this.onCameraSelect(selection.tempFilePaths[0])});
    }});
  }
  onCameraSelect(path:string){if(!path)return;this.showCamera=false;this.clearResult();this.sourcePath=path;}
  setFormat(value:string){ if(this.busy||value===this.outputFormat)return; this.outputFormat=value; this.clearResult(); }
  onTargetChange(event:any){ if(this.busy)return; this.targetIndex=Number(event.detail.value); this.clearResult(); }
  async onAction(){ if(this.busy||!this.sourcePath)return; if(this.resultPath)await this.save(); else await this.convert(); }
  async convert(){ this.busy=true; this.processing=true; try{const result:any=await uploadFile('/convert_image','input_image',this.sourcePath,{data:{output_format:this.outputFormat,target_kb:this.targetValues[this.targetIndex]}});if(!result.image_base64)throw new Error('服务器未返回图片');this.resultPath=await writeTemporaryImage(result.image_base64,'convert');this.width=result.width;this.height=result.height;this.sizeBytes=result.size_bytes;this.targetMet=result.target_met;}catch(error:any){uni.showModal({title:'转换失败',content:error.message||'请稍后重试',showCancel:false});}finally{this.processing=false;this.busy=false;} }
  async save(){ this.busy=true; try{if(!this.rewarded){const access=await adManager.authorize();if(!access)return;this.memberState=access==='member'?'member':'ordinary';this.rewarded=access==='ad';}this.saving=true;this.processing=true;await new Promise<void>((resolve,reject)=>uni.saveImageToPhotosAlbum({filePath:this.resultPath,success:()=>resolve(),fail:()=>reject(new Error('保存失败，请检查相册权限'))}));this.rewarded=false;uni.showToast({title:'保存成功',icon:'success'});}catch(error:any){uni.showModal({title:'保存失败',content:error.message||'请稍后重试',showCancel:false});}finally{this.processing=false;this.saving=false;this.busy=false;} }
}
</script>
<style lang="scss" scoped>
@import '@/assets/design-tokens.scss'; .page{min-height:100vh;background:$page;color:$ink;box-sizing:border-box;padding:24rpx 28rpx calc(190rpx + env(safe-area-inset-bottom))}.preview{@include card;height:400rpx;display:flex;align-items:center;justify-content:center;box-sizing:border-box;margin-bottom:20rpx}.preview.has-image{height:410rpx;background:transparent;box-shadow:none;margin-bottom:0}.preview image{width:100%;height:100%;border-radius:12rpx}.placeholder{display:flex;flex-direction:column;align-items:center}.preview-icon{width:92rpx;height:92rpx;display:flex;align-items:center;justify-content:center;border-radius:28rpx;background:#eaf2fc}.placeholder-title{font-size:29rpx;font-weight:600;margin-top:20rpx}.placeholder-hint{color:$muted;font-size:23rpx;margin-top:8rpx}.choose-button{height:64rpx;display:flex;align-items:center;justify-content:center;gap:8rpx;padding:0 24rpx;margin-top:22rpx;border-radius:32rpx;background:#fff1ef;color:$brand;font-size:24rpx;font-weight:600}.change-photo{text-align:center;color:$brand;font-size:25rpx;padding:18rpx}.card{@include card;padding:28rpx;margin-bottom:20rpx}.title{font-size:30rpx;font-weight:650;margin-bottom:20rpx}.tabs{display:flex;gap:16rpx}.tabs view{flex:1;text-align:center;padding:20rpx 0;border:1rpx solid #d5d7db;border-radius:14rpx;font-size:28rpx}.tabs .active{border-color:$brand;background:#fff6f5;color:$brand;font-weight:600}.hint{color:$muted;font-size:23rpx;margin-top:16rpx;line-height:1.5}.picker{display:flex;align-items:center;justify-content:space-between;padding:20rpx;border:1rpx solid $border;border-radius:12rpx;font-size:28rpx}.result-row{display:flex;justify-content:space-between;padding:18rpx 0;border-top:1rpx solid $border;font-size:26rpx}.result-row text:first-child{color:$muted}.warning{color:#a44736;font-size:24rpx;line-height:1.5;margin-top:10rpx}.bottom{position:fixed;left:0;right:0;bottom:0;background:$page;padding:12rpx 28rpx calc(20rpx + env(safe-area-inset-bottom))}.save-hint{text-align:center;color:$muted;font-size:24rpx;margin-bottom:14rpx}.primary-button{@include primary-button}.disabled{opacity:.55}
</style>
