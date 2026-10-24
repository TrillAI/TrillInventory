// "Name it, then choose from options" tests — mocked network.
// Run: node tests/picker.js
const fs = require('fs');
const path = require('path');
let JSDOM;
try { JSDOM = require('jsdom').JSDOM; } catch (e) { JSDOM = require('/tmp/node_modules/jsdom').JSDOM; }

const html = require('./fixture-app')(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'));
let fails = 0;
const check = (l, c, x) => { if (!c) { fails++; console.log('  FAIL  ' + l + (x !== undefined ? '  -> ' + x : '')); } else console.log('  ok    ' + l); };

const searchCalls = [];
let searchMode = 'hit';

const SEARCH_ITEMS = [
  { upc: '0070847024033', title: 'Monster Energy Original 16 fl oz Can', brand: 'Monster Energy',
    category: 'Food, Beverages & Tobacco > Beverages > Sports & Energy Drinks', size: '',
    lowest_recorded_price: 2.49, highest_recorded_price: 4.99,
    images: ['https://example.test/monster.jpg'],
    offers: [{ merchant: 'Target', price: 2.99 }] },
  { upc: '0070847024040', title: '(12 cans) Monster Energy Zero Ultra 16 fl oz', brand: 'Monster Energy',
    category: 'Food, Beverages & Tobacco > Beverages > Energy Drinks', size: '',
    lowest_recorded_price: 29.99, highest_recorded_price: 39.99, images: [], offers: [] },
  // deliberately bad data: a 24-pack listing priced like a single can
  { upc: '0070847024057', title: 'Monster Energy Original 16 Ounce (24 Pack)', brand: 'Monster Energy',
    category: 'Food, Beverages & Tobacco > Beverages > Energy Drinks', size: '',
    lowest_recorded_price: 6.00, highest_recorded_price: 9.00, images: [], offers: [] }
];

function mockFetch(url) {
  if (url.indexOf('/search') > -1) {
    searchCalls.push(url);
    if (searchMode === 'fail') return Promise.resolve({ ok: false, status: 500, text: () => Promise.resolve('') });
    return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve(JSON.stringify({ code: 'OK', total: 2, items: SEARCH_ITEMS })) });
  }
  if (url.indexOf('upcitemdb') > -1) {
    return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve(JSON.stringify({ code: 'OK', items: [] })) });
  }
  return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve('{"items":[]}') });
}

const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://harrys.local/',
  beforeParse(win) {
    win.localStorage.setItem('hs.lookupSchema','2');
    // Pre-seed the lookup cache so the unknown-scan flow doesn't walk all three
    // throttled providers before showing the naming form.
    win.localStorage.setItem('hs.netcache', JSON.stringify({
      '085555555555': { upc: '085555555555', identity: null, offers: [], oldOffers: [], sources: [], at: Date.now() }
    }));
    win.fetch = (url) => mockFetch(url);
    win.AbortController = class { constructor(){ this.signal = {}; } abort(){} };
    win.HTMLMediaElement.prototype.play = function () { return Promise.resolve(); };
  }
});
const { window } = dom;
const doc = window.document;
const $ = id => doc.getElementById(id);
const click = el => el && el.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
const type = (el, v) => { el.value = v; el.dispatchEvent(new window.Event('input', { bubbles: true })); };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const opts = () => Array.from(doc.querySelectorAll('#matchList [data-match]'));

