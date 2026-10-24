const fs=require('fs'),assert=require('assert');let JSDOM;try{JSDOM=require('jsdom').JSDOM}catch(e){JSDOM=require('/tmp/node_modules/jsdom').JSDOM}
let html=fs.readFileSync(__dirname+'/../index.html','utf8').replace('boot();\n\n})();',`boot();window.hostTest={seed:function(){EXTRA.push({upc:'test-123',name:'Test product',brand:'Test',size:'20-count pack',price:8.99,cost:5,pack:10,par:20,rp:4,image:'https://example.test/package.jpg'});INV['test-123']={qty:7,first:1,last:2,scans:3};rebuildIndex();lsSet('hs.catalog',EXTRA);lsSet('hs.inventory',INV);},get:getProduct,inv:function(){return INV;},show:function(){currentUpc='test-123';showPriceEditor('test-123');},save:savePriceEdit};})();`);
const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://harrys.local/',beforeParse(w){w.confirm=()=>true;w.fetch=()=>Promise.reject(Error('offline'));}});
const w=dom.window,t=w.hostTest,$=id=>w.document.getElementById(id),call=(a,b={})=>JSON.parse(w.__trillServerRequest(a,JSON.stringify(b)));
try{
 assert.equal(call('state').items.length,0,'no fake seed inventory');t.seed();let row=call('state').items[0];assert.equal(row.name,'Test product');assert.equal(row.qty,7);assert.equal(typeof row.image,'string');
 let edit={upc:row.upc,expected:row.version,qty:9,price:9.99,cost:5.5};assert.equal(call('edit',edit).status,200);assert.equal(t.inv()['test-123'].qty,9);assert.equal(t.inv()['test-123'].scans,3);assert.equal(t.get(row.upc).image,'https://example.test/package.jpg');assert.equal(t.get(row.upc).price,9.99);
 assert.equal(call('edit',edit).status,409,'stale edits rejected');row=call('state').items[0];edit.expected=row.version;
 for(const patch of [{qty:-1},{qty:1.5},{price:'8.99'},{price:1.234},{cost:-2},{upc:'not-found'}]){const result=call('edit',{...edit,...patch});assert([400,404].includes(result.status));}
 t.show();$('editShelfPrice').value='12.99';edit={...edit,price:10.99};assert.equal(call('edit',edit).status,200);t.save();assert.equal(t.get(row.upc).price,10.99,'phone refuses stale edit');assert($('editPriceError').textContent.includes('another device'));
 row=call('state').items[0];const proto=Object.getPrototypeOf(w.localStorage),old=proto.setItem,prior=w.localStorage.getItem('hs.catalog');let failed=false;proto.setItem=function(k,v){if(k==='hs.inventory'&&!failed){failed=true;throw Error('quota')}return old.call(this,k,v);};
 assert.equal(call('edit',{...edit,expected:row.version,qty:200,price:11.99}).status,507);assert.equal(w.localStorage.getItem('hs.catalog'),prior);assert.equal(t.inv()['test-123'].qty,9);proto.setItem=old;
 assert.equal(call('edit',{...edit,expected:row.version,qty:0,price:0,cost:0}).status,200);assert.equal(call('state').items[0].qty,0);
 console.log('BROWSER HOST OK: real data only, shared edits, persistence, conflict detection, phone stale edits, validation, rollback');
}finally{dom.window.close()}
