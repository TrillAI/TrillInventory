const fs=require('fs'), assert=require('assert');
let JSDOM;try{JSDOM=require('jsdom').JSDOM}catch(e){JSDOM=require('/tmp/node_modules/jsdom').JSDOM}
let html=fs.readFileSync(__dirname+'/../index.html','utf8');
html=html.replace('boot();\n\n})();',`boot();
window.testAPI={expand:upceToUpca,candidates:barcodeCandidates,lookup:lookupOnline,
 settings:S,cache:NETCACHE,show:showUnknownForm,save:saveObservedPrice,links:refreshRetailerLinks,
 observations:OBSERVED,providers:runProviders,
 setCode:function(code){currentUpc=code;},
 mockProviders:function(fn){runProviders=fn;},
 mockUPC:function(fn){provUPCitemdb=fn;},
 mockOFF:function(fn){provOFF=fn;},
 note:onlineNote};
})();`);
const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://harrys.local/',pretendToBeVisual:true,beforeParse(w){w.fetch=()=>Promise.reject(Error('offline'));w.confirm=()=>true;w.HTMLMediaElement.prototype.play=()=>Promise.resolve();}});
const w=dom.window, t=w.testAPI, $=id=>w.document.getElementById(id);
(async()=>{
 assert.equal(t.expand('04252614'),'042100005264');
 assert.equal(t.expand('01234565'),'012345000065');
 assert.equal(t.expand('01234566'),'');
 assert.equal(t.expand('21234565'),'');
 assert.deepEqual(Array.from(t.candidates('4006381333931')),['4006381333931']);
 assert(t.candidates('0049000042566').includes('049000042566'));
 assert(t.candidates('00049000042566').includes('049000042566'));
 assert.equal(t.candidates('01234565')[0],'01234565');
 let calls=[];
 t.mockProviders(code=>{calls.push(code);return Promise.resolve({identity:code.length===13?{name:'Recovered product'}:null,offers:[],sources:[{name:'test',ok:true,note:''}],at:Date.now()})});
 const r=await t.lookup('085555555555',true);
 assert.equal(r.identity.name,'Recovered product');assert.equal(calls.length,2);
 calls=[];await t.lookup('085555555555');assert.equal(calls.length,0);
 await t.lookup('085555555555',true);assert.equal(calls.length,2);
 t.cache['099999999999']={identity:null,offers:[],sources:[],at:Date.now()-61000};
 calls=[];await t.lookup('099999999999');assert(calls.length>0);
 t.mockProviders(code=>Promise.resolve({identity:null,offers:[],sources:[{name:'test',ok:false,note:'network failed'}],at:Date.now()}));
 await t.lookup('088888888888',true);assert(!t.cache['088888888888']);
 assert(t.note({sources:[{name:'test',note:'rate limited'}]}).includes('Lookup incomplete'));
 t.settings.netPrices=false;t.settings.netIdentity=true;
 let identityCalls=0;
 t.mockUPC(()=>{identityCalls++;return Promise.resolve({ok:true,identity:{name:'Identity only'},offers:[]})});
 t.mockOFF(()=>Promise.resolve({ok:false,note:'not in database'}));
 t.settings.netProvider='upcitemdb';
 const identityResult=await t.providers('085555555555');
 assert.equal(identityCalls,1);assert.equal(identityResult.identity.name,'Identity only');
 assert.equal(identityResult.offers.length,0);
 t.settings.onlineEnabled=false;
 t.setCode('085555555555');t.show('085555555555',null,null);
 assert.equal($('retailZip').value,'37311');
 assert.equal($('retailLinks').querySelectorAll('a').length,5);
 $('retailQuery').value='Marlboro Gold 100s';t.links();
 assert($('retailLinks').querySelector('a').href.includes('Marlboro%20Gold%20100s'));
 const before=w.localStorage.getItem('hs.inventory');
 $('observedStore').value='Walmart — checked store';$('observedPrice').value='8.99';$('observedUnit').value='20-count pack';t.save();
 assert.equal(t.observations['085555555555'][0].price,8.99);
 assert.equal(t.observations['085555555555'][0].zip,'37311');
 assert.equal(w.localStorage.getItem('hs.inventory'),before);
 assert($('observedRows').textContent.includes('not live'));
 $('observedPrice').value='-1';t.save();assert.equal(t.observations['085555555555'].length,1);
 console.log('LOOKUP + RETAILERS OK: barcode conversions, fallback, cache expiry, force retry, errors, search links, observations');
 dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1});
