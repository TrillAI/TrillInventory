from pathlib import Path
r=Path('/home/user/trill-inventory');p=r/'index.html';s=p.read_text()
s=s.replace('autoAdd:false, continuous:false,','autoAdd:false, continuous:false, fastScan:false,')
s=s.replace('    <div id="hud">','''    <div id="hud">
      <div class="fast-controls"><button class="btn" id="btnFastScan" aria-pressed="false">⚡ Fast scan: off</button><button class="btn" id="btnFastUndo" hidden disabled>Undo last +1</button></div>
      <div id="fastScanStatus" class="fast-status" role="status" aria-live="polite" hidden></div>''')
pos=s.index('</style>');s=s[:pos]+'''
.fast-controls{display:flex;gap:8px;margin-bottom:8px}.fast-controls .btn{padding:10px 12px;font-size:.76rem;background:var(--surface-2);border:1px solid var(--line)}
#btnFastScan[aria-pressed="true"]{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.fast-status{padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:var(--surface);font-size:.75rem;line-height:1.5;margin-bottom:8px}
.fast-status.error{border-color:var(--danger);color:var(--danger)}
''' +s[pos:]
# Real ZXing UMD 0.21 API uses a numeric delay and continuous callback method.
a=s.index('    zxReader = new window.ZXing.BrowserMultiFormatReader');b=s.index("    $('retHint').textContent",a)
s=s[:a]+'''    zxReader = new window.ZXing.BrowserMultiFormatReader(zxHints(), S.fastScan ? 120 : 500);
    zxReader.timeBetweenDecodingAttempts=S.fastScan ? 100 : (S.advScan ? 110 : 160);
    zxActive = true;
    zxReader.decodeContinuously($('video'), function(result, err){
      if(!zxActive || scanPaused) return;
      if(result){
        var txt = '', fmt = '';
        try { txt = result.getText(); } catch(e){}
        try { fmt = zxFormatName(result.getBarcodeFormat()); } catch(e){}
        if(txt) onScan(txt, 'camera', fmt);
      }else if(err && (err.name==='NotFoundException' || (typeof err.getKind==='function' && err.getKind()==='NotFoundException'))){
        fastNoCode();
      }
    });
''' +s[b:]
s=s.replace("if(zxReader){ try { zxReader.reset(); } catch(e){} zxReader = null; }", "if(zxReader){try{zxReader.stopContinuousDecode();}catch(e){} try { zxReader.reset(); } catch(e){} zxReader = null; }")
s=s.replace("      if(code) onScan(code, 'camera', codes[0].format || '');\n    }", "      if(code) onScan(code, 'camera', codes[0].format || '');\n    }else fastNoCode();")
s=s.replace("  var now = Date.now();\n  if(upc === lastUpc", "  if(S.fastScan){\n    if(source==='camera' && !fastCaptureReady())return;\n    if(!fastScanAccepted(upc,source || 'manual'))return;\n    return commitFastScan(upc);\n  }\n  var now = Date.now();\n  if(upc === lastUpc",1)
s=s.replace("    {k:'autoAdd', t:'toggle'", "    {k:'fastScan', t:'toggle', label:'Fast scan · +1 per scan', d:'Save every barcode immediately without a product sheet. Clear the barcode from view before scanning an identical item. Overrides review/quantity settings.'},\n    {k:'autoAdd', t:'toggle'",1)
s=s.replace("  $('navInvSub').textContent =", "  renderFastStatus();\n  $('navInvSub').textContent =",1)
s=s.replace("  $('btnManual').addEventListener('click', viewManual);", "  $('btnManual').addEventListener('click', viewManual);\n  $('btnFastScan').addEventListener('click',function(){setFastScan(!S.fastScan,true);});\n  $('btnFastUndo').addEventListener('click',undoFastScan);")
s=s.replace("      var k = t.getAttribute('data-toggle');\n      S[k]", "      var k = t.getAttribute('data-toggle');\n      if(k==='fastScan'){setFastScan(!S.fastScan,false);t.setAttribute('aria-checked',String(!!S.fastScan));return;}\n      S[k]",1)
# No parallel photo lookups for an unresolved placeholder. Identity worker triggers photo lookup later.
s=s.replace('return p && !p.needsReview && !p.imageVerifiedAt', 'return p && !p.fastUnresolved && !p.needsReview && !p.imageVerifiedAt')
s=s.replace("  if(p.needsReview)body +=", "  if(p.fastUnresolved || p.fastNeedsReview)body += '<div class=\"prodnote\">ℹ️ <div>Counted in Fast scan. ' + (p.fastUnresolved ? 'Product details are not identified yet; the barcode and stock are saved.' : 'Details came from a barcode database. Check them against the package.') + ' Use Correct saved details to review.</div></div>';\n  if(p.needsReview)body +=",1)
s=s.replace("needsReview:false,identityReviewedAt:Date.now()", "needsReview:false,fastUnresolved:false,fastNeedsReview:false,identityReviewedAt:Date.now()")
s=s.replace("  setTimeout(scheduleMissingPhotos,1200);", "  setTimeout(function(){scheduleFastDetails();scheduleMissingPhotos();},1200);")
s=s.replace("label:'Version 1.13.0'", "label:'Version 1.14.0'")
p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=r/f;s=p.read_text().replace('1.13.0','1.14.0').replace('--version-code 16','--version-code 17').replace('versionCode="16"','versionCode="17"');p.write_text(s)
