# Trill Inventory — Android APK

`TrillInventory-1.4.0.apk` · 165 KB · package `com.harrys.scan` · versionName 1.4.0 · minSdk 23 (Android 6) · targetSdk 34

The same inventory scanner as `../index.html`, wrapped in a native Android shell so it installs
like a real app: own icon, real camera permission, persistent storage, working hardware back button.

---

## Install

**On the phone (no computer needed)**

1. Copy `TrillInventory-1.4.0.apk` to the device (download, USB, Drive, email to yourself).
2. Tap it. Android will warn about unknown sources — choose **Settings → Allow from this source**.
3. Tap **Install**. First launch asks for camera access; grant it.
4. Because it was sideloaded by a self-signed certificate, Play Protect may show
   *"unsafe app blocked"* → tap **More details → Install anyway**. That's expected for any
   non-Play-Store build.

**Over USB (adb)**

```bash
adb install -r TrillInventory-1.4.0.apk
```

---

## What the native shell adds

| Thing | Why it needed the APK |
|---|---|
| Camera permission | A browser tab can be blocked by iframe/permissions policy; the app grants it properly |
| Hardware back button | Closes the detail sheet, then the drawer, then exits — wired to `__hsHandleBack()` in the web app |
| Persistent storage | WebView DOM storage survives app restarts; inventory isn't lost |
| Export / copy | `AndroidHost.saveFile()` writes JSON/CSV to the app's `exports/` folder; `copyText()` fills the clipboard |
| Offline barcode decoding | ZXing 0.21.3 is **bundled inside the APK** — scanning works with no network and no Google Play Services |
| Native HTTP bridge | UPCitemdb only serves CORS headers to its own origin, so `fetch()` from the app is blocked. The bridge performs the request in Java instead — host-allowlisted to the three price databases, HTTPS only, 256 KB response cap. |

The web UI is served to the WebView through a request interceptor under the virtual origin
`https://harrys.local/`. That's what makes it a *secure context*, which `getUserMedia` requires —
loading straight from `file://` would silently kill the camera.

## v1.4.0 changes — torch, recognition, copy

**Copy.** The footer note now reads "Trill Inventory · built for Inventory".

**Flashlight behaviour.** Previously the torch fired for a quarter-second on each read. Now:

- The torch **stays lit the whole time the scanner is armed** (new setting *Flashlight stays on*).
- A successful read **blanks the torch for ~340 ms** as the confirmation cue, alongside the beep
  and screen flash.
- It **relights as soon as the scanner is ready again** — i.e. when you dismiss the review sheet.
- While the review sheet is open the scanner isn't armed, so the light rests (and saves battery).

Two independent toggles now: *Flashlight stays on* and *Flash off on each scan*. Devices that
don't expose the torch constraint simply skip it — the screen flash and beep still fire, and the
app detects rejection rather than assuming success.

**Advanced barcode recognition.**

- **More symbologies** — Code 93 added alongside UPC-A/E, EAN-8/13, Code 39, Code 128, ITF and
  Codabar. Optional 2D pass (QR, Data Matrix, PDF417, Aztec) for shelf and case labels.
- **TRY_HARDER decoding** with a faster per-frame cadence (110 ms) for damaged, curved or
  angled labels.
- **UPC-E → UPC-A expansion.** An 8-digit UPC-E is expanded to its 12-digit UPC-A with a
  recomputed check digit, so a compressed code matches the catalog entry.
- **EAN-13 folding.** US EAN-13 codes with a leading zero resolve to the UPC-A record.
- **One stock line per product.** However a barcode is read, it's canonicalised to the form the
  catalog stores, so scanning the same item as UPC-E and then UPC-A doesn't create two counts.
- **Symbology shown** in the sheet header (e.g. "Scanned from camera · EAN-13"), with the raw
  reading displayed when it was normalised.

## v1.3.0 changes — rename, splash, themes, motion

**Renamed to Trill Inventory.** Launcher label, in-app branding, wordmark, launcher icon (purple
card + dark "T"), theme colours and export filenames all updated. The **package name stays
`com.harrys.scan`** on purpose — changing it would install as a separate app and orphan the
inventory already on the device. App name changes; identity doesn't.

**Animated splash screen.** The logo draws itself in strokes over ~2 seconds: the rounded frame
traces first, then the T's crossbar and stem, then the underline and centre dot, then the solid
"T" fills in, then the wordmark letters rise one at a time, then a light sweep crosses the screen
and it fades into the app. Tappable to skip, and it degrades to a static finished logo when
animations are turned off.

