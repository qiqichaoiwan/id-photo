const assert = require('assert');
const fs = require('fs');
const path = require('path');

const src = path.join(__dirname, '..', 'src');
const config = JSON.parse(fs.readFileSync(path.join(src, 'pages.json'), 'utf8'));
const pages = [...config.pages];
for (const pkg of config.subPackages || []) {
  for (const page of pkg.pages) pages.push({...page, path: `${pkg.root}/${page.path}`});
}
assert.strictEqual(new Set(pages.map(page => page.path)).size, pages.length, 'duplicate page route');
for (const page of pages) {
  const file = path.join(src, `${page.path}.vue`);
  assert(fs.existsSync(file), `missing page: ${page.path}`);
  assert.strictEqual(page.style.navigationBarBackgroundColor, '#ffffff', `${page.path}: navigation background`);
  assert.strictEqual(page.style.navigationBarTextStyle, 'black', `${page.path}: navigation text`);
  const content = fs.readFileSync(file, 'utf8');
  const start = content.indexOf('<template>');
  const end = content.lastIndexOf('</template>');
  assert(start >= 0 && end > start, `${page.path}: template missing`);
  const template = content.slice(start, end).replace(/<!--[\s\S]*?-->/g, '');
  assert(!template.includes('-->'), `${page.path}: dangling template comment`);
}
const tokens = fs.readFileSync(path.join(src, 'assets', 'design-tokens.scss'), 'utf8');
for (const token of ['$brand:', '$page:', '$surface:', '$ink:', '$muted:', '$blue:', '$teal:', '$violet:', '$amber:']) {
  assert(tokens.includes(token), `missing design token ${token}`);
}
console.log(`${pages.length} registered pages passed navigation and template consistency checks`);
