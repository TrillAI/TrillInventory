const fs=require('fs'),assert=require('assert'),cp=require('child_process');
let JSDOM;try{JSDOM=require('jsdom').JSDOM}catch(e){JSDOM=require('/tmp/node_modules/jsdom').JSDOM}
// Check the actual compiled object registered with addJavascriptInterface, not a JS mock alone.
const path=__dirname+'/../android/build/classes/com/harrys/scan/MainActivity$HostBridge.class';
const bytecode=cp.execFileSync('/usr/local/jdk17/bin/javap',['-p','-v',path],{encoding:'utf8'});
const method=bytecode.split('public void httpGet(java.lang.String, java.lang.String);')[1].split('public void copyText')[0];
assert(method.includes('android.webkit.JavascriptInterface'));
assert(method.includes('MainActivity.httpGet'));
let html=fs.readFileSync(__dirname+'/../index.html','utf8').replace('boot();\n\n})();',`boot();window.testAPI={raw:rawGet,off:provOFF,settings:S};})();`);
let response={code:200,body:'{"status":1,"code":"12345678","product":{"product_name":"Test item"}}'},calls=0;
const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://harrys.local/',beforeParse(w){
 w.AndroidHost={httpGet(url,id){calls++;setTimeout(()=>w.__hsHttpResult(id,response.code,response.body),0);}};
 w.fetch=()=>{throw Error('native build must not use browser fetch')};
}});
(async()=>{
 const t=dom.window.testAPI;t.settings.netMinInterval=0;
 assert.equal((await t.off('12345678')).identity.name,'Test item');
 response={code:404,body:'{"status":0,"status_verbose":"product not found"}'};
 assert.equal((await t.off('12345678')).note,'not in database');
 response={code:404,body:'<html>Not Found</html>'};
 assert.equal((await t.off('12345678')).note,'http 404');
 response={code:403,body:'<html>Forbidden</html>'};
 assert.equal((await t.off('12345678')).note,'http 403');
 delete dom.window.AndroidHost.httpGet;
 await assert.rejects(t.raw('https://api.upcitemdb.com/'),/Android lookup connection unavailable/);
 assert.equal(calls,4);
 console.log('BRIDGE + ERRORS OK: compiled annotated bridge, native callbacks, missing product vs endpoint failure');dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1});
