from pathlib import Path
p=Path('/home/user/trill-inventory/index.html');s=p.read_text()
pos=s.index('/* Searches product databases by name.')
s=s[:pos]+'''/* Tobacco identity assistance: never infer a SKU from a brand or prefix. */
function isTobacco(text){
  return /\\b(tobacco|cigarettes?|cigarillos?|cigars?|snuff|snus|dip|vapes?|nicotine|marlboro|newport|camel|pall mall|winston|kool|salem|american spirit|grizzly|copenhagen|skoal|zyn|on!|velo|black & mild|swisher)\\b/i.test(text || '');
}
function tobaccoText(it){ return [it.title, it.brand, it.category, it.size].filter(Boolean).join(' '); }
function tobaccoVariant(text){
  var t = String(text || '').toLowerCase();
  return {
    menthol: /non[- ]?menthol/.test(t) ? 'non-menthol' : /menthol/.test(t) ? 'menthol' : '',
    length: /\\b100(?:s|mm)?\\b/.test(t) ? '100s' : /\\b120(?:s|mm)?\\b/.test(t) ? '120s' : /\\bking(?:s)?\\b/.test(t) ? 'king' : '',
    unit: /\\bcarton\\b/.test(t) ? 'carton' : /\\bpack\\b/.test(t) ? 'pack' : '',
    strength: (t.match(/\\b\\d+(?:\\.\\d+)?\\s*mg\\b/) || [''])[0].replace(/\\s/g,'')
  };
}
function tobaccoWarnings(query, it){
  var a = tobaccoVariant(query), b = tobaccoVariant(tobaccoText(it)), warnings = [];
  Object.keys(a).forEach(function(k){ if(a[k] && b[k] && a[k] !== b[k]) warnings.push(a[k] + ' ≠ ' + b[k]); });
  return warnings;
}
function prepareTobaccoMatches(items, query){
  if(!isTobacco(query)) return items;
  return items.slice().sort(function(a,b){
    function score(it){
      var exact = it.code && barcodeCandidates(it.code).indexOf(String(currentUpc)) >= 0;
      var text = tobaccoText(it).toLowerCase();
      var words = query.toLowerCase().split(/\\s+/).filter(Boolean);
      return (exact ? 1000 : 0) + words.filter(function(w){return text.indexOf(w)>=0;}).length * 5 - tobaccoWarnings(query,it).length * 30;
    }
    return score(b)-score(a);
  });
}
function tobaccoHelperHTML(){
  return '<details class="setgroup"><summary>Cigarettes, cigars, dip or nicotine? Tap here</summary><div class="setgroup-body">' +
    '<p class="desc">Scan the retail barcode, not the tax stamp. Pack and carton barcodes can be different. Never substitute a nearby barcode.</p>' +
    '<div class="field"><label>Brand and variant</label><input id="tobaccoName" placeholder="e.g. Marlboro Gold or ZYN Cool Mint"></div>' +
    '<div class="row2"><div class="field"><label>Product type</label><select id="tobaccoType"><option>Cigarettes</option><option>Cigars</option><option>Cigarillos</option><option>Dip tobacco</option><option>Nicotine pouches</option><option>Vape</option></select></div>' +
    '<div class="field"><label>Size / strength / unit</label><input id="tobaccoVariant" placeholder="100s non-menthol pack, or 6 mg"></div></div>' +
    '<button class="btn btn-block" data-act="tobaccoFind">Find this tobacco product</button>' +
    '<p class="desc">Results are suggestions, not verified matches. Check the flavor, length, strength and pack/carton. No result? Save the printed name under the scanned barcode; future scans work offline. Set your actual shelf price — tobacco taxes and listing units vary.</p></div></details>';
}

'''+s[pos:]
s=s.replace("  var t = String(text || '').toLowerCase();\n  var map = [", "  var t = String(text || '').toLowerCase();\n  if(isTobacco(t)) return 'Tobacco';\n  var map = [")
s=s.replace("  body += '<div class=\"sect-title\">Product identity</div>';", "  body += tobaccoHelperHTML();\n  body += '<div class=\"sect-title\">Product identity</div>';")
s=s.replace("  matchState.items = items || [];", "  matchState.selected = -1;\n  matchState.items = prepareTobaccoMatches(items || [], matchState.query);") # selection needs preserve rerender
s=s.replace("  matchState.selected = -1;\n  matchState.items = prepare", "  matchState.items = prepare")
s=s.replace("  matchState.query = query;", "  matchState.query = query;\n  matchState.selected = -1;")
s=s.replace("    var price = it.priceLow > 0 ? money(unitPriceOf(it)) : '';", "    var tobacco = isTobacco(tobaccoText(it)) || isTobacco(matchState.query);\n    if(tobacco) meta += ' · ' + (tobaccoWarnings(matchState.query,it).join(' · ') || 'Verify variant and retail unit') + ' · Barcode: ' + (it.code || 'not supplied');\n    var price = tobacco && !it.local ? '' : it.priceLow > 0 ? money(unitPriceOf(it)) : '';")
s=s.replace("  matchState.selected = idx;\n\n  var setV", "  var tobacco = isTobacco(tobaccoText(it)) || isTobacco(matchState.query);\n  if(tobacco && !confirm('Confirm the printed brand, variant, strength and pack/carton match this result.\\n' + it.title + '\\n' + tobaccoWarnings(matchState.query,it).join(', ') + '\\nThe scanned barcode will be kept; this does not prove the barcodes are equivalent.')) return;\n  matchState.selected = idx;\n\n  var setV")
s=s.replace("  if(it.pack > 0) setV('newPack', it.pack);", "  if(it.pack > 0 && !tobacco) setV('newPack', it.pack);")
s=s.replace("  if(it.priceLow > 0){\n    var unitPrice", "  if(tobacco && !it.local){\n    setV('newPrice', ''); setV('newCost', '');\n    warnMsg = 'Identity selected — enter your actual shelf price and cost';\n  } else if(it.priceLow > 0){\n    var unitPrice")
s=s.replace("  if(act === 'matchSearch'){", "  if(act === 'tobaccoFind'){\n    var name = $('tobaccoName').value.trim();\n    if(!name){ toast('Enter the printed brand and variant', 'bad'); return; }\n    var query = name + ' ' + $('tobaccoType').value + ' ' + $('tobaccoVariant').value.trim();\n    $('newName').value = query.trim(); $('matchQuery').value = query.trim(); $('newCat').value = 'Tobacco';\n    runMatchSearch(query); return;\n  }\n  if(act === 'matchSearch'){")
s=s.replace("  pre.nOffers = offers.length;", "  pre.nOffers = offers.length;\n  if(isTobacco(pre.name + ' ' + pre.cat)){ pre.price = 0; pre.cost = 0; return pre; }")
s=s.replace("  if(item.pack > 0) entry.pack = item.pack;", "  if(item.pack > 0 && !isTobacco(tobaccoText(item))) entry.pack = item.pack;")
s=s.replace("  if(alsoPrice && item.priceLow > 0){", "  if(alsoPrice && isTobacco(tobaccoText(item)) && !item.local){ toast('Tobacco identity only — set your actual shelf price manually', 'bad'); alsoPrice = false; }\n  if(alsoPrice && item.priceLow > 0){")
p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=Path('/home/user/trill-inventory')/f;s=p.read_text().replace('1.4.0','1.5.0').replace('--version-code 5','--version-code 6').replace('versionCode="5"','versionCode="6"');p.write_text(s)
