from pathlib import Path
r=Path('/home/user/trill-inventory');p=r/'index.html';s=p.read_text();s=s.replace("  body += '<div class=\"sect-title\">Pricing</div>';", "  body += '<div class=\"sect-title\">Pricing</div>';\n  body += '<button class=\"btn btn-primary btn-block\" data-act=\"editPrice\" style=\"margin-bottom:12px\">✎ Edit price</button>';")
pos=s.index('/* sheet actions */');s=s[:pos]+'''/* Quick, offline price editing. Stock counts are never touched. */
var priceEditState = null;
function showPriceEditor(upc){
  var p = getProduct(upc); if(!p) return;
  var qty = pendingQty;
  openSheet('Edit price', p.name + ' · ' + upc,
    '<p class="desc">Price for one inventory unit — not the entire case. Current shelf price: <b>' + money(p.price) + '</b>.</p>' +
    '<div class="field"><label for="editShelfPrice">New shelf price</label><input id="editShelfPrice" type="text" inputmode="decimal" autocomplete="off" value="' + Number(p.price || 0).toFixed(2) + '"></div>' +
    '<div class="field"><label for="editUnitCost">Unit cost (optional)</label><input id="editUnitCost" type="text" inputmode="decimal" autocomplete="off" value="' + Number(p.cost || 0).toFixed(2) + '"></div>' +
    '<p class="desc">Leave unit cost blank to keep the existing cost. Saving changes pricing only — not your stock, picture, or product identity.</p>' +
    '<div id="editPricePreview" class="prodnote" aria-live="polite"></div>' +
    '<p id="editPriceError" role="alert" style="color:var(--bad)"></p>',
    '<button class="btn" data-act="cancelPrice">Cancel</button><button class="btn btn-primary" id="savePriceButton" data-act="savePrice">Save price</button>');
  priceEditState = {upc:upc, qty:qty, cost:Number(p.cost || 0)};
  ['editShelfPrice','editUnitCost'].forEach(function(id){
    $(id).addEventListener('input', previewPriceEdit);
    $(id).addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();savePriceEdit();}});
  });
  previewPriceEdit();$('editShelfPrice').focus();$('editShelfPrice').select();
}
function parsePriceInput(value){
  var text = String(value || '').trim();
  if(!/^(?:\\d{1,5}(?:\\.\\d{0,2})?|\\.\\d{1,2})$/.test(text)) return null;
  var value = Number(text);
  return isFinite(value) && value >= 0 && value <= 99999.99 ? Math.round(value * 100)/100 : null;
}
function priceEditValues(){
  var price = parsePriceInput($('editShelfPrice').value), raw = $('editUnitCost').value.trim();
  var cost = raw === '' ? priceEditState.cost : parsePriceInput(raw);
  return {price:price,cost:cost};
}
function previewPriceEdit(){
  if(!priceEditState || !$('editShelfPrice')) return;
  var v = priceEditValues(), valid = v.price !== null && v.cost !== null;
  $('savePriceButton').disabled = !valid;
  $('editPriceError').textContent = valid ? '' : 'Enter a nonnegative amount with up to two decimal places (for example, 8.99).';
  $('editPricePreview').textContent = valid ?
    'New price: ' + money(v.price) + ' · Profit/unit: ' + money(v.price-v.cost) +
    (v.price > 0 ? ' · Margin: ' + ((v.price-v.cost)/v.price*100).toFixed(1) + '%' : ' · No margin on a zero price') +
    (v.price < v.cost ? ' — Below unit cost' : '') : 'Check the amounts above.';
}
function returnFromPriceEdit(){
  var state = priceEditState; if(!state) return;
  priceEditState = null;
  showResult(state.upc,'price'); pendingQty = state.qty; refreshQtyVal();
}
function savePriceEdit(){
  var state = priceEditState;
  if(!state || !sheetOpen || state.upc !== currentUpc || !$('editShelfPrice')) return;
  var v = priceEditValues();
  if(v.price === null || v.cost === null){previewPriceEdit();return;}
  if(v.price === 0 && !confirm('Set this product’s shelf price to zero?')) return;
  var next = EXTRA.map(function(p){return Object.assign({},p);});
  var entry = next.find(function(p){return String(p.upc)===String(state.upc);});
  if(!entry){entry={upc:state.upc};next.push(entry);}
  entry.price=v.price;entry.cost=v.cost;entry.priceEditedAt=Date.now();
  try {
    if(!storageOK) throw new Error('Storage unavailable');
    localStorage.setItem('hs.catalog',JSON.stringify(next));
  } catch(e){$('editPriceError').textContent='Could not save: device storage is full or unavailable. Your previous price is unchanged.';return;}
  EXTRA=next;rebuildIndex();
  PRICEMETA[state.upc]={price:v.price,source:'manual edit',at:entry.priceEditedAt};lsSet('hs.pricemeta',PRICEMETA);
  returnFromPriceEdit();toast('Price saved: ' + money(v.price) + ' — stock unchanged','good');
}

''' +s[pos:]
s=s.replace("function sheetAction(act, btn){", "function sheetAction(act, btn){\n  if(act === 'editPrice'){showPriceEditor(currentUpc);return;}\n  if(act === 'savePrice'){savePriceEdit();return;}\n  if(act === 'cancelPrice'){returnFromPriceEdit();return;}")
p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=r/f;s=p.read_text().replace('1.7.0','1.8.0').replace('--version-code 9','--version-code 10').replace('versionCode="9"','versionCode="10"');p.write_text(s)
