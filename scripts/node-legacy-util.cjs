// The UniApp 2.x build chain still calls a few util type helpers removed from
// recent Node releases.  Keep the compatibility shim local to build commands;
// it does not change application runtime code.
const util = require('node:util');

if (!util.isRegExp) util.isRegExp = value => value instanceof RegExp;
if (!util.isString) util.isString = value => typeof value === 'string';
if (!util.isObject) util.isObject = value => value !== null && typeof value === 'object';
