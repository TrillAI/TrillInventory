from pathlib import Path
r=Path('/home/user/trill-inventory');p=r/'index.html';s=p.read_text()
s=s.replace('Tobacco listings may be unavailable.','Some retailers may not list this product.')
s=s.replace('e.g. 20-count pack or 12 fl oz can','e.g. single bottle or 6-pack')
s=s.replace('|snus|dip|vapes?', '|snus|vapes?').replace('|newport|camel|pall mall', '|newport|pall mall').replace('|american spirit|grizzly|copenhagen', '|american spirit|copenhagen')
# contextual helper: cigarette mentions only after cigarette identity is established
s=s.replace('function tobaccoHelperHTML(){\n  return', '''function tobaccoHelperHTML(text){
  var cigarette=/\\b(cigarettes?|marlboro|newport|pall mall|winston|kool|salem|american spirit)\\b/i.test(text || '') || /\\bcamel\\b/i.test(text || '') && /\\b(tobacco|menthol|100s|filters?)\\b/i.test(text || '');
  var types=cigarette ? ['Cigarettes'] : ['Tobacco','Cigars','Cigarillos','Dip tobacco','Nicotine pouches','Vape'];
  return''')
s=s.replace('Cigarettes, cigars, dip or nicotine? Tap here', "' + (cigarette ? 'Cigarette product details' : 'Tobacco product details') + '")
s=s.replace('placeholder="e.g. Marlboro Gold or ZYN Cool Mint"','placeholder="Printed brand and variant"')
s=s.replace('<option>Cigarettes</option><option>Cigars</option><option>Cigarillos</option><option>Dip tobacco</option><option>Nicotine pouches</option><option>Vape</option>', "' + types.map(function(t){return '<option>'+t+'</option>';}).join('') + '")
s=s.replace("  body += tobaccoHelperHTML();", "  body += '<div id=\"tobaccoContext\"></div>';")
s=s.replace('function wireMatchPicker(pre){', '''function syncTobaccoContext(){
  var box=$('tobaccoContext');if(!box)return;
  var text=[$('newName'),$('newBrand'),$('newCat')].map(function(el){return el ? el.value : '';}).join(' ');
  var active=isTobacco(text), html=active ? tobaccoHelperHTML(text) : '';
  if(box._contextHTML!==html){box.innerHTML=html;box._contextHTML=html;}
}
function wireMatchPicker(pre){''')
s=s.replace("  if(!nameEl || !qEl) return;\n  var t = null;", "  if(!nameEl || !qEl) return;\n  syncTobaccoContext();\n  ['newName','newBrand','newCat'].forEach(function(id){var el=$(id);if(el){el.addEventListener('input',syncTobaccoContext);el.addEventListener('change',syncTobaccoContext);}});\n  var t = null;")
s=s.replace("  renderMatchOptions(matchState.items, '');\n  toast(warnMsg", "  syncTobaccoContext();\n  renderMatchOptions(matchState.items, '');\n  toast(warnMsg")
# Exact-image metadata from the same barcode checked by each provider.
s=s.replace("category: cat, image: (it.images && it.images[0]) || ''", "category: cat, image: (it.images && it.images[0]) || '', images:(it.images || []).slice(0,3), source:'UPCitemdb'")
s=s.replace("image: it.product.image_url || ''", "image: it.product.image_url || '', barcode:upc, source:'Open Prices'")
s=s.replace('categories,image_small_url\'', 'categories,image_front_url,image_small_url\'')
s=s.replace("image: p.image_small_url || ''", "image: p.image_front_url || p.image_small_url || '', barcode:upc, source:'Open Food Facts'")
s=s.replace('netAutoApply:false, netImages:true, netNameSearch:true', 'netAutoApply:false, netImages:true, netNameSearch:true, autoPhotos:true')
s=s.replace("{k:'netImages', t:'toggle', label:'Show product images', d:'Load product photos from Open Food Facts.'},", "{k:'netImages', t:'toggle', label:'Show product images', d:'Display barcode-matched online photos.'},\n    {k:'autoPhotos', t:'toggle', label:'Automatic product photos', d:'Find barcode-matched photos for saved and imported products. Uses the online request budget; never replaces a confirmed photo.'},")
# No incidental name-search image becomes a saved product image.
s=s.replace("    image: (m && m.image) || '',", "    image: '',")
s=s.replace("  if(item.image && !base.imageVerifiedAt) entry.image = item.image;", "  // Photo resolution is handled separately using the saved product barcode, never a name-search thumbnail.")
# Show/update photo only; preserve the rest of the sheet while a job finishes.
s=s.replace("  if(p.image && (S.netImages || /^data:image\\//.test(p.image))){", "  body += '<div id=\"productPhotoSlot\">';\n  if(p.image && (S.netImages || /^data:image\\//.test(p.image))){",1)
s=s.replace("  body +=   '<div class=\"hero-info\"><h3>' + esc(p.name)", "  body += '</div>';\n  body +=   '<div class=\"hero-info\"><h3>' + esc(p.name)",1)
s=s.replace("  body += retailerPanel(upc, p.name);", "  body += '<p class=\"desc\" id=\"autoPhotoStatus\" aria-live=\"polite\"></p>';\n  body += retailerPanel(upc, p.name);",1)
s=s.replace("  openSheet(p.name, subtitle, body, foot);", "  openSheet(p.name, subtitle, body, foot);\n  updateAutoPhotoUI(upc);queueAutoPhoto(upc);")
# user override prevents subsequent automated replacement/removal undo
s=s.replace("entry.imageVerifiedAt=url ? Date.now() : 0;", "entry.imageVerifiedAt=url ? Date.now() : 0;entry.imageAutoBlocked=!url;entry.imageBarcode='';")
s=s.replace("record.image='';record.imageVerifiedAt=0;record.imageSource='';", "record.image='';record.imageVerifiedAt=0;record.imageSource='';record.imageAutoBlocked=false;")
s=s.replace("  toast('Updated ' + (entry.name || '').slice(0, 30), 'good');", "  queueAutoPhoto(upc);\n  toast('Updated ' + (entry.name || '').slice(0, 30), 'good');")
s=s.replace("  viewImport();\n}\nfunction download", "  viewImport();\n  scheduleMissingPhotos();\n}\nfunction download")
s=s.replace("  runSplash();\n  if(!ONBOARDED)", "  runSplash();\n  setTimeout(scheduleMissingPhotos,1200);\n  if(!ONBOARDED)")
s=s.replace("      if(k === 'torchSteady'", "      if(k === 'autoPhotos' || k === 'netImages' || k === 'onlineEnabled')scheduleMissingPhotos();\n      if(k === 'torchSteady'")
s=s.replace("label:'Version 1.12.0'", "label:'Version 1.13.0'")
p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=r/f;s=p.read_text().replace('1.12.0','1.13.0').replace('--version-code 15','--version-code 16').replace('versionCode="15"','versionCode="16"');p.write_text(s)
