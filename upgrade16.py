from pathlib import Path
p=Path('/home/user/trill-inventory/index.html');s=p.read_text();a=s.index('function upceToUpca(');b=s.index('\nfunction barcodeCandidates',a)
s=s[:a]+'''function upceToUpca(code){
  if(!/^[01]\\d{7}$/.test(code)) return '';
  var ns = code.charAt(0), x = code.substr(1,6), last = +x.charAt(5), payload;
  if(last <= 2) payload = ns + x.substr(0,2) + last + '0000' + x.substr(2,3);
  else if(last === 3) payload = ns + x.substr(0,3) + '00000' + x.substr(3,2);
  else if(last === 4) payload = ns + x.substr(0,4) + '00000' + x.charAt(4);
  else payload = ns + x.substr(0,5) + '0000' + last;
  var expanded = payload + code.charAt(7);
  return checkDigitOK(expanded) === true ? expanded : '';
}
''' + s[b:]
s=s.replace("      if(upca) out.push(upca);", "      out.push(digits); // EAN-8 and UPC-E are distinct; do not silently replace the scanned number\n      if(upca) out.push(upca);")
s=s.replace("    if(digits.length === 13) out.push(digits.substr(1));", "    if(digits.length === 14 && digits.substr(0,2) === '00') out.push(digits.substr(2), digits.substr(1));")
# allow identity even with price fetching disabled
s=s.replace("    if((name === 'upcitemdb' || name === 'openprices') && !S.netPrices) return step();", "    if(name === 'openprices' && !S.netPrices) return step();\n    if(name === 'upcitemdb' && !S.netPrices && !S.netIdentity) return step();")
s=s.replace("        if(res.offers && res.offers.length) result.offers = result.offers.concat(res.offers);", "        if(S.netPrices && res.offers && res.offers.length) result.offers = result.offers.concat(res.offers);")
a=s.index('function lookupOnline(upc, force)');b=s.index('\nfunction guessCategory',a)
s=s[:a]+'''function lookupOnline(upc, force){
  var ttl = Math.max(1, S.netCacheHours) * 3600000;
  var c = NETCACHE[upc];
  // Empty results expire quickly. Transport/rate-limit errors are never cached.
  if(c && !c.identity && !(c.offers || []).length && !(c.oldOffers || []).length) ttl = 60000;
  var failed = c && (c.sources || []).some(function(x){return /timeout|http |rate limit|failed|network|limit reached/i.test(x.note || '');});
  if(c && !failed && !force && c.at && (Date.now() - c.at) < ttl){
    var copy = JSON.parse(JSON.stringify(c)); copy.cached = true;
    return Promise.resolve(copy);
  }
  var candidates = barcodeCandidates(upc), tried = [];
  var merged = {upc:upc, identity:null, offers:[], oldOffers:[], sources:[], at:Date.now()};
  function next(){
    var code = candidates.shift();
    if(!code) return Promise.resolve(merged);
    tried.push(code);
    return runProviders(code).then(function(res){
      merged.sources = merged.sources.concat((res.sources || []).map(function(x){return Object.assign({}, x, {barcode:code});}));
      merged.identity = merged.identity || res.identity;
      merged.offers = merged.offers.concat(res.offers || []);
      merged.oldOffers = merged.oldOffers.concat(res.oldOffers || []);
      if(merged.identity || merged.offers.length || merged.oldOffers.length || Date.now() < netPenaltyUntil) return merged;
      return next();
    });
  }
  return next().then(function(res){
    res.tried = tried;
    var errors = res.sources.some(function(x){return /timeout|http |rate limit|failed|network|limit reached/i.test(x.note || '');});
    if(!errors){ NETCACHE[upc] = JSON.parse(JSON.stringify(res)); saveNetCache(); }
    return res;
  });
}
''' +s[b:]
# unknown retry easy accessible. inline retailer helper preserves editing state
s=s.replace("  body += onlineNote(res);", "  body += onlineNote(res);\n  body += '<button class=\"btn btn-block\" data-act=\"retryBarcode\">Retry barcode lookup (ignore cache)</button>';\n  body += retailerPanel(upc, pre.name);")
s=s.replace("  body += '<div class=\"hero-info\"><h3>' + esc(id.name", "  body += '<div class=\"hero-info\"><h3>' + esc(id.name") # no-op
s=s.replace("  // pack-size sanity check\n", "  body += retailerPanel(upc, id.name || (local && local.name));\n  // pack-size sanity check\n")
s=s.replace("  // ---- stock block", "  body += retailerPanel(upc, p.name);\n  // ---- stock block")
s=s.replace("'Suggested shelf price'", "'Online reference price (not local)'")
s=s.replace("(o.date ? esc(ago(o.date)) : 'date unknown') + '</small></div>'", "(o.date ? esc(ago(o.date)) : 'date unknown') + ' · Local store unverified</small></div>'")
# async race guard and retry
s=s.replace("var onlineResult = null, onlineLoading = false;", "var onlineResult = null, onlineLoading = false, unknownRequest = 0;")
s=s.replace("function showUnknown(upc){", "function showUnknown(upc, force){\n  var request = ++unknownRequest;")
s=s.replace("  lookupOnline(upc).then(function(res){", "  lookupOnline(upc, !!force).then(function(res){")
# only unknown section
start=s.index('function showUnknown(');end=s.index('function prefillFromOnline',start)
part=s[start:end].replace("if(!sheetOpen || currentUpc !== upc)","if(request !== unknownRequest || !sheetOpen || currentUpc !== upc)")
s=s[:start]+part+s[end:]
s=s.replace("  if(act === 'checkOnline'){", "  if(act === 'retryBarcode'){ showUnknown(currentUpc, true); return; }\n  if(act === 'retailerSearch'){ refreshRetailerLinks(); return; }\n  if(act === 'saveObserved'){ saveObservedPrice(); return; }\n  if(act === 'checkOnline'){")
pos=s.index('function todayKey()')
s=s[:pos]+'''// Local comparison observations are explicitly user-entered, never retailer API quotes.
var RETAILAREA = lsGet('trill.retailArea', '37311');
var OBSERVED = lsGet('trill.observedPrices', {});
var RETAILERS = [
  ['Walmart','https://www.walmart.com/search?q='],
  ['Target','https://www.target.com/s?searchTerm='],
  ['Kroger','https://www.kroger.com/search?query='],
  ['Walgreens','https://www.walgreens.com/search/results.jsp?Ntt='],
  ['CVS','https://www.cvs.com/search?searchTerm=']
];
function retailerLinks(query){
  return RETAILERS.map(function(r){ return '<a class="btn" style="text-decoration:none" href="' + esc(r[1] + encodeURIComponent(query)) + '">' + esc(r[0]) + ' ↗</a>'; }).join(' ');
}
function observedHTML(upc){
  var rows = (OBSERVED[upc] || []).slice().reverse();
  return rows.map(function(o){return '<div class="offer"><div class="op">' + money(o.price) + '</div><div class="om"><b>' + esc(o.store) + '</b><small>ZIP ' + esc(o.zip) + ' · ' + esc(o.unit) + ' · ' + esc(ago(o.at)) + '<br>User-entered observation — not live</small></div></div>';}).join('') || '<p class="desc">No local observations saved for this barcode.</p>';
}
function retailerPanel(upc, name){
  return '<details class="setgroup"><summary>Compare nearby-store prices · ' + esc(RETAILAREA) + '</summary><div class="setgroup-body">' +
    '<p class="desc"><b>Manual retailer check — not automatic local pricing.</b> Open a retailer, select your actual store near the ZIP below, and confirm product size, availability and price. Search links do not select a store or guarantee a match. Links send only your search text to that retailer.</p>' +
    '<div class="row2"><div class="field"><label>Area ZIP</label><input id="retailZip" inputmode="numeric" maxlength="5" value="' + esc(RETAILAREA) + '"></div><div class="field"><label>Barcode or product name</label><input id="retailQuery" value="' + esc(name || upc) + '"></div></div>' +
    '<button class="btn btn-block" data-act="retailerSearch">Update search links / save area</button>' +
    '<div id="retailLinks" style="display:flex;flex-wrap:wrap;gap:8px;margin:12px 0">' + retailerLinks(name || upc) + '</div>' +
    '<p class="desc">If a barcode search finds nothing, enter the printed brand, flavor and size above. Tobacco listings may be unavailable.</p>' +
    '<div class="sect-title">Record a price you checked</div>' +
    '<div class="field"><label>Retailer and exact store / address</label><input id="observedStore" placeholder="e.g. Walmart, street or store number"></div>' +
    '<div class="row2"><div class="field"><label>Observed price (USD)</label><input id="observedPrice" type="number" min="0.01" step="0.01" inputmode="decimal"></div><div class="field"><label>Exact listing size / unit</label><input id="observedUnit" placeholder="e.g. 20-count pack or 12 fl oz can"></div></div>' +
    '<button class="btn btn-block" data-act="saveObserved">Save comparison only</button>' +
    '<p class="desc">Confirm the exact product first. Saving records the current time and never changes your shelf price or inventory.</p><div id="observedRows">' + observedHTML(upc) + '</div></div></details>';
}
function refreshRetailerLinks(){
  var zip = $('retailZip').value.trim(), q = $('retailQuery').value.trim();
  if(!/^\\d{5}$/.test(zip) || !q){ toast('Enter a five-digit ZIP and product or barcode', 'bad'); return; }
  RETAILAREA = zip; lsSet('trill.retailArea', zip);
  $('retailLinks').innerHTML = retailerLinks(q);
  toast('Links updated. Select the exact store on the retailer website.');
}
function saveObservedPrice(){
  var store = $('observedStore').value.trim(), unit = $('observedUnit').value.trim(), zip = $('retailZip').value.trim();
  var price = Number($('observedPrice').value);
  if(!store || !unit || !/^\\d{5}$/.test(zip) || !isFinite(price) || price <= 0 || price > 99999){ toast('Enter store, ZIP, listing size and a valid price', 'bad'); return; }
  var rows = OBSERVED[currentUpc] || [];
  rows.push({store:store.slice(0,150), unit:unit.slice(0,100), zip:zip, price:Math.round(price*100)/100, at:Date.now()});
  OBSERVED[currentUpc] = rows.slice(-30); lsSet('trill.observedPrices', OBSERVED);
  RETAILAREA = zip; lsSet('trill.retailArea', zip);
  $('observedRows').innerHTML = observedHTML(currentUpc);
  toast('Comparison saved — inventory and shelf price unchanged', 'good');
}

''' + s[pos:]
p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=Path('/home/user/trill-inventory')/f;s=p.read_text().replace('1.5.0','1.6.0').replace('--version-code 6','--version-code 7').replace('versionCode="6"','versionCode="7"');p.write_text(s)
