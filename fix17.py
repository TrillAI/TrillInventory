from pathlib import Path
root=Path('/home/user/trill-inventory')
p=root/'android/src/com/harrys/scan/MainActivity.java';s=p.read_text();s=s.replace('    private class HostBridge {','''    private class HostBridge {

        @JavascriptInterface
        public void httpGet(final String url, final String reqId) {
            MainActivity.this.httpGet(url, reqId);
        }
''');s=s.replace('HarrysScan/1.1 (Android)','TrillInventory/1.6.1 (Android)');s=s.replace('conn.setInstanceFollowRedirects(true);','conn.setInstanceFollowRedirects(false); // Do not follow redirects outside the host allowlist.')
p.write_text(s)
p=root/'index.html';s=p.read_text();a=s.index('function provOFF(upc)');b=s.index('/* ---- name search',a);part=s[a:b];part=part.replace("      if(!r.ok) return { ok:false, note:'http ' + r.status };\n      var d = parseJSON(r.text);", "      var d = parseJSON(r.text);\n      // OFF uses a structured 404 for an absent product. An HTML 404 is a service error.\n      if(r.status === 404 && d && d.status === 0) return { ok:false, note:'not in database' };\n      if(!r.ok) return { ok:false, note:'http ' + r.status };\n")
s=s[:a]+part+s[b:]
# fail explicitly instead of silently falling through to a CORS-blocked browser path on old native wrappers
s=s.replace("function onlineReady(){", "function nativeLookupBroken(){ return !!window.AndroidHost && !hasNativeHttp(); }\nfunction onlineReady(){")
s=s.replace("  timeoutMs = timeoutMs || 13000;", "  timeoutMs = timeoutMs || 13000;\n  if(nativeLookupBroken()) return Promise.reject(new Error('Android lookup connection unavailable — install Trill Inventory 1.6.1 or later'));")
old="if(failures.length) txt = 'Lookup incomplete — ' + esc(failures.map(function(x){return x.name + ': ' + x.note;}).join('; ')) + '. This does not mean the barcode is invalid. Retry later or name it below.';"
new="""if(failures.length){
    txt = 'Some lookup services could not be reached. This does not mean the barcode is invalid. You can retry later, search by name, or save the printed details below.' +
      '<details style="margin-top:8px"><summary>Lookup incomplete — service details</summary>' +
      esc(failures.map(function(x){return x.name + ': ' + x.note;}).filter(function(v,i,a){return a.indexOf(v)===i;}).join('; ')) + '</details>';
  }"""
assert old in s;s=s.replace(old,new);p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=root/f;s=p.read_text().replace('1.6.0','1.6.1').replace('--version-code 7','--version-code 8').replace('versionCode="7"','versionCode="8"');p.write_text(s)
