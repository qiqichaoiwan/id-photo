# 小七快照拍后端与管理后台

本目录包含可独立部署的完整后端：HivisionIDPhotos 基础源码位于 `hivision-core/`，微信登录、会员、虚拟支付与消息推送、服务监控和会员管理后台位于 `hivision-overlay/`。下载本仓库后不需要再克隆 HivisionIDPhotos；运行 `./bootstrap.sh` 会创建 Python 环境、安装依赖并下载经过 SHA-256 校验的模型文件。

## 来源与许可证

- 基线：[HivisionIDPhotos](https://github.com/Zeyi-Lin/HivisionIDPhotos)，提交 `5c191e2577f14755a69d9df6db415fab23aca484`，完整源码已包含在 `hivision-core/`。
- `hivision-overlay/deploy_api.py` 是接入登录、会员、支付和监控后的 API 入口；其余 `miniapp_*`、`setup_*` 和 `start_*` 文件为本项目扩展。
- 上游项目按 Apache-2.0 发布，许可证副本见 [LICENSE-HIVISION-APACHE-2.0](LICENSE-HIVISION-APACHE-2.0)。本项目根目录的 MIT 许可不替代上游许可。

## 下载后启动

以下命令从本仓库根目录执行：

```sh
cd backend
./bootstrap.sh
./configure.sh
./start-all.sh
```

`bootstrap.sh` 会下载约 275 MB 的模型权重。权重没有放入 GitHub 仓库，因为 BiRefNet 文件超过 GitHub 单文件限制；下载地址、文件大小和 SHA-256 已固定在 `scripts/download_models.py` 中。若只需要较小的 MODNet 模型，可执行：

```sh
./.venv/bin/python scripts/download_models.py --models hivision_modnet modnet_photographic_portrait_matting
```

`configure.sh` 会交互式生成微信 AppSecret、支付 AppKey、推送密钥和后台密码；输入内容不会显示。支付开关默认关闭，必须完成微信商品和消息推送配置后，再在本机 `.env.miniapp.payment` 中明确改为 `true`。如果只需要运行图片 API，仍需创建 `.env.miniapp`，但可以不启动支付接收和后台服务。

`start-all.sh` 启动图片 API（8080）、支付消息接收（8092）和会员后台（8091），默认只监听本机；日志写入 `.runtime/logs/`。`start-gradio.sh` 启动完整 HivisionIDPhotos Gradio 界面（7860）。沙箱使用 `start_miniapp_sandbox.sh` 和独立配置、数据库，不能把沙箱商品用于现网。

如果只需要单独启动服务，可执行：

```sh
./hivision-overlay/start_miniapp_api.sh
./hivision-overlay/start_miniapp_push.sh
./hivision-overlay/start_membership_admin.sh
./start-gradio.sh
```

启动脚本会自动把 `hivision-core` 和 `hivision-overlay` 放入 `PYTHONPATH`，不依赖当前工作目录。

## 一键恢复

仓库根目录的 `scripts/recover_xiaoqi_photo.sh` 用于当前 Mac 的故障恢复。它会先校验后端配置和 Tunnel ingress，再重启图片 API、支付推送、会员后台、可选沙箱和两个照片 Cloudflare Tunnel，最后检查本机与公网健康入口。脚本不改写密钥、会员数据库或 Tunnel 配置：

```sh
./scripts/recover_xiaoqi_photo.sh
./scripts/recover_xiaoqi_photo.sh --check  # 只检查，不重启
```

当前设备也安装了 `recover-xiaoqi-photo` 命令和桌面快捷方式。默认后端目录是 `/Users/qiqi/HivisionIDPhotos`；迁移到其他设备时可用 `IDPHOTO_ROOT`、`CLOUDFLARED_CONFIG` 覆盖路径。

## 后台公网访问

当前地址为 [https://idphoto-admin.ruize.eu.org/](https://idphoto-admin.ruize.eu.org/)。Cloudflare Access 要求已授权的管理员邮箱验证，后台还要求输入 `admin` 和本机设置的密码；Access 会话有效期为 6 小时。管理后台、Cloudflare Tunnel、网络和这台 Mac 均需正常运行。

后台直接监听 `127.0.0.1:8091`，公网主机名保存在后端本地 `.env.miniapp.admin` 的 `IDPHOTO_ADMIN_PUBLIC_HOST` 中。Cloudflare Tunnel 的管理域名规则必须配置 Access JWT 校验，并且 Access 应用要配置限制管理员的策略；应用自身只检查转发头是否存在，不验证 JWT 签名。示例：

```yaml
ingress:
  - hostname: admin.example.com
    service: http://127.0.0.1:8091
    originRequest:
      access:
        required: true
        teamName: "<Cloudflare Access team name>"
        audTag:
          - "<该 Access 应用的 AUD>"
  # 在这里保留原有照片服务和支付回调等规则，最后保留兜底规则。
  - service: http_status:404
```

上例是配置结构，不是可直接替换当前整份配置的文件。更改 Tunnel 配置前应备份并使用 `cloudflared tunnel ingress validate` 校验，再逐个重启使用同一配置的进程；不要将后台端口直接暴露公网，也不要省略 Access 校验。当前入口的匿名访问已检查为跳转到 Access 登录页；完整的邮箱验证码及后台密码登录尚未通过公网实测。

## 定位用户与处理退款申请

小程序用户可在“我的”页面复制会员编号，发给管理员。管理员在后台“用户与会员”输入完整编号查询，核对编号与会员记录后可延长会员自然月或指定到期时间；操作会记录原因，不会创建支付订单。也可以在“订单与退款”的订单详情中选择“查看该用户”。会员编号与微信登录账户绑定，不是设备本地 ID，也不是微信 OpenID；请勿把编号作为身份核验的唯一依据。

用户可在购买记录中提交退款申请；后台“订单与退款”可记录处理进度和给用户的说明，此操作不会发起实际退款或自动更改会员。普通虚拟支付订单应先在微信公众平台的虚拟支付交易订单中核实并处理；Apple 内购订单应引导用户向 Apple 申请，退款结果以相应平台为准。退款后按支付事件及用户实际情况人工核对会员权益。

## 数据和密钥

`.env.miniapp*`、Cloudflare 凭据、管理员密码、会员数据库及身份密钥均不在仓库中。默认数据目录是 `.miniapp_data/`；SQLite 数据库必须与其中的 `identity.key` 作为一组安全备份。备份正在运行的 SQLite 时应使用 SQLite 在线备份功能，恢复前停止相关服务并先备份现有数据。

会员套餐与支付上线状态、已完成的验证和已知限制见 [实施记录](../docs/implementation-v2.md)。
