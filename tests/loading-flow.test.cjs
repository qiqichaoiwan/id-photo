const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ts = require('typescript');

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function loadComponent(file, modules, uni) {
  const source = fs.readFileSync(path.join(__dirname, '..', file), 'utf8');
  const script = source.match(/<script lang="ts">([\s\S]*?)<\/script>/);
  assert(script, `missing TypeScript in ${file}`);
  const code = ts.transpileModule(script[1], { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019, experimentalDecorators: true } }).outputText;
  const mod = { exports: {} };
  const decorator = () => () => {};
  const common = {
    vue: { __esModule: true, default: class Vue {} },
    'vue-property-decorator': { Component: () => target => target, Prop: decorator, Watch: decorator },
    'vuex-class': { Getter: decorator, Mutation: decorator },
    '@/components/LoadingOverlay.vue': { __esModule: true, default: {} },
    '@/components/PhotoCamera.vue': { __esModule: true, default: {} },
  };
  vm.runInNewContext(code, { module: mod, exports: mod.exports, require(name) {
    if (name in modules) return modules[name];
    if (name in common) return common[name];
    throw Error(`unexpected import ${name}`);
  }, uni, Promise, Error, Number, Math, JSON, console });
  return mod.exports.default;
}
const noop = () => {};
const tick = () => new Promise(resolve => setImmediate(resolve));

async function resultFlow(file) {
  let ad = deferred(), saved = null, modal = 0;
  const uni = { saveImageToPhotosAlbum(options) { saved = options; }, showToast: noop, showModal() { modal++; } };
  const Page = loadComponent(file, {
    '@/utils/ad-manager': { adManager: { show: () => ad.promise } },
    '@/utils/image-file': { writeTemporaryImage: async () => '/tmp/test.png', removeTemporaryImage: noop }
  }, uni);
  const page = new Page(); page.imagePath = '/tmp/source.png';
  let operation = page.saveImage();
  assert.strictEqual(page.saving, true); assert.strictEqual(page.processing, false, 'do not cover the ad');
  ad.resolve(false); await operation;
  assert.strictEqual(page.saving, false); assert.strictEqual(page.processing, false); assert.strictEqual(saved, null);

  ad = deferred(); operation = page.saveImage(); ad.resolve(true); await tick();
  assert.strictEqual(page.processing, true, 'show feedback while saving');
  assert(saved); saved.success(); await operation;
  assert.strictEqual(page.saving, false); assert.strictEqual(page.processing, false); assert.strictEqual(modal, 0);

  saved = null; ad = deferred(); operation = page.saveImage(); ad.resolve(true); await tick();
  saved.fail({errMsg:'saveImageToPhotosAlbum:fail'}); await operation;
  assert.strictEqual(page.processing, false); assert.strictEqual(page.saving, false); assert.strictEqual(modal, 1);
  ad = deferred(); operation = page.saveImage(); ad.reject(Error('ad unavailable')); await operation;
  assert.strictEqual(page.processing, false); assert.strictEqual(page.saving, false); assert.strictEqual(modal, 2);
}

async function convertFlow() {
  let upload = deferred(), ad = deferred(), saved = null, modal = 0;
  const Page = loadComponent('src/pages/convert/index.vue', {
    '@/utils/request': { uploadFile: () => upload.promise },
    '@/utils/image-file': { writeTemporaryImage: async () => '/tmp/result.png', removeTemporaryImage: noop },
    '@/utils/ad-manager': { adManager: { authorize: () => ad.promise } }, '@/api/membership': { getMembershipStatus: noop }
  }, { showModal() { modal++; }, showToast: noop, saveImageToPhotosAlbum(options) { saved = options; } });
  const page = new Page(); page.sourcePath = '/tmp/source.png';
  let operation = page.convert();
  assert.strictEqual(page.processing, true); assert.strictEqual(page.busy, true);
  upload.resolve({image_base64:'test',width:20,height:30,size_bytes:100,target_met:true}); await operation;
  assert.strictEqual(page.resultPath, '/tmp/result.png'); assert.strictEqual(page.processing, false); assert.strictEqual(page.busy, false);
  upload = deferred(); operation = page.convert(); upload.reject(Error('offline')); await operation;
  assert.strictEqual(page.processing, false); assert.strictEqual(page.busy, false); assert.strictEqual(modal, 1);
  operation = page.save();
  assert.strictEqual(page.busy, true); assert.strictEqual(page.processing, false, 'do not cover the ad');
  ad.resolve(null); await operation;
  assert.strictEqual(page.busy, false); assert.strictEqual(page.processing, false); assert.strictEqual(saved, null);
  ad = deferred(); operation = page.save(); ad.resolve('member'); await tick();
  assert.strictEqual(page.saving, true); assert.strictEqual(page.processing, true, 'show feedback while saving');
  saved.success(); await operation;
  assert.strictEqual(page.saving, false); assert.strictEqual(page.processing, false); assert.strictEqual(page.busy, false);
  saved = null; ad = deferred(); operation = page.save(); ad.resolve('member'); await tick();
  saved.fail(); await operation;
  assert.strictEqual(page.saving, false); assert.strictEqual(page.processing, false); assert.strictEqual(page.busy, false); assert.strictEqual(modal, 2);
}

