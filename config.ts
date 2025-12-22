interface EnvironmentConfig {
  host: string;
}

const baseApi: { [key: string]: EnvironmentConfig } = {
  // 开发版
  development: {
    host: "https://your-api",
  },
  // 体验版
  trial: {
     host: "https://your-api",
  },
  // 正式版
  release: {
     host: "https://your-api",
  },
  // uniapp 正式环境
  production: {
    host: "https://your-api",
  },
};

// 环境
export const env = process.env.NODE_ENV;
// host
export const baseUrl = baseApi[env].host;

// 微信广告配置
export const adConfig = {
  // 激励视频广告单元ID
  rewardedVideoAdUnitId: 'adunit-微信小程序激励广告',
};
