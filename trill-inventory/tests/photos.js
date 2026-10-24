const fs=require('fs'), assert=require('assert');let JSDOM;try{JSDOM=require('jsdom').JSDOM}catch(e){JSDOM=require('/tmp/node_modules/jsdom').JSDOM}
let html=require('./fixture-app')(fs.readFileSync(__dirname+'/../index.html','utf8')).replace('boot();\n\n})();',`boot();window.testPhoto={show:showPhotoEditor,set:setPhotoCandidate,save:saveProductPhoto,get:getProduct,state:function(){return photoState;},store:persistProductPhoto,close:closeSheet,lookup:lookupPhoto,mock:function(fn){lookupOnline=fn;},setCode:function(c){currentUpc=c;},s:S};})();`);
const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://harrys.local/',beforeParse(w){w.confirm=()=>true;w.fetch=()=>Promise.reject(Error('offline'));}});
const w=dom.window,t=w.testPhoto,$=id=>w.document.getElementById(id),code='049000042566';
(async()=>{
 const before=JSON.stringify(t.get(code));
 t.setCode(code);t.show(code);assert($('photoFile'));assert($('photoSave').disabled);
 t.set(t.state(),'https://example.test/actual.jpg','Test barcode source');
 t.save(false);assert.equal(JSON.stringify(t.get(code)),before);
 $('photoPreview').querySelector('img').dispatchEvent(new w.Event('load'));
 assert($('photoSave').disabled);$('photoConfirm').checked=true;$('photoConfirm').dispatchEvent(new w.Event('change'));assert(!$('photoSave').disabled);
 t.save(false);const p=t.get(code);assert.equal(p.image,'https://example.test/actual.jpg');assert(p.imageVerifiedAt);
 const orig=JSON.parse(before);for(const k of Object.keys(orig)){if(k!=='image') assert.deepEqual(p[k],orig[k],k);}
 t.show(code);t.set(t.state(),'https://example.test/broken.jpg','Broken');$('photoPreview').querySelector('img').dispatchEvent(new w.Event('error'));assert($('photoSave').disabled);assert.equal(t.get(code).image,'https://example.test/actual.jpg');
 t.save(true);assert.equal(t.get(code).image,'');assert.equal(t.get(code).price,orig.price);
 // Late network response cannot change another sheet.
 t.show(code);let resolve;t.mock(()=>new Promise(r=>resolve=r));t.lookup();t.close();resolve({identity:{image:'https://example.test/late.jpg'}});await new Promise(r=>setTimeout(r,0));assert.equal(t.get(code).image,'');
 // Storage errors are surfaced, not falsely reported as saved.
 const proto=Object.getPrototypeOf(w.localStorage), old=proto.setItem;proto.setItem=function(){throw Error('full');};assert.equal(t.store(code,'https://example.test/no.jpg','test'),false);assert.equal(t.get(code).image,'');proto.setItem=old;
 console.log('PHOTOS OK: preview, confirmation, image error, metadata preservation, removal, stale lookup, storage failure');dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
