const fs=require('fs'),assert=require('assert');const {chromium}=require('/tmp/node_modules/playwright-core');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});try{
 const page=await browser.newPage({viewport:{width:412,height:892},deviceScaleFactor:1});const html=fs.readFileSync(__dirname+'/../index.html','utf8');
 await page.route('https://harrys.local/**',r=>r.fulfill({contentType:'text/html',body:html}));await page.goto('https://harrys.local/');
 assert.equal(await page.locator('.t-piece').count(),5);assert.equal(await page.locator('.movie-particles i').count(),16);
 assert.equal(await page.locator('#splash').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(2, 6, 4)');
 await page.waitForTimeout(6400);await page.screenshot({path:__dirname+'/../shots/1.11-assembly.png'});
 await page.waitForTimeout(3200);assert(Number(await page.locator('.sp-fill').evaluate(e=>getComputedStyle(e).opacity))>.99);assert(Number(await page.locator('.splash-sub').evaluate(e=>getComputedStyle(e).opacity))>.9);await page.screenshot({path:__dirname+'/../shots/1.11-finished.png'});
 await page.waitForSelector('#splash',{state:'detached',timeout:2500});assert.equal(await page.locator('#app').evaluate(e=>e.inert),false);
 await page.reload();await page.click('#splashSkip');await page.waitForSelector('#splash',{state:'detached',timeout:1000});assert.equal(await page.locator('#app').evaluate(e=>e.inert),false);
 await page.emulateMedia({reducedMotion:'reduce'});await page.reload();assert.equal(await page.locator('.sp-fill').evaluate(e=>getComputedStyle(e).opacity),'1');await page.waitForSelector('#splash',{state:'detached',timeout:3000});
 await page.emulateMedia({reducedMotion:'no-preference'});await page.evaluate(()=>localStorage.setItem('hs.settings',JSON.stringify({theme:'daylight',animate:true})));await page.reload();assert.equal(await page.locator('#splash').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(2, 6, 4)');await page.click('#splashSkip');assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('hs.settings')).theme),'daylight');
 console.log('CINEMATIC OK: assembly, complete logo/title, timed exit, skip, reduced motion, purple-black intro with saved themes retained');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