**16 themes.** Trill (new default, purple on near-black), Midnight, Carbon, Nord, Dracula, Forest,
Ocean, Sunset, Ember, Neon, Berry, High Contrast, Paper, Snow, Mint Cream, Daylight. Each is a
complete palette — background, three surface levels, borders, text, muted text, accent and accent
ink — and each card in the picker previews its real colours. Reachable from **Left menu → Themes**
or Settings → Appearance. Selection persists and the Android `theme-color` follows it.

**More animation throughout:**

- Ripple on every button, icon button and stepper tap
- Staggered entrances for inventory, catalog, restock, history and search results
- Sheets cascade their content in; drawers spring open
- Scan button breathes; brand mark has a periodic light sweep
- Stock number pops when a count changes after cataloging
- Toast bounces in; settings categories cascade; error shake utility
- All of it respects the **Animations** toggle, which disables motion app-wide

### Bugs found by driving the UI with a real browser engine

1. **Drawers couldn't be tapped.** The scrim sat at `z-index:45` above the drawers at `40`, so it
   intercepted taps and blurred the panel — the left menu and settings were effectively unusable
   by touch. Drawers now sit above the scrim.
2. **Collapsed settings groups weren't hidden.** WebView reported closed `<details>` as fully laid
   out, so every category rendered at once. Now explicitly hidden when closed.
3. **Theme changes reset the panel.** Selecting a theme re-rendered the whole settings panel,
   which threw away the scroll position and detached the node under the user's finger. It now
   updates the selection in place.

## v1.2.0 changes

**Name it, then pick the match.** When you scan a barcode the app doesn't know, or you add a
product by hand, the form now watches the name field. Type three characters and it searches
product databases, then shows **selectable option cards** — thumbnail, title, brand, size, price,
and which source it came from. Tapping one fills in the name, brand, size, category, case pack,
price and cost in a single action. Options also come from your own catalog, so it still works with
online lookup switched off.

- **Update product info** — on any catalog item, the result sheet now offers `✎ Update info`.
  Search, pick the correct match, and it updates name/brand/size/category/image. Your price and
  stock count are only touched by the separate **Apply + price** button.
- **Add a product** — new menu entry for adding an item with no barcode at all: name it, pick a
  match, set the count.
- Match metadata (chosen barcode, title, image, timestamp) is stored on the product, so the details
  sheet shows what it was matched to and when.
- New setting: **Settings → Online prices → Search by product name**.

### Traps this handles, found by testing against the real API

1. **Multipack prices.** A listing titled *"Monster Energy 12 count 16 fl oz"* priced $19.98 is a
   case, not a can. Per-unit prices are derived before they reach the shelf-price field, and the
   card shows the unit price with a `12-pack` tag.
2. **Nonsense derived prices.** Live data includes listings like *"16 Ounce (24 Pack)"* at $6.00,
   implying $0.25/can. If a candidate's unit price falls outside 0.35×–3× the other candidates,
   the app **leaves the price blank** and tells you to set it yourself rather than writing a wrong
   number.
3. **`pack` means two different things.** Online listings parse "units in this listing"; catalog
   products store "units per case". Conflating them silently divided single-item prices by 24.
   They're now separate fields (`listingPack`).
4. **Seed-product corruption.** Price/info overrides used to replace the entire product record
   instead of merging over it, so editing a price could blank out the name and supplier. Fixed,
   with a regression test.
5. **Junk titles** — `(12 cans)`, `Pack of 24`, and empty `( )` are stripped from product names.

## v1.1.0 changes

**Demo mode removed.** The simulated-scan button is gone. Manual entry remains as the fallback
when there's no camera or no decoder.

**Real online pricing.** Unknown barcodes and any catalog item can now be priced from public
product databases. Three keyless providers, tried in order:

| Provider | Gives you | Notes |
|---|---|---|
| **UPCitemdb** | Product identity + live retailer offers in USD | Free trial tier: ~100 lookups/day and it throttles bursts hard (`TOO_FAST`). APK only — it blocks cross-origin reads, hence the native bridge. |
| **Open Prices** | Crowd-submitted shelf prices with store name and date | Genuinely useful in Europe; **very thin US coverage** — often returns nothing for US convenience items. |
| **Open Food Facts** | Name, brand, size, category, photo | No prices. Reliable identity fallback. |

