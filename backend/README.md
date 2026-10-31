# 小七快照拍后端与管理后台

本目录保存微信小程序所用的后端扩展：图片 API 的适配、微信登录、会员、虚拟支付与消息推送、服务监控，以及会员管理后台。当前运行环境位于独立的 HivisionIDPhotos 工作目录；这里是可用于重建该扩展的代码副本，不会自动更新正在运行的服务。

## 来源与许可证

- 基线：[HivisionIDPhotos](https://github.com/Zeyi-Lin/HivisionIDPhotos)，提交 `5c191e2577f14755a69d9df6db415fab23aca484`。
- `hivision-overlay/deploy_api.py`、`requirements.txt` 和 `.gitignore` 基于该版本修改；其余 `miniapp_*`、`setup_*` 和 `start_*` 文件为本项目扩展。
- 上游项目按 Apache-2.0 发布，许可证副本见 [LICENSE-HIVISION-APACHE-2.0](LICENSE-HIVISION-APACHE-2.0)。本项目根目录的 MIT 许可不替代上游许可。

## 在新目录重建

以下命令从本仓库根目录执行，创建新的后端目录，不能直接覆盖现有运行中的后端：

```sh
export IDPHOTO_MINIAPP_REPO="$(pwd)"
git clone https://github.com/Zeyi-Lin/HivisionIDPhotos.git ../HivisionIDPhotos-new
git -C ../HivisionIDPhotos-new checkout --detach 5c191e2577f14755a69d9df6db415fab23aca484
cp -R "$IDPHOTO_MINIAPP_REPO/backend/hivision-overlay/." ../HivisionIDPhotos-new/
cd ../HivisionIDPhotos-new
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-app.txt uvicorn python-multipart pillow
```

按上游文档准备所需模型权重。再为全新环境运行以下配置脚本，密钥和密码在本机输入：

```sh
.venv/bin/python setup_miniapp_secrets.py
.venv/bin/python setup_payment_secrets.py
.venv/bin/python setup_membership_admin.py
```

`setup_miniapp_secrets.py` 使用本小程序的 AppID；给其他小程序部署时须修改该脚本中的 AppID。支付配置脚本默认关闭现网支付，并生成新的消息推送 Token 和 AES Key。微信端商品、消息推送及支付配置需要使用对应环境的实际参数；已有环境应保留原配置，不要重新生成后直接覆盖。设置管理员密码的脚本会改写当前数据目录的管理员密码，运行前应确认目标环境。

通过 `./start_miniapp_api.sh`、`./start_miniapp_push.sh` 和 `./start_membership_admin.sh` 分别启动 API、推送与后台。进程默认仅监听本机，具体生产部署还需要持续运行、HTTPS、反向代理、监控和备份。沙箱通过独立配置和数据库运行，不能把沙箱商品用于现网。

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

## 数据和密钥

`.env.miniapp*`、Cloudflare 凭据、管理员密码、会员数据库及身份密钥均不在仓库中。默认数据目录是 `.miniapp_data/`；SQLite 数据库必须与其中的 `identity.key` 作为一组安全备份。备份正在运行的 SQLite 时应使用 SQLite 在线备份功能，恢复前停止相关服务并先备份现有数据。

会员套餐与支付上线状态、已完成的验证和已知限制见 [实施记录](../docs/implementation-v2.md)。
