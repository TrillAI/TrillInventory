const fs=require('fs'),assert=require('assert');let JSDOM;try{JSDOM=require('jsdom').JSDOM}catch(e){JSDOM=require('/tmp/node_modules/jsdom').JSDOM}
let html=require('./fixture-app')(fs.readFileSync(__dirname+'/../index.html','utf8')).replace('boot();\n\n})();',`boot();window.priceTest={show:function(c){currentUpc=c;pendingQty=6;showPriceEditor(c);},save:savePriceEdit,cancel:returnFromPriceEdit,get:getProduct,parse:parsePriceInput,qty:function(){return pendingQty;}};})();`);
const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://harrys.local/',beforeParse(w){w.confirm=()=>true;w.fetch=()=>Promise.reject(Error('offline'));}});
const w=dom.window,t=w.priceTest,$=id=>w.document.getElementById(id),code='049000042566';
try{
 const p=JSON.parse(JSON.stringify(t.get(code))), inv=w.localStorage.getItem('hs.inventory');
 assert.equal(t.parse('8.99'),8.99);assert.equal(t.parse('.99'),.99);assert.equal(t.parse('0'),0);
 for(const val of ['','-1','1.234','Infinity','1e3','12abc','100000']) assert.equal(t.parse(val),null);
 t.show(code);$('editShelfPrice').value='3.49';$('editUnitCost').value='';t.save();assert.equal(t.get(code).price,3.49);assert.equal(t.get(code).cost,p.cost);assert.equal(t.qty(),6);
 for(const key of Object.keys(p)){if(!['price','cost'].includes(key)) assert.deepEqual(t.get(code)[key],p[key],key);}
 assert.equal(w.localStorage.getItem('hs.inventory'),inv);
 t.show(code);$('editShelfPrice').value='9.99';t.cancel();assert.equal(t.get(code).price,3.49);
 t.show(code);$('editShelfPrice').value='-1';t.save();assert.equal(t.get(code).price,3.49);
 $('editShelfPrice').value='4.99';$('editUnitCost').value='2.25';t.save();assert.equal(t.get(code).cost,2.25);
 t.show(code);$('editShelfPrice').value='0';w.confirm=()=>false;t.save();assert.equal(t.get(code).price,4.99);
 w.confirm=()=>true;const proto=Object.getPrototypeOf(w.localStorage),old=proto.setItem;proto.setItem=()=>{throw Error('full')};$('editShelfPrice').value='7.99';t.save();assert.equal(t.get(code).price,4.99);assert($('editPriceError').textContent.includes('Could not save'));proto.setItem=old;
 console.log('PRICE EDIT OK: validation, save, cost optional, cancel, zero confirmation, stock/identity preserved, storage failure');
}finally{dom.window.close()}