How the app behaves around that reality:

- **Cache first.** Results are stored locally (`netCacheHours`, default 24 h) so re-scanning the
  same item costs nothing.
- **Serialized + throttled.** One request at a time with a configurable gap (default 1.5 s), a
  daily cap (default 60), and a 2-minute backoff when a provider returns 429.
- **Early exit.** It stops spending requests as soon as a *current* price is found.
- **Historical fallback.** If every price is older than `maxAgeDays` (default 730), the app still
  shows it — clearly labelled "Historical price" with the observation date — instead of nothing.
- **Pack-size guard.** If the online listing's size disagrees with the catalog entry (12-pack vs
  20 oz single), the sheet warns before you can apply the price. Live testing caught exactly this
  on the sample Coca-Cola barcode, which actually resolves upstream to a 12-pack.
- **Nothing to hide.** The lookup sends only the barcode. No account, no device ID, no inventory.
  Turn it off entirely in Settings → Online prices to run fully offline.

### Accuracy, stated plainly

These are **published retail prices from public databases**, not Harry's POS data. They're a
sanity-check reference, not a price book. Adopt them with your eyes open, and always confirm
against the shelf tag or invoice. Where the app can't find a current price it says so rather than
inventing one.

---

## Known limitations

- **Torch pulse.** The "flashlight flashes on scan" setting drives `applyConstraints({torch})`.
  WebView only supports that on some devices; when unsupported it's skipped silently and the
  white **screen flash** still fires. Same for `BarcodeDetector`, which is why ZXing is bundled.
- **Not tested on a physical device by me** — this sandbox has no KVM, so no emulator could boot.
  Everything below it is verified mechanically (signature, dex, assets, both JS test suites), but
  first-run behavior on your hardware is unverified.
- **Self-signed** with `android/harrys-release.jks` (alias `harrys`, password `harrys2026`).
  Keep that keystore — you need the same key to ship an update over the top. For Play Store
  distribution you'd need an AAB and your own upload key.
- **Portrait only**, immersive full-screen, phone form factor. Fine for a shelf-counting tool.
- **Browser vs APK.** In a browser tab, UPCitemdb blocks cross-origin reads, so only Open Prices
  and Open Food Facts answer. The APK is the complete version. The app detects this and says so in
  the Online prices screen.
- **Sample barcodes are illustrative.** The seeded catalog's UPCs are structurally valid but
  don't all match the real pack size for that product — which is exactly why the pack-size guard
  exists.

---

## Rebuild

The whole pipeline is `android/build.sh` — no Gradle, no Android Studio.

```bash
cd android && ./build.sh
```

It runs `aapt2 → javac → d8 → zip → zipalign → apksigner` and drops a fresh APK one level up.
Requires a JDK 17 and Android SDK build-tools 34 + platform 34.

Edits to the web app happen in `../index.html`; the build copies it into `assets/www/` and injects
the ZXing `<script>` tag automatically, so the browser version and the APK never drift apart.

## File map

```
harrys-scan/
├── index.html                  the app (browser + APK source of truth)
├── TrillInventory-1.4.0.apk        signed, installable build
├── tests/
│   ├── smoke.js                30+ UI/behaviour checks in jsdom
│   ├── online.js               price engine, cache, 429 backoff, pack guard (mocked net)
│   ├── picker.js               name-it → choose-from-options → update flows
│   ├── theme-splash.js         splash timeline, all 16 palettes, motion hooks
│   ├── torch-recognition.js    torch state machine, hints, UPC-E/EAN normalisation
│   ├── native-path.js          mocked camera + ZXing path checks
│   └── live-online.js          hits the real APIs — manual, needs network
└── android/
    ├── build.sh                full APK pipeline
    ├── AndroidManifest.xml     camera, vibrate, internet (lookup only)
    ├── src/com/harrys/scan/
    │   └── MainActivity.java   WebView host, asset interceptor, HTTP + file bridges
    ├── res/                    icon (vector), theme, strings
    ├── vendor/zxing.min.js     bundled offline decoder
    ├── assets/www/             generated at build time
    └── harrys-release.jks      signing key — keep this
```

## Verify

```bash
sha256sum TrillInventory-1.4.0.apk
/usr/local/android-sdk/build-tools/34.0.0/apksigner verify --print-certs TrillInventory-1.4.0.apk
cd .. && for t in smoke online picker native-path theme-splash torch-recognition; do node tests/$t.js; done
node tests/live-online.js      # optional: real network
```

