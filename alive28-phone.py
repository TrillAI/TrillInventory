from pathlib import Path
p=Path('/home/user/trill-inventory/index.html');s=p.read_text()
s=s.replace("strength: (t.match", "variant: (t.match(/\\b(red|gold|silver|blue|black|orange|turkish royal|turkish gold)\\b/) || [''])[0],\n    strength: (t.match")
insert='''/* Explicit cigarette inventory units: never merge pack and carton barcodes. */
function isCigarette(p){return !!p && /\\b(cigarettes?|marlboro|newport|pall mall|winston|kool|salem|american spirit|parliament|benson.*hedges)\\b/i.test([p.name,p.brand,p.size].join(' ')) || !!p && /\\bcamel\\b/i.test(p.name+' '+p.brand) && /\\b(tobacco|menthol|100s|filters?|king)\\b/i.test(p.name+' '+p.cat+' '+p.size);}
function cigarettePanel(p,qty){
  if(!isCigarette(p))return '';
  var c=p.cigaretteProfile,confirmed=c && c.unit && c.packs>=2;
  var text=confirmed ? 'Counts and prices are per '+c.unit+'. '+c.packs+' packs per carton'+(c.sticks?' · '+c.sticks+' cigarettes per pack':'')+'.' : 'Confirm the inventory unit from the package. Pack and carton barcodes remain separate; no automatic conversion or merging.';
  if(confirmed && c.unit==='pack')text+=' On hand: '+Math.floor(qty/c.packs)+' full carton equivalents + '+(qty%c.packs)+' loose packs.';
  if(confirmed && c.unit==='carton')text+=' On hand: '+qty+' cartons = '+(qty*c.packs)+' pack equivalents. Loose packs belong under their own barcode.';
  return '<div class="stockbox cigarette-box"><div class="sect-title">Cigarette stock · 21+</div><p class="desc">'+esc(text)+'</p><button class="btn btn-block" data-act="cigaretteSetup">'+(confirmed?'Edit':'Set up')+' pack / carton details</button>'+(confirmed && c.unit==='pack'?'<button class="btn btn-block" data-act="quick" data-n="'+c.packs+'" style="margin-top:8px">Select 1 carton · '+c.packs+' packs</button>':'')+'<p class="desc">Fast scan still adds exactly 1 saved inventory unit per scan. Check brand, color/variant, menthol and length; tax stamps are not product barcodes.</p></div>';
}
var cigaretteEdit=null;
function showCigaretteSetup(){
  var p=getProduct(currentUpc);if(!isCigarette(p))return;var c=p.cigaretteProfile || {};
  cigaretteEdit={upc:currentUpc,original:JSON.stringify(p)};
  openSheet('Pack & carton setup',p.name,'<p class="desc">Choose what this exact barcode represents. This does not convert existing counts or prices. If you counted a different unit before, correct stock and prices before continuing.</p><div class="field"><label>Inventory unit for this barcode</label><select id="cigUnit"><option value="pack">One pack</option><option value="carton">One carton</option></select></div><div class="field"><label>Confirmed packs per carton</label><input id="cigPacks" type="number" min="2" max="100" value="'+(c.packs || '')+'" placeholder="Read the carton; do not guess"></div><div class="field"><label>Cigarettes per pack (optional)</label><input id="cigSticks" type="number" min="1" max="100" value="'+(c.sticks || '')+'"></div><label><input type="checkbox" id="cigConfirmed"> I checked this package and the existing count/price units.</label><p id="cigError" role="alert"></p>','<button class="btn" data-act="cigaretteCancel">Cancel</button><button class="btn btn-primary" data-act="cigaretteSave">Save unit details</button>');
  $('cigUnit').value=c.unit || 'pack';
}
function saveCigaretteSetup(){
  if(!cigaretteEdit || currentUpc!==cigaretteEdit.upc || !$('cigPacks'))return;
  var p=getProduct(currentUpc),packs=Number($('cigPacks').value),sticks=Number($('cigSticks').value),unit=$('cigUnit').value;
  if(JSON.stringify(p)!==cigaretteEdit.original){$('cigError').textContent='Product changed. Cancel and reopen.';return;}
  if(!$('cigConfirmed').checked || !Number.isInteger(packs) || packs<2 || packs>100 || !Number.isInteger(sticks) || sticks<0 || sticks>100 || !/^(pack|carton)$/.test(unit)){$('cigError').textContent='Confirm the package and enter 2–100 packs per carton. Optional cigarettes per pack must be a whole number up to 100.';return;}
  var next=EXTRA.filter(function(x){return String(x.upc)!==String(currentUpc);}).concat([Object.assign({},p,{cigaretteProfile:{unit:unit,packs:packs,sticks:sticks,confirmedAt:Date.now()}})]);
  try{if(!storageOK)throw Error();localStorage.setItem('hs.catalog',JSON.stringify(next));}catch(e){$('cigError').textContent='Could not save. Previous details are unchanged.';return;}
  EXTRA=next;rebuildIndex();cigaretteEdit=null;showResult(currentUpc,'unit setup');hostPublish();
}

'''
s=s.replace('function tobaccoText(it)',insert+'function tobaccoText(it)',1)
s=s.replace("  body += retailerPanel(upc, p.name);","  body += retailerPanel(upc, p.name);\n  body += cigarettePanel(p,qty);",1)
s=s.replace("  if(act==='correctProduct')", "  if(act==='cigaretteSetup'){showCigaretteSetup();return;}\n  if(act==='cigaretteSave'){saveCigaretteSetup();return;}\n  if(act==='cigaretteCancel'){cigaretteEdit=null;showResult(currentUpc,'manual');return;}\n  if(act==='hostRevoke'){if(confirm('Forget all remembered browsers? They will need to pair again.'))viewBrowserHost(parseJSON(window.AndroidHost.forgetBrowserDevices()));return;}\n  if(act==='hostRenew'){viewBrowserHost(parseJSON(window.AndroidHost.renewBrowserCode()));return;}\n  if(act==='correctProduct')",1)
s=s.replace("  showResult(upc, source || 'manual');","  recordLiveScan(upc,'Scanned · awaiting review');\n  showResult(upc, source || 'manual');",1)
s=s.replace("  fastSessionCount++;fastLastEvent", "  recordLiveScan(upc,'Added 1 inventory unit');\n  fastSessionCount++;fastLastEvent",1)
s=s.replace("/* Phone-hosted LAN dashboard.",'''var latestScan=null,liveScanNumber=0;
function recordLiveScan(upc,message){latestScan={id:Date.now()+'-'+(++liveScanNumber),upc:String(upc),at:Date.now(),message:message};hostPublish();}
function liveScanRecord(){if(!latestScan)return null;var p=getProduct(latestScan.upc);return Object.assign({},latestScan,{product:p?browserRecord(p):{upc:latestScan.upc,name:'Unknown barcode',qty:0,priceSet:false,costSet:false}});}
function hostPublish(){try{var h=window.AndroidHost;if(h && h.isHosting && h.isHosting() && h.publishState)h.publishState(window.__trillServerRequest('state','{}'));}catch(e){}}
setInterval(hostPublish,500);
/* Phone-hosted LAN dashboard.''',1)
s=s.replace("return {upc:String(p.upc),name:p.name,brand:", "return {image:displayableProductPhoto(p)?p.image:'',category:p.cat || 'Other',cigaretteProfile:p.cigaretteProfile || null,upc:String(p.upc),name:p.name,brand:",1)
s=s.replace("{status:200,items:browserProducts().map(browserRecord),at:Date.now()}","{status:200,items:browserProducts().map(browserRecord),latestScan:liveScanRecord(),history:HIST.slice(0,100)}",1)
s=s.replace("Keep Trill open on this screen.","Keep Trill open; you can close this panel and scan while hosting.").replace("Stop and restart to revoke all current codes.","Trusted browsers stay paired after restarting hosting. Use Forget devices to revoke access. Codes and QR links expire after 10 minutes; renew them below.")
s=s.replace("  openSheet('Browser access',state.running?",'''  if(state.running){
    var url=(state.addresses || [])[0];
    if(url && typeof qrcode==='function'){
      var qr=qrcode(0,'M');qr.addData(url+'/#pair='+encodeURIComponent(state.qrToken || state.token));qr.make();
      html+='<div class="sect-title">Or scan to pair automatically</div><div class="pair-qr" aria-label="Scan this QR code on your viewing device">'+qr.createSvgTag({cellSize:4,margin:16,scalable:true})+'</div><p class="desc">Same Wi-Fi required. The QR supplies the code automatically. Only scan this on a device you trust; successful pairing grants editing access.</p>';
    }
    html+='<button class="btn btn-block" data-act="hostRenew">New 10-minute code / QR</button><button class="btn btn-block" data-act="hostRevoke" style="margin-top:8px">Forget all remembered devices</button>';
  }
  openSheet('Browser access',state.running?''',1)
