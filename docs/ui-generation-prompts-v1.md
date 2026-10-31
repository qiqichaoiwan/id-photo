# 补充 UI 设计图：生成提示词

本文件记录本次两张补充设计图使用的内置 imagegen 提示词。文案和状态规则以 [需求汇总 V2](requirements-membership-v2.md) 为准。

## 会员状态图

参考图：`ui-membership-mobile-v1.png`。

```text
Use case: ui-mockup. Asset: a high fidelity supplemental WeChat mini program mobile UI design sheet for “小七快照拍”. Reference image 1 is a style reference only: keep the soft coral red, off-white background, white rounded cards, dark readable Simplified Chinese type, understated icons and small WeChat capsule. Create FOUR complete tall phone screens side by side, sufficiently large and legible, straight-on design presentation on a light grey canvas. Every screen is a separate independently usable mini program page; realistic spacing.
1. 支付取消 screen, large muted cancel icon, title exactly “支付已取消”, explanatory text exactly “订单尚未完成支付”, primary button “查看订单”, secondary “返回会员中心”.
2. 支付失败 screen, gentle error icon, title “支付未完成”, text “请先查看订单状态”, primary “查看订单”, secondary “返回会员中心”. Avoid suggesting paying again while payment status is unknown.
3. 我的 screen with expired membership card, title exactly “会员已到期”, text “续费后继续享受免广告保存”, coral button “选择套餐”, list item “购买记录”.
4. 购买记录 screen: status chips and calm list cards; examples exactly “3个月会员  ¥24.00” and “已开通”, “1个月会员  ¥12.00” and “已取消”. Include tiny “示意” text so example records are not actual orders.
Design should be complete and realistic, not a poster; no invented discounts, no extraneous content or English, correct Chinese and numbers.
```

修正提示词：

```text
Edit this existing UI mockup with one tiny textual correction. In the THIRD phone only, the top small grey subtitle below 普通用户 currently says 暂未开通会员; replace it with exactly 会员已到期. Keep every other element, spelling, price, icon, layout, color, dimensions, and all other screens unchanged. Do not add new text.
```

## 保存和常用工具图

参考图：`ui-design-v1.png`。

```text
Use case: ui-mockup. Asset: high fidelity supplemental WeChat mini program mobile UI design sheet for “小七快照拍”. Input image 1 is a style reference only, not an edit target: keep soft coral red, off-white backgrounds, white rounded cards, clean simplified Chinese text and WeChat capsule. Create FOUR complete tall phone screens in a single landscape sheet side by side, large and readable, visual design reference; no editing existing design.
Screen 1: certificate photo result page, a simple anonymous portrait preview, title “照片预览”, chip “普通用户”, helper “观看完整广告后保存”, primary coral button “观看广告并保存”, smaller text link “了解会员”.
Screen 2: same certificate photo result page and matching portrait, chip “会员”, helper “会员免广告保存”, primary coral button “直接保存”.
Screen 3: independent photo background change tool, title “更换底色”, sample portrait on white, background selection circles with exact labels “白色”, “蓝色”, “红色”, button “生成照片”.
Screen 4: format and compression tool, title “格式与压缩”, format selection labels “JPG” and “PNG”, target size input with “目标大小” and “KB”, actual result details with “图片大小”, primary button “转换并保存”.
Keep small status bars, generous touch targets. Do not portray platform ads themselves, fake special offers or extra charges. No English beyond JPG, PNG, KB.
```

修正提示词：

```text
Edit this existing UI mockup while preserving the layout and style. On screen 1, replace the smaller grey text under 观看完整广告后保存 with exactly 完成广告后可保存照片. On screen 2, replace the smaller grey text under 会员免广告保存 with exactly 可直接保存照片, and replace the bottom link 了解会员 with exactly 查看会员权益. Keep all other screens, content, amounts, portraits, colors, icons, composition, text, dimensions and layout unchanged.
```
