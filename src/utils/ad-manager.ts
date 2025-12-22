/**
 * 激励视频广告管理器
 * 统一管理小程序激励视频广告
 */

import { adConfig } from '@/config';

declare const wx: WechatMiniprogram.Wx;

class AdManager {
  private videoAd: any = null;
  private adUnitId: string = adConfig.rewardedVideoAdUnitId;

  /**
   * 初始化激励视频广告
   */
  init() {
    if (typeof wx === 'undefined' || !wx.createRewardedVideoAd) {
      console.warn('当前环境不支持激励视频广告');
      return;
    }

    try {
      this.videoAd = wx.createRewardedVideoAd({ adUnitId: this.adUnitId });
      
      this.videoAd.onLoad(() => {
        console.log('激励视频广告加载成功');
      });
      
      this.videoAd.onError((err: any) => {
        console.error('激励视频广告加载失败', err);
      });
    } catch (error) {
      console.error('创建激励视频广告失败:', error);
    }
  }

  /**
   * 显示激励视频广告并等待用户完成观看
   * @returns Promise<boolean> 用户是否完整观看了广告
   */
  async show(): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.videoAd) {
        console.warn('激励视频广告实例不存在');
        resolve(false);
        return;
      }

      try {
        this.videoAd.show().catch(() => {
          // 显示失败，尝试重新加载
          this.videoAd?.load()
            .then(() => this.videoAd?.show())
            .catch(() => resolve(false));
        });

        const handleClose = (res: any) => {
          try {
            this.videoAd?.offClose(handleClose);
          } catch (e) {
            console.warn('移除广告关闭监听器失败:', e);
          }
          
          resolve(res?.isEnded || false);
        };

        this.videoAd.onClose(handleClose);
      } catch (error) {
        console.error('显示广告过程中发生错误:', error);
        resolve(false);
      }
    });
  }

  /**
   * 销毁广告实例
   */
  destroy() {
    this.videoAd = null;
  }
}

// 导出单例
export const adManager = new AdManager();
export default adManager;
