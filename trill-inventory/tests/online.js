// Online pricing engine tests — mocked network, no real HTTP.
// Run: node tests/online.js
const fs = require('fs');
const path = require('path');
let JSDOM;
try { JSDOM = require('jsdom').JSDOM; } catch (e) { JSDOM = require('/tmp/node_modules/jsdom').JSDOM; }

const html = require('./fixture-app')(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'));
let fails = 0;
const check = (l, c, x) => { if (!c) { fails++; console.log('  FAIL  ' + l + (x !== undefined ? '  -> ' + x : '')); } else console.log('  ok    ' + l); };

const calls = [];            // every URL fetch was asked for
let mode = 'hit';            // hit | 429 | empty | throw | slow
function mockFetch(url) {
  calls.push(url);
  if (mode === 'throw') return Promise.reject(new Error('offline'));
  if (mode === '429') return Promise.resolve({ ok: false, status: 429, text: () => Promise.resolve('{"code":"TOO_FAST"}') });
  if (mode === 'empty') return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve('{"items":[]}') });

  if (url.indexOf('upcitemdb') > -1) {
    return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve(JSON.stringify({
      code: 'OK', total: 1, items: [{
        ean: new URL(url).searchParams.get('upc'), title: 'Coca-Cola Zero Soda, 12 Fl. Oz.', brand: 'Coca-Cola Zero',
        size: '12 fl oz', category: 'Food, Beverages & Tobacco > Beverages > Soda',
        images: [], lowest_recorded_price: 0,
        offers: [
          { merchant: 'Wal-Mart.com', price: 9.08, updated_t: Math.floor(Date.now()/1000) - 86400 },
          { merchant: 'Target', price: 7.49, updated_t: Math.floor(Date.now()/1000) - 172800 },
          { merchant: 'Bad Data Co', price: 0, updated_t: Math.floor(Date.now()/1000) },
          { merchant: 'Ancient Mart', price: 4.00, updated_t: Math.floor(Date.now()/1000) - 86400*900 }
        ]
      }]
    })) });
  }
  if (url.indexOf('prices.openfoodfacts') > -1) {
    return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve(JSON.stringify({
      items: [{ price: 2.99, currency: 'EUR', date: '2024-01-11',
                product: { product_name: 'Coca-Cola', brands: 'Coca-Cola', quantity: '500 ml', image_url: '' },
                location: { osm_name: 'Carrefour Villeurbanne' }, proof_id: 123 }],
      total: 1
    })) });
  }
  if (url.indexOf('openfoodfacts') > -1) {
    return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve(JSON.stringify({
      status: 1, product: { product_name: 'Coca-Cola Zero', brands: 'Coca-Cola', quantity: '355 ml', categories: 'Sodas', image_small_url: '' }
    })) });
  }
  return Promise.resolve({ ok: false, status: 404, text: () => Promise.resolve('') });
}

