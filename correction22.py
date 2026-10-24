from pathlib import Path
p=Path('/home/user/trill-inventory/index.html');s=p.read_text();pos=s.index('/* sheet actions */');s=s[:pos]+'''/* Correct one saved record without adding another unit or erasing stock. */
var correctionState=null;
function showProductCorrection(upc){
  var p=getProduct(upc);if(!p)return;
  correctionState={upc:upc,price:Number(p.price || 0),cost:Number(p.cost || 0),original:JSON.stringify(p)};
  var body='<p class="desc">Read the name and size from the actual package. Barcode <b>'+esc(upc)+'</b> and all stock counts stay unchanged. Blank price/cost keeps your saved amount.</p>';
  [['correctName','Product name',p.name],['correctBrand','Brand',p.brand || ''],['correctSize','Exact size / pack variant',p.size || '']].forEach(function(f){body+='<div class="field"><label>'+f[1]+'</label><input id="'+f[0]+'" value="'+esc(f[2])+'"></div>';});
  body+='<div class="row2"><div class="field"><label>Shelf price (optional)</label><input id="correctPrice" inputmode="decimal" placeholder="Keep '+Number(p.price || 0).toFixed(2)+'"></div><div class="field"><label>Unit cost (optional)</label><input id="correctCost" inputmode="decimal" placeholder="Keep '+Number(p.cost || 0).toFixed(2)+'"></div></div>';
  body+='<label style="display:block;margin:12px 0"><input id="correctChecked" type="checkbox"> I checked these details against the actual package.</label>';
  body+='<label style="display:block;margin:12px 0"><input id="correctKeepPicture" type="checkbox"> Keep the current picture (only if it matches).</label><p class="desc">Otherwise the picture is removed. Use Update picture after saving to add the right one.</p><p id="correctError" role="alert"></p>';
  openSheet('Correct product details',p.name,body,'<button class="btn" data-act="correctCancel">Cancel</button><button class="btn btn-primary" data-act="correctSave">Save correction</button>');
}
function saveProductCorrection(){
  var state=correctionState;if(!state || !$('correctName') || currentUpc!==state.upc)return;
  var p=getProduct(state.upc);
  if(JSON.stringify(p)!==state.original){$('correctError').textContent='This record changed on another device. Cancel and reopen before editing.';return;}
  var name=$('correctName').value.trim(),size=$('correctSize').value.trim();
  if(!name || !size || !$('correctChecked').checked){$('correctError').textContent='Enter the name and size, then confirm the actual package.';return;}
  var a=$('correctPrice').value.trim(),b=$('correctCost').value.trim(),price=a ? parsePriceInput(a) : state.price,cost=b ? parsePriceInput(b) : state.cost;
  if(price===null || cost===null){$('correctError').textContent='Enter valid nonnegative prices with at most two decimals.';return;}
  var record=Object.assign({},p,{name:name.slice(0,180),brand:$('correctBrand').value.trim().slice(0,80),size:size.slice(0,100),price:price,cost:cost,needsReview:false,identityReviewedAt:Date.now()});
  if(p.legacySource){record.specs=[];record.desc='Product details corrected against package.';record.supplier='Unassigned';record.shelf='Unassigned';}
  if(!$('correctKeepPicture').checked){record.image='';record.imageVerifiedAt=0;record.imageSource='';}
  var next=EXTRA.filter(function(x){return String(x.upc)!==String(state.upc);}).concat([record]);
  try{if(!storageOK)throw new Error('no storage');localStorage.setItem('hs.catalog',JSON.stringify(next));}catch(e){$('correctError').textContent='Could not save. Your previous record is unchanged.';return;}
  EXTRA=next;rebuildIndex();
  if(a || b){PRICEMETA[state.upc]={price:price,source:'manual correction',at:Date.now()};lsSet('hs.pricemeta',PRICEMETA);}
  correctionState=null;showResult(state.upc,'correction');toast('Details corrected — stock count unchanged','good');
}

''' +s[pos:];s=s.replace("function sheetAction(act, btn){", "function sheetAction(act, btn){\n  if(act==='correctProduct'){showProductCorrection(currentUpc);return;}\n  if(act==='correctSave'){saveProductCorrection();return;}\n  if(act==='correctCancel'){correctionState=null;showResult(currentUpc,'manual');return;}")
p.write_text(s)
p=Path('/home/user/trill-inventory/android/vendor/remote.html');s=p.read_text().replace("tr.children[0].querySelector('b').textContent=r.name;", "tr.children[0].querySelector('b').textContent=(r.needsReview?'⚠ Review on phone: ':'')+r.name;");p.write_text(s)
