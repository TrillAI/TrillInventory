package com.harrys.scan;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.webkit.ConsoleMessage;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;

import org.json.JSONObject;

import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.Charset;
import java.util.HashMap;
import java.util.Map;

/**
 * Harry's Scan - native WebView shell.
 *
 * The entire UI is the bundled web app in assets/www. This shell exists to supply
 * the things a browser tab cannot: a real camera permission grant, an app icon,
 * persistent local storage, hardware-back handling, and file/clipboard bridges.
 */
public class MainActivity extends Activity {

    private static final String HOST = "harrys.local";
    private static final String START_URL = "https://" + HOST + "/index.html";
    private static final int REQ_CAMERA = 1001;
    private static final int MAX_BODY = 262144; // 256 KB cap on lookup responses

    private WebView web;
    private LocalServer localServer;
    private volatile int hostEpoch = 0;
    private ValueCallback<Uri[]> fileCallback;
    private static final int REQ_PHOTO_FILE = 1002;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        hideSystemUi();

        web = new WebView(this);
        web.setBackgroundColor(0xFF08070F);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false); // lets the scan beep play without a tap
        s.setAllowFileAccess(true); // only used by the local-asset fallback below
        s.setAllowContentAccess(true); // User-selected image URIs from the system picker.
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);
        s.setCacheMode(WebSettings.LOAD_NO_CACHE);

        web.addJavascriptInterface(new HostBridge(), "AndroidHost");

        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest req) {
                Uri url = req.getUrl();
                if (url == null || !HOST.equals(url.getHost())) return null;

                String path = url.getPath();
                if (path == null || path.isEmpty() || "/".equals(path)) path = "/index.html";

                try {
                    InputStream in = getAssets().open("www" + path);
                    Map<String, String> headers = new HashMap<String, String>();
                    headers.put("Cache-Control", "no-store");
                    WebResourceResponse res =
                            new WebResourceResponse(mimeOf(path), "utf-8", in);
                    res.setResponseHeaders(headers);
                    return res;
                } catch (IOException e) {
                    return new WebResourceResponse("text/plain", "utf-8",
                            new ByteArrayInputStream(
                                    "Not found".getBytes(Charset.forName("utf-8"))));
                }
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                Uri url = req.getUrl();
                if (url != null && HOST.equals(url.getHost())) return false;
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, url));
                } catch (Exception ignored) { }
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                hideSystemUi();
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest req, WebResourceError err) {
                // Belt and braces: if the intercepted https origin cannot load, fall back
                // to the plain asset URL so the app still opens offline.
                if (req != null && req.isForMainFrame()) {
                    view.loadUrl("file:///android_asset/www/index.html");
                }
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                             WebChromeClient.FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                // Honor the page's accept attribute: photo inputs get the photo
                // picker; .nes / .csv / anything else gets a real file picker.
                // (Previously this hardcoded image/*, so the ROM and CSV pickers
                // wrongly opened the photo gallery.)
                String[] accepts = null;
                try { accepts = params != null ? params.getAcceptTypes() : null; } catch (Exception ignored) { }
                boolean wantsImage = false, wantsAny = false, wantsRom = false, wantsCsv = false;
                java.util.ArrayList<String> mimes = new java.util.ArrayList<>();
                if (accepts != null) {
                    for (String raw : accepts) {
                        if (raw == null) continue;
                        for (String part : raw.split(",")) {
                            String a = part.trim().toLowerCase();
                            if (a.isEmpty()) continue;
                            if (a.equals(".nes")) { wantsRom = true; wantsAny = true; }
                            else if (a.equals(".csv") || a.equals("text/csv")) { wantsCsv = true; wantsAny = true; if (!mimes.contains("text/csv")) mimes.add("text/csv"); }
                            else if (a.startsWith("image/") || a.equals(".jpg") || a.equals(".jpeg") || a.equals(".png") || a.equals(".webp") || a.equals(".gif")) wantsImage = true;
                            else if (a.contains("/")) { wantsAny = true; if (!mimes.contains(a)) mimes.add(a); }
                            else wantsAny = true;
                        }
                    }
                }
                Intent pick = new Intent(Intent.ACTION_GET_CONTENT);
                pick.addCategory(Intent.CATEGORY_OPENABLE);
                String title = "Choose file";
                if (wantsImage && !wantsAny) {
                    pick.setType("image/*");
                    title = "Choose product photo";
                } else {
                    // */* so formats with no registered MIME type (.nes ROMs,
                    // some CSVs) are actually selectable in the Files picker.
                    pick.setType("*/*");
                    if (!mimes.isEmpty()) pick.putExtra(Intent.EXTRA_MIME_TYPES, mimes.toArray(new String[0]));
                    if (wantsRom) title = "Choose ROM file (.nes)";
                    else if (wantsCsv) title = "Choose CSV file";
                }
                try { startActivityForResult(Intent.createChooser(pick, title), REQ_PHOTO_FILE); }
                catch (Exception e) { fileCallback.onReceiveValue(null); fileCallback = null; }
                return true;
            }

            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        boolean wantsCamera = false;
                        for (String r : request.getResources()) {
                            if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(r)) wantsCamera = true;
                        }
                        if (wantsCamera && hasCamera()) request.grant(request.getResources());
                        else request.deny();
                    }
                });
            }

            @Override
            public boolean onConsoleMessage(ConsoleMessage m) {
                return true; // keep the log clean
            }
        });

        if (!hasCamera() && Build.VERSION.SDK_INT >= 23) {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, REQ_CAMERA);
        }

        web.loadUrl(START_URL);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_PHOTO_FILE && fileCallback != null) {
            Uri selected = resultCode == RESULT_OK && data != null ? data.getData() : null;
            fileCallback.onReceiveValue(selected == null ? null : new Uri[]{selected});
            fileCallback = null;
        }
    }

    private boolean hasCamera() {
        if (Build.VERSION.SDK_INT < 23) return true;
        return checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] results) {
        super.onRequestPermissionsResult(code, perms, results);
        if (code == REQ_CAMERA && web != null) {
            // Reload so the page re-negotiates the camera cleanly after the grant.
            web.reload();
        }
    }

    @Override
    public void onBackPressed() {
        if (web == null) {
            super.onBackPressed();
            return;
        }
        // Let the web app close its own sheet/drawer first; finish only if it declines.
        web.evaluateJavascript(
                "(window.__hsHandleBack && window.__hsHandleBack()) ? 'true' : 'false'",
                new ValueCallback<String>() {
                    @Override
                    public void onReceiveValue(String value) {
                        boolean handled = value != null && value.contains("true");
                        if (!handled) finish();
                    }
                });
    }

    private void hideSystemUi() {
        View d = getWindow().getDecorView();
        d.setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }

    private static String mimeOf(String path) {
        String p = path.toLowerCase();
        if (p.endsWith(".html") || p.endsWith(".htm")) return "text/html";
        if (p.endsWith(".js")) return "application/javascript";
        if (p.endsWith(".css")) return "text/css";
        if (p.endsWith(".json")) return "application/json";
        if (p.endsWith(".csv")) return "text/csv";
        if (p.endsWith(".svg")) return "image/svg+xml";
        if (p.endsWith(".png")) return "image/png";
        if (p.endsWith(".jpg") || p.endsWith(".jpeg")) return "image/jpeg";
        if (p.endsWith(".woff2")) return "font/woff2";
        return "application/octet-stream";
    }

    /**
     * Hosts the price lookup is allowed to reach. Anything else is refused outright,
     * so a compromised page inside the WebView cannot exfiltrate data through the bridge.
     */
    private static final Set<String> ALLOWED_HOSTS = new HashSet<String>(Arrays.asList(
            "api.upcitemdb.com",
            "prices.openfoodfacts.org",
            "world.openfoodfacts.org",
            "images.openfoodfacts.org"));

    /**
     * Performs an HTTPS GET off the UI thread and hands the body back to JavaScript.
     *
     * This exists because UPCitemdb only serves CORS headers to its own origin, so a
     * plain fetch() from the app's origin is blocked by the WebView. Routing through
     * native code sidesteps CORS without disabling WebView security globally.
     */
    @JavascriptInterface
    public void httpGet(final String url, final String reqId) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                int code = 0;
                String body = "";
                HttpURLConnection conn = null;
                try {
                    URL u = new URL(url);
                    if (!"https".equalsIgnoreCase(u.getProtocol())) {
                        throw new IllegalArgumentException("https only");
                    }
                    String host = u.getHost();
                    if (host == null || !ALLOWED_HOSTS.contains(host.toLowerCase())) {
                        throw new IllegalArgumentException("host not allowed: " + host);
                    }

                    conn = (HttpURLConnection) u.openConnection();
                    conn.setRequestMethod("GET");
                    conn.setConnectTimeout(8000);
                    conn.setReadTimeout(12000);
                    conn.setInstanceFollowRedirects(false); // Do not follow redirects outside the host allowlist.
                    conn.setRequestProperty("Accept", "application/json");
                    conn.setRequestProperty("User-Agent", "TrillInventory/1.6.1 (Android)");
                    conn.setRequestProperty("Accept-Encoding", "identity");

                    code = conn.getResponseCode();
                    InputStream in = (code >= 200 && code < 300)
                            ? conn.getInputStream() : conn.getErrorStream();

                    if (in != null) {
                        ByteArrayOutputStream out = new ByteArrayOutputStream();
                        byte[] buf = new byte[4096];
                        int n, total = 0;
                        while ((n = in.read(buf)) != -1) {
                            total += n;
                            if (total > MAX_BODY) break;
                            out.write(buf, 0, n);
                        }
                        in.close();
                        body = out.toString("UTF-8");
                    }
                } catch (Exception e) {
                    body = "{\"error\":\"" + String.valueOf(e.getMessage())
                            .replace("\\", "\\\\").replace("\"", "'") + "\"}";
                } finally {
                    if (conn != null) conn.disconnect();
                }

                final String js = "window.__hsHttpResult(" + JSONObject.quote(reqId) + ","
                        + code + "," + JSONObject.quote(body) + ")";
                web.post(new Runnable() {
                    @Override
                    public void run() {
                        web.evaluateJavascript(js, null);
                    }
                });
            }
        }).start();
    }

    private String serverStatus(String error) {
        JSONObject o = new JSONObject();
        try {
            boolean active=localServer!=null && localServer.isRunning();
            o.put("running",active); o.put("error",error);
            org.json.JSONArray addresses=new org.json.JSONArray();
            if(active){
                o.put("token",localServer.pairingCode());o.put("qrToken",localServer.token());
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
    private LocalServer.Reply browserRequest(final String action, final String body, final int epoch) throws Exception {
        final java.util.concurrent.CountDownLatch latch=new java.util.concurrent.CountDownLatch(1);
        final java.util.concurrent.atomic.AtomicBoolean active=new java.util.concurrent.atomic.AtomicBoolean(true);
        final LocalServer.Reply[] reply=new LocalServer.Reply[1];
        runOnUiThread(new Runnable(){public void run(){
            if(!active.get() || epoch!=hostEpoch || localServer==null || !localServer.isRunning()){latch.countDown();return;}
            String js="window.__trillServerRequest ? window.__trillServerRequest("+JSONObject.quote(action)+","+JSONObject.quote(body)+") : JSON.stringify({status:503,error:'App is loading'})";
            web.evaluateJavascript(js,new ValueCallback<String>(){public void onReceiveValue(String result){
                try {
                    Object decoded=new org.json.JSONTokener(result).nextValue();
                    JSONObject data=new JSONObject(String.valueOf(decoded));
                    reply[0]=new LocalServer.Reply(data.optInt("status",200),data.toString());
                }catch(Exception e){reply[0]=new LocalServer.Reply(503,"{\"error\":\"App is loading\"}");}
                latch.countDown();
            }});
        }});
        boolean done=latch.await(7,java.util.concurrent.TimeUnit.SECONDS); active.set(false);
        if(!done || reply[0]==null) return new LocalServer.Reply(503,"{\"error\":\"Phone did not respond. Refresh before retrying.\"}");
        return reply[0];
    }
    @Override
    protected void onDestroy(){
        hostEpoch++;
        if(localServer!=null)localServer.stop();
        if(fileCallback!=null){fileCallback.onReceiveValue(null);fileCallback=null;}
        super.onDestroy();
    }

    /** Small bridge so exports and "copy order list" work inside the app sandbox. */
    private class HostBridge {
        @JavascriptInterface
        public String localServerStatus(){return serverStatus("");}
        @JavascriptInterface
        public String startLocalServer(){
            try {
                if(localServer==null || !localServer.isRunning()){
                    ByteArrayOutputStream bytes=new ByteArrayOutputStream();
                    InputStream in=getAssets().open("www/remote.html");
                    byte[] buffer=new byte[4096];int n;while((n=in.read(buffer))!=-1)bytes.write(buffer,0,n);in.close();
                    final int epoch=++hostEpoch;
                    localServer=new LocalServer(bytes.toByteArray(), new LocalServer.Handler(){
                        public LocalServer.Reply handle(String action,String body)throws Exception{return browserRequest(action,body,epoch);}
                    },new LocalServer.TrustStore(){
                        public java.util.Set<String> load(){return new java.util.HashSet<String>(getSharedPreferences("trill-pairing",MODE_PRIVATE).getStringSet("devices",new java.util.HashSet<String>()));}
                        public void save(java.util.Set<String> values){if(!getSharedPreferences("trill-pairing",MODE_PRIVATE).edit().putStringSet("devices",values).commit())throw new IllegalStateException("Could not save trusted browsers");}
                    });
                    localServer.start(8765);
                    runOnUiThread(()->getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON));
                }
                return serverStatus("");
            }catch(Exception e){if(localServer!=null)localServer.stop();return serverStatus("Could not start hosting. Port 8765 may already be in use.");}
        }
        @JavascriptInterface
        public String stopLocalServer(){hostEpoch++;if(localServer!=null)localServer.stop();runOnUiThread(()->getWindow().clearFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON));return serverStatus("");}
        @JavascriptInterface public boolean isHosting(){return localServer!=null && localServer.isRunning();}
        @JavascriptInterface public void publishState(String state){if(localServer!=null && localServer.isRunning())localServer.publish(state);}
        @JavascriptInterface public String forgetBrowserDevices(){if(localServer!=null)localServer.forgetDevices();return serverStatus("");}
        @JavascriptInterface public String renewBrowserCode(){if(localServer!=null)localServer.renewPairing();return serverStatus("");}


        @JavascriptInterface
        public void httpGet(final String url, final String reqId) {
            MainActivity.this.httpGet(url, reqId);
        }


        @JavascriptInterface
        public void copyText(final String text) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    ClipboardManager cm =
                            (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                    if (cm != null) cm.setPrimaryClip(ClipData.newPlainText("Harry's Scan", text));
                }
            });
        }

        @JavascriptInterface
        public void saveFile(final String name, final String content) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    try {
                        File dir = new File(getExternalFilesDir(null), "exports");
                        if (!dir.exists() && !dir.mkdirs()) {
                            throw new IOException("could not create exports folder");
                        }
                        File f = new File(dir, name.replaceAll("[^A-Za-z0-9._-]", "_"));
                        OutputStreamWriter w = new OutputStreamWriter(
                                new FileOutputStream(f), Charset.forName("utf-8"));
                        w.write(content);
                        w.close();
                        Toast.makeText(MainActivity.this,
                                "Saved to " + f.getAbsolutePath(), Toast.LENGTH_LONG).show();
                    } catch (Exception e) {
                        Toast.makeText(MainActivity.this,
                                "Save failed: " + e.getMessage(), Toast.LENGTH_LONG).show();
                    }
                }
            });
        }
    }
}
