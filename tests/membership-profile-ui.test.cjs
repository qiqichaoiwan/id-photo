// Isolated developer-tools simulation: no real login, network, clipboard or payment.
const assert = require('assert');
const path = require('path');
const automator = require(process.env.WECHAT_AUTOMATOR_PATH || '/tmp/qingcun-wechat-tools/node_modules/miniprogram-automator');
const projectPath = process.env.WECHAT_PROJECT_PATH || path.resolve(__dirname, '../dist/build/mp-weixin');
const cliPath = process.env.WECHAT_CLI_PATH || '/Applications/wechatwebdevtools.app/Contents/MacOS/cli';

(async () => {
  const mini = await automator.launch({cliPath, projectPath, trustProject:true, timeout:60000});
  try {
    await mini.evaluate(() => {
      wx.__profileOriginal = {login:wx.login, request:wx.request, setClipboardData:wx.setClipboardData};
      wx.__profileTest = {fail:true, copied:''};
      wx.login = options => options.success && options.success({code:'isolated-mock'});
      wx.setClipboardData = options => { wx.__profileTest.copied = options.data; options.success && options.success({}); };
      wx.request = options => {
        let data = {}, statusCode = 200;
        if (options.url.endsWith('/auth/wechat')) data = {token:'mock-token', expires_in:3600};
        else if (options.url.endsWith('/membership/status')) data = {active:false, status:'none', expires_at:null};
        else if (options.url.endsWith('/membership/profile')) {
          if (wx.__profileTest.fail) { statusCode = 503; data = {detail:'暂不可用'}; }
          else data = {user_ref:'1234567890abcdef'};
        } else { statusCode = 404; data = {detail:'not found'}; }
        setTimeout(() => { options.success && options.success({statusCode, data}); options.complete && options.complete({statusCode, data}); }, 20);
        return {abort:() => {}};
      };
    });
    const page = await mini.reLaunch('/pages/mine/index');
    await page.waitFor(800);
    assert((await (await page.$('.profile-id')).text()).includes('暂不可用'), '失败状态未显示');
    assert((await (await page.$('.profile-id-action')).text()).includes('重新查询'), '重试入口未显示');
    await mini.evaluate(() => { wx.__profileTest.fail = false; });
    await (await page.$('.profile-id-action')).tap();
    await page.waitFor(500);
    assert((await (await page.$('.profile-id')).text()).includes('1234567890abcdef'), '会员编号未完整显示');
    assert((await (await page.$('.profile-id-action')).text()).includes('复制编号'), '复制入口未显示');
    await (await page.$('.profile-id-action')).tap();
    await page.waitFor(300);
    assert.strictEqual(await mini.evaluate(() => wx.__profileTest.copied), '1234567890abcdef');
    console.log('隔离模拟通过：编号失败提示、重试、显示与复制');
  } finally {
    try { await mini.evaluate(() => { if (wx.__profileOriginal) { wx.login=wx.__profileOriginal.login; wx.request=wx.__profileOriginal.request; wx.setClipboardData=wx.__profileOriginal.setClipboardData; } delete wx.__profileOriginal; delete wx.__profileTest; }); } catch (_) {}
    await mini.disconnect();
  }
})().catch(error => { console.error('隔离模拟失败:', error.message); process.exitCode = 1; });
