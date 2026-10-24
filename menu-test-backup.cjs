const fs=require('fs'),assert=require('assert');const {chromium}=require('/tmp/node_modules/playwright-core');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});try{
const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true});const errors=[];page.on('pageerror',e=>errors.push(e.message));
let html=fs.readFileSync(__dirname+'/../index.html','utf8').replace('boot();\n\n})();',`boot();startCamera=async function(){camOn=true;renderHud();};window.menuTest={state:()=>({paused:scanPaused,sheet:sheetOpen,upc:currentUpc}),drawer:openDrawer,scan:()=>onScan('MENU-TEST','camera','CODE-128')};})();`);
await page.addInitScript(()=>{localStorage.setItem('hs.settings',JSON.stringify({onlineEnabled:false,autoPhotos:false,animate:false}));localStorage.setItem('hs.onboarded','true')});await page.route('https://harrys.local/**',r=>r.fulfill({contentType:'text/html',body:html}));await page.goto('https://harrys.local/');await page.tap('#splashSkip');
const drawer=()=>page.locator('#app').getAttribute('data-drawer');const back=()=>page.evaluate(()=>window.__hsHandleBack());
assert.equal(await page.locator('[data-nav="store"]').count(),0);
const routes=['scan','inventory','restock','history','catalog','import','addproduct','online','browser','themes','settings','guide'];
for(const route of routes){await page.tap('#btnMenu');await page.locator('[data-nav="'+route+'"]').tap();
if(route==='scan'){assert.equal(await drawer(),'none');assert.equal((await page.evaluate(()=>menuTest.state())).paused,false);}
else if(route==='themes'||route==='settings'){assert.equal(await drawer(),'right');if(route==='themes')await page.locator('[data-theme-pick]').first().waitFor({state:'visible'});await back();}
else if(route==='guide'){assert.equal(await page.locator('#onboard').evaluate(e=>e.classList.contains('off')),false);await back();assert(await page.locator('#onboard').evaluate(e=>e.classList.contains('off')));}
else {assert.equal(await drawer(),'none');assert((await page.evaluate(()=>menuTest.state())).sheet,route);assert(await page.locator('#scrim').evaluate(e=>e.classList.contains('on')));await page.tap('#sheetClose');}
assert.equal((await page.evaluate(()=>menuTest.state())).paused,false,route+' resumes');console.log('touch route OK',route);}
// Actual touchscreen drags through CDP, not DOM click dispatch.
const cdp=await page.context().newCDPSession(page);
async function swipe(x,y,dx,dy,cancel=false){await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});for(let i=1;i<=10;i++){await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+dx*i/10,y:y+dy*i/10}]});await page.waitForTimeout(20)}await cdp.send('Input.dispatchTouchEvent',{type:cancel?'touchCancel':'touchEnd',touchPoints:[]});await page.waitForTimeout(100)}
await page.tap('#btnMenu');await swipe(200,650,0,-280);assert.equal(await drawer(),'left');assert(await page.locator('#drawerLeft .drawer-body').evaluate(e=>e.scrollTop)>0);await back();
await swipe(2,420,250,0);assert.equal(await drawer(),'left');await swipe(270,420,-240,0);assert.equal(await drawer(),'none');
await swipe(388,420,-250,0);assert.equal(await drawer(),'right');await swipe(100,420,260,0);assert.equal(await drawer(),'none');
await page.tap('#btnMenu');await swipe(270,400,-220,0,true);assert.equal(await drawer(),'left');await page.locator('[data-nav="inventory"]').tap();assert((await page.evaluate(()=>menuTest.state())).sheet);await back();
await page.tap('#btnMenu');await page.evaluate(()=>menuTest.scan());assert.equal((await page.evaluate(()=>menuTest.state())).sheet,false);await back();await page.evaluate(()=>menuTest.scan());assert((await page.evaluate(()=>menuTest.state())).sheet);
await page.evaluate(()=>menuTest.drawer('right'));assert.equal((await page.evaluate(()=>menuTest.state())).upc,null);await back();assert.equal((await page.evaluate(()=>menuTest.state())).paused,false);
await page.tap('#btnMenu');await page.keyboard.press('Escape');assert.equal(await drawer(),'none');assert(await page.locator('#drawerLeft').evaluate(e=>e.inert));assert(await page.locator('#sheet').evaluate(e=>e.inert));
assert.deepEqual(errors,[]);console.log('MENU TOUCH OK: all routes, scrolling, edge swipes, both drawer closes, cancellation, back/Escape, scanner resumption, hidden panels inert');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
