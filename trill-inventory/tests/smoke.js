// Headless smoke test for Harry's Scan (jsdom). Run: node tests/smoke.js
const fs = require('fs');
const path = require('path');
let JSDOM;
try { JSDOM = require('jsdom').JSDOM; }
catch (e) { JSDOM = require('/tmp/node_modules/jsdom').JSDOM; }

const file = path.join(__dirname, '..', 'index.html');
const html = require('./fixture-app')(fs.readFileSync(file, 'utf8'));
const errs = [];
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://example.com/' });
const { window } = dom;
window.addEventListener('error', e => errs.push('ERR: ' + e.message));
const doc = window.document;
const $ = id => doc.getElementById(id);
const click = el => el && el.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
const sleep = ms => new Promise(r => setTimeout(r, ms));
let fails = 0;
function check(label, cond, extra) {
  if (!cond) { fails++; console.log('  FAIL  ' + label + (extra ? '  -> ' + extra : '')); }
  else console.log('  ok    ' + label);
}

(async () => {
  await sleep(150);
  console.log('\n[1] boot & onboarding');
  check('no boot errors', errs.length === 0, errs.join('; '));
  check('onboarding shown on first run', !$('onboard').classList.contains('off'));
  for (let i = 0; i < 4; i++) { click($('obNext')); await sleep(25); }
  await sleep(150);
  check('onboarding dismissed', $('onboard').classList.contains('off'));
  check('starts with empty inventory', window.localStorage.getItem('hs.inventory') === null);
  check('camera fallback message shown (no camera here)', $('camMsg').classList.contains('on'));

  console.log('\n[2] manual scan -> detail sheet');
  click($('btnManual')); await sleep(60);
  check('manual entry sheet opens', $('sheetTitle').textContent === 'Manual entry');
  $('manualUpc').value = '049000042566';
  click(doc.querySelector('#sheetFoot [data-act="manualGo"]')); await sleep(250);
  const txt = () => $('sheetBody').textContent;
  check('product resolved', $('sheetTitle').textContent === 'Coca-Cola Classic', $('sheetTitle').textContent);
  check('shows remaining stock', /Remaining in stock/.test(txt()));
  check('shows shelf price', /2\.49/.test(txt()));
  check('shows order recommendation', /Order recommendation/.test(txt()));
  check('shows deep details', /Supplier/.test(txt()) && /Shelf location/.test(txt()));

  console.log('\n[3] quantity controls & cataloging');
  click(doc.querySelector('[data-act="quick"][data-n="6"]')); await sleep(20);
  check('quick +6 sets pending qty', $('qtyVal').textContent === '6');
  click(doc.querySelector('[data-act="inc"]')); await sleep(20);
  click(doc.querySelector('[data-act="inc"]')); await sleep(20);
  check('stepper increments', $('qtyVal').textContent === '8');
  click(doc.querySelector('#sheetFoot [data-act="add"]')); await sleep(150);
  const inv = JSON.parse(window.localStorage.getItem('hs.inventory') || '{}');
  check('inventory persisted 8 units', inv['049000042566'] && inv['049000042566'].qty === 8, JSON.stringify(inv['049000042566']));
  check('scan-next button appears after add', !!doc.querySelector('#sheetFoot [data-act="scannext"]'));

  console.log('\n[4] unknown barcode -> custom product');
  click($('btnManual')); await sleep(50);
  $('manualUpc').value = '999999999999';
  click(doc.querySelector('#sheetFoot [data-act="manualGo"]')); await sleep(250);
  check('unknown product form opens', /Unknown/.test($('sheetTitle').textContent));
  $('newName').value = 'Test Cola'; $('newPrice').value = '1.99'; $('newCost').value = '0.90';
  click(doc.querySelector('#sheetFoot [data-act="saveNew"]')); await sleep(250);
  check('custom product resolved after save', $('sheetTitle').textContent === 'Test Cola', $('sheetTitle').textContent);

  console.log('\n[5] main menu views');
  click($('btnMenu')); await sleep(120);
  check('left drawer opens', doc.getElementById('app').getAttribute('data-drawer') === 'left');
  click(doc.querySelector('[data-nav="inventory"]')); await sleep(350);
  check('inventory lists 2 products', doc.querySelectorAll('#invList .list-row').length === 2);
  click($('btnMenu')); await sleep(120);
  click(doc.querySelector('[data-nav="restock"]')); await sleep(350);
  check('restock list populated', doc.querySelectorAll('#sheetBody .list-row').length > 0);
  click($('btnMenu')); await sleep(120);
  click(doc.querySelector('[data-nav="history"]')); await sleep(350);
  check('history has entries', doc.querySelectorAll('#sheetBody .list-row').length === 2);

  console.log('\n[6] settings');
  click($('btnSettings')); await sleep(140);
  check('settings drawer opens', doc.getElementById('app').getAttribute('data-drawer') === 'right');
  check('7 setting categories', doc.querySelectorAll('#settingsBody details.setgroup').length === 7);
  check('56 setting rows', doc.querySelectorAll('#settingsBody .set-row').length === 56, doc.querySelectorAll('#settingsBody .set-row').length);
  const sw = doc.querySelector('#settingsBody [data-toggle="beep"]');
  click(sw); await sleep(40);
  check('toggle persists', JSON.parse(window.localStorage.getItem('hs.settings')).beep === false);
  const tc = doc.querySelector('#settingsBody [data-theme-pick="ocean"]');
  click(tc); await sleep(60);
  check('theme picker applies a palette',
        doc.documentElement.style.getPropertyValue('--accent') === '#38bdf8',
        doc.documentElement.style.getPropertyValue('--accent'));

  console.log('\n[7] CSV import');
  click($('btnMenu')); await sleep(120);
  click(doc.querySelector('[data-nav="import"]')); await sleep(400);
  check('import sheet opens', $('sheetTitle').textContent === 'Import & export');
  $('csvText').value = 'upc,name,price,cost,units_per_case\n123123123123,Zap Energy,3.99,2.10,12\n049000042566,Coke Updated,2.79,1.40,24';
  click(doc.querySelector('[data-action="csvDo"]')); await sleep(300);
  check('import reports 1 new + 1 updated', /1 new, 1 updated/.test($('toast').textContent), $('toast').textContent);
  click($('btnManual')); await sleep(60);
  $('manualUpc').value = '123123123123';
  click(doc.querySelector('#sheetFoot [data-act="manualGo"]')); await sleep(250);
  check('imported product resolvable', $('sheetTitle').textContent === 'Zap Energy');
  check('imported price applied', /3\.99/.test(txt()));

  console.log('\n[8] hardware-back hook');
  check('__hsHandleBack defined', typeof window.__hsHandleBack === 'function');
  click($('sheetClose')); await sleep(120);
  check('back hook returns false when nothing open', window.__hsHandleBack() === false);

  console.log('\n' + (fails ? 'FAILURES: ' + fails : 'ALL CHECKS PASSED') + (errs.length ? ' | errors: ' + errs.join('; ') : ''));
  process.exit(fails ? 1 : 0);
})();
