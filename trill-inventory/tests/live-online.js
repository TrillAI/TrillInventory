// LIVE integration check — hits the real public APIs. Needs network access.
// Not part of the default suite (they're offLINE-safe); run manually:
//   node tests/live-online.js
const fs = require('fs');
const path = require('path');
let JSDOM;
try { JSDOM = require('jsdom').JSDOM; } catch (e) { JSDOM = require('/tmp/node_modules/jsdom').JSDOM; }

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://harrys.local/',
  beforeParse(win) {
    win.fetch = (url, opts) => globalThis.fetch(url, opts);   // real network
    win.AbortController = globalThis.AbortController;
    win.HTMLMediaElement.prototype.play = function () { return Promise.resolve(); };
  }
});
const { window } = dom;
const doc = window.document;
const $ = id => doc.getElementById(id);
const click = el => el && el.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  await sleep(150);
  for (let i = 0; i < 4; i++) { click($('obNext')); await sleep(25); }
  await sleep(200);

  click($('btnMenu')); await sleep(150);
  click(doc.querySelector('[data-nav="online"]')); await sleep(350);
  $('onlineUpc').value = '049000042566';       // real Coca-Cola UPC, known to exist upstream
  click(doc.querySelector('[data-act="onlineGo"]'));

  for (let i = 0; i < 24; i++) {               // wait for the throttled request chain
    await sleep(1000);
    if (!/Searching online/.test($('sheetBody').textContent)) break;
  }
  const txt = $('sheetBody').textContent.replace(/\s+/g, ' ').trim();
  console.log('\n--- rendered result ---\n' + txt.slice(0, 900));
  console.log('\n--- parsed signals ---');
  console.log('suggested price shown :', /Suggested shelf price/.test(txt));
  console.log('offers rendered       :', (txt.match(/\$\d+\.\d\d/g) || []).slice(0, 6).join(', ') || 'none');
  console.log('sources listed        :', (txt.match(/UPCITEMDB|OPEN PRICES|OPEN FOOD FACTS/gi) || []).join(', ') || 'none');
  process.exit(0);
})();
