const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ts = require('typescript');

const root = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'src/components/PhotoCamera.vue'), 'utf8');
const camera = source.match(/<camera\b[\s\S]*?<\/camera>/);
assert(camera, 'shared camera component is missing');
assert(camera[0].includes('@initdone="onCameraReady"'), 'WeChat camera initialization event is missing');
assert(!/<(?:svg|view|text|u-icon)\b/.test(camera[0]), 'camera overlay must use supported cover components');
for (const name of ['guide-head', 'guide-eye-line', 'guide-shoulder-left', 'guide-shoulder-right', 'camera-close', 'camera-guide-toggle']) {
  assert(camera[0].includes(name), `missing camera guide or control: ${name}`);
}
assert(camera[0].includes('v-if="guideEnabled"'), 'guide visibility must follow toggle');
assert(camera[0].includes("guideEnabled ? '开' : '关'"), 'toggle must show its current state');
assert(source.includes('辅助线不会出现在照片中'));
for (const name of ['album', 'switch']) {
  const asset = `/static/camera/${name}.png`;
  assert(camera[0].includes(asset));
  assert(fs.existsSync(path.join(root, 'src', asset)));
}
const scenes = {
  'src/pages/photo/index.vue': true,
  'src/pages/matting/index.vue': true,
  'src/pages/matting/upload.vue': true,
  'src/pages/watermark/index.vue': false,
  'src/pages/watermark/upload.vue': false,
  'src/pages/convert/index.vue': false
};
for (const [file, guideOn] of Object.entries(scenes)) {
  const pageSource = fs.readFileSync(path.join(root, file), 'utf8');
  assert(pageSource.includes('<PhotoCamera v-if="showCamera"'), `${file} must use shared camera`);
  assert(!/<camera\b|<svg\b|createCameraContext\(/.test(pageSource), `${file} still has a private camera`);
  assert.strictEqual(!pageSource.includes(':guide-initially-enabled="false"'), guideOn, `${file} guide default`);
  assert(pageSource.includes('@select="onCameraSelect"') && pageSource.includes('@close="showCamera = false"'));
}

const decorator = () => () => {};
const defaultModules = {
  vue: { __esModule: true, default: class Vue { $emit(...args) { this.emitted.push(args); } } },
  'vue-property-decorator': { Component: () => target => target, Prop: decorator },
  'vuex-class': { Getter: decorator, Mutation: decorator },
  '@/api/photo': { GeneratePhoto() {} }, '@/api/matting': { humanMatting() {} },
  '@/api/watermark': { addWatermark() {} }, '@/model/Colors': { Colors: [] },
  '@/components/LoadingOverlay.vue': { __esModule: true, default: {} },
  '@/components/PhotoCamera.vue': { __esModule: true, default: {} },
  '@/utils/image-file': { writeTemporaryImage() {}, removeTemporaryImage() {} },
  '@/utils/request': { uploadFile() {} }, '@/utils/ad-manager': { adManager: {} },
  '@/api/membership': { getMembershipStatus() {} }
};
let currentCapture, cameraCalls = 0, albumCalls = 0, toasts = [], settings, album, actions, selection, navigated;
const uni = {
  createCameraContext() { return { takePhoto(options) { currentCapture = options; cameraCalls++; } }; },
  showToast(options) { toasts.push(options.title); },
  openSetting(options) { settings = options; },
  chooseImage(options) { selection = options; },
  chooseMedia(options) { album = options; albumCalls++; },
  showActionSheet(options) { actions = options; },
  navigateTo(options) { navigated = options.url; }
};
function load(file) {
  const text = fs.readFileSync(path.join(root, file), 'utf8');
  const script = text.match(/<script lang="ts">([\s\S]*?)<\/script>/)[1];
  const code = ts.transpileModule(script, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019, experimentalDecorators: true } }).outputText;
  const moduleObject = { exports: {} };
  vm.runInNewContext(code, { module: moduleObject, exports: moduleObject.exports, require(name) {
    if (name in defaultModules) return defaultModules[name];
    throw Error(`unexpected import ${name}`);
  }, uni, wx: {}, Promise, Error, Number, Math, JSON, console, decodeURIComponent, encodeURIComponent });
  return moduleObject.exports.default;
}
const Camera = load('src/components/PhotoCamera.vue');
function createCamera(guide = true, position = 'front') {
  const instance = new Camera(); instance.emitted = []; instance.guideInitiallyEnabled = guide; instance.initialPosition = position; instance.created(); return instance;
}
const page = createCamera();
assert.strictEqual(page.guideEnabled, true);
page.toggleGuide(); assert.strictEqual(page.guideEnabled, false);
page.toggleGuide(); assert.strictEqual(page.guideEnabled, true);
assert.strictEqual(createCamera(false, 'back').guideEnabled, false);
assert.strictEqual(createCamera(false, 'back').cameraPosition, 'back');
page.capturePhoto(); assert.strictEqual(cameraCalls, 0, 'do not capture before initialization');
assert(toasts.includes('相机正在启动，请稍候'));
page.onCameraReady(); page.capturePhoto(); page.capturePhoto();
assert.strictEqual(cameraCalls, 1, 'prevent duplicate capture');
page.switchCamera(); assert.strictEqual(page.cameraPosition, 'front', 'do not switch while capturing');
currentCapture.fail(); assert.strictEqual(page.capturing, false);
page.switchCamera(); assert.strictEqual(page.cameraPosition, 'back');
page.toggleGuide(); page.capturePhoto(); currentCapture.success({ tempImagePath: '/tmp/photo.jpg' });
assert.strictEqual(page.showCamera, false); assert.strictEqual(page.showCapturePreview, true);
page.retakePhoto(); assert.strictEqual(page.showCamera, true); assert.strictEqual(page.guideEnabled, false, 'retake retains toggle state');
page.onCameraReady(); page.capturePhoto(); currentCapture.success({ tempImagePath: '/tmp/second.jpg' });
page.confirmCapture(); assert.deepStrictEqual(page.emitted.pop(), ['select', '/tmp/second.jpg']);
page.confirmCapture(); assert.strictEqual(page.emitted.length, 0, 'prevent duplicate confirmation');