(async () => {
  await sleep(150);
  for (let i = 0; i < 4; i++) { click($('obNext')); await sleep(25); }
  await sleep(200);

  console.log('\n[1] unknown scan -> name it -> options appear automatically');
  click($('btnManual')); await sleep(60);
  $('manualUpc').value = '085555555555';           // not in catalog, valid-ish
  click(doc.querySelector('#sheetFoot [data-act="manualGo"]')); await sleep(1200);
  check('naming form shown', !!$('newName'));
  check('picker present but empty', $('matchList') && opts().length === 0);
  type($('newName'), 'Monster Energy');
  await sleep(1400);                                // debounce 750ms + request
  check('search was triggered by typing', searchCalls.length > 0, JSON.stringify(searchCalls.slice(-1)));
  check('candidate options rendered', opts().length >= 2, opts().length);
  check('option shows brand + price', /Monster Energy/.test($('matchList').textContent) && /2\.49/.test($('matchList').textContent));
  check('multi-pack title cleaned', /Monster Energy Zero Ultra/.test($('matchList').textContent));

  console.log('\n[2] choosing an option fills the form');
  click(opts()[0]); await sleep(120);
  check('name filled from match', $('newName').value.indexOf('Monster Energy Original') > -1, $('newName').value);
  check('brand filled', $('newBrand').value === 'Monster Energy', $('newBrand').value);
  check('size derived from title', /16 fl oz/.test($('newSize').value), $('newSize').value);
  check('category guessed', $('newCat').value === 'Energy Drinks', $('newCat').value);
  check('unverified search price not copied', $('newPrice').value === '', $('newPrice').value);
  check('unit cost is not fabricated', $('newCost').value === '', $('newCost').value);
  check('selection marked in list', doc.querySelector('#matchList .opt.sel') !== null);

  console.log('\n[2b] multipack listing is converted to a per-unit price');
  click(opts()[1]); await sleep(150);
  check('12-pack detected in title', /12-pack/.test($('matchList').textContent), $('matchList').textContent.slice(0, 80));
  check('multipack reference not silently applied', $('newPrice').value === '', $('newPrice').value);
  check('listing units do not overwrite case pack', $('newPack').value === '1', $('newPack').value);
  check('parenthetical pack stripped from name', $('newName').value.indexOf('(12 cans)') === -1, $('newName').value);
  click(opts()[0]); await sleep(150);   // back to the single can for the remaining checks
  check('single-unit reference still needs manual price', $('newPrice').value === '', $('newPrice').value);

  console.log('\n[2c] implausible multipack price is rejected');
  click(opts()[2]); await sleep(150);
  check('nonsense unit price not written', $('newPrice').value === '', JSON.stringify($('newPrice').value));
  check('user is warned why', /actual shelf price/i.test($('toast').textContent), $('toast').textContent);
  check('identity still applied', /Monster Energy Original/.test($('newName').value), $('newName').value);
  check('empty parens stripped from title', !/\(\s*\)/.test($('newName').value), $('newName').value);
  click(opts()[0]); await sleep(150);

  console.log('\n[3] saving keeps the match metadata and manually entered price');
  $('newPrice').value = '2.49';
  click(doc.querySelector('#sheetFoot [data-act="saveNew"]')); await sleep(300);
  const cat = JSON.parse(window.localStorage.getItem('hs.catalog') || '[]');
  const saved = cat[cat.length - 1];
  check('saved with chosen name', /Monster Energy Original/.test(saved.name), saved.name);
  check('unverified name-search thumbnail not stored', saved.image === '', saved.image);
  check('matched barcode stored', saved.matchCode === '0070847024033', saved.matchCode);
  check('size stored on product', /16 fl oz/.test(saved.size), saved.size);
  check('price stored', saved.price === 2.49, saved.price);
  check('image is not guessed from name search', !doc.querySelector('#sheetBody img.pimg'));

  console.log('\n[4] update info on an existing product');
  click($('sheetClose')); await sleep(150);
  click($('btnMenu')); await sleep(120);
  click(doc.querySelector('[data-nav="catalog"]')); await sleep(300);
  click(doc.querySelector('[data-cat="049000042566"]')); await sleep(300);
  check('update-info button offered', !!doc.querySelector('[data-act="updateInfo"]'));
  const origName = $('sheetTitle').textContent;
  let chosenTitle = '';
  click(doc.querySelector('[data-act="updateInfo"]')); await sleep(1500);
  check('update sheet opened', $('sheetTitle').textContent === 'Update product info', $('sheetTitle').textContent);
  const uOpts = opts();
  check('options listed for existing product', uOpts.length >= 2, uOpts.length);
  chosenTitle = uOpts[1].querySelector('.oi b').textContent.trim();
  click(uOpts[1]); await sleep(150);
  check('option can be selected', doc.querySelectorAll('#matchList .opt.sel').length === 1);
  check('apply buttons available', !!doc.querySelector('#sheetFoot [data-act="applyInfo"]'));
  click(doc.querySelector('#sheetFoot [data-act="applyInfo"]')); await sleep(400);
  const cat2 = JSON.parse(window.localStorage.getItem('hs.catalog') || '[]');
  const coke = cat2.find(x => x.upc === '049000042566');
  check('override written with chosen title', !!coke && coke.name === chosenTitle, coke && coke.name);
  check('result sheet now titled with new name', $('sheetTitle').textContent === chosenTitle, $('sheetTitle').textContent);
  check('price NOT changed without opt-in', coke && coke.price === 2.49, coke && coke.price);
  check('rest of the product survived the override', /Cold Beverages|Energy/.test($('sheetBody').textContent));

  console.log('\n[5] search failure falls back to local catalog');
  searchMode = 'fail';
  click($('sheetClose')); await sleep(150);
  click($('btnMenu')); await sleep(120);
  click(doc.querySelector('[data-nav="addproduct"]')); await sleep(300);
  check('add-product sheet opens', $('sheetTitle').textContent === 'Add product', $('sheetTitle').textContent);
  type($('newName'), 'Coca'); await sleep(1400);
  check('local matches offered when search fails', /Your catalog/.test($('matchList').textContent), $('matchList').textContent.slice(0, 90));
  check('local fallback explained', /showing your catalog/i.test($('matchList').textContent));

  console.log('\n[6] manual add without a barcode');
  searchMode = 'hit';
  click(opts()[0]); await sleep(150);
  click(doc.querySelector('#sheetFoot [data-act="saveNew"]')); await sleep(300);
  const cat3 = JSON.parse(window.localStorage.getItem('hs.catalog') || '[]');
  check('manual product saved', cat3.some(x => String(x.upc).indexOf('manual-') === 0), cat3.length);
  const inv = JSON.parse(window.localStorage.getItem('hs.inventory') || '{}');
  check('manual product counted in inventory', Object.keys(inv).some(k => k.indexOf('manual-') === 0));

  console.log('\n' + (fails ? 'FAILURES: ' + fails : 'PICKER OK'));
  process.exit(fails ? 1 : 0);
})();
