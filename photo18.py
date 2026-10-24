from pathlib import Path
r=Path('/home/user/trill-inventory');p=r/'index.html';s=p.read_text()
pos=s.index('/* sheet actions */')
s=s[:pos]+'''/* Picture updates are separate from identity, stock and pricing. */
var photoState = null, photoStream = null, photoGeneration = 0;
function stopPhotoCapture(){
  if(photoStream){ photoStream.getTracks().forEach(function(t){t.stop();}); photoStream = null; }
}
function photoActive(state){ return state === photoState && state.token === photoGeneration && sheetOpen && currentUpc === state.upc && !!$('photoPreview'); }
function photoMessage(text){ if($('photoStatus')) $('photoStatus').textContent = text; }
function showPhotoEditor(upc){
  var p = getProduct(upc); if(!p) return;
  var html = '<p class="desc">Match the brand, flavor, strength and pack size against the actual package. A barcode database image can still be outdated or wrong. Nothing changes until you confirm.</p>' +
    '<div id="photoPreview" style="text-align:center;min-height:180px;padding:16px;background:var(--s2);border-radius:16px"></div>' +
    '<p class="desc" id="photoStatus">Choose a barcode lookup, upload, or camera photo.</p>' +
    '<button class="btn btn-block" data-act="photoLookup">Find picture by this barcode</button>' +
    '<div class="row2" style="margin:12px 0"><label class="btn" style="text-align:center">Upload photo<input id="photoFile" type="file" accept="image/jpeg,image/png,image/webp" style="display:none"></label>' +
    '<button class="btn" data-act="photoCamera">Take photo</button></div>' +
    '<video id="photoVideo" autoplay playsinline muted style="display:none;width:100%;max-height:300px;border-radius:16px"></video>' +
    '<button id="photoSnap" class="btn btn-block" data-act="photoSnap" style="display:none">Capture package</button>' +
    '<label style="display:block;margin:14px 0"><input type="checkbox" id="photoConfirm"> I checked that this picture matches this exact product.</label>' +
    '<button class="btn btn-block" data-act="photoRemove">Remove incorrect picture</button>';
  openSheet('Update picture', p.name + ' · ' + upc, html,
    '<button class="btn" data-act="photoCancel">Cancel</button><button class="btn btn-primary" id="photoSave" data-act="photoSave" disabled>Use this picture</button>');
  photoState = {upc:upc, token:photoGeneration, url:'', source:'', ready:false};
  var state = photoState;
  $('photoFile').addEventListener('change', function(){
    var f = this.files && this.files[0]; if(!f) return;
    if(!/^image\\/(jpeg|png|webp)$/.test(f.type) || f.size > 15*1024*1024){photoMessage('Choose a JPG, PNG or WebP image under 15 MB.');return;}
    stopPhotoCapture();
    var reader = new FileReader();
    reader.onerror = function(){if(photoActive(state)) photoMessage('Could not read this image. Try a different file.');};
    reader.onload = function(){
      if(!photoActive(state)) return;
      var img = new Image();
      img.onload = function(){
        if(!photoActive(state)) return;
        try { setPhotoCandidate(state, compressedPhoto(img), 'Your uploaded package photo'); }
        catch(e){ photoMessage('Could not process this image.'); }
      };
      img.onerror = function(){if(photoActive(state)) photoMessage('This file could not be decoded.');};
      img.src = reader.result;
    };
    reader.readAsDataURL(f);
  });
  $('photoConfirm').addEventListener('change', updatePhotoSave);
  if(p.image){ setPhotoCandidate(state, p.image, p.imageSource || 'Current picture'); }
}
function compressedPhoto(image){
  var w = image.videoWidth || image.naturalWidth, h = image.videoHeight || image.naturalHeight;
  if(!w || !h) throw new Error('Image not ready');
  var scale = Math.min(1,640/Math.max(w,h)), c = document.createElement('canvas');
  c.width = Math.round(w*scale); c.height = Math.round(h*scale);
  c.getContext('2d').drawImage(image,0,0,c.width,c.height);
  return c.toDataURL('image/jpeg',0.78);
}
function updatePhotoSave(){
  if($('photoSave')) $('photoSave').disabled = !(photoState && photoState.ready && $('photoConfirm').checked);
}
function setPhotoCandidate(state, url, source){
  if(!photoActive(state)) return;
  if(!/^https:\\/\\//i.test(url) && !/^data:image\\/(jpeg|png|webp);base64,/i.test(url)){photoMessage('Unsupported image address. Upload a package photo instead.');return;}
  state.url = url; state.source = source; state.ready = false;
  $('photoConfirm').checked = false; updatePhotoSave();
  var img = document.createElement('img'); img.alt = 'Product picture to verify';
  img.style.cssText = 'width:100%;max-width:320px;height:230px;object-fit:contain;background:white;border-radius:12px';
  img.onload = function(){if(photoActive(state) && state.url === url){state.ready = true;photoMessage(source + ' — verify the package before saving.');updatePhotoSave();}};
  img.onerror = function(){if(photoActive(state) && state.url === url){state.ready = false;photoMessage('The image could not load. Upload or take a package photo instead.');updatePhotoSave();}};
  $('photoPreview').replaceChildren(img); img.src = url;
}
function lookupPhoto(){
  var state = photoState; if(!state || !photoActive(state)) return;
  if(!onlineReady()){photoMessage('Online lookup is off. You can still upload or take a photo.');return;}
  photoMessage('Checking this barcode for a product image…');
  $('photoSave').disabled = true; state.ready = false;
  lookupOnline(state.upc, true).then(function(res){
    if(!photoActive(state)) return;
    var id = res.identity || {};
    if(!id.image){photoMessage('No usable picture found for this barcode. Upload or take a photo of the actual package.');return;}
    setPhotoCandidate(state, id.image, 'Barcode database: ' + (id.name || state.upc));
  }).catch(function(){if(photoActive(state)) photoMessage('Picture lookup failed. Your current picture is unchanged. Try a photo instead.');});
}
async function startPhotoCapture(){
  var state = photoState; if(!state || !photoActive(state)) return;
  stopPhotoCapture(); stopCamera();
  try {
    var ps = await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});
    if(!photoActive(state)){ps.getTracks().forEach(function(t){t.stop();});return;}
    photoStream = ps; var v = $('photoVideo'); v.srcObject = ps; v.style.display='block'; await v.play();
    if(!photoActive(state)){stopPhotoCapture();return;}
    $('photoSnap').style.display='block';photoMessage('Frame the front of the actual package, then capture.');
  } catch(e){stopPhotoCapture();if(photoActive(state)) photoMessage('Camera unavailable. Allow camera access or upload a photo.');}
}
function capturePhoto(){
  var state = photoState; if(!state || !photoActive(state)) return;
  try { var url = compressedPhoto($('photoVideo')); stopPhotoCapture(); $('photoVideo').style.display='none'; $('photoSnap').style.display='none'; setPhotoCandidate(state,url,'Your camera photo'); }
  catch(e){photoMessage('Camera is not ready yet. Try capture again.');}
}
function persistProductPhoto(upc, url, source){
  var next = EXTRA.map(function(p){return Object.assign({},p);}), entry = next.find(function(p){return String(p.upc)===String(upc);});
  if(!entry){entry={upc:upc};next.push(entry);}
  entry.image=url;entry.imageSource=source;entry.imageVerifiedAt=url ? Date.now() : 0;
  try {
    if(!storageOK) throw new Error('Storage unavailable');
    localStorage.setItem('hs.catalog',JSON.stringify(next));
  } catch(e){toast('Picture not saved — storage unavailable or full. Existing picture kept.', 'bad');return false;}
  EXTRA=next;rebuildIndex();return true;
}
function saveProductPhoto(remove){
  var state = photoState; if(!state || !photoActive(state)) return;
  if(!remove && (!state.ready || !$('photoConfirm').checked)) return;
  if(remove && !confirm('Remove this product picture? Product details and stock stay unchanged.')) return;
  if(!persistProductPhoto(state.upc,remove?'':state.url,remove?'':state.source)) return;
  var upc = state.upc;showResult(upc,'picture');toast(remove?'Picture removed':'Product picture updated','good');
}

''' +s[pos:]
s=s.replace("function openSheet(title, sub, bodyHTML, footHTML){", "function openSheet(title, sub, bodyHTML, footHTML){\n  stopPhotoCapture(); photoGeneration++;")
s=s.replace("function closeSheet(){", "function closeSheet(){\n  stopPhotoCapture(); photoGeneration++;")
s=s.replace("  // ---- recommendation", "  body += '<button class=\"btn btn-block\" data-act=\"updatePhoto\" style=\"margin-bottom:14px\">Update picture</button>';\n  // ---- recommendation")
s=s.replace("if(p.image && S.netImages)","if(p.image && (S.netImages || /^data:image\\//.test(p.image)))")
s=s.replace("function sheetAction(act, btn){", """function sheetAction(act, btn){
  if(act === 'updatePhoto'){showPhotoEditor(currentUpc);return;}
  if(act === 'photoLookup'){lookupPhoto();return;}
  if(act === 'photoCamera'){startPhotoCapture();return;}
  if(act === 'photoSnap'){capturePhoto();return;}
  if(act === 'photoSave'){saveProductPhoto(false);return;}
  if(act === 'photoRemove'){saveProductPhoto(true);return;}
  if(act === 'photoCancel'){showResult(currentUpc,'picture');return;}
""")
# Do not undo a user-verified photo when updating unrelated product info.
s=s.replace("  if(item.image) entry.image = item.image;", "  if(item.image && !base.imageVerifiedAt) entry.image = item.image;")
p.write_text(s)
p=r/'android/src/com/harrys/scan/MainActivity.java';s=p.read_text().replace('    private WebView web;', '    private WebView web;\n    private ValueCallback<Uri[]> fileCallback;\n    private static final int REQ_PHOTO_FILE = 1002;')
s=s.replace('        s.setAllowContentAccess(false);','        s.setAllowContentAccess(true); // User-selected image URIs from the system picker.')
s=s.replace('        web.setWebChromeClient(new WebChromeClient() {', '''        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                             WebChromeClient.FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                Intent pick = new Intent(Intent.ACTION_GET_CONTENT);
                pick.addCategory(Intent.CATEGORY_OPENABLE);
                pick.setType("image/*");
                try { startActivityForResult(Intent.createChooser(pick, "Choose product photo"), REQ_PHOTO_FILE); }
                catch (Exception e) { fileCallback.onReceiveValue(null); fileCallback = null; }
                return true;
            }
''')
s=s.replace('    private boolean hasCamera() {', '''    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_PHOTO_FILE && fileCallback != null) {
            Uri selected = resultCode == RESULT_OK && data != null ? data.getData() : null;
            fileCallback.onReceiveValue(selected == null ? null : new Uri[]{selected});
            fileCallback = null;
        }
    }

    private boolean hasCamera() {''');p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=r/f;s=p.read_text().replace('1.6.1','1.7.0').replace('--version-code 8','--version-code 9').replace('versionCode="8"','versionCode="9"');p.write_text(s)
