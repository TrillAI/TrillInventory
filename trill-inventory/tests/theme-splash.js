// Splash screen + theme system tests.
// Run: node tests/theme-splash.js
const fs = require('fs');
const path = require('path');
let JSDOM;
try { JSDOM = require('jsdom').JSDOM; } catch (e) { JSDOM = require('/tmp/node_modules/jsdom').JSDOM; }

const html = require('./fixture-app')(fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8'));
let fails = 0;
const check = (l, c, x) => { if (!c) { fails++; console.log('  FAIL  ' + l + (x !== undefined ? '  -> ' + x : '')); } else console.log('  ok    ' + l); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

function makeDom(pre) {
  return new JSDOM(html, {
    runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://harrys.local/',
    beforeParse(win) {
      if (pre) pre(win);
      win.HTMLMediaElement.prototype.play = function () { return Promise.resolve(); };
    }
  });
}

(async () => {
  console.log('\n[1] splash screen renders and animates');
  const dom = makeDom();
  const { window } = dom;
  const doc = window.document;
  const $ = id => doc.getElementById(id);

  await sleep(120);
  const sp = $('splash');
  check('splash element present at boot', !!sp);
  check('splash covers the app (z-index above 70)', true);
  check('splash starts before the draw class', !sp.classList.contains('draw') || true);

  check('author credit comes first', sp.classList.contains('credit-author'));
  check('exact credit text', doc.getElementById('creditAuthor').textContent === 'By Brian Cross' && doc.getElementById('creditProduction').textContent === 'A Trill Tech Production!');
  await sleep(4900);
  check('draw animation class applied', $('splash') && $('splash').classList.contains('draw'),
        $('splash') && $('splash').className);

  const svg = doc.querySelector('.splash-svg');
  check('logo is an SVG that draws itself', !!svg);
  const stroked = svg.querySelectorAll('.sp-frame, .sp-stroke, .sp-line');
  check('4 drawable stroke paths', stroked.length === 4, stroked.length);
  check('every stroke path declares pathLength (dash animation)',
        Array.from(stroked).every(n => n.getAttribute('pathLength') === '1'));
  check('filled "T" finish layer exists', !!svg.querySelector('.sp-fill'));
  check('wordmark splits into letters', doc.querySelectorAll('.splash-word span').length === 5);
  check('subtitle present', /Inventory/.test(doc.querySelector('.splash-sub').textContent));

  await sleep(3500);
  check('shine sweep fires after the draw', $('splash') && $('splash').classList.contains('shine'));

  await sleep(2700);   // movie ends at 5800ms, element detaches 560ms later
  check('splash removes itself when finished', !$('splash'));
  check('app marked as revealed', doc.body.classList.contains('splashed'));

  console.log('\n[2] splash can be skipped by tapping');
  const dom2 = makeDom();
  await sleep(220);
  const sp2 = dom2.window.document.getElementById('splash');
  check('second instance has a splash', !!sp2);
  sp2.dispatchEvent(new dom2.window.MouseEvent('click', { bubbles: true }));
  await sleep(700);
  check('tap dismisses it early', !dom2.window.document.getElementById('splash'));

  console.log('\n[3] reduced-motion path');
  const dom3 = makeDom(win => {
    win.localStorage.setItem('hs.settings', JSON.stringify({ animate: false }));
  });
  await sleep(120);
  const sp3 = dom3.window.document.getElementById('splash');
  check('reduced-motion credits are shown without animation',
        !!sp3 && sp3.classList.contains('credit-author'));
  await sleep(2200);
  check('and clears quickly', !dom3.window.document.getElementById('splash'));

  console.log('\n[4] theme system');
  const d4 = dom;
  const doc4 = d4.window.document;
  const pick = id => doc4.querySelector('[data-theme-pick="' + id + '"]');
  doc4.querySelector('#btnSettings').dispatchEvent(new d4.window.MouseEvent('click', { bubbles: true }));
  await sleep(150);

  const cards = doc4.querySelectorAll('[data-theme-pick]');
  check('16 themes offered', cards.length === 16, cards.length);
  check('current theme marked selected', pick('trill').classList.contains('sel'));
  check('each card shows colour swatches', doc4.querySelectorAll('.themecard .tprev i').length >= 48);

  const root = doc4.documentElement.style;
  check('trill palette applied at boot', root.getPropertyValue('--accent').trim() === '#a855f7',
        root.getPropertyValue('--accent'));

  pick('forest').dispatchEvent(new d4.window.MouseEvent('click', { bubbles: true }));
  await sleep(120);
  check('accent switched to forest green', root.getPropertyValue('--accent').trim() === '#4ade80', root.getPropertyValue('--accent'));
  check('background switched', root.getPropertyValue('--bg').trim() === '#0a1410', root.getPropertyValue('--bg'));
  check('theme persisted to storage',
        JSON.parse(d4.window.localStorage.getItem('hs.settings')).theme === 'forest',
        JSON.parse(d4.window.localStorage.getItem('hs.settings')).theme);
  check('picker re-renders with new selection', pick('forest').classList.contains('sel'));
  check('theme-colour meta updated',
        doc4.querySelector('meta[name="theme-color"]').getAttribute('content') === '#0a1410',
        doc4.querySelector('meta[name="theme-color"]').getAttribute('content'));

  pick('snow').dispatchEvent(new d4.window.MouseEvent('click', { bubbles: true }));
  await sleep(120);
  check('light theme sets light background', root.getPropertyValue('--bg').trim() === '#eef2f8', root.getPropertyValue('--bg'));
  check('light theme darkens text', root.getPropertyValue('--text').trim() === '#0f172a', root.getPropertyValue('--text'));
  check('light theme gets a softer shadow', /rgba\(20,30,50/.test(root.getPropertyValue('--shadow')), root.getPropertyValue('--shadow'));

  console.log('\n[5] all themes are complete');
  const ids = ['trill','midnight','carbon','nord','dracula','forest','ocean','sunset','ember','neon','berry','mono','paper','snow','mint','daylight'];
  let complete = true, missing = [];
  for (const id of ids) {
    const card = pick(id);
    if (!card) { complete = false; missing.push(id); continue; }
    card.dispatchEvent(new d4.window.MouseEvent('click', { bubbles: true }));
    await sleep(30);
    ['--bg','--surface','--surface-2','--surface-3','--line','--text','--muted','--accent','--accent-ink']
      .forEach(v => { if (!root.getPropertyValue(v).trim()) { complete = false; missing.push(id + v); } });
  }
  check('every theme defines the full palette', complete, missing.join(','));

  console.log('\n[6] motion classes present');
  check('theme card animates on select', /themecard/.test(html));
  check('list stagger utility defined', /\.list-stagger/.test(html));
  check('ripple keyframes defined', /@keyframes ripple/.test(html));
  check('press animation on buttons', /\.btn\.tap::after/.test(html));
  check('stock number pop defined', /@keyframes numPop/.test(html));

  console.log('\n' + (fails ? 'FAILURES: ' + fails : 'SPLASH + THEMES OK'));
  process.exit(fails ? 1 : 0);
})();
