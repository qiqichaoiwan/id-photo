interface EnvironmentConfig {
  host: string;
}

const baseApi: { [key: string]: EnvironmentConfig } = {
  // 开发版
  development: {
    host: "https://photo.ruize.eu.org",
  },
  // 体验版
  trial: {
     host: "https://photo.ruize.eu.org",
  },
  // 正式版
  release: {
     host: "https://photo.ruize.eu.org",
  },
  // uniapp 正式环境
  production: {
    host: "https://photo.ruize.eu.org",
  },
};

// 环境
export const env = process.env.NODE_ENV;
// host
export const baseUrl = baseApi[env].host;

// 微信广告配置
export const adConfig = {
  // 激励视频广告单元ID
  rewardedVideoAdUnitId: 'adunit-c1929ce9fe7e079a',
};
