// Torch behaviour + advanced barcode recognition tests.
// Run: node tests/torch-recognition.js
const fs = require('fs');
const path = require('path');
let JSDOM;
try { JSDOM = require('jsdom').JSDOM; } catch (e) { JSDOM = require('/tmp/node_modules/jsdom').JSDOM; }

const html = require('./fixture-app')(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'));
let fails = 0;
const check = (l, c, x) => { if (!c) { fails++; console.log('  FAIL  ' + l + (x !== undefined ? '  -> ' + x : '')); } else console.log('  ok    ' + l); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

// every torch applyConstraints call, in order
const torchCalls = [];
const lastTorch = () => torchCalls.length ? torchCalls[torchCalls.length - 1] : null;

const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://harrys.local/',
  beforeParse(win) {
    const track = {
      kind: 'video',
      stop() {},
      getSettings: () => ({ width: 1280, height: 720 }),
      getCapabilities: () => ({ torch: true }),
      applyConstraints(c) {
        const adv = c && c.advanced && c.advanced[0];
        if (adv) torchCalls.push({ torch: !!adv.torch, at: Date.now() });
        return Promise.resolve();
      }
    };
    Object.defineProperty(win.navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia: () => Promise.resolve({ getVideoTracks: () => [track], getTracks: () => [track] }) }
    });
    win.HTMLMediaElement.prototype.play = function () { return Promise.resolve(); };
    // fake bundled ZXing with the API surface the app uses
    win.ZXing = {
      DecodeHintType: { POSSIBLE_FORMATS: 0, TRY_HARDER: 1 },
      BarcodeFormat: { UPC_A: 1, UPC_E: 2, EAN_13: 3, EAN_8: 4, CODE_39: 5, CODE_93: 6,
                       CODE_128: 7, ITF: 8, CODABAR: 9, QR_CODE: 10, DATA_MATRIX: 11,
                       PDF_417: 12, AZTEC: 13 },
      BrowserMultiFormatReader: function (hints, opts) { win.__hints = hints; win.__opts = opts; win.__zx = this; }
    };
    win.ZXing.BrowserMultiFormatReader.prototype.decodeContinuously = function (v, cb) { win.__cb = cb; };
    win.ZXing.BrowserMultiFormatReader.prototype.reset = function () {};
  }
});
const { window } = dom;
const doc = window.document;
const $ = id => doc.getElementById(id);
const click = el => el && el.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));

