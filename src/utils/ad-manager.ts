import { adConfig } from '@/config';
import { getMembershipStatus } from '@/api/membership';

declare const wx: any;
export type SaveAccess = 'member' | 'ad' | null;

class AdManager {
  private videoAd: any = null;
  private active: Promise<SaveAccess> | null = null;

  private init(): boolean {
    if (this.videoAd) return true;
    // #ifdef MP-WEIXIN
    if (!adConfig.rewardedVideoAdUnitId || typeof wx === 'undefined' || !wx.createRewardedVideoAd) return false;
    try {
      this.videoAd = wx.createRewardedVideoAd({ adUnitId: adConfig.rewardedVideoAdUnitId });
      return true;
    } catch (_) { return false; }
    // #endif
    // #ifndef MP-WEIXIN
    return false;
    // #endif
  }

  /** Fetch membership for each save; a local flag never grants the entitlement. */
  async authorize(): Promise<SaveAccess> {
    if (this.active) return null;
    this.active = this.authorizeOnce().then((result) => {
      this.active = null;
      return result;
    }, (error) => {
      this.active = null;
      throw error;
    });
    return this.active;
  }

  async show(): Promise<boolean> { return !!(await this.authorize()); }

  private async authorizeOnce(): Promise<SaveAccess> {
    try {
      const status = await getMembershipStatus();
      if (status.active === true) return 'member';
    } catch (_) {
      // If the entitlement cannot be confirmed, keep the ordinary-user ad flow.
    }
    return (await this.showVideo()) ? 'ad' : null;
  }

  private async showVideo(): Promise<boolean> {
    if (!this.init()) {
      uni.showToast({ title: '广告暂不可用，请稍后重试', icon: 'none' });
      return false;
    }
    const ad = this.videoAd;
    return new Promise<boolean>((resolve) => {
      let settled = false;
      let attempting = true;
      const finish = (completed: boolean, unavailable: boolean = false) => {
        if (settled) return;
        settled = true;
        try { ad.offClose(onClose); } catch (_) { /* listener may already be removed */ }
        try { if (ad.offError) ad.offError(onError); } catch (_) { /* listener may already be removed */ }
        if (!completed) uni.showToast({ title: unavailable ? '广告暂不可用，请稍后重试' : '请看完广告后再继续', icon: 'none' });
        resolve(completed);
      };
      const onClose = (result: any) => finish(!result || result.isEnded === true);
      const onError = () => { if (!attempting) finish(false, true); };
      try {
        ad.onClose(onClose);
        if (ad.onError) ad.onError(onError);
        Promise.resolve().then(() => ad.show()).catch(() => {
          if (settled) return;
          return Promise.resolve().then(() => ad.load()).then(() => {
            if (!settled) return ad.show();
          });
        }).then(() => { attempting = false; }).catch(() => finish(false, true));
      } catch (_) { finish(false, true); }
    });
  }
}

export const adManager = new AdManager();
export default adManager;
