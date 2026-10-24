from pathlib import Path
r=Path('/home/user/trill-inventory');p=r/'android/src/com/harrys/scan/MainActivity.java';s=p.read_text().replace('    private WebView web;', '    private WebView web;\n    private LocalServer localServer;')
pos=s.index('    /** Small bridge')
s=s[:pos]+'''    private String serverStatus(String error) {
        JSONObject o = new JSONObject();
        try {
            boolean active=localServer!=null && localServer.isRunning();
            o.put("running",active); o.put("error",error);
            org.json.JSONArray addresses=new org.json.JSONArray();
            if(active){
                o.put("token",localServer.token());
                java.util.Enumeration<java.net.NetworkInterface> interfaces=java.net.NetworkInterface.getNetworkInterfaces();
                while(interfaces.hasMoreElements()){
                    java.net.NetworkInterface network=interfaces.nextElement();
                    if(!network.isUp() || network.isLoopback()) continue;
                    java.util.Enumeration<java.net.InetAddress> ips=network.getInetAddresses();
                    while(ips.hasMoreElements()){
                        java.net.InetAddress ip=ips.nextElement();
                        if(ip instanceof java.net.Inet4Address && ip.isSiteLocalAddress())
                            addresses.put("http://"+ip.getHostAddress()+":"+localServer.port());
                    }
                }
            }
            o.put("addresses",addresses);
        } catch(Exception e) { }
        return o.toString();
    }
    private LocalServer.Reply browserRequest(final String action, final String body) throws Exception {
        final java.util.concurrent.CountDownLatch latch=new java.util.concurrent.CountDownLatch(1);
        final java.util.concurrent.atomic.AtomicBoolean active=new java.util.concurrent.atomic.AtomicBoolean(true);
        final LocalServer.Reply[] reply=new LocalServer.Reply[1];
        runOnUiThread(new Runnable(){public void run(){
            if(!active.get() || localServer==null || !localServer.isRunning()){latch.countDown();return;}
            String js="window.__trillServerRequest ? window.__trillServerRequest("+JSONObject.quote(action)+","+JSONObject.quote(body)+") : JSON.stringify({status:503,error:'App is loading'})";
            web.evaluateJavascript(js,new ValueCallback<String>(){public void onReceiveValue(String result){
                try {
                    Object decoded=new org.json.JSONTokener(result).nextValue();
                    JSONObject data=new JSONObject(String.valueOf(decoded));
                    reply[0]=new LocalServer.Reply(data.optInt("status",200),data.toString());
                }catch(Exception e){reply[0]=new LocalServer.Reply(503,"{\\"error\\":\\"App is loading\\"}");}
                latch.countDown();
            }});
        }});
        boolean done=latch.await(7,java.util.concurrent.TimeUnit.SECONDS); active.set(false);
        if(!done || reply[0]==null) return new LocalServer.Reply(503,"{\\"error\\":\\"Phone did not respond. Refresh before retrying.\\"}");
        return reply[0];
    }
    @Override
    protected void onDestroy(){
        if(localServer!=null)localServer.stop();
        if(fileCallback!=null){fileCallback.onReceiveValue(null);fileCallback=null;}
        super.onDestroy();
    }

''' +s[pos:]
s=s.replace('    private class HostBridge {','''    private class HostBridge {
        @JavascriptInterface
        public String localServerStatus(){return serverStatus("");}
        @JavascriptInterface
        public String startLocalServer(){
            try {
                if(localServer==null || !localServer.isRunning()){
                    ByteArrayOutputStream bytes=new ByteArrayOutputStream();
                    InputStream in=getAssets().open("www/remote.html");
                    byte[] buffer=new byte[4096];int n;while((n=in.read(buffer))!=-1)bytes.write(buffer,0,n);in.close();
                    localServer=new LocalServer(bytes.toByteArray(), new LocalServer.Handler(){
                        public LocalServer.Reply handle(String action,String body)throws Exception{return browserRequest(action,body);}
                    });
                    localServer.start(8765);
                }
                return serverStatus("");
            }catch(Exception e){if(localServer!=null)localServer.stop();return serverStatus("Could not start hosting. Port 8765 may already be in use.");}
        }
        @JavascriptInterface
        public String stopLocalServer(){if(localServer!=null)localServer.stop();return serverStatus("");}
''');p.write_text(s)
p=r/'android/build.sh';s=p.read_text().replace('cp "$ROOT/vendor/zxing.min.js" "$ROOT/assets/www/zxing.min.js"','cp "$ROOT/vendor/zxing.min.js" "$ROOT/assets/www/zxing.min.js"\ncp "$ROOT/vendor/remote.html" "$ROOT/assets/www/remote.html"');p.write_text(s)
p=r/'index.html';s=p.read_text();s=s.replace('      <button class="nav-item" data-nav="store">','      <button class="nav-item" data-nav="browser"><div class="nav-ico">▣</div><div class="nav-txt"><b>Browser access</b><small>Host on this phone · Wi-Fi</small></div><span class="nav-arrow">›</span></button>\n      <button class="nav-item" data-nav="store">')
s=s.replace("else if(what === 'inventory') viewInventory();", "else if(what === 'browser') viewBrowserHost();\n      else if(what === 'inventory') viewInventory();")
pos=s.index('/* Quick, offline price editing.')
s=s[:pos]+'''/* Phone-hosted LAN dashboard. Only explicit fields can be edited remotely. */
function browserRecord(p){
  var inv=INV[p.upc], qty=inv ? Number(inv.qty || 0) : 0;
  var price=Number(p.price || 0),cost=Number(p.cost || 0),rec=recommend(p,qty);
  return {upc:String(p.upc),name:p.name,brand:p.brand || '',size:p.size || '',qty:qty,price:price,cost:cost,
    rp:Number(p.rp || 0),par:Number(p.par || 0),reorder:rec.units,
    version:JSON.stringify([qty,price,cost])};
}
function browserProducts(){
  return allCatalog().filter(function(p){return !!INV[p.upc] || EXTRA.some(function(e){return String(e.upc)===String(p.upc);});});
}
window.__trillServerRequest=function(action,raw){
  try {
    if(action==='state')return JSON.stringify({status:200,items:browserProducts().map(browserRecord),at:Date.now()});
    if(action!=='edit')return JSON.stringify({status:400,error:'Unsupported operation'});
    var d=JSON.parse(raw),p=browserProducts().find(function(p){return String(p.upc)===String(d.upc);});
    if(!p)return JSON.stringify({status:404,error:'Saved product not found'});
    if(d.expected!==browserRecord(p).version)return JSON.stringify({status:409,error:'This item changed on another device. Refresh and try again.'});
    if(!Number.isInteger(d.qty) || d.qty<0 || d.qty>1000000 || ![d.price,d.cost].every(function(v){return typeof v==='number' && isFinite(v) && v>=0 && v<=99999.99 && Math.abs(v*100-Math.round(v*100))<0.000001;}))return JSON.stringify({status:400,error:'Invalid stock count or price'});
    var next=EXTRA.map(function(e){return Object.assign({},e);}),entry=next.find(function(e){return String(e.upc)===String(p.upc);});
    if(!entry){entry={upc:p.upc};next.push(entry);}
    var priceChanged=Number(p.price || 0)!==d.price || Number(p.cost || 0)!==d.cost;
    entry.price=d.price;entry.cost=d.cost;
    if(priceChanged)entry.priceEditedAt=Date.now();
    var inventory=Object.assign({},INV),old=INV[p.upc];
    inventory[p.upc]=Object.assign({},old || {first:Date.now(),scans:0},{qty:d.qty,last:Date.now()});
    if(!storageOK)return JSON.stringify({status:507,error:'Phone storage is unavailable'});
    var oldCatalog=localStorage.getItem('hs.catalog'),oldInv=localStorage.getItem('hs.inventory');
    try {
      localStorage.setItem('hs.catalog',JSON.stringify(next));localStorage.setItem('hs.inventory',JSON.stringify(inventory));
    }catch(e){
      try{if(oldCatalog===null)localStorage.removeItem('hs.catalog');else localStorage.setItem('hs.catalog',oldCatalog);if(oldInv===null)localStorage.removeItem('hs.inventory');else localStorage.setItem('hs.inventory',oldInv);}catch(ignore){}
      return JSON.stringify({status:507,error:'Could not save on the phone. Free storage and refresh.'});
    }
    EXTRA=next;INV=inventory;rebuildIndex();
    if(priceChanged){PRICEMETA[p.upc]={price:d.price,source:'browser edit',at:Date.now()};lsSet('hs.pricemeta',PRICEMETA);}
    renderHud();
    if(sheetOpen && currentUpc===String(p.upc) && $('qtyVal')){var pending=pendingQty;showResult(currentUpc,'browser');pendingQty=pending;refreshQtyVal();}
    toast('Browser updated '+p.name,'good');
    return JSON.stringify({status:200,item:browserRecord(getProduct(p.upc))});
  }catch(e){return JSON.stringify({status:400,error:'Invalid request or app not ready'});}
};
function viewBrowserHost(result){
  var host=window.AndroidHost,available=host && host.startLocalServer;
  var state=result || (available ? parseJSON(host.localServerStatus()) : null) || {running:false};
  var html='<p class="desc">Open your phone’s inventory on a computer or another browser on the same trusted Wi-Fi. Connected users can change prices, unit cost and total stock counts.</p>';
  if(!available){html+='<div class="prodnote">Phone hosting requires the Android APK. Install version 1.9.0 or later.</div>';openSheet('Browser access','Android phone host',html,'');return;}
  html+='<div class="prodnote">Trusted private Wi-Fi only. This uses unencrypted HTTP. Anyone with the connection code can edit your inventory. Never forward this port or use it on public Wi-Fi.</div>';
  if(state.error)html+='<p class="desc">'+esc(state.error)+'</p>';
  if(state.running){
    html+='<div class="sect-title">1. Open this address on your computer</div>';
    (state.addresses || []).forEach(function(url){html+='<div class="field"><input readonly value="'+esc(url)+'" onclick="this.select()"></div>';});
    if(!(state.addresses || []).length)html+='<p class="desc">No local IPv4 address found. Connect to Wi-Fi, then refresh this screen.</p>';
    html+='<div class="sect-title">2. Enter this connection code</div><div class="field"><input readonly value="'+esc(state.token || '')+'" onclick="this.select()"></div><button class="btn btn-block" data-act="copyHostCode">Copy connection code</button>';
    html+='<p class="desc">Keep Trill open on this screen. Switching apps, locking the phone, Wi-Fi changes, or Android power management may interrupt hosting. Guest Wi-Fi often blocks device-to-device connections. Stop and restart to revoke all current codes.</p>';
  }else html+='<p class="desc">Hosting is off by default. Start it only when you need browser access. No cloud account or internet hosting is used.</p>';
  openSheet('Browser access',state.running?'Hosting on port 8765':'Not hosting',html,
    '<button class="btn" data-act="hostRefresh">Refresh</button><button class="btn btn-primary" data-act="'+(state.running?'hostStop':'hostStart')+'">'+(state.running?'Stop hosting':'Start hosting')+'</button>');
}

''' +s[pos:]
# discover recommend actual function below if needed
s=s.replace("function sheetAction(act, btn){", """function sheetAction(act, btn){
  if(act==='hostStart'){viewBrowserHost(parseJSON(window.AndroidHost.startLocalServer()));return;}
  if(act==='hostStop'){viewBrowserHost(parseJSON(window.AndroidHost.stopLocalServer()));return;}
  if(act==='hostRefresh'){viewBrowserHost();return;}
  if(act==='copyHostCode'){var state=parseJSON(window.AndroidHost.localServerStatus());if(state && state.token){window.AndroidHost.copyText(state.token);toast('Connection code copied');}return;}
""")
s=s.replace("priceEditState = {upc:upc, qty:qty, cost:Number(p.cost || 0)};", "priceEditState = {upc:upc, qty:qty, cost:Number(p.cost || 0), originalPrice:Number(p.price || 0)};")
s=s.replace("  var v = priceEditValues();\n  if(v.price === null", "  var latest=getProduct(state.upc);\n  if(Number(latest.price || 0)!==state.originalPrice || Number(latest.cost || 0)!==state.cost){$('editPriceError').textContent='Price changed on another device. Cancel and reopen Edit price.';return;}\n  var v = priceEditValues();\n  if(v.price === null")
p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=r/f;s=p.read_text().replace('1.8.0','1.9.0').replace('--version-code 10','--version-code 11').replace('versionCode="10"','versionCode="11"');p.write_text(s)
