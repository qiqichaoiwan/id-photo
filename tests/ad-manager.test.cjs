// Isolated contract checks: no WeChat ad, user data, or network is accessed.
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const ts = require('typescript');
const path = require('path');

const source = fs.readFileSync(path.join(__dirname, '../src/utils/ad-manager.ts'), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019 } }).outputText;

function setup({membership, ad}) {
  const notifications = [];
  let adCreations = 0;
  const module = { exports: {} };
  const sandbox = { module, exports: module.exports, Promise, setTimeout,
    uni: { showToast: message => notifications.push(message.title) },
    wx: ad ? { createRewardedVideoAd: () => { adCreations++; return ad; } } : {},
    require(name) {
      if (name === '@/config') return { adConfig: { rewardedVideoAdUnitId: 'test-unit' } };
      if (name === '@/api/membership') return { getMembershipStatus: membership };
      throw new Error('Unexpected import: ' + name);
    }
  };
  vm.runInNewContext(compiled, sandbox);
  return { manager: module.exports.adManager, notifications, creations: () => adCreations };
}

function video({ended = true, failFirst = false, failLoad = false} = {}) {
  let close, error, calls = 0, loaded = 0, removed = 0;
  return {
    onClose: fn => { close = fn; }, offClose: () => { removed++; close = null; },
    onError: fn => { error = fn; }, offError: () => { error = null; },
    load: () => { loaded++; return failLoad ? Promise.reject(new Error('load failed')) : Promise.resolve(); },
    show: () => {
      calls++;
      if (failFirst && calls === 1) return Promise.reject(new Error('show failed'));
      setTimeout(() => { if (close) close({isEnded: ended}); }, 5);
      return Promise.resolve();
    },
    stats: () => ({calls, loaded, removed})
  };
}

(async () => {
  let ad = video(), env = setup({membership: async () => ({active: true}), ad});
  assert.strictEqual(await env.manager.authorize(), 'member');
  assert.strictEqual(env.creations(), 0);

  ad = video(); env = setup({membership: async () => ({active: false}), ad});
  assert.strictEqual(await env.manager.authorize(), 'ad');
  assert.strictEqual(ad.stats().removed, 1);

  ad = video({ended: false}); env = setup({membership: async () => ({active: false}), ad});
  assert.strictEqual(await env.manager.authorize(), null);
  assert(env.notifications.includes('请看完广告后再继续'));

  ad = video(); env = setup({membership: async () => {throw Error('offline');}, ad});
  assert.strictEqual(await env.manager.authorize(), 'ad');

  ad = video({failFirst: true}); env = setup({membership: async () => ({active: false}), ad});
  assert.strictEqual(await env.manager.authorize(), 'ad');
  assert.strictEqual(ad.stats().loaded, 1);
  assert.strictEqual(ad.stats().calls, 2);

  ad = video({failFirst: true, failLoad: true}); env = setup({membership: async () => ({active: false}), ad});
  assert.strictEqual(await env.manager.authorize(), null);
  assert(env.notifications.includes('广告暂不可用，请稍后重试'));

  env = setup({membership: async () => ({active: false})});
  assert.strictEqual(await env.manager.authorize(), null);
  assert(env.notifications.includes('广告暂不可用，请稍后重试'));

  ad = video(); env = setup({membership: async () => ({active: false}), ad});
  const first = env.manager.authorize(), second = env.manager.authorize();
  assert.strictEqual(await second, null);
  assert.strictEqual(await first, 'ad');
  console.log('8 ad and membership scenarios passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