page.openCamera(); page.onCameraReady(); page.capturePhoto();
const staleCapture = currentCapture; page.closeCamera(); staleCapture.success({ tempImagePath: '/tmp/stale.jpg' });
assert.strictEqual(page.showCapturePreview, false, 'closed camera must ignore a late callback');
page.openCamera(); page.onCameraReady(); page.capturePhoto();
const interruptedCapture = currentCapture; page.onCameraStop(); assert(page.cameraError.includes('中断'));
interruptedCapture.success({ tempImagePath: '/tmp/interrupted.jpg' }); assert.strictEqual(page.showCapturePreview, false);
page.retryCamera(); page.onCameraError(); assert(page.cameraError.includes('相机权限'));
page.openCameraSettings(); settings.success({ authSetting: { 'scope.camera': true } });
assert.strictEqual(page.cameraError, ''); assert.strictEqual(page.cameraReady, false);
page.onCameraError(); page.openCameraSettings(); const lateSettings = settings; page.closeCamera();
lateSettings.success({ authSetting: { 'scope.camera': true } }); assert.strictEqual(page.showCamera, false);

page.openCamera(); page.chooseFromAlbum(); assert.strictEqual(page.showCamera, false);
page.chooseFromAlbum(); assert.strictEqual(albumCalls, 1, 'prevent duplicate album pickers');
album.fail({ errMsg: 'cancel' }); assert.strictEqual(page.showCamera, true, 'cancel returns to camera');
page.chooseFromAlbum(); album.success({ tempFiles: [{ tempFilePath: '/tmp/album.jpg' }] });
assert.deepStrictEqual(page.emitted.pop(), ['select', '/tmp/album.jpg']);
page.openCamera(); page.chooseFromAlbum(); const lateAlbum = album; page.beforeDestroy();
lateAlbum.success({ tempFiles: [{ tempFilePath: '/tmp/late.jpg' }] });
assert(!page.emitted.some(event => event[1] === '/tmp/late.jpg'), 'disposed camera ignores late album results');

for (const file of ['src/pages/photo/index.vue', 'src/pages/matting/index.vue', 'src/pages/watermark/index.vue']) {
  const Page = load(file); const instance = new Page(); let processed = 0;
  instance.confirmSelect = () => { processed++; };
  instance.showCamera = true; instance.onCameraSelect('/tmp/chosen.jpg');
  assert.strictEqual(instance.showCamera, false); assert.strictEqual(instance.imagePath, '/tmp/chosen.jpg'); assert.strictEqual(processed, 1, file);
}
for (const kind of ['matting', 'watermark']) {
  const Upload = load(`src/pages/${kind}/upload.vue`); const upload = new Upload();
  upload.onCameraSelect('/tmp/old upload.jpg'); assert.strictEqual(upload.show, true);
  upload.confirmSelect(); assert(navigated.includes(encodeURIComponent('/tmp/old upload.jpg')));
  const Main = load(`src/pages/${kind}/index.vue`); const main = new Main();
  main.onLoad({ image: encodeURIComponent('/tmp/old upload.jpg') });
  assert.strictEqual(main.imagePath, '/tmp/old upload.jpg', 'legacy uploaded photo must reach target page');
  assert.strictEqual(kind === 'matting' ? main.show : main.preselectedImage, true);
}
const Watermark = load('src/pages/watermark/index.vue'); const watermark = new Watermark();
watermark.chooseImage('camera'); assert.strictEqual(watermark.showCamera, false); assert(toasts.includes('请先输入水印文字'));
watermark.watermarkText = '测试'; watermark.chooseImage('camera'); assert.strictEqual(watermark.showCamera, true);
const Convert = load('src/pages/convert/index.vue'); const convert = new Convert();
let cleared = 0; convert.clearResult = () => { cleared++; };
convert.choosePhoto(); actions.success({ tapIndex: 0 }); assert.strictEqual(convert.showCamera, true);
convert.onCameraSelect('/tmp/convert.jpg'); assert.strictEqual(convert.sourcePath, '/tmp/convert.jpg'); assert.strictEqual(cleared, 1);
convert.choosePhoto(); actions.success({ tapIndex: 1 }); assert.deepStrictEqual(Array.from(selection.sourceType), ['album']);
selection.success({ tempFilePaths: ['/tmp/album-convert.png'] }); assert.strictEqual(convert.sourcePath, '/tmp/album-convert.png'); assert.strictEqual(cleared, 2);
console.log('shared camera, all six entries, guide toggle, preview, album, errors and business handoffs passed');