async function electronicPreviewFlow() {
  const photo = {id:'one',name:'测试照片',hdBase64:'data:image/png;base64,AA=='};
  let stored = [photo], writes = 0, opened = [], removed = [];
  const Page = loadComponent('src/pages/electronic/index.vue', {
    '@/utils/electronic-photo': {ElectronicPhotoManager:{getAll:()=>stored}},
    '@/utils/ad-manager': {adManager:{}},
    '@/utils/image-file': {writeTemporaryImage:async()=>{writes++;return '/tmp/preview.png'},removeTemporaryImage:p=>removed.push(p)},
    '@/components/InlineState.vue': {__esModule:true,default:{}}
  }, {previewImage(options){opened.push(options.current)},showToast:noop});
  const page = new Page(); page.loadPhotos();
  await page.selectPhoto(photo); await page.selectPhoto(photo);
  assert.strictEqual(writes, 1); assert.deepStrictEqual(opened, ['/tmp/preview.png','/tmp/preview.png']);
  stored = []; page.loadPhotos();
  assert(removed.includes('/tmp/preview.png'), 'removed photos must release their preview file');
}

async function photoFlow() {
  let ad = deferred(), color = deferred(), saved = null, modal = 0;
  const Page = loadComponent('src/pages/photo/edit.vue', {
    '@/api/photo': { AddBackgroudColor: () => color.promise, GenerateLayoutPhoto: noop },
    '@/utils/electronic-photo': { ElectronicPhotoManager: {} },
    '@/utils/storage': { __esModule:true, default:{recordPhotoCreated:noop} },
    '@/utils/ad-manager': { adManager: { authorize: () => ad.promise } },
    '@/api/membership': { getMembershipStatus: noop },
    '@/utils/image-file': { writeTemporaryImage: async () => '/tmp/result.png', removeTemporaryImage: noop }
  }, { saveImageToPhotosAlbum(options) { saved=options; }, showToast:noop, showModal() { modal++; } });
  const page = new Page();
  page.photoPath = {base64Path:'/tmp/source.png',base64HDPath:'/tmp/source.png'};
  page.photoSize = {name:'test',dpi:300,pxWidth:295,pxHeight:413};
  let operation = page.save();
  assert.strictEqual(page.busy, true); assert.strictEqual(page.processing, false, 'do not cover the ad');
  ad.resolve(null); await operation;
  assert.strictEqual(page.busy, false); assert.strictEqual(page.processing, false);
  ad = deferred(); operation = page.save(); ad.resolve('ad'); await tick();
  assert.strictEqual(page.processing, true); color.resolve({image_base64:'test'}); await tick();
  assert.strictEqual(page.processing, false); assert(saved); saved.success(); await operation;
  assert.strictEqual(page.busy, false); assert.strictEqual(page.processing, false); assert.strictEqual(modal, 0);
  ad = deferred(); color = deferred(); operation = page.save(); ad.resolve('member'); await tick();
  assert.strictEqual(page.processing, true); color.reject(Error('offline')); await operation;
  assert.strictEqual(page.busy, false); assert.strictEqual(page.processing, false); assert.strictEqual(modal, 1);
}

(async () => {
  const Overlay = loadComponent('src/components/LoadingOverlay.vue', {}, {});
  const overlay = new Overlay();
  for (const [input, expected] of [[-2,0],[42.6,43],[140,100],['invalid',0]]) {
    overlay.progress = input; assert.strictEqual(overlay.safeProgress, expected);
  }
  await resultFlow('src/pages/matting/result.vue');
  await resultFlow('src/pages/watermark/result.vue');
  await convertFlow(); await photoFlow(); await electronicPreviewFlow();
  console.log('loading feedback and electronic photo preview flows passed');
})().catch(error => { console.error(error); process.exitCode=1; });
