// Native file-chooser regression: the WebView chooser must honor each input's
// accept attribute (photos for photo inputs, real files for .nes/.csv).
const fs = require('fs'), path = require('path');
const java = fs.readFileSync(path.join(__dirname, '..', 'android/src/com/harrys/scan/MainActivity.java'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const ok = (n, c) => { console.log((c ? '  ok    ' : '  FAIL  ') + n); if (!c) process.exitCode = 1; };
ok('chooser reads getAcceptTypes()', java.includes('getAcceptTypes()'));
ok('chooser no longer hardcodes image/* for everything', !/pick\.setType\("image\/\*"\)\s*;\s*try/.test(java));
ok('photo inputs still get image/*', java.includes('wantsImage && !wantsAny') && java.includes('pick.setType("image/*")'));
ok('.nes accepts route to a file picker (*/*)', java.includes('wantsRom') && java.includes('pick.setType("*/*")'));
ok('chooser title adapts (ROM/CSV/photo)', java.includes('Choose ROM file (.nes)') && java.includes('Choose CSV file'));
ok('web ROM input still declares accept=.nes', /id="emuRomFile" accept="\.nes"/.test(html));
ok('web CSV input declares accept=.csv', html.includes('accept=".csv,text/csv"'));
console.log(process.exitCode ? 'NATIVE CHOOSER TEST FAILED' : 'NATIVE CHOOSER TEST OK');
