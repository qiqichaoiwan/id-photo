# 小程序内容安全审核验证说明

## 已接入的能力

后端在图片进入 HivisionIDPhotos 推理前调用微信内容安全接口。检测结果为风险或接口不可用时，图片处理会停止并返回提示；原始图片、`access_token`、AppSecret、OpenID 不写入内容安全审计日志。

| 能力 | 后端接口 | 小程序入口 | 结果 |
| --- | --- | --- | --- |
| 图片检测 | `imgSecCheck` | 我的 → 服务状态 → 图片检测 | 返回 `errcode`、`errmsg`、`trace_id` 和 SHA-256 摘要 |
| 文本检测 | `msgSecCheck` | 我的 → 服务状态 → 文本检测 | 返回微信文本检测结果 |
| 异步媒体检测 | `mediaCheckAsync` | 我的 → 服务状态 → 异步媒体检测 | 返回受理结果，最终判定由微信消息推送回调记录 |

## 审核录屏步骤

1. 使用管理员或开发者账号打开体验版，进入 **我的 → 服务状态**。
2. 点 **上传照片并验证**，选择一张普通、清晰的人像照片，等待页面显示 `检测通过`、`errcode：0` 和检测编号（如有）。
3. 在 **文本检测** 中保留默认的安全演示文本，点 **检测这段文本**，录下页面显示 `检测通过` 和 `errcode：0`。
4. 在 **异步媒体检测** 中保留默认的 `https://photo.ruize.eu.org/content-security/demo-media`，点 **提交异步媒体检测**，录下页面显示 `已提交，等待微信异步回调` 和 `errcode：0`。
5. 返回服务状态卡片，录下 **内容安全检测：已配置微信图片、文本和媒体内容安全检查** 的状态。
6. 将三段接口返回值录屏和服务状态截图上传到微信公众平台审核说明。录屏中不要展示任何 AppSecret、支付密钥或用户隐私照片。

## 运行配置

生产环境保持：

```dotenv
IDPHOTO_CONTENT_SECURITY_ENABLED=true
WECHAT_APP_ID=wx7db67e2346adbeca
WECHAT_APP_SECRET=（仅保存在服务器的 .env.miniapp）
```

`/content-security/demo-media` 只返回固定的一像素演示图片，供 `mediaCheckAsync` 读取；它不接收用户上传内容。所有真实图片处理接口仍会在推理前执行图片检测。

## 提审前自检

- 后端可访问 `https://photo.ruize.eu.org/health` 和 `/service-status`。
- 小程序合法域名继续使用 `photo.ruize.eu.org`。
- 微信消息推送安全模式仍指向 `/payment/notify`，媒体异步回调会在该入口记录判定元数据。
- 体验版可完成登录并进入服务状态页；不需要真实支付。
