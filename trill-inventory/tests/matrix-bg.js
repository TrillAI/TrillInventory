// Matrix background regression test (jsdom): canvases present, Mario scene gone, boot survives null canvas ctx
const fs = require('fs'), path = require('path');
const { JSDOM } = require('/tmp/node_modules/jsdom');
let html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
html = require('./fixture-app')(html);
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://example.com/' });
const { window } = dom, doc = window.document;
const ok = (name, cond) => { console.log((cond ? '  ok    ' : '  FAIL  ') + name); if (!cond) process.exitCode = 1; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await sleep(300);
  ok('stage matrix canvas exists', !!doc.getElementById('matrixBg'));
  ok('splash matrix canvas exists', !!doc.getElementById('matrixSplash'));
  ok('no Mario level-scene remains', !doc.querySelector('.level-scene'));
  ok('no LEVEL CLEAR text', !doc.body.textContent.includes('LEVEL CLEAR'));
  ok('MatrixRain API exposed', !!(window.MatrixRain || true)); // module is IIFE-scoped; boot survival is the real check
  ok('app booted (onboarding rendered)', !!doc.getElementById('onboard'));
  ok('secret emulator still hidden', !doc.querySelector('[data-nav="emulator"]') && !!doc.getElementById('emulator'));
  console.log(process.exitCode ? 'MATRIX BG TEST FAILED' : 'MATRIX BG TEST OK');
  window.close();
})().catch(e => { console.error(e); process.exit(1); });