## 1.5.0 — Tobacco lookup assistance
- Unknown-product form now offers a guided tobacco search for cigarettes, cigars, cigarillos, dip, nicotine pouches and vapes.
- Search ranking and warnings compare explicit menthol, length, strength and pack/carton details. Missing details still require verification.
- Tobacco candidate selection requires label confirmation and preserves the scanned barcode. Public search prices are not copied into the new-product form; tobacco count quantities are not mistaken for case packs.
- No new data provider or guaranteed tobacco coverage. Saved barcode records work offline.
- Seven JS suites passed; signed APK verified. Physical Android camera/torch testing still required.

## 1.6.0 — Unknown barcode fixes and local comparison workflow
- Fixed UPC-E expansion: branch on the sixth payload digit, retain the number system, validate the supplied check digit. Invalid UPC-E codes are not silently repaired.
- Nonzero-leading EAN-13 codes no longer lose their first digit. Zero-padded GTIN-14 handling added. Raw eight-digit codes remain primary to avoid assuming EAN-8 is UPC-E.
- Lookup retries supported equivalent forms on missing results; negative cache expires after one minute and transport/rate-limit failures are not cached. Identity lookup remains available when price lookup is off.
- Unknown screen supports forced retry, explicit service-error status and a manual-entry escape while lookup runs.
- Walmart, Target, Kroger, Walgreens and CVS search links; default area 37311. The user must select an actual store on the retailer site. These links are NOT live local pricing integrations and do not send/select the ZIP automatically.
- Separate user-entered local observations include store, ZIP, size/unit, USD price and recording timestamp. These do not modify shelf price or inventory. Online provider offers are labeled as unverified for the local store.
- Eight JS suites pass. APK compiled and signature verified; not run on physical Android hardware. Actual retailer website availability and store-price coverage are not guaranteed.

## 1.6.1 — Native lookup bridge repair
- Root defect found: httpGet was annotated on MainActivity, but the object exposed to JavaScript was HostBridge, which had no httpGet method. Added an annotated HostBridge delegate. The APK now exposes the intended native transport instead of silently falling back to CORS-restricted browser fetch.
- Added compiled-bytecode verification of the exposed annotated method/delegation plus callback tests; prior mocked-native tests did not catch this Java wiring defect.
- OFF JSON 404/status=0 is treated as a missing product, while HTML 404 and access errors remain service errors. Error details are expandable, not mistaken for invalid barcodes.
- Native HTTP redirects disabled to preserve the host allowlist. Old/incomplete native bridges produce an actionable update error.
- Nine suites pass; signed APK verified. Live sandbox probes: UPCitemdb 200 for 049000042566, Open Prices 200/no observations, OFF 403. No physical-device runtime test; user-specific 404 source remains unconfirmed.

## 1.7.0 — Product picture correction
- Product detail has Update picture, available offline as well as online.
- Fresh barcode lookup offers a candidate image; preview must load and the user must confirm the exact package before saving. No generic or AI-generated substitute is used.
- Camera capture and JPG/PNG/WebP upload are available; local photos are resized to a maximum 640 px and stored with the catalog for offline display. Android system image-picker support added.
- Remove incorrect picture; image source/confirmation timestamp; image-only saves preserve product identity, stock and prices. Confirmed photos are protected from unrelated info updates.
- Storage failure keeps the previous picture and shows an error. Closing the editor stops its camera and invalidates late lookup responses.
- Ten automated suites pass, including photo workflow and compiled native bridge checks. Signed APK built/verified. Camera capture, Android picker, and retailer-hosted image availability still require physical-device testing.

## 1.8.0 — Quick price editing
- Edit price button in the product Pricing section, available offline.
- Selected shelf-price field with decimal keyboard; optional unit cost; live profit/margin preview and below-cost warning.
- Save price or Cancel; Enter also saves. Invalid/negative/overprecision values blocked; zero price requires confirmation.
- Catalog-only save preserves stock, image, identity and pending add quantity. Storage failure leaves old price intact and reports an error. Pricing provenance marked manual edit.
- Eleven automated suites passed. Signed APK verified; physical-device testing remains outstanding.

