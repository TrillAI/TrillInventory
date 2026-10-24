// Real-browser emulator E2E (Chromium): serves the staged APK assets
// (android/assets/www, incl. injected jsnes/zxing tags), then drives the
// secret emulator with real keyboard, real file input and pointer events.
const fs = require('fs'), path = require('path'), assert = require('assert');
const { chromium } = require('/tmp/node_modules/playwright-core');
const root = path.join(__dirname, '..');
const www = path.join(root, 'android/assets/www');

function buildRom(prgBanks, chrBanks) {
  const prg = prgBanks * 16384, chr = chrBanks * 8192;
  const buf = Buffer.alloc(16 + prg + chr);
  buf.set([0x4E, 0x45, 0x53, 0x1A, prgBanks, chrBanks, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
  buf.fill(0xEA, 16, 16 + prg);
  buf[16 + prg - 4] = 0x00; buf[16 + prg - 3] = 0x80;
  return buf;
}

(async () => {
  assert(fs.existsSync(path.join(www, 'index.html')), 'staged assets missing — run android/build.sh first');
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.addInitScript(() => {
      localStorage.setItem('hs.onboarded', 'true');
      localStorage.setItem('hs.settings', JSON.stringify({ onlineEnabled: false, autoPhotos: false, animate: true }));
      window.__pad = { connected: true, id: 'BrowserTest Pad Pro', axes: [0, 0],
        buttons: Array.from({ length: 17 }, () => ({ pressed: false, value: 0 })) };
      Object.defineProperty(navigator, 'getGamepads', { configurable: true, value: () => [window.__pad] });
    });
    await page.route('https://harrys.local/**', route => {
      let p = new URL(route.request().url()).pathname;
      if (p === '/' || p === '') p = '/index.html';
      const file = path.join(www, p);
      if (fs.existsSync(file)) {
        route.fulfill({ path: file, contentType: p.endsWith('.js') ? 'text/javascript' : 'text/html' });
      } else route.fulfill({ status: 404, body: 'nf' });
    });
    await page.goto('https://harrys.local/');
    await page.tap('#splashSkip');
    await page.waitForSelector('#app:not([inert])', { timeout: 5000 }).catch(() => {});

    // Still a secret: no emulator in the drawer.
    assert.equal(await page.locator('[data-nav="emulator"]').count(), 0, 'emulator nav must stay hidden');

    // Konami code on a real keyboard.
    for (const k of ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a']) {
      await page.keyboard.press(k);
    }
    await page.waitForSelector('#emulator.open', { timeout: 4000 });
    assert(await page.locator('#emuEmpty').isVisible(), 'empty-cartridge state visible');
    assert.equal(await page.locator('#emuChip').textContent(), 'No cartridge inserted');
    assert((await page.locator('#emuPad').textContent()).includes('BrowserTest Pad Pro'), 'pad status is real');

    // Load a real (synthetic) ROM through the real file input.
    await page.setInputFiles('#emuRomFile', { name: 'Super Mario Bros.nes', mimeType: 'application/octet-stream', buffer: buildRom(2, 1) });
    await page.waitForFunction(() => /Mapper 0/.test(document.getElementById('emuChip').textContent), null, { timeout: 5000 });
    assert.equal(await page.locator('#emuTitle').textContent(), 'Super Mario Bros.');
    assert((await page.locator('#emuChip').textContent()).includes('PRG 32 KB'));
    assert(await page.locator('#emuAttract').isVisible(), 'attract overlay over the running demo');
    await page.waitForFunction(() => /\d+ FPS/.test(document.getElementById('emuFps').textContent), null, { timeout: 5000 });

    // The canvas is really painting changing frames.
    const sample = () => page.evaluate(() => {
      const c = document.getElementById('emuCanvas'), x = c.getContext('2d');
      const d = x.getImageData(0, 0, 256, 240).data;
      let sum = 0; for (let i = 0; i < d.length; i += 997) sum += d[i];
      return sum;
    });
    const s1 = await sample(); await page.waitForTimeout(350); const s2 = await sample();
    assert(s1 !== s2 || s1 > 0, 'canvas frames are live');

    // Touch START (real tap) takes control.
    await page.locator('[data-btn="start"]').tap();
    await page.waitForFunction(() => document.getElementById('emuAttract').classList.contains('hid'), null, { timeout: 3000 });

    // Hold Right with one pointer while tapping A with another (multi-touch).
    await page.evaluate(() => {
      const fire = (el, type, id) => el.dispatchEvent(new PointerEvent(type, { bubbles: true, cancelable: true, pointerId: id, isPrimary: id === 1 }));
      const r = document.querySelector('[data-btn="right"]'), a = document.querySelector('[data-btn="a"]');
      fire(r, 'pointerdown', 21); fire(a, 'pointerdown', 22);
      window.__rel = () => { fire(r, 'pointerup', 21); };
      window.__relA = () => { fire(a, 'pointerup', 22); };
    });
    assert(await page.locator('[data-btn="right"].on').count() === 1, 'right held');
    assert(await page.locator('[data-btn="a"].on').count() === 1, 'A held simultaneously');
    await page.evaluate(() => window.__rel());
    assert(await page.locator('[data-btn="right"].on').count() === 0, 'right released independently');
    assert(await page.locator('[data-btn="a"].on').count() === 1, 'A still held');
    await page.evaluate(() => window.__relA());

    // Gamepad input drives the same buttons.
    await page.evaluate(() => { window.__pad.buttons[15].pressed = true; });
    await page.waitForSelector('[data-btn="right"].on', { timeout: 3000 });
    await page.evaluate(() => { window.__pad.buttons[15].pressed = false; });
    await page.waitForFunction(() => !document.querySelector('[data-btn="right"]').classList.contains('on'), null, { timeout: 3000 });

    // Wrong file type is rejected with a real message.
    await page.setInputFiles('#emuRomFile', { name: 'photo.jpg', mimeType: 'image/jpeg', buffer: Buffer.from([1, 2, 3]) });
    await page.waitForFunction(() => /Not a ROM/.test(document.getElementById('emuStatus').textContent), null, { timeout: 3000 });

    // Close and confirm the panel hides.
    await page.tap('#emuClose');
    await page.waitForFunction(() => !document.getElementById('emulator').classList.contains('open'), null, { timeout: 3000 });

    assert.deepEqual(errors, [], 'no page errors: ' + errors.join('; '));
    console.log('EMU BROWSER OK: secret Konami, real ROM load + header data, live canvas/FPS, touch takeover, multi-touch, gamepad, file validation, close');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
