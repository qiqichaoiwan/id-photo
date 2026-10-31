# UI 风格调整 V2：生成提示词

参考图为用户提供的证件照主流程设计稿；使用内置 imagegen 工具生成。

## 会员购买流程（ui-membership-purchase-v2.png）

```text
Use case: ui-mockup. Make a refined high-fidelity Chinese WeChat mini program UI concept for 小七快照拍. Image 1 is the user's visual reference and the strongest design authority: match its three-phone presentation, precise layout density and generous breathing room, off-white/light grey backgrounds, white surfaces, fine grey outlines, subtle soft shadow, restrained warm coral red for selected elements and the primary button, black headings with grey explanatory text, balanced Chinese system typography, consistent modest-radius rounded cards, line icons, header and WeChat capsule, and practical tool-app feel. The result should look like additional real screens from exactly the same application, not a redesign of the reference. Three complete phone screenshots side-by-side, front-on, on the same warm grey canvas as the reference, with no extra device frames. Use large legible Chinese, natural alignment, professional spacing and visual hierarchy. Avoid oversized crowns, red alarm banners, cartoon output photos, gold premium styling, fake discounts, gratuitous badges, highly saturated backgrounds or exaggerated decorations. Show tiny Chinese text clearly; every phone screen must be complete.
Panel 1, title “会员中心”: elegant small pale-coral card styled like the reference home banner, with modest photo-card illustration and text “会员免广告保存”. Below, show a clean section “选择会员套餐”, with three equal tiles exactly: “1个月  ¥12”, “3个月  ¥24”, “12个月  ¥68”. The 3-month tile has a thin coral outline. Below show one clean row “会员权益” with “免广告保存”, and a short note “单次购买，不自动续费” and “按自然月计算，续费时长叠加”. Bottom primary button exactly “开通会员 ¥24”.
Panel 2, title “确认订单”: card with selected “3个月会员” and “¥24.00”, then quiet aligned rows “会员时长 3个月”, “会员权益 免广告保存”, “续费规则 时长叠加”, “购买方式 单次购买”. Show “不自动续费” and a bottom primary button “确认支付 ¥24.00”.
Panel 3, title “我的”: an understated user header and a pale white-to-coral membership card reading “会员已开通”, “有效期至 2027-01-30（示意）”, “会员免广告保存”, and a small quiet “手动续费” action. Below are simple rows “会员中心”, “购买记录”, “使用帮助”, and the same bottom navigation as the reference. Do not imply automatic renewal or add other paid benefits.
```

## 会员状态（ui-membership-states-v2.png）

```text
Use case: ui-mockup. Make a refined high-fidelity Chinese WeChat mini program UI concept for 小七快照拍. Image 1 is the user's visual reference and the strongest design authority: match its three-phone presentation, precise layout density and generous breathing room, off-white/light grey backgrounds, white surfaces, fine grey outlines, subtle soft shadow, restrained warm coral red for selected elements and the primary button, black headings with grey explanatory text, balanced Chinese system typography, consistent modest-radius rounded cards, line icons, header and WeChat capsule, and practical tool-app feel. The result should look like additional real screens from exactly the same application, not a redesign of the reference. Three complete phone screenshots side-by-side, front-on, on the same warm grey canvas as the reference, with no extra device frames. Use large legible Chinese, natural alignment, professional spacing and visual hierarchy. Avoid oversized crowns, red alarm banners, cartoon output photos, gold premium styling, fake discounts, gratuitous badges, highly saturated backgrounds or exaggerated decorations. Show tiny Chinese text clearly; every phone screen must be complete.
Panel 1, title “订单状态”: an understated small clock symbol, clean header “支付确认中”, grey helper “正在确认支付结果，请勿重复付款”, a simple light card with “订单已创建”, “等待支付确认”, “会员权益开通”; bottom buttons “刷新状态” and “查看订单”.
Panel 2, title “订单状态”: a small calm circular neutral icon, clear message “支付已取消”, helper “订单尚未完成支付”, buttons “查看订单” and “返回会员中心”. Do not suggest payment succeeded or imply automatic retry.
Panel 3, title “我的”: muted user identity, subtle pale card “会员已到期”, helper “续费后继续享受免广告保存”, button “选择套餐”, rows “会员中心”, “购买记录”, and the same bottom navigation as the reference.
Use restrained visual weight with lots of useful breathing room, secondary actions in outline or text. Each state must be distinct and truthful.
```

## 结果保存与图片工具（ui-save-tools-v2.png）

