interface EnvironmentConfig {
  host: string;
}

const defaultHost = 'https://photo.ruize.eu.org';
const baseApi: { [key: string]: EnvironmentConfig } = {
  development: { host: process.env.VUE_APP_API_DEVELOPMENT || process.env.VUE_APP_API_BASE_URL || defaultHost },
  trial: { host: process.env.VUE_APP_API_TRIAL || process.env.VUE_APP_API_BASE_URL || defaultHost },
  release: { host: process.env.VUE_APP_API_RELEASE || process.env.VUE_APP_API_BASE_URL || defaultHost }
};

declare const wx: any;

function getEnvironment(): string {
  // #ifdef MP-WEIXIN
  try {
    const version = wx.getAccountInfoSync().miniProgram.envVersion;
    if (version === 'develop') return 'development';
    if (version === 'trial' || version === 'release') return version;
  } catch (_) {
    // Older developer tools may not provide account information.
  }
  // #endif
  return process.env.NODE_ENV === 'production' ? 'release' : 'development';
}

export const env = getEnvironment();
export const baseUrl = baseApi[env].host.replace(/\/$/, '');

// Set VUE_APP_REWARDED_VIDEO_AD_UNIT_ID in .env.local before building.
export const adConfig = {
  rewardedVideoAdUnitId: process.env.VUE_APP_REWARDED_VIDEO_AD_UNIT_ID || ''
};