s=s.replace("  if(act==='hostStart'){viewBrowserHost(parseJSON(window.AndroidHost.startLocalServer()));return;}","  if(act==='hostStart'){viewBrowserHost(parseJSON(window.AndroidHost.startLocalServer()));hostPublish();return;}")
a=s.index('  if(!INV[upc]) INV[upc]',s.index('function addToInventory'));b=s.index('  beep(); haptic(25);',a)
s=s[:a]+'''  var old=INV[upc],total=(old?Number(old.qty):0)+qty,now=Date.now();
  if(!Number.isInteger(qty) || qty<1 || !Number.isInteger(total) || total>1000000){toast('Invalid quantity or stock limit reached','bad');return false;}
  var inventory=Object.assign(Object.create(null),INV);
  inventory[upc]=Object.assign({},old || {first:now,scans:0},{qty:total,last:now,scans:(old && old.scans || 0)+1});
  var history=[{upc:upc,name:(p && p.name)||'Unknown item',qty:qty,at:now,kind:'add'}].concat(HIST).slice(0,600);
  try{fastWrite(EXTRA,inventory,history);}catch(e){toast('Stock was not saved: storage unavailable or full','bad');return false;}
  INV=inventory;HIST=history;renderHud();
  if(latestScan && latestScan.upc===upc)latestScan.message='Added '+qty+' inventory units';hostPublish();
'''+s[b:]
s=s.replace("  INV=inventory;HIST=history;fastSessionCount", "  if(latestScan && latestScan.upc===last.upc)latestScan.message='Last +1 undone';\n  INV=inventory;HIST=history;hostPublish();fastSessionCount",1)
s=s.replace("Version 1.15.0","Version 1.16.0")
# Embed QR runtime for offline use, keeping the main IIFE as the last script.
s=s.replace('<script>','<script>\n'+Path('/home/user/trill-inventory/android/vendor/qrcode.js').read_text()+'\n</script>\n<script>',1)
p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=Path('/home/user/trill-inventory')/f;t=p.read_text().replace('1.15.0','1.16.0').replace('versionCode="18"','versionCode="19"');p.write_text(t)
