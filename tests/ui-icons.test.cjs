const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const iconSource = fs.readFileSync(path.join(root, 'node_modules/uview-ui/components/u-icon/icons.js'), 'utf8');
const knownIcons = new Set(Array.from(iconSource.matchAll(/'uicon-([^']+)'/g), match => match[1]));
const nativeToastIcons = new Set(['success', 'error', 'loading', 'none']);
const problems = [];

function scan(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const filename = path.join(directory, entry.name);
    if (entry.isDirectory()) { scan(filename); continue; }
    if (!entry.name.endsWith('.vue')) continue;
    const source = fs.readFileSync(filename, 'utf8');
    const check = name => {
      if (!knownIcons.has(name)) problems.push(`${path.relative(root, filename)}: ${name}`);
    };
    for (const tag of source.matchAll(/<(u-icon|InlineState)\b([^>]*)>/g)) {
      const attribute = tag[1] === 'u-icon' ? 'name' : 'icon';
      const match = tag[2].match(new RegExp(`(?:^|\\s)${attribute}\\s*=\\s*["']([^"']+)["']`));
      if (match) check(match[1]);
      const conditional = tag[2].match(/\?\s*'([^']+)'\s*:\s*'([^']+)'/);
      if (conditional) { check(conditional[1]); check(conditional[2]); }
    }
    for (const match of source.matchAll(/\bicon\s*:\s*'([^']+)'/g)) {
      if (!nativeToastIcons.has(match[1])) check(match[1]);
    }
  }
}

scan(path.join(root, 'src'));
assert.deepStrictEqual(problems, [], `Unsupported uView icons:\n${problems.join('\n')}`);
console.log('UI icon names: all static and listed icons exist in uView');