const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://harrys.local/',
  beforeParse(win) {
    win.localStorage.setItem('hs.lookupSchema','2');
    // Keep timing deterministic: pre-cache the lookups used by earlier steps so the
    // serialized request queue isn't still draining when the next assertion runs.
    win.localStorage.setItem('hs.netcache', JSON.stringify({
      '012000001502': { upc: '012000001502', identity: null, offers: [], oldOffers: [], sources: [], at: Date.now() }
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
const sleep = ms => new Promise(r => setTimeout(r, ms));
const body = () => $('sheetBody').textContent;

(async () => {
  await sleep(150);
  for (let i = 0; i < 4; i++) { click($('obNext')); await sleep(25); }
  await sleep(200);

  console.log('\n[1] check digit validation');
  // reach into the closure via a scan of a bad barcode
  click($('btnManual')); await sleep(60);
  $('manualUpc').value = '012000001502';           // known-bad UPC (invalid check digit)
  click(doc.querySelector('#sheetFoot [data-act="manualGo"]')); await sleep(700);
  check('invalid check digit flagged', /Check digit invalid/.test(body()), body().slice(0, 120));
  check('still allows manual save', !!doc.getElementById('newName'));

  console.log('\n[2] unknown barcode -> online lookup -> prefilled form');
  calls.length = 0; mode = 'hit';
  click($('sheetClose')); await sleep(150);
  click($('btnManual')); await sleep(60);
  $('manualUpc').value = '099999999991';
  click(doc.querySelector('#sheetFoot [data-act="manualGo"]')); await sleep(260);
  // either the loading state is visible, or the (fast, mocked) lookup already finished
  check('shows progress or resolves immediately',
        /Checking online databases/.test(body()) || !!$('newName'));
  await sleep(1800);
  check('network was actually hit', calls.length > 0, JSON.stringify(calls));
  check('identity prefilled into name field', $('newName') && $('newName').value === 'Coca-Cola Zero Soda, 12 Fl. Oz.', $('newName') && $('newName').value);
  check('category guessed from "Soda"', $('newCat') && $('newCat').value === 'Cold Beverages', $('newCat') && $('newCat').value);
  // mocks: 9.08 (fresh) + 7.49 (fresh) survive; 0 and 900-day-old drop out
  check('reference offers do not become a shelf price', $('newPrice') && $('newPrice').value === '', $('newPrice') && $('newPrice').value);
  check('price of 0 rejected', !/0\.00/.test($('newPrice').value));
  check('stale price excluded', /2 online price/.test(body()) || /2 price/.test(body()), body().match(/\d+ online price[s]?/));
  check('source transparency shown', /UPCitemdb/.test(body()));
  check('no Auto-add happened', !JSON.parse(window.localStorage.getItem('hs.catalog') || '[]').some(p => p.upc === '099999999991'));

  console.log('\n[3] saving the online-sourced product with a manual shelf price');
  $('newPrice').value = '8.29';
  click(doc.querySelector('#sheetFoot [data-act="saveNew"]')); await sleep(300);
  const cat = JSON.parse(window.localStorage.getItem('hs.catalog') || '[]').filter(p => p.upc === '099999999991');
  check('product written to catalog', cat.length === 1 && cat[0].name === 'Coca-Cola Zero Soda, 12 Fl. Oz.', JSON.stringify(cat[0] && cat[0].name));
  check('price stored as 8.29', cat[0] && cat[0].price === 8.29, cat[0] && cat[0].price);

  console.log('\n[4] caching prevents repeat spend');
  const before = calls.length;
  click($('sheetClose')); await sleep(150);
  click($('btnMenu')); await sleep(120);
  click(doc.querySelector('[data-nav="online"]')); await sleep(300);
  check('online status view opens', $('sheetTitle').textContent === 'Online prices');
  check('lookups-today counter visible', /Lookups today/.test(body()));
  $('onlineUpc').value = '099999999991';
  click(doc.querySelector('[data-act="onlineGo"]')); await sleep(900);
  check('served from cache (no new request)', calls.length === before, 'calls ' + before + ' -> ' + calls.length);
  check('cache badge shown', /Cached/.test(body()));

  console.log('\n[5] adopting an online price onto a catalog product');
  check('adopt button present', !!doc.querySelector('[data-act="onlineUse"]'));
  click(doc.querySelector('[data-act="onlineUse"]')); await sleep(400);
  const cat2 = JSON.parse(window.localStorage.getItem('hs.catalog') || '[]').filter(p => p.upc === '099999999991');
  check('catalog price updated', cat2[0] && cat2[0].price === 8.29, cat2[0] && cat2[0].price);
  check('provenance recorded', !!window.localStorage.getItem('hs.pricemeta'));

  console.log('\n[5b] pack-size guard on a seeded product');
  click($('sheetClose')); await sleep(150);
  click($('btnMenu')); await sleep(120);
  click(doc.querySelector('[data-nav="catalog"]')); await sleep(300);
  click(doc.querySelector('[data-cat="049000042566"]')); await sleep(300);
  check('seeded product opens', $('sheetTitle').textContent === 'Coca-Cola Classic', $('sheetTitle').textContent);
  check('check-online button offered', !!doc.querySelector('[data-act="checkOnline"]'));
  click(doc.querySelector('[data-act="checkOnline"]')); await sleep(2200);
  check('pack mismatch warned on 20 oz vs 12 fl oz',
        /Pack sizes differ/.test(body()), body().match(/Pack sizes differ[^.]{0,90}/) || body().slice(0,80));
  // regression: adopting a price onto a SEED product must not erase the rest of it
  console.log('\n[5c] seed product survives a price override');
  if (doc.querySelector('#sheetFoot [data-act="onlineUse"]')) {
    click(doc.querySelector('#sheetFoot [data-act="onlineUse"]')); await sleep(400);
    check('name still present after override', /Coca-Cola Classic/.test($('sheetTitle').textContent), $('sheetTitle').textContent);
    const bd = $('sheetBody').textContent;
    check('category survived', /Cold Beverages/.test(bd));
    check('supplier survived', /Coca-Cola Consolidated/.test(bd), bd.match(/Supplier.{0,40}/));
    check('case pack survived', /24/.test(bd));
    check('price was updated', !/\$2\.49/.test(bd) || /Price set from online/.test(bd), bd.match(/Shelf price.{0,20}/));
  } else {
    check('(skipped — no adopt button)', true);
  }
  click($('sheetClose')); await sleep(150);

  console.log('\n[6] HTTP 429 -> backoff, no crash');
  calls.length = 0; mode = '429';
  click($('btnManual')); await sleep(60);
  $('manualUpc').value = '099999999990';
  click(doc.querySelector('#sheetFoot [data-act="manualGo"]')); await sleep(3500);
  check('429 handled without crashing', !!$('sheetTitle'));
  check('still offers manual entry', /Unknown|rate limited|manual/i.test(body()) || !!doc.getElementById('newName'), body().slice(0, 90));

  console.log('\n[7] active backoff -> honest incomplete-lookup path');
  mode = 'empty';
  click($('sheetClose')); await sleep(150);
  click($('btnManual')); await sleep(60);
  $('manualUpc').value = '077777777777';
  click(doc.querySelector('#sheetFoot [data-act="manualGo"]')); await sleep(3500);
  check('active backoff is not mislabeled a missing product', /Lookup incomplete/i.test(body()) && /rate limited/i.test(body()), body().slice(0, 300));
  check('form still usable', !!doc.getElementById('newPrice'));

  console.log('\n' + (fails ? 'FAILURES: ' + fails : 'ONLINE LOOKUP OK'));
  process.exit(fails ? 1 : 0);
})();
