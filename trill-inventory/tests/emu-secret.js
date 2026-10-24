// Secret-emulator regression test (jsdom): hidden nav, Konami unlock, 7-tap unlock, close
const fs = require('fs'), path = require('path');
const { JSDOM } = require('/tmp/node_modules/jsdom');
let html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
html = require('./fixture-app')(html);
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://example.com/' });
const { window } = dom, doc = window.document;
const $ = id => doc.getElementById(id);
const ok = (name, cond) => console.log((cond ? '  ok    ' : '  FAIL  ') + name) || (!cond && (process.exitCode = 1));
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await sleep(300);
  ok('no visible emulator nav item', !doc.querySelector('[data-nav="emulator"]'));
  ok('emulator panel exists but hidden', !!$('emulator') && !$('emulator').classList.contains('open'));
  ok('drawer has no NES mention', !doc.getElementById('drawerLeft').textContent.includes('NES'));

  // --- Konami code: ArrowUp ArrowUp ArrowDown ArrowDown ArrowLeft ArrowRight ArrowLeft ArrowRight b a
  const KEYCODES = { ArrowUp:38, ArrowDown:40, ArrowLeft:37, ArrowRight:39, b:66, a:65 };
  function key(k){ const ev = new window.KeyboardEvent('keydown', { bubbles:true }); Object.defineProperty(ev, 'keyCode', { value: KEYCODES[k] }); window.dispatchEvent(ev); }
  ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight','b'].forEach(key);
  ok('partial Konami (9/10) stays hidden', !$('emulator').classList.contains('open'));
  key('a');
  await sleep(50);
  ok('full Konami unlocks + opens emulator', $('emulator').classList.contains('open'));
  ok('secret flash shown', $('emuFlash').classList.contains('show'));
  ok('toast announces secret', doc.getElementById('toast').textContent.includes('Secret unlocked'));

  // close via ✕, then re-lock check: single tap on logo must NOT reopen
  $('emuClose').dispatchEvent(new window.MouseEvent('click', { bubbles:true }));
  ok('close button hides emulator', !$('emulator').classList.contains('open'));
  const logo = doc.querySelector('.brand-mark');
  for (let i=0;i<3;i++) logo.dispatchEvent(new window.MouseEvent('click', { bubbles:true }));
  ok('3 logo taps do not unlock', !$('emulator').classList.contains('open'));
  for (let i=0;i<4;i++) logo.dispatchEvent(new window.MouseEvent('click', { bubbles:true }));
  await sleep(50);
  ok('7 total logo taps unlock', $('emulator').classList.contains('open'));
  $('emuClose').dispatchEvent(new window.MouseEvent('click', { bubbles:true }));

  // typing Konami letters in an input must not unlock (scanner guard)
  const inp = doc.createElement('input'); doc.body.appendChild(inp);
  ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight','b','a']
    .forEach(k => { const ev = new window.KeyboardEvent('keydown', { bubbles:true }); Object.defineProperty(ev, 'keyCode', { value: KEYCODES[k] }); inp.dispatchEvent(ev); });
  await sleep(50);
  ok('Konami typed in input ignored', !$('emulator').classList.contains('open'));
  inp.remove();
  console.log(process.exitCode ? 'EMU SECRET TEST FAILED' : 'EMU SECRET TEST OK');
  window.close();
})().catch(e => { console.error(e); process.exit(1); });
