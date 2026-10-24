// Deep emulator test (jsdom + REAL jsnes + synthetic valid iNES ROMs):
// ROM picking validation, iNES header parsing -> real UI data, attract takeover,
// multi-touch controls, keyboard, gamepad, live FPS, start/stop of the frame loop.
const fs = require('fs'), path = require('path');
const { JSDOM } = require('/tmp/node_modules/jsdom');
const root = path.join(__dirname, '..');
let html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const jsnesSrc = fs.readFileSync(path.join(root, 'android/vendor/jsnes.min.js'), 'utf8');
html = html.replace('<script>', '<script>' + jsnesSrc + '\n</script><script>'); // inject emulator lib like build.sh does
html = require('./fixture-app')(html);

const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://example.com/',
  beforeParse(window) {
    // Fake 2D canvas (jsdom has none) that records putImageData calls.
    window.__putCount = 0;
    window.HTMLCanvasElement.prototype.getContext = function () {
      const self = this;
      return { canvas: self,
        createImageData: (w, h) => ({ width: w, height: h, data: new Uint8ClampedArray(w * h * 4) }),
        putImageData: () => { window.__putCount++; },
        fillRect: () => {}, fillText: () => {}, drawImage: () => {} };
    };
    // Stubbed standard-mapping gamepad the test can manipulate.
    window.__pad = { connected: true, id: 'DeepTest Pad 3000', axes: [0, 0],
      buttons: Array.from({ length: 17 }, () => ({ pressed: false, value: 0 })) };
    Object.defineProperty(window.navigator, 'getGamepads', { configurable: true, value: () => [window.__pad] });
  }
});
const { window } = dom, doc = window.document;
const $ = id => doc.getElementById(id);
let failures = 0;
const ok = (name, cond) => { console.log((cond ? '  ok    ' : '  FAIL  ') + name); if (!cond) failures++; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function until(fn, what, ms = 4000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { if (fn()) return true; await sleep(40); }
  console.log('  (timeout waiting: ' + what + ')'); return false;
}
function buildRom(prgBanks, chrBanks, mapper) {
  const prg = prgBanks * 16384, chr = chrBanks * 8192;
  const buf = new Uint8Array(16 + prg + chr);
  buf.set([0x4E, 0x45, 0x53, 0x1A, prgBanks, chrBanks, (mapper & 0x0F) << 4, mapper & 0xF0, 0, 0, 0, 0, 0, 0, 0, 0]);
  buf.fill(0xEA, 16, 16 + prg);                    // NOP sled
  buf[16 + prg - 4] = 0x00; buf[16 + prg - 3] = 0x80; // reset vector -> $8000
  return buf;
}
function pickFile(input, bytes, name) {
  const file = new window.File([bytes], name, { type: 'application/octet-stream' });
  Object.defineProperty(input, 'files', { configurable: true, value: [file] });
  input.dispatchEvent(new window.Event('change', { bubbles: true }));
}
function key(code, type) {
  const ev = new window.KeyboardEvent(type || 'keydown', { bubbles: true, cancelable: true });
  Object.defineProperty(ev, 'keyCode', { value: code });
  window.dispatchEvent(ev);
}
function pev(el, type, id) {
  const ev = new window.MouseEvent(type, { bubbles: true, cancelable: true });
  Object.defineProperty(ev, 'pointerId', { value: id });
  el.dispatchEvent(ev);
}
const btn = name => doc.querySelector('[data-btn="' + name + '"]');

(async () => {
  await sleep(350);
  console.log('[setup]');
  ok('jsnes library loaded', typeof window.jsnes !== 'undefined' && !!window.jsnes.NES);
  ok('ROM input accepts .nes', ($('emuRomFile').getAttribute('accept') || '').includes('.nes'));
  ok('chip starts as real empty state', $('emuChip').textContent === 'No cartridge inserted');
  ok('empty-cartridge overlay visible before ROM', !$('emuEmpty').classList.contains('hid'));
  ok('controller status shows the connected pad (real data)', $('emuPad').textContent.includes('DeepTest Pad 3000'));

  console.log('[open via Konami]');
  [38, 38, 40, 40, 37, 39, 37, 39, 66, 65].forEach(c => key(c));
  ok('emulator opens', await until(() => $('emulator').classList.contains('open'), 'panel open'));
  ok('controls hidden until a ROM loads', $('emuControls').hidden === true);

  console.log('[ROM load -> real parsed data]');
  pickFile($('emuRomFile'), buildRom(2, 1, 0), 'demo_game.nes');
  ok('chip shows parsed header data', await until(() => /Mapper 0/.test($('emuChip').textContent), 'chip'));
  ok('chip shows PRG/CHR sizes', /PRG 32 KB/.test($('emuChip').textContent) && /CHR 8 KB/.test($('emuChip').textContent));
  ok('chip shows file size', /KB · Mapper/.test($('emuChip').textContent));
  ok('title comes from the ROM filename', $('emuTitle').textContent === 'demo game');
  ok('empty overlay hides after load', $('emuEmpty').classList.contains('hid'));
  ok('attract overlay shows after load', !$('emuAttract').classList.contains('hid'));
  ok('controls appear after load', $('emuControls').hidden === false);
  ok('frames are rendering (putImageData)', await until(() => window.__putCount > 5, 'frames'));
  ok('live FPS readout appears', await until(() => /\d+ FPS/.test($('emuFps').textContent), 'fps', 3000));

  console.log('[touch takeover + multi-touch]');
  pev(btn('start'), 'pointerdown', 1);
  ok('first touch dismisses attract (takeover)', $('emuAttract').classList.contains('hid'));
  ok('START button shows pressed state', btn('start').classList.contains('on'));
  pev(btn('start'), 'pointerup', 1);
  ok('START releases', !btn('start').classList.contains('on'));
  pev(btn('right'), 'pointerdown', 11);
  pev(btn('a'), 'pointerdown', 12);
  ok('multi-touch: Right and A held together', btn('right').classList.contains('on') && btn('a').classList.contains('on'));
  pev(btn('right'), 'pointerup', 11);
  ok('releasing Right keeps A held', !btn('right').classList.contains('on') && btn('a').classList.contains('on'));
  pev(btn('a'), 'pointerup', 12);
  ok('all touch buttons released', !btn('a').classList.contains('on'));

  console.log('[keyboard]');
  key(39); ok('arrow key lights Right', btn('right').classList.contains('on'));
  key(39, 'keyup'); ok('keyup releases Right', !btn('right').classList.contains('on'));
  key(90); ok('Z lights A', btn('a').classList.contains('on'));
  key(90, 'keyup'); ok('Z release clears A', !btn('a').classList.contains('on'));

  console.log('[gamepad]');
  window.__pad.buttons[15].pressed = true; // D-pad right
  ok('gamepad Right presses on-screen Right', await until(() => btn('right').classList.contains('on'), 'pad right', 2500));
  window.__pad.buttons[15].pressed = false;
  ok('gamepad release clears Right', await until(() => !btn('right').classList.contains('on'), 'pad release', 2500));
  window.__pad.buttons[0].pressed = true; // A
  ok('gamepad A presses A', await until(() => btn('a').classList.contains('on'), 'pad A', 2500));
  window.__pad.buttons[0].pressed = false;
  await sleep(150);

  console.log('[ROM picker validation]');
  pickFile($('emuRomFile'), new Uint8Array([1, 2, 3]), 'holiday-photo.jpg');
  await sleep(120);
  ok('photo rejected with a real message', /Not a ROM/.test($('emuStatus').textContent));
  pickFile($('emuRomFile'), new Uint8Array(64), 'fake.nes');
  await sleep(120);
  ok('bad .nes rejected (no iNES header)', /no iNES header/.test($('emuStatus').textContent) && $('emuChip').textContent === 'Invalid ROM');
  ok('previous good ROM still running', window.__putCount > 20);

  console.log('[Mario-named ROM gets Mario treatment]');
  pickFile($('emuRomFile'), buildRom(2, 1, 0), 'Super Mario Bros.nes');
  ok('title becomes Super Mario Bros.', await until(() => $('emuTitle').textContent === 'Super Mario Bros.', 'mario title'));
  ok('attract title is Mario', $('emuAttTitle').textContent === 'SUPER MARIO BROS.');
  ok('attract restarted for the new ROM', !$('emuAttract').classList.contains('hid'));
  ok('World 1-1 hint restored', /World 1-1/.test($('emuAttStart').textContent));

  console.log('[close stops the loop]');
  const frozen = await (async () => { await sleep(120); return window.__putCount; })();
  $('emuClose').dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
  await sleep(300);
  ok('panel closed', !$('emulator').classList.contains('open'));
  ok('no frames render after close', window.__putCount <= frozen + 1);

  console.log(failures ? '\nEMU DEEP TEST: ' + failures + ' FAILURE(S)' : '\nEMU DEEP TEST OK');
  process.exitCode = failures ? 1 : 0;
  window.close();
})().catch(e => { console.error(e); process.exit(1); });
