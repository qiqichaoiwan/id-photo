import { baseUrl } from '@/config';

declare const wx: any;

let token: string | null = null;
let expiresAt = 0;
let loginInFlight: Promise<string> | null = null;

export function currentToken(): string | null {
  return token && Date.now() < expiresAt ? token : null;
}

export function invalidateToken(): void {
  token = null;
  expiresAt = 0;
}

export function loginToBackend(): Promise<string> {
  if (loginInFlight) return loginInFlight;
  loginInFlight = new Promise<string>((resolve, reject) => {
    // #ifdef MP-WEIXIN
    wx.login({
      success: (login: any) => {
        if (!login.code) {
          reject(new Error('微信登录失败，请重试'));
          return;
        }
        uni.request({
          url: `${baseUrl}/auth/wechat`,
          method: 'POST',
          data: { code: login.code },
          timeout: 15000,
          success: (response: any) => {
            const result = response.data || {};
            if (response.statusCode !== 200 || typeof result.token !== 'string') {
              reject(new Error(result.detail || '登录服务暂不可用，请稍后重试'));
              return;
            }
            token = result.token;
            expiresAt = Date.now() + Math.max(0, Number(result.expires_in || 3600) - 60) * 1000;
            resolve(result.token);
          },
          fail: () => reject(new Error('无法连接登录服务，请检查网络'))
        });
      },
      fail: () => reject(new Error('微信登录失败，请重试'))
    });
    // #endif
    // #ifndef MP-WEIXIN
    reject(new Error('当前环境不支持微信登录'));
    // #endif
  }).then((result) => {
    loginInFlight = null;
    return result;
  }, (error) => {
    loginInFlight = null;
    throw error;
  });
  return loginInFlight;
}
