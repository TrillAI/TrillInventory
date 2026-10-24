from pathlib import Path
root=Path('/home/user/trill-inventory');p=root/'android/src/com/harrys/scan/LocalServer.java';s=p.read_text()
s=s.replace('private String token;', '''private volatile String token;
    public interface TrustStore { Set<String> load(); void save(Set<String> values); }
    private TrustStore trustStore;
    private final Set<String> trusted=Collections.synchronizedSet(new HashSet<String>());
    private String pairCode;
    private long pairExpires, attemptWindow;
    private int attempts;
    private final Object changes=new Object();
    private volatile String snapshot;
    private volatile long revision;
    private final Semaphore watchers=new Semaphore(4);
    public LocalServer(byte[] page,Handler handler,TrustStore store){this(page,handler);trustStore=store;trusted.addAll(store.load());}
    private static String secret(){byte[] r=new byte[24];new SecureRandom().nextBytes(r);StringBuilder b=new StringBuilder();for(byte v:r)b.append(String.format(Locale.US,"%02x",v&255));return b.toString();}
    public synchronized String pairingCode(){return pairCode;}
    public synchronized void forgetDevices(){trusted.clear();if(trustStore!=null)trustStore.save(new HashSet<String>());renewPairing();}
    public synchronized void renewPairing(){pairCode=String.format(Locale.US,"%06d",new SecureRandom().nextInt(1000000));pairExpires=System.currentTimeMillis()+600000;token=secret();attempts=0;attemptWindow=0;}
    public void publish(String state){if(state==null || state.length()>8000000)return;synchronized(changes){if(!state.equals(snapshot)){snapshot=state;revision++;changes.notifyAll();}}}
    private boolean authenticated(String header){if(header==null || !header.startsWith("Bearer "))return false;String value=header.substring(7),current=token;return (current!=null && MessageDigest.isEqual(current.getBytes(StandardCharsets.UTF_8),value.getBytes(StandardCharsets.UTF_8))) || trusted.contains(value);}
    private synchronized String pair(String header){
        long now=System.currentTimeMillis();if(now-attemptWindow>60000){attemptWindow=now;attempts=0;}
        if(++attempts>10 || now>pairExpires || header==null || !header.startsWith("Bearer "))return null;
        String value=header.substring(7);boolean valid=MessageDigest.isEqual(pairCode.getBytes(StandardCharsets.UTF_8),value.getBytes(StandardCharsets.UTF_8)) || MessageDigest.isEqual(token.getBytes(StandardCharsets.UTF_8),value.getBytes(StandardCharsets.UTF_8));
        if(!valid || trusted.size()>=32)return null;
        String credential=secret();trusted.add(credential);if(trustStore!=null)trustStore.save(new HashSet<String>(trusted));return credential;
    }''')
s=s.replace('byte[] random=new byte[24]; new SecureRandom().nextBytes(random);\n        StringBuilder b=new StringBuilder(); for(byte v:random)b.append(String.format(Locale.US,"%02x",v & 255)); token=b.toString();','renewPairing();snapshot=null;revision=0;')
s=s.replace('new ThreadPoolExecutor(4,4,','new ThreadPoolExecutor(8,8,')
s=s.replace('running=false;','running=false; synchronized(changes){changes.notifyAll();}',1)
a=s.index('            if(!request[1].equals("/api/state")');b=s.index('            Reply reply;',a)
s=s[:a]+'''            if("POST".equals(request[0]) && "/api/pair".equals(request[1])){
                String credential=pair(headers.get("authorization"));
                if(credential==null){json(socket,401,"Pairing failed. Check the code; after repeated attempts wait one minute. Codes expire after ten minutes. At most 32 devices can be remembered.");return;}
                send(socket,200,"application/json",("{\\"credential\\":\\""+credential+"\\"}").getBytes(StandardCharsets.UTF_8));return;
            }
            boolean events=request[1].matches("/api/events\\\\?after=[0-9]{1,18}");
            if(!request[1].equals("/api/state") && !request[1].equals("/api/edit") && !events){json(socket,404,"Not found");return;}
            String supplied=headers.get("authorization");
            if(!authenticated(supplied)){json(socket,401,"Connection code required");return;}
            if(events && "GET".equals(request[0])){
                if(!watchers.tryAcquire()){json(socket,503,"Live viewer limit reached; manual refresh remains available");return;}
                try{
                    long after=Long.parseLong(request[1].substring(request[1].indexOf('=')+1));
                    if(snapshot==null){Reply initial=handler.handle("state","{}");if(initial.status==200)publish(initial.body);}
                    String body;long deadline=System.currentTimeMillis()+20000;
                    synchronized(changes){while(running && revision==after && System.currentTimeMillis()<deadline)changes.wait(Math.max(1,deadline-System.currentTimeMillis()));body="{\\"revision\\":"+revision+",\\"state\\":"+(snapshot==null?"null":snapshot)+"}";}
                    if(!running || !authenticated(supplied)){json(socket,401,"Connection revoked");return;}
                    send(socket,200,"application/json",body.getBytes(StandardCharsets.UTF_8));
                }finally{watchers.release();}return;
            }
'''+s[b:]
s=s.replace("connect-src 'self'; frame-ancestors", "connect-src 'self'; img-src https: data:; font-src data:; frame-ancestors")
p.write_text(s)
p=root/'android/src/com/harrys/scan/MainActivity.java';s=p.read_text().replace('o.put("token",localServer.token());','o.put("token",localServer.pairingCode());o.put("qrToken",localServer.token());')
s=s.replace('''                    });
                    localServer.start(8765);''','''                    },new LocalServer.TrustStore(){
                        public java.util.Set<String> load(){return new java.util.HashSet<String>(getSharedPreferences("trill-pairing",MODE_PRIVATE).getStringSet("devices",new java.util.HashSet<String>()));}
                        public void save(java.util.Set<String> values){getSharedPreferences("trill-pairing",MODE_PRIVATE).edit().putStringSet("devices",values).commit();}
                    });
                    localServer.start(8765);
                    runOnUiThread(()->getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON));''')
s=s.replace('public String stopLocalServer(){hostEpoch++;if(localServer!=null)localServer.stop();return serverStatus("");}', '''public String stopLocalServer(){hostEpoch++;if(localServer!=null)localServer.stop();runOnUiThread(()->getWindow().clearFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON));return serverStatus("");}
        @JavascriptInterface public boolean isHosting(){return localServer!=null && localServer.isRunning();}
        @JavascriptInterface public void publishState(String state){if(localServer!=null && localServer.isRunning())localServer.publish(state);}
        @JavascriptInterface public String forgetBrowserDevices(){if(localServer!=null)localServer.forgetDevices();return serverStatus("");}
        @JavascriptInterface public String renewBrowserCode(){if(localServer!=null)localServer.renewPairing();return serverStatus("");}''')
p.write_text(s)