## 1.9.0 — Phone-hosted browser dashboard
- Menu → Browser access → Start hosting binds a bounded HTTP server on port 8765. Private IPv4 addresses and a per-session 192-bit random connection code are shown in-app. Hosting is off on startup; stop/restart rotates credentials; Activity destruction stops it.
- Browser dashboard: saved/tracked products only, name/barcode search, low-stock filter, reorder suggestions, total units, editable shelf price/cost/stock count. Refreshes every five seconds. Barcode images are not included in the browser dashboard.
- Browser edits operate on the existing phone catalog/inventory through the UI-thread WebView bridge, rather than a separate browser database. Value-based conflict checks protect against stale browser edits and stale phone price edits. Persistence errors are reported; inventory/catalog writes attempt rollback together.
- Authenticated JSON endpoints, strict Host/Origin checks, private-address restriction, no CORS, request/body bounds, bounded thread pool, no filesystem routes, no external resources, code kept only in browser memory. Anyone with the code has edit privileges; no per-user roles or audit log.
- HTTP is NOT encrypted. Trusted Wi-Fi only; do not port-forward, expose publicly or use on guest/public networks. Keep the phone awake with Trill open. No background service or remote internet hosting is provided.
- Thirteen JavaScript suites plus a Java real-socket server suite passed. APK compiled and signature verified. Android phone-to-computer LAN operation is not physically tested in this environment.

## 1.10.0 — More motion, without delaying work
- Phone: staggered menu entries, individual pricing-card entrances, filling stock bars, photo reveals, rolling/pop feedback on counters, price-change outline, button press/hover feedback, expanding settings sections and success-toast timer.
- Browser: dashboard/card entrance cascade, modal entrance, animated totals, row entrance and change highlights, button/input feedback and connection indicator. Keyed rows preserve DOM/focus during refresh; unchanged rows do not reanimate every five seconds.
- Browser has a persistent Motion on/off control. Phone uses Settings → Appearance → Animations. Both honor live system reduced-motion changes; active animations are cancelled on opt-out. Static splash remains fully visible under reduced motion.
- Exact quantities/prices update immediately; animation does not gate scanning, saves or network calls. Phone CSS animations pause when the document is hidden.
- Fourteen JS suites, real Chromium animation/focus tests, and Java real-socket server tests passed. APK built and signature verified. Android hardware behavior remains unverified.

## 1.10.1 — Wrong-product and wrong-price corrections
- Retired the sample catalog from active lookups. New installs start with no saved catalog, not fictional names/sizes/prices tied to real UPCs. A migration-only copy is used solely to preserve previously counted products and partial overrides, then discarded from the active runtime.
- Legacy-dependent saved products are flagged Review required, with stock counts and user overrides preserved. Old cross-barcode name-search matches are also flagged unless subsequently reviewed. Browser rows indicate review is needed on the phone.
- Exact UPC/EAN/zero-padded GTIN matching for provider responses; unrelated or barcode-less responses are rejected instead of using the first item. Open Prices observations and OFF identities are checked too. Old online cache entries invalidated once.
- Eight-digit numbers are no longer assumed to be UPC-E: expansion requires a camera-reported UPC-E format. Native detector now passes the detected format to the scan handler.
- Unknown products always require a manual save. Database identity suggestions do not fill shelf prices, estimated costs or case quantities. Unset shelf prices/costs are marked Not set in product details and browser rows. Name-search matches with a different barcode require explicit confirmation.
- Bulk refresh caches reference prices only; it no longer overwrites saved shelf prices. Explicit price adoption requires listing-unit confirmation. Update-info price adoption uses the per-unit value rather than dropping the whole multipack price onto one item.
- Wrong product? Correct saved details: edit name/brand/size/category, optionally correct prices, confirm against package, and remove the old image unless explicitly retained. Correcting a record never adds stock. Storage and concurrent-edit checks included.
- Fifteen JS suites (including fresh-install integrity and migration tests), real Chromium motion tests and the real-socket Java server suite passed. Legacy UI tests now load explicit test-only catalog fixtures; no test fixture is shipped as an active default. Signed APK verified. Physical-device behavior and public-database factual accuracy remain unverified.

