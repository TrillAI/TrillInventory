from pathlib import Path
r=Path('/home/user/trill-inventory');p=r/'index.html';s=p.read_text()
s=s.replace('var SEED = [','var LEGACY_CATALOG = [',1)
s=s.replace('  SEED.concat(EXTRA).forEach(function(p){','  EXTRA.forEach(function(p){')
s=s.replace('  // allCatalog() merges EXTRA over SEED field-by-field, so a price or info\n  // override never wipes out the rest of the product record.','  // Only explicitly saved/imported records belong in the active catalog.')
# retire all legacy migration data after one in-memory pass; never seed scans
pos=s.index('function persist(){')
s=s[:pos]+'''// Recover old counted records and partial overrides without creating a starter catalog.
(function migrateLegacyCatalog(){
  var next=EXTRA.map(function(p){return Object.assign({},p);}), changed=false;
  LEGACY_CATALOG.forEach(function(old){
    var index=next.findIndex(function(p){return String(p.upc)===String(old.upc);}),saved=index>=0 ? next[index] : null;
    if(!INV[old.upc] && !saved)return;
    if(saved && saved.name && saved.sku!==old.sku)return;
    if(saved && saved.identityReviewedAt)return;
    var record=Object.assign({},old,saved || {},{needsReview:true,legacySource:true});
    if(index>=0)next[index]=record;else next.push(record);
    changed=true;
  });
  if(changed){EXTRA=next;lsSet('hs.catalog',EXTRA);}
  LEGACY_CATALOG=[];
  rebuildIndex();
})();

''' +s[pos:]
s=s.replace("var NETCACHE = lsGet('hs.netcache', {});", "var NETCACHE = lsGet('hs.lookupSchema',0)===2 ? lsGet('hs.netcache', {}) : {};\nlsSet('hs.lookupSchema',2);lsSet('hs.netcache',NETCACHE);")
s=s.replace("      var upca = upceToUpca(digits);\n      out.push(digits); // EAN-8 and UPC-E are distinct; do not silently replace the scanned number\n      if(upca) out.push(upca);", "      out.push(digits); // Expand only when the camera positively reports UPC-E, not for EAN-8/manual digits.")
s=s.replace("if(code) onScan(code, 'camera');", "if(code) onScan(code, 'camera', codes[0].format || '');")
s=s.replace("  var canonical = canonicalCode(raw);", "  var decoded=/^upc[-_ ]?e$/i.test(format || '') ? (upceToUpca(raw) || raw) : raw;\n  var canonical = canonicalCode(decoded);")
pos=s.index('function provUPCitemdb(upc)')
s=s[:pos]+'''function sameRetailBarcode(a,b){
  function key(v){var x=String(v || '').trim();if(/^00\\d{12}$/.test(x))x=x.slice(2);else if(/^0\\d{12}$/.test(x))x=x.slice(1);return x;}
  return !!key(a) && key(a)===key(b);
}

''' +s[pos:]
s=s.replace("      var it = d.items[0], offers = [];", "      var it=d.items.find(function(item){return [item.upc,item.ean,item.gtin].some(function(code){return sameRetailBarcode(upc,code);});});\n      if(!it)return {ok:false,note:'provider returned a different or unverified barcode'};\n      var offers = [];")
s=s.replace("name: it.title || '', brand: it.brand || '', size: it.size || '',", "name: it.title || '', brand: it.brand || '', size: it.size || '', barcode:upc,",1)
s=s.replace("      d.items.forEach(function(it){\n        var pr", "      d.items.forEach(function(it){\n        if(!sameRetailBarcode(upc,it.product_code || (it.product && it.product.code)))return;\n        var pr")
s=s.replace(".json?fields=product_name,brands,quantity,categories,image_small_url", ".json?fields=code,product_name,brands,quantity,categories,image_small_url")
s=s.replace("      var p = d.product;\n      return {", "      var p = d.product;\n      if(!sameRetailBarcode(upc,d.code || p.code))return {ok:false,note:'provider returned a different or unverified barcode'};\n      return {")
s=s.replace("      body += '<div class=\"hero-info\"><h3>'", "      body += '<div class=\"hero-info\"><h3>'")
# banner and correction action on every saved record
needle="  var body = '';\n  body += '<div class=\"hero\">';"
s=s.replace(needle,"  var body = '';\n  if(p.needsReview)body += '<div class=\"prodnote\">⚠️ <div><b>Review required.</b> This saved record used an old sample catalog. Its name, size, price or picture may be wrong. Your counts and edits were kept; check the package and correct the record below.</div></div>';\n  body += '<button class=\"btn btn-block\" data-act=\"correctProduct\" style=\"margin-bottom:12px\">Wrong product? Correct saved details</button>';\n  body += '<div class=\"hero\">';",1)
# always explicit save; no autosaving guessed records
s=s.replace("    if(S.netAutoApply && pre.name && pre.price > 0){\n      saveAutoProduct(upc, pre, res);\n      return;\n    }", "    // Online identity is a suggestion; never auto-save an unconfirmed product.")
a=s.index('  pre.price = suggestedPrice(offers)');b=s.index('  return pre;',a)
# tobacco early return inside block: replace whole tail through next function
end=s.index('\nfunction onlineNote',a)
s=s[:a]+'''  pre.price = 0; pre.cost = 0; pre.pack = 1; // Provider listings are not the store's shelf price or case pack.
  pre.nOffers = offers.length;
  return pre;
}
''' +s[end:]
s=s.replace("  if(!it) return;\n  var tobacco =", "  if(!it) return;\n  if(!it.local && !sameRetailBarcode(currentUpc,it.code) && !confirm('This search result has a different or missing barcode. It is only a suggestion. Confirm the printed brand, variant and size match before using it.\\n' + it.title))return;\n  var tobacco =",1)
s=s.replace("  if(it.pack > 0 && !tobacco) setV('newPack', it.pack);", "  if(it.local && it.pack > 0) setV('newPack',it.pack);")
a=s.index("  if(tobacco && !it.local){",s.index('function chooseMatch'));b=s.index("  var catEl",a)
s=s[:a]+'''  if(!it.local){
    setV('newPrice','');setV('newCost','');
    warnMsg='Product suggestion selected — enter your actual shelf price and unit cost';
  }else if(it.priceLow > 0){setV('newPrice',Number(it.priceLow).toFixed(2));}
''' +s[b:]
s=s.replace("  if(isTobacco(tobaccoText(item)) && !confirm('Verify this tobacco variant and pack/carton against the printed label before applying: ' + item.title)) return;", "  if(!confirm('Confirm the printed product name, variant and size match this suggestion. Stock will not change.\\n' + item.title + '\\nResult barcode: ' + (item.code || 'not supplied') + '\\nScanned barcode: ' + upc))return;")
s=s.replace("  if(item.pack > 0 && !isTobacco(tobaccoText(item))) entry.pack = item.pack;", "  if(item.local && item.pack > 0)entry.pack=item.pack;")
s=s.replace("  if(alsoPrice && item.priceLow > 0){\n    entry.price = item.priceLow;\n    PRICEMETA[upc] = { price: item.priceLow", "  if(alsoPrice && item.priceLow > 0 && confirm('This is an online reference, not your local shelf price. Verify the exact listing unit before applying ' + money(unitPriceOf(item)) + '.')){\n    entry.price = Math.round(unitPriceOf(item)*100)/100;\n    PRICEMETA[upc] = { price: entry.price")
s=s.replace("    if(!entry && SEED.some(function(x){ return String(x.upc) === upc; })){", "    if(!entry){")
s=s.replace("function applyOnlinePrice(upc, price, res){", "function applyOnlinePrice(upc, price, res){\n  if(!confirm('Verify the listing size and units before applying ' + money(price) + '. This is an online reference, not a verified local shelf price.'))return;")
s=s.replace("found + ' of ' + batch.length + ' updated'", "found + ' of ' + batch.length + ' have reference prices'")
s=s.replace("'Updated shelf prices from the median online price.'", "'Reference prices cached. Your shelf prices were NOT changed. Open each product to review.'")
a=s.index('      if(sug > 0){',s.index('function refreshPrices()'));b=s.index('      done++;',a);s=s[:a]+"      if(sug > 0)found++;\n"+s[b:]
s=s.replace("This uses ' + batch.length + ' of your ' + S.netDailyCap + ' daily lookups.", "Each product can use several provider requests, counted against your ' + S.netDailyCap + ' daily request budget.")
s=s.replace("    {k:'netAutoApply', t:'toggle', label:'Auto-add unknown products', d:'Skip the form and catalog new barcodes automatically.'},", "    {k:'netAutoApply', t:'note', label:'Confirm new products', d:'Unknown barcodes always require review. Online prices and case quantities are not automatically applied.'},")
# keep extra metadata and synced copies for review indicator
s=s.replace("rp:Number(p.rp || 0),par:Number(p.par || 0),reorder:rec.units,", "rp:Number(p.rp || 0),par:Number(p.par || 0),reorder:rec.units,needsReview:!!p.needsReview,")
# show name when user saved old seed exact misleading elsewhere marked name needsReview displays tag next to name enough
s=s.replace("      <button class=\"nav-item\" data-nav=\"catalog\"><div class=\"nav-ico\">🏷️</div><div class=\"nav-txt\"><b>Price catalog</b><small id=\"navCatSub\">Harry's shelf prices</small>", "      <button class=\"nav-item\" data-nav=\"catalog\"><div class=\"nav-ico\">🏷️</div><div class=\"nav-txt\"><b>Price catalog</b><small id=\"navCatSub\">Your saved products</small>")
s=s.replace("label:'Version 1.10.0'", "label:'Version 1.10.1'")
p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=r/f;s=p.read_text().replace('1.10.0','1.10.1').replace('--version-code 12','--version-code 13').replace('versionCode="12"','versionCode="13"');p.write_text(s)
