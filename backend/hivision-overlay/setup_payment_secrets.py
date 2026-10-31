"""Store WeChat virtual-payment configuration locally without echoing secrets."""
import base64
import getpass
import os
import secrets
import shlex

PATH = '.env.miniapp.payment'


def main():
    if os.path.exists(PATH):
        raise SystemExit('配置文件已存在，未覆盖。如需更换密钥，请先安全备份后手动编辑。')
    offer = input('微信 OfferID [1450701119]：').strip() or '1450701119'
    if not offer.isdigit() or len(offer) > 32:
        raise SystemExit('OfferID 格式无效，未保存。')
    app_key = getpass.getpass('现网 AppKey（输入不显示）：').strip()
    # Generate new values because this mini-program has not enabled message push.
    # They are stored locally and can be entered in the WeChat console later.
    token = secrets.token_hex(16)
    while True:
        aes = base64.b64encode(secrets.token_bytes(32)).decode('ascii').rstrip('=')
        if aes.isalnum():
            break
    if not app_key or len(aes) != 43:
        raise SystemExit('配置不完整，未保存。')
    try:
        if len(base64.b64decode(aes + '=', validate=True)) != 32:
            raise ValueError()
    except ValueError:
        raise SystemExit('EncodingAESKey 格式无效，未保存。')
    fields = {'WECHAT_OFFER_ID': offer, 'WECHAT_PAY_APP_KEY': app_key,
              'WECHAT_PUSH_TOKEN': token, 'WECHAT_PUSH_AES_KEY': aes,
              'IDPHOTO_PAYMENT_ENABLED': 'false'}
    fd = os.open(PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as out:
        for key, value in fields.items():
            out.write(f'export {key}={shlex.quote(value)}\n')
    print('配置已保存。真实收款仍关闭；商品发布和推送配置完成后再开启。')


if __name__ == '__main__':
    main()