## 1.11.0 — Purple-and-black cinematic startup
- New 5.8-second intro: purple particles converge, five separate gradient pieces fly/rotate into a complete T, orbital lines settle, frame draws, soft seal wave expands, and the Trill Inventory wordmark resolves before revealing the app.
- Black background, violet light, subtle perspective floor, tagline and movie progress line. Uses local SVG/CSS only; no downloaded media, audio, advertising or network dependency.
- Skip intro button and tap-anywhere dismissal; startup timers are cleared on skip. Underlying app controls are inert while the movie is present, released immediately on dismissal. Reduced-motion/disabled-animation mode shows the finished logo briefly without assembly.
- Default Trill theme deepened to purple and black; explicit saved theme choices retained. Intro palette stays purple/black regardless of the selected app theme. Android window/WebView background matches the intro.
- Fifteen JS regression suites, real Chromium cinematic and dashboard-motion tests, and Java real-socket server tests pass. Cinematic screenshots checked at mid-assembly and completed-logo stages. Signed APK verified. Physical Android playback/performance still needs hardware testing.

## 1.12.0 — Icon-matched theme and opening credits
- Default Trill palette now uses the launcher icon's exact near-black #08070f, purple #a855f7 and dark ink #150a24. Initial CSS, Android window/WebView, favicon and local browser dashboard use the matching palette. Existing explicit theme choices are preserved.
- Startup order: “By Brian Cross” fades in/holds/fades out for 2.4 seconds; “A Trill Tech Production!” does the same for 2.4 seconds; then the existing 5.74-second T-building movie continues and reveals the app.
- Skip intro skips the entire sequence and clears all pending startup timers. Reduced motion displays each credit statically for 0.8 seconds, then the completed logo briefly.
- Fifteen JS suites, real Chromium credit/cinematic/dashboard-motion tests, and real-socket Java server tests passed. Both credit screens visually checked via screenshot. Signed APK compiled/verified; Android hardware playback remains unverified.

## 1.13.0 — Contextual tobacco controls and automatic product photos
- Unknown and ordinary-product scan forms no longer contain the generic cigarette/tobacco helper. It appears only after the product name/category identifies tobacco. Cigarette-specific copy/type is shown only for identified cigarette products, not other tobacco types. Changing identity/category removes unrelated controls without rebuilding the form.
- Removed the generic tobacco warning from retailer search panels. Ordinary food names such as French onion dip no longer trigger tobacco classification.
- Automatic product photos default on: new saves, imported items and existing eligible saved items are queued for barcode-only photo matching. Confirmed manual-match barcodes can be used for products added without their own barcode. Items without a usable retail barcode require a manually chosen photo.
- Reuses fresh exact-barcode image metadata, then checks UPCitemdb and Open Food Facts. Preloads images, tries alternate images and a fallback provider, rejects mismatched barcodes and known size/tobacco-variant conflicts, and never saves name-search thumbnails as product photos.
- User-confirmed/uploaded photos are never replaced. Explicit photo removal blocks automatic re-addition. Late responses are discarded if identity or picture changes. Old unverified name-search images are hidden until matched or manually confirmed.
- Photo updates are persisted separately from prices/counts and replace only the visible image/status, preserving the in-progress quantity. Barcode-match provenance is distinct from user confirmation. Website photos remain URL-based and depend on image-host availability; they are not guaranteed offline or factually correct merely because the barcode matches.
- Settings → Online prices → Automatic product photos provides opt-out. Existing request budgets/backoff apply; retry delay prevents repeated missing-photo requests. No guaranteed coverage for every product; missing or uncertain photos retain a placeholder and Update picture fallback.
- Sixteen JS regression suites, a real Chromium automatic-image/context test, dashboard motion tests, and real-socket Java server tests passed. Signed APK verified. Physical Android camera/lookup behavior remains unverified.

## 1.14.0 — Fast scan mode
- Scanner screen Fast scan toggle and Settings → Scanning → Fast scan. Each accepted read durably adds exactly 1 unit without opening a product sheet, regardless of default quantity, review/continuous settings or automatic-save preference. Mode preference persists; camera still requires an explicit start/action.
- Nonmodal last-count/session status and guarded Undo last +1. Known product prices/details stay unchanged. Unknown barcodes are immediately saved as Unknown item with unset prices, then exact-barcode identity is looked up serially in the background; images follow identification. Network failure never blocks counts or launches a sheet.
- Held/repeated/alternating visible codes are suppressed until at least two empty decode results spanning about 650 ms clear the latch. Different new barcodes can be counted consecutively. Brief decode flicker and the 340 ms torch pulse do not normally rearm the same code. This is a decode-based safeguard, not physical-object tracking; move identical barcodes fully out of view between items.
- Fast scanning pauses for sheets, drawers, onboarding/splash and hidden documents. Every count saves immediately. Storage failure rolls back writes, leaves in-memory count unchanged, and stops camera capture with a visible error. Undo refuses to alter a count changed since that scan.
- Fixed a pre-existing real decoder API mismatch: bundled ZXing 0.21 uses a numeric timeBetweenScansMillis, timeBetweenDecodingAttempts property, and decodeContinuously(video, callback), not an options object passed to the one-shot decodeFromVideoElement method. Regression mocks updated; the actual bundled loop is exercised with synthetic decoded frames/errors.
- Eighteen JS suites, real Chromium Fast scan UI and automatic-photo tests, and the real-socket Java server suite passed. Signed APK verified. Physical phone camera throughput and duplicate suppression still require hardware testing.

