# 小程序 UI 精修与验证记录

日期：2026 年 10 月 31 日（北京时间）

## 本轮改动

- 以 `ui-design-v1.png` 为视觉参考，将首页、照片工具、个人中心、会员和说明页面统一到浅色背景、白色卡片、品牌红主操作，以及蓝、青、紫、琥珀色辅助图标的设计体系。样式变量与公共规则见 `src/assets/design-tokens.scss` 和 `src/assets/legacy-page-themes.scss`。
- 重绘首页、电子照、我的三组底部导航图标，普通态与选中态使用一致的轮廓；选中态使用品牌红。
- 统一图片处理等待卡片、进度显示与错误及空状态。广告等待与图片处理等待分开，避免在广告尚未结束时显示保存中。
- 重新组织“我的”页面的个人信息、会员、照片和支持入口，并增加会员查询失败时的提示；会员中心使用与个人中心一致的图标语言。
- 修复旧页面把不存在的 uView 图标名直接显示为文字的问题，补充图标名称检查；优化格式转换页面选择照片的空状态。
- 修复电子照卡片无法预览的问题。预览时复用临时文件，在删除照片、清理和离开页面时释放相应缓存。
- 首页与个人中心接入服务状态入口，可查看连接、模型、图片工具、登录、会员和购买状态；支付关闭单独显示，不作为服务故障。

## 页面与交互验证

- 微信开发者工具逐页截图审计了 23 个注册页面，并在修正后再次逐页复查。检查范围包含首页、电子照、我的、状态、证件照、抠图、水印、格式转换、会员、历史与说明页面。
- 在开发者工具中检查了证件照和转换等待状态、个人中心会员有效与查询失败状态、会员和电子照入口、订单空状态。电子照卡片点击与临时文件复用使用模拟预览窗口验证。
- 在浏览器的 H5 预览中补充检查了 320、375、414 像素宽的首页，以及 320 像素宽的个人中心、照片选择、格式转换和会员页；页面没有横向溢出，会员说明可滚动到固定按钮上方。修复了首页窄屏下“更多”和箭头换行的问题。H5 预览不代表微信真机表现。
- 交互回归覆盖首页搜索及自定义规格、状态刷新、证件照处理与编辑、水印、人像抠图、格式转换、历史规格重做，以及会员三档套餐和购买关闭状态。测试中照片处理连接真实后端；广告、相册保存回调使用模拟。
- 前端自动检查覆盖广告和会员场景、服务状态、23 个页面的导航和模板、等待及保存流程、导航图标图像与 uView 图标名称。
- 后端 14 项隔离测试通过，覆盖状态接口和限流、会员自然月与续费、退款标记、并发保护、示例照片处理及错误输入。公网状态接口检查结果为服务正常、会员购买未开放。

本轮截图采用微信开发者工具中的 iPhone 12/13 Pro 模拟器，使用项目自带示例照片：

- [首页与底部导航](ui-refinement-2026-10-31/home.png)
- [320 像素宽首页浏览器预览](ui-refinement-2026-10-31/home-h5-320.png)
- [个人中心](ui-refinement-2026-10-31/mine.png)
- [证件照等待](ui-refinement-2026-10-31/loading-photo.png)
- [格式转换空状态](ui-refinement-2026-10-31/convert-empty.png)
- [人像抠图结果](ui-refinement-2026-10-31/matting-result.png)
- [会员中心](ui-refinement-2026-10-31/membership.png)

## 验证边界

- 开发者工具的模拟测试不能代替真实手机上的相机、相册权限和激励广告展示，也未逐一覆盖其他微信机型尺寸。图片预览窗口及保存回调在本轮使用模拟。
- 未发起 iPhone 真实付款或退款；根据现有要求，正式会员购买开关保持关闭。此前 Android 沙箱的购买和续费已由用户在手机上确认，本轮没有重复创建支付订单。
- 服务状态反映连接、基础配置及近期已记录异常；它不保证每一次图片处理、微信登录或第三方支付都能成功。断连时无法单独判断故障位于手机网络、隧道还是后端。
- 构建产物保存在本机 `dist/ui-audit/mp-weixin`，本次 UI 修改尚未上传或发布为微信正式版。构建出现当前 npm 与 Node 版本匹配及 Browserslist 数据过期提示，构建仍成功。

## 复现

```sh
cd /Users/qiqi/id-photo
export PATH=/Users/qiqi/.npm/_npx/ebaba8b9e55fd0a9/node_modules/node/bin:$PATH
UNI_OUTPUT_DIR=/Users/qiqi/id-photo/dist/ui-audit/mp-weixin npm run build:mp-weixin
node tests/loading-flow.test.cjs
node tests/ad-manager.test.cjs
node tests/service-status.test.cjs
node tests/ui-consistency.test.cjs
node tests/ui-icons.test.cjs
python3 tests/tab-icons.test.py
```

```sh
cd /Users/qiqi/HivisionIDPhotos
PYTHONPATH=.:test IDPHOTO_TEST_IMAGE=/Users/qiqi/id-photo/src/static/example.jpeg \
  .venv/bin/python -m unittest -v test_miniapp_status test_miniapp_membership_rules \
  test_creator_concurrency test_miniapp_functional
```
