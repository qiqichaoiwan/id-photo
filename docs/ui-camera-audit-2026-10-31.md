# 拍摄界面统一审计

## 覆盖范围

- 证件照：`pages/photo/index`
- 人像抠图：`pages/matting/index`、`pages/matting/upload`
- 图片加水印：`pages/watermark/index`、`pages/watermark/upload`
- 格式转换：`pages/convert/index`

以上入口使用同一个 `PhotoCamera` 组件，取景、关闭、相册、翻转、拍摄、预览、重拍和出错恢复采用统一布局。相机内的辅助线可开启或关闭，重拍时保留当前选择；证件照和人像场景默认开启，水印和转换场景默认关闭。辅助线仅用于取景，不会写入照片。

格式转换提供拍摄和相册两个入口。水印仍要求先填写水印文字；旧上传页面交接照片时，业务页能接收所选路径并继续处理。

## 验证

- 构建微信小程序成功。
- `tests/camera-flow.test.cjs`：检查六个入口的组件接入、辅助线状态、相机初始化、拍摄保护、重拍、相册、权限恢复、延迟回调及业务交接。
- `tests/camera-ui-audit.cjs`：在微信开发者工具逐个打开六个入口，检查相机默认状态、辅助线切换后的渲染、镜头切换、模拟拍摄后的预览与重拍。
- `tests/camera-legacy-handoff.test.cjs`：验证两个旧上传入口的照片交接及包含特殊字符的路径。
- `tests/camera-integration.test.cjs`：模拟相机返回示例照片，证件照、抠图、水印和格式转换使用真实后端处理。
- 加载反馈、图标、23 个已注册页面的静态一致性、广告会员和服务状态回归检查通过。

微信开发者工具的自动化测试需要安装 `miniprogram-automator` 并能够控制已授权的开发者工具。默认使用本机的测试依赖位置；也可通过 `WECHAT_AUTOMATOR_PATH`、`WECHAT_CLI_PATH` 和 `WECHAT_PROJECT_PATH` 指定路径。相机界面测试截图默认保存在 `dist/ui-audit/camera`。

开发者工具没有物理摄像头，拍照结果由测试回调模拟。真机取景、权限提示、不同机型的原生相机图层和实际成像仍需通过手机验证。测试期间正式会员购买保持关闭。

## 开发版

2026-10-31 已上传微信开发版 `1.2.0`（AppID：`wx7db67e2346adbeca`），并生成对应的开发者工具预览码。上传前已核对服务状态、正式购买开关和激励广告位配置。
