/// <reference types='@dcloudio/types' />
import Vue from 'vue'

// 微信小程序全局对象声明
declare const wx: WechatMiniprogram.Wx;

declare module "vue/types/options" {
  type Hooks = App.AppInstance & Page.PageInstance;
  interface ComponentOptions<V extends Vue> extends Hooks {
    /**
     * 组件类型
     */
    mpType?: string;
  }
}
