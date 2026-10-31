const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const ts = require('typescript');
const path = require('path');
const source = fs.readFileSync(path.join(__dirname, '../src/api/service-status.ts'), 'utf8');
const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019 } }).outputText;
function api(response, failed = false) {
  const module = {exports:{}};
  let requested;
  vm.runInNewContext(code, {module, exports:module.exports, Promise, Error,
    require(name) { if(name === '@/config') return {baseUrl:'https://example.test'}; throw Error(name); },
    uni:{request(options){requested=options;failed ? options.fail({}) : options.success(response);}}});
  return {fetch:module.exports.fetchServiceStatus, request:()=>requested};
}
const snapshot = {status:'ok', checked_at:'2026-10-31T00:00:00Z', note:'基础检查', checks:[{id:'photo',name:'照片',state:'ok',detail:'已检查'}]};
(async()=>{
  let test = api({statusCode:200, data:snapshot});
  assert.strictEqual((await test.fetch()).status,'ok');
  assert.strictEqual(test.request().url,'https://example.test/service-status');
  assert.strictEqual(test.request().timeout,8000);
  test = api({statusCode:200,data:{...snapshot,status:'degraded'}});
  assert.strictEqual((await test.fetch()).status,'degraded');
  for(const data of [null,{...snapshot,note:null},{...snapshot,status:'broken'},{...snapshot,checks:[{id:'photo',name:'照片',state:'wrong',detail:'检查'}]}])
    await assert.rejects(api({statusCode:200,data}).fetch());
  await assert.rejects(api({statusCode:503,data:snapshot}).fetch());
  await assert.rejects(api(null,true).fetch(), /暂时无法连接服务/);
  console.log('8 service status scenarios passed');
})().catch(e=>{console.error(e);process.exitCode=1});