```text
Use case: ui-mockup. Make a refined high-fidelity Chinese WeChat mini program UI concept for 小七快照拍. Image 1 is the user's visual reference and the strongest design authority: match its three-phone presentation, precise layout density and generous breathing room, off-white/light grey backgrounds, white surfaces, fine grey outlines, subtle soft shadow, restrained warm coral red for selected elements and the primary button, black headings with grey explanatory text, balanced Chinese system typography, consistent modest-radius rounded cards, line icons, header and WeChat capsule, and practical tool-app feel. The result should look like additional real screens from exactly the same application, not a redesign of the reference. Three complete phone screenshots side-by-side, front-on, on the same warm grey canvas as the reference, with no extra device frames. Use large legible Chinese, natural alignment, professional spacing and visual hierarchy. Avoid oversized crowns, red alarm banners, cartoon output photos, gold premium styling, fake discounts, gratuitous badges, highly saturated backgrounds or exaggerated decorations. Show tiny Chinese text clearly; every phone screen must be complete.
Panel 1, title “编辑证件照”: show a lifelike professional ID portrait photo like the reference's rightmost page, not an illustration. Below, a clean row of specification “一寸照” and “295×413 px”, the same white, blue, red background color selectors as the reference and an output method row. A discreet helper reads “观看完整广告后保存” and the fixed bottom coral button reads “观看广告并保存”.
Panel 2, title “编辑证件照”: the same visual and layout using the same realistic photo and selectors, but a discreet helper reads “会员免广告保存” and the fixed bottom coral button reads “直接保存”. Keep the distinction explicit and avoid an oversized membership banner.
Panel 3, title “格式与压缩”: a small realistic photo preview, then a white form with “图片格式” choices “JPG” and “PNG”, “目标大小” with “200 KB”, and a subtle results section reading “图片大小 182 KB” and “图片尺寸 295×413 px”. Bottom coral primary button “转换并保存”. The example is only a design illustration.
No cartoon faces in actual photo output. No extra charges, no unconfirmed special quality claims.
```

## 后台套餐管理（ui-membership-admin-v2.png）

```text
Use case: ui-mockup. Create one refined realistic desktop admin webpage for 小七快照拍. Image 1 is the user's mobile UI style reference: translate its visual design to a professional desktop dashboard using the same coral red, off-white background, white cards, subtle cool grey dividers, dark neutral Chinese type, clean line icons, quiet spacing, with no heavy colored banners. One front-on whole desktop interface, not a collage. Left sidebar: “总览”, “套餐管理” selected, “会员管理”, “订单管理”, “系统设置”. Main title “会员套餐管理”, action “新建套餐”. Clean table with columns “套餐名称”, “时长”, “价格”, “微信商品”, “状态”, “操作”, and rows exactly “1个月会员 / 1个月 / ¥12.00 / 待关联 / 草稿 / 编辑”, “3个月会员 / 3个月 / ¥24.00 / 待关联 / 草稿 / 编辑”, “12个月会员 / 12个月 / ¥68.00 / 待关联 / 草稿 / 编辑”. Right-side editing panel with “编辑套餐”, “套餐名称 3个月会员”, “会员时长 3个月”, “价格 ¥24.00”, “期限规则 按自然月”, “会员权益 免广告保存”, “微信道具 ID 待关联”, and a small note “核对微信商品和价格后上架”; primary button “保存草稿”. Make 免广告保存 a fixed read-only entitlement rather than an unchecked checkbox. Draft states are examples. Avoid invented profits, fake dashboards, excessive gradient or decorative crowns.
```


## 局部校正提示词

### 会员页文案校正

```text
Edit this existing Chinese UI design sheet. On the FIRST phone only, in the pale membership banner under the headline 会员免广告保存, replace the small subtitle 高清电子照，纯净无广告 with the exact text 保存照片，无需观看广告. This is the only change. Preserve every other phone, text, accurate prices 12/24/68, illustrations, icons, hierarchy, whitespace, composition, dimensions, colors and layout exactly.
```

### 格式工具广告提示校正

```text
Edit this existing Chinese UI design sheet. On the THIRD phone only, add a small unobtrusive grey line of text immediately above the red bottom button: 普通用户观看广告后保存. This is the only change; keep the output values, portrait, layout, buttons and all other screen text unchanged. Preserve the two other phones exactly. Match the subtle grey caption styling under the second phone's output section.
```

### 后台时长输入框

```text
Edit this desktop UI mockup only in the right-hand 编辑套餐 panel: change the 会员时长 control from a dropdown showing 3个月 to an editable numeric input showing 3 with a fixed suffix 个月, no dropdown arrow. This shows the admin can enter a custom number of natural months. Keep every other element, every price, copy, color, typeface, proportions, and composition unchanged.
```