## 1.15.0 — Menu and navigation repair (version code 18)
- Removed the Store info / Location & shift notes menu entry and its obsolete placeholder page; inventory, catalog, history, and preferences are not cleared.
- Drawer taps no longer start a swipe. Horizontal drags activate only after a movement threshold; vertical scrolling and form controls remain usable. Both drawers now support swipe-close, with cancelled gestures restoring their state and accidental post-swipe clicks suppressed.
- Synchronous menu routing; shared overlay state keeps the backdrop, scanner pause, torch resumption and hidden-panel inert/ARIA state consistent. Closing product details via navigation clears stale product/photo/lookup state. Camera reads cannot open a result over a menu.
- Back/Escape dismisses a replayed setup guide; initial onboarding Back returns to the previous step. Removed obsolete branding from the import menu subtitle.
- Verification: 18 JS suites; Chromium mobile touch tests for all 12 remaining destinations, vertical scrolling, both edge gestures, swipe-close, cancellation, close buttons, backdrop, settings toggle, Back/Escape and scanning resumption. Fast-scan, automatic-photo and motion Chromium tests passed; Java real-socket LAN tests passed. APK signature verified with the existing upgrade key.
- No physical Android-device testing was performed. Install as an update over the previous app; do not uninstall if keeping device-local inventory.

## 1.16.0 — Live dashboard, pairing, cigarette units and motion (code 19)
- Explicit cigarette pack/carton profiles, confirmed carton quantity selection, pack equivalents, expanded brand recognition and color/variant mismatch warnings. Separate barcodes are not merged; Fast scan remains +1 per saved unit.
- Normal stock additions now use the durable rollback-safe writer rather than mutating in-memory stock before persistence. Remote unset prices are no longer silently prefilled as zero.
- Authenticated long-poll change notifications, immediate latest-scan publication and 500ms checks for other changes. Four live watcher slots in an eight-worker bounded server; state/edit routes retain private-peer, Host, Origin, size and authorization checks.
- Six-digit pairing codes; QR carries a strong random secret in the URL fragment, removed on load. Successful pairing exchanges for a separate 192-bit random credential saved by the browser and persisted on Android through private preferences. 10-minute pairing expiry, ten attempts/minute global limit, 32-device cap, native revoke-all and renew controls. Server restarts preserve trusted credentials; previous ephemeral tokens are invalidated.
- Phone hosting keeps the screen awake while active. No background-service or public-hosting guarantee; HTTP remains unencrypted and trusted-LAN-only.
- Dashboard Insights/Inventory/Activity/Live scan tabs, grid/list, verified product photos or honest placeholders, category/7-day/24-hour charts based on stored history, non-interrupting scan notification, focus-preserving table updates, and remembered reconnect.
- Embedded Manrope variable font (OFL), local QR encoder (MIT), custom vector Mario-inspired no-fail level loop and additional startup/chart/panel animations. Camera unobstructed; reduced motion and toggles honored. Updated home UI and legacy visible branding. Third-party notices included in APK assets.
- Tests: all prior 18 JS suites plus cigarette/live-state suite; Chromium menu touch, fast scan, photos, motion, cinematic and credits; new live/pairing browser tests (saved reconnect, QR-fragment cleanup, scan notification during an edit, grid and charts); actual rendered QR decoded by OpenCV; existing Java socket suite plus new pairing/persistence/revocation/rate-limit/long-poll timing suite.
- See Browser-access-guide.md for operational limits. Physical Android device/camera/Wi-Fi/QR-scanner behavior remains untested.
- Final hardening: browser trust preferences are excluded from Android cloud backup/device transfer; inventory backup settings remain intact. Large embedded manual photos are resized to small dashboard-only previews with two-at-a-time processing; original phone photos are not modified.
