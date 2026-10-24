// Verifies the APK's in-WebView camera path: mocked getUserMedia + ZXing decoder.
// Proves that with ZXing bundled, the app takes the "live scanning" branch instead
// of falling back to Demo/Manual.  Run: node tests/native-path.js
const fs = require('fs');
const path = require('path');
let JSDOM;
try { JSDOM = require('jsdom').JSDOM; } catch (e) { JSDOM = require('/tmp/node_modules/jsdom').JSDOM; }

const html = require('./fixture-app')(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'));
const errs = [];
let fails = 0;
const check = (l, c, x) => { if (!c) { fails++; console.log('  FAIL  ' + l + (x ? '  -> ' + x : '')); } else console.log('  ok    ' + l); };

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'https://harrys.local/index.html',
  beforeParse(win) {
    // --- fake camera ---
    const track = {
      kind: 'video',
      stop() { win.__trackStopped = true; },
      getSettings: () => ({ width: 1280, height: 720 }),
      applyConstraints: () => Promise.resolve()
    };
    Object.defineProperty(win.navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: () => Promise.resolve({
          getVideoTracks: () => [track],
          getTracks: () => [track]
        })
      }
    });
    win.HTMLMediaElement.prototype.play = function () { return Promise.resolve(); };

    // --- fake bundled ZXing (same API surface the APK ships) ---
    win.ZXing = {
      BrowserMultiFormatReader: function (hints, opts) {
        this.opts = opts;
        win.__zxOpts = opts;
        win.__zxInstance = this;
      }
    };
    win.ZXing.BrowserMultiFormatReader.prototype.decodeContinuously = function (video, cb) {
      win.__zxVideo = video;
      win.__zxCb = cb;
    };
    win.ZXing.BrowserMultiFormatReader.prototype.reset = function () { win.__zxReset = true; };
  }
});

const { window } = dom;
const doc = window.document;
const $ = id => doc.getElementById(id);
const click = el => el && el.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  window.addEventListener('error', e => errs.push(e.message));
  await sleep(150);

  console.log('\n[1] boot with bundled decoder present');
  check('no boot errors', errs.length === 0, errs.join('; '));

  console.log('\n[2] onboarding -> first scan');
  for (let i = 0; i < 4; i++) { click($('obNext')); await sleep(30); }
  await sleep(400);
  check('camera starts without error banner', !$('camMsg').classList.contains('on'),
        $('camMsgTitle').textContent);
  check('ZXing reader constructed', !!window.__zxInstance);
  check('scan throttle options passed', typeof window.__zxOpts === 'number' && window.__zxInstance.timeBetweenDecodingAttempts > 0);
  check('decoding bound to the <video> element', window.__zxVideo === $('video'));
  check('HUD reports camera live', /Camera live/.test($('hudChips').textContent), $('hudChips').textContent);

  console.log('\n[3] a decoded barcode flows through the normal path');
  window.__zxCb({ getText: () => '049000042566' }, null);
  await sleep(250);
  check('sheet opens for decoded UPC', $('sheetTitle').textContent === 'Coca-Cola Classic',
        $('sheetTitle').textContent);
  check('stock + price rendered', /Remaining in stock/.test($('sheetBody').textContent));

  console.log('\n[4] scanning pauses while reviewing');
  window.__zxCb({ getText: () => '012000001502' }, null);
  await sleep(120);
  check('second decode ignored while sheet is open', $('sheetTitle').textContent === 'Coca-Cola Classic');

  console.log('\n[5] stop camera tears the reader down');
  click($('sheetClose')); await sleep(120);
  click($('btnScan')); await sleep(150);
  check('zxing reader reset', window.__zxReset === true);
  check('camera track stopped', window.__trackStopped === true);
  check('button back to Start camera', $('btnScan').textContent.indexOf('Start camera') > -1);

  console.log('\n' + (fails ? 'FAILURES: ' + fails : 'NATIVE PATH OK') + (errs.length ? ' | errors: ' + errs.join('; ') : ''));
  process.exit(fails ? 1 : 0);
})();
