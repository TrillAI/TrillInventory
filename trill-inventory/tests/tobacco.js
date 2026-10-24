const fs=require('fs'),assert=require('assert');
let JSDOM;try{JSDOM=require('jsdom').JSDOM}catch(e){JSDOM=require('/tmp/node_modules/jsdom').JSDOM}
const checks = `
S.onlineEnabled=false;
if(guessCategory('ZYN Cool Mint 6 mg nicotine pouches')!=='Tobacco') throw Error('category');
if(guessCategory('Coca Cola soda')!=='Cold Beverages') throw Error('regression');
if(tobaccoWarnings('Marlboro non-menthol 100s pack',{title:'Marlboro menthol king carton'}).length!==3) throw Error('variants');
currentUpc='085555555555';
showUnknownForm(currentUpc,null,null);
if(document.getElementById('tobaccoName')) throw Error('helper shown for unknown product');
showUnknownForm(currentUpc,{name:'Marlboro cigarettes',cat:'Tobacco',brand:'Marlboro',price:0,cost:0,pack:10},null);
if(!document.getElementById('tobaccoName')) throw Error('contextual helper missing');
matchState.query='Marlboro cigarettes 100s pack';
renderMatchOptions([{title:'Marlboro cigarettes 100s pack 20 count',category:'Tobacco',code:'123456789012',pack:20,listingPack:true,priceLow:9,source:'test'}],'');
chooseMatch(0);
if(document.getElementById('newPrice').value!=='') throw Error('unverified price');
if(document.getElementById('newPack').value==='20') throw Error('cigarettes mistaken for packs');
if(document.getElementById('newCat').value!=='Tobacco') throw Error('form category');
if(currentUpc!=='085555555555') throw Error('barcode replaced');
var pre=prefillFromOnline({identity:{name:'Camel cigarettes'},offers:[{price:10}]});
if(pre.price!==0 || pre.cost!==0) throw Error('automatic price');
`;
const dom=new JSDOM(fs.readFileSync(__dirname+'/../index.html','utf8').replace('boot();\n\n})();', 'boot();\n' + checks + '\nwindow.__tested=true;\n})();'),{runScripts:'dangerously',url:'https://harrys.local/',pretendToBeVisual:true,beforeParse(w){w.fetch=()=>Promise.reject(Error('offline'));w.confirm=()=>true;w.HTMLMediaElement.prototype.play=()=>Promise.resolve();}});
const w=dom.window;
assert(w.__tested,'injected tests completed');console.log('TOBACCO LOOKUP OK');dom.window.close();