(async () => {
  await sleep(150);
  for (let i = 0; i < 4; i++) { click($('obNext')); await sleep(25); }
  await sleep(500);

  console.log('\n[1] torch is ON while the scanner is armed');
  check('torch turned on at camera start', lastTorch() && lastTorch().torch === true, JSON.stringify(torchCalls));

  console.log('\n[2] it blanks on a scan, then relights when ready');
  torchCalls.length = 0;
  window.__cb({ getText: () => '049000042566', getBarcodeFormat: () => 3 }, null);
  await sleep(120);
  check('torch switched OFF on read', lastTorch() && lastTorch().torch === false, JSON.stringify(torchCalls));
  check('sheet opened for review', $('sheet').classList.contains('on'));
  await sleep(500);
  check('stays off while reviewing (not armed)', lastTorch() && lastTorch().torch === false, JSON.stringify(torchCalls));

  click($('sheetClose'));
  await sleep(300);
  check('relights once the scanner is ready again', lastTorch() && lastTorch().torch === true, JSON.stringify(torchCalls));

  console.log('\n[3] steady-off setting leaves the torch alone');
  window.__S_off = true;
  click($('btnSettings')); await sleep(200);
  const sw = doc.querySelector('#settingsBody [data-toggle="torchSteady"]');
  check('steady torch setting exists', !!sw);
  click(sw); await sleep(150);           // turn it off
  click($('scrim')); await sleep(250);
  torchCalls.length = 0;
  window.__cb({ getText: () => '070847811169', getBarcodeFormat: () => 3 }, null);
  await sleep(600);
  const after = torchCalls.filter(c => c.torch === true);
  check('no steady relight when the setting is off', after.length === 0, JSON.stringify(torchCalls));
  // restore
  click($('btnSettings')); await sleep(200);
  click(doc.querySelector('#settingsBody [data-toggle="torchSteady"]')); await sleep(120);
  click($('scrim')); await sleep(200);
  click($('sheetClose')); await sleep(250);

  console.log('\n[4] advanced recognition is configurable');
  click($('btnSettings')); await sleep(200);
  const adv = doc.querySelector('#settingsBody [data-toggle="advScan"]');
  const twoD = doc.querySelector('#settingsBody [data-toggle="scan2D"]');
  check('advanced recognition toggle present', !!adv);
  check('2D symbology toggle present', !!twoD);
  check('advanced is on by default', adv.getAttribute('aria-checked') === 'true');
  check('2D is off by default', twoD.getAttribute('aria-checked') === 'false');
  click($('scrim')); await sleep(200);

  console.log('\n[5] decoder hints');
  check('ZXing reader got a hints map', !!window.__hints && typeof window.__hints.get === 'function');
  const formats = window.__hints.get(0);
  check('retail formats requested', Array.isArray(formats) && formats.length >= 9, formats && formats.length);
  check('TRY_HARDER enabled when advanced', window.__hints.get(1) === true);
  check('faster scan cadence in advanced mode', window.__zx.timeBetweenDecodingAttempts === 110, window.__zx.timeBetweenDecodingAttempts);

  console.log('\n[6] UPC-E and EAN-13 fold onto the catalog entry');
  // EAN normalisation UI coverage; UPC-E expansion is tested directly in lookup-retailers.js.
  window.__cb({ getText: () => '012000003455', getBarcodeFormat: () => 1 }, null);
  await sleep(250);
  const upcaKey = $('sheetTitle').textContent;
  click($('sheetClose')); await sleep(250);
  // EAN-13 form of the same product (leading zero)
  window.__cb({ getText: () => '0049000042566', getBarcodeFormat: () => 3 }, null);
  await sleep(250);
  check('EAN-13 with leading zero matches the UPC-A entry',
        $('sheetTitle').textContent === 'Coca-Cola Classic', $('sheetTitle').textContent);
  check('symbology shown to the user', /EAN-13/.test($('sheetSub').textContent), $('sheetSub').textContent);
  check('raw reading shown when normalised', /0049000042566/.test($('sheetSub').textContent), $('sheetSub').textContent);

  console.log('\n[7] the same product scanned in two symbologies is one stock line');
  const inv = JSON.parse(window.localStorage.getItem('hs.inventory') || '{}');
  addQty(3);
  await sleep(200);
  click($('sheetClose'));
  // the 3s duplicate cooldown is correct app behaviour — wait it out so the
  // second read of the same product is accepted
  await sleep(3300);
  window.__cb({ getText: () => '049000042566', getBarcodeFormat: () => 1 }, null);
  await sleep(250);
  addQty(2);
  await sleep(200);
  const inv2 = JSON.parse(window.localStorage.getItem('hs.inventory') || '{}');
  const keys = Object.keys(inv2).filter(k => k.indexOf('49000042566') > -1);
  check('one canonical key only', keys.length === 1, JSON.stringify(Object.keys(inv2)));
  check('quantities accumulated', inv2[keys[0]] && inv2[keys[0]].qty >= 5, inv2[keys[0]] && inv2[keys[0]].qty);

  function addQty(n) {
    for (let i = 1; i < n; i++) click(doc.querySelector('[data-act="inc"]'));
    click(doc.querySelector('#sheetFoot [data-act="add"]'));
  }

  console.log('\n[8] the copy change');
  check("footer reads 'built for Inventory'", /built for Inventory/.test(html));
  check("no longer says Harry's Gas Stations in the footer",
        !/built for Harry/.test(html));

  console.log('\n' + (fails ? 'FAILURES: ' + fails : 'TORCH + RECOGNITION OK'));
  process.exit(fails ? 1 : 0);
})();
