# 微信小程序与 HivisionIDPhotos 的运行说明

## 当前环境

- 小程序 AppID：`wx7db67e2346adbeca`，接口地址：`https://photo.ruize.eu.org`。
- 在微信公众平台将该 HTTPS 域名分别加入 **request 合法域名**和 **uploadFile 合法域名**，并配置小程序隐私保护指引。域名的具体配置以微信后台为准。
- 激励视频广告位通过 `VUE_APP_REWARDED_VIDEO_AD_UNIT_ID` 配置。当前机器的 `.env.local` 已填写，其他机器可复制 `.env.example` 为 `.env.local`。修改环境变量后需要重新构建或重启监听进程。广告不可用或未看完时不会保存照片。
- 不要把微信 AppSecret、后端令牌密钥放进小程序代码或提交到 Git。

## 启动小程序

项目使用 Vue 2 和 uni-app。使用 Node.js 20：

```sh
cd /Users/qiqi/id-photo
PATH="/Users/qiqi/.npm/_npx/ebaba8b9e55fd0a9/node_modules/node/bin:$PATH" yarn dev:mp-weixin
```

在微信开发者工具中导入 `/Users/qiqi/id-photo/dist/dev/mp-weixin`。正式构建使用 `yarn build:mp-weixin`，输出到 `dist/build/mp-weixin`。编译成功不等于真机广告或登录验证成功。

## 后端服务

仓库已经包含 HivisionIDPhotos 基础源码和小程序后端扩展，位于 `backend/hivision-core` 和 `backend/hivision-overlay`。新机器不需要另外克隆上游项目。微信 AppSecret 和随机生成的令牌签名密钥保存在权限为 `600` 的 `.env.miniapp`，已加入后端 `.gitignore`。首次配置时在本机终端执行：

```sh
cd /path/to/id-photo/backend
./bootstrap.sh
./configure.sh
```

按提示输入 AppSecret，终端不会显示输入内容。若配置文件已存在，脚本不会覆盖；更换密钥时请自行安全编辑该本地文件。服务通过 `hivision-overlay/start_miniapp_api.sh` 读取配置，只监听 `127.0.0.1:8080`；Cloudflare Tunnel 将公网域名转发到此端口。开发环境可在 `backend` 目录执行 `./start-all.sh` 一次启动 API、支付消息接收和管理后台；生产环境应为三个服务分别配置进程管理。修改配置或后端代码后重新运行启动脚本：

```sh
cd /path/to/id-photo/backend
./hivision-overlay/start_miniapp_api.sh
curl https://photo.ruize.eu.org/health
```

`/health` 应返回 `{"status":"ok"}`；未登录访问图片接口应返回 401。后端日志为 `/tmp/hivision-api.log` 和 `/tmp/hivision-api-error.log`。此前的启动项文件已备份在 `~/Library/LaunchAgents/`，恢复旧启动命令之前也需恢复匹配的后端代码或提供必需的环境变量。

鉴权默认开启，启动时缺少配置会失败。`IDPHOTO_AUTH_REQUIRED=false` 仅适用于隔离的本地开发实例；不要用于公网服务。前端连接该无鉴权实例时，还需在 `.env.local` 设置 `VUE_APP_BACKEND_AUTH_REQUIRED=false` 并重新构建。登录令牌只在小程序内存中保存，过期后重新登录。

限流使用单进程内存，适合当前单进程部署；多进程或多机器部署需要共享限流存储。`IDPHOTO_TRUST_CLOUDFLARE=true` 仅适用于服务只接受可信的本机 Cloudflare Tunnel 转发时；直接暴露或使用其他代理时应调整配置，避免信任伪造的来源地址。图片单张最多 20MB，支持 JPG、PNG、WebP，最大 2000 万像素且单边不超过 8192 像素。

## 一键恢复

仓库中的 `scripts/recover_xiaoqi_photo.sh` 会先校验后端配置和 Cloudflare ingress，再按顺序重启图片 API、支付推送、会员后台、可选沙箱以及两个照片 Tunnel，最后检查本机和公网健康入口。它不会修改密钥、会员数据库或 Tunnel 配置。当前设备已安装快捷命令：

```sh
recover-xiaoqi-photo
```

也可以先只检查、不重启：

```sh
recover-xiaoqi-photo --check
```

如果命令不存在，从仓库根目录执行：

```sh
cp scripts/recover_xiaoqi_photo.sh "$HOME/bin/recover-xiaoqi-photo"
chmod 755 "$HOME/bin/recover-xiaoqi-photo"
```

恢复脚本默认使用 `/Users/qiqi/HivisionIDPhotos` 和 `~/.cloudflared/config.yml`；迁移设备时可通过 `IDPHOTO_ROOT` 和 `CLOUDFLARED_CONFIG` 覆盖。脚本返回非零状态表示有检查未通过，应查看终端输出和 `/tmp/hivision-api*.log`、`/tmp/idphoto-payment-*.log`、`/tmp/idphoto-membership-admin*.log` 以及 `~/.cloudflared/*.log`。

## 验收清单

1. 在开发工具或真机选取一张有且只有一张清晰正脸的照片，生成标准照和高清照。
2. 验证人脸对齐、水平翻转、美白及模型选择，并检查背景色与三种相纸排版、裁剪线。
3. 验证抠图和水印；调整水印字号、透明度、角度、颜色及间距。
4. 完整观看广告后保存到相册；中途关闭及广告加载失败时确认不会保存。广告填充和权限情况以真实微信环境为准。
5. 保存电子照、再次下载、清理缓存；确认相册内已有照片不会被清理。本地存储大小显示不包含临时文件。

## 尚未开放的页面

`pages/photo/enhanced-edit` 是旧的实验页面，目前没有主流程入口；其中的亮度、对比度、锐化和饱和度控件尚未完成接入和验收。正式使用请走当前证件照页面中的美白、人脸对齐和翻转选项。
