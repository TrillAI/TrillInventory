package com.harrys.scan;

import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;

/** Small foreground LAN server. No filesystem access, proxying or public hosting. */
public final class LocalServer {
    public interface Handler { Reply handle(String action, String body) throws Exception; }
    public static final class Reply {
        public final int status; public final String body;
        public Reply(int status, String body) { this.status=status; this.body=body; }
    }
    private final Handler handler;
    private final byte[] page;
    private ServerSocket listener;
    private volatile boolean running;
    private ThreadPoolExecutor pool;
    private final Set<Socket> clients = Collections.synchronizedSet(new HashSet<Socket>());
    private volatile String token;
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
    }
    public LocalServer(byte[] page, Handler handler) { this.page=page; this.handler=handler; }
    public synchronized void start(int port) throws IOException {
        if (running) return;
        renewPairing();snapshot=null;revision=0;
        listener=new ServerSocket(); listener.setReuseAddress(true); listener.bind(new InetSocketAddress("0.0.0.0",port),16);
        pool=new ThreadPoolExecutor(8,8,0,TimeUnit.SECONDS,new ArrayBlockingQueue<Runnable>(16));
        running=true;
        final ServerSocket socket=listener;
        new Thread(new Runnable(){public void run(){
            while(running && !socket.isClosed()){
                try {
                    final Socket client=socket.accept(); client.setSoTimeout(5000); clients.add(client);
                    try { pool.execute(new Runnable(){public void run(){serve(client);}}); }
                    catch(RejectedExecutionException e){ clients.remove(client);client.close(); }
                }catch(IOException e){break;}
            }
        }},"Trill LAN listener").start();
    }
    public synchronized void stop(){
        running=false; synchronized(changes){changes.notifyAll();}
        try{if(listener!=null)listener.close();}catch(IOException ignored){}
        synchronized(clients){for(Socket s:clients)try{s.close();}catch(IOException ignored){} clients.clear();}
        if(pool!=null)pool.shutdownNow(); token=null;
    }
    public boolean isRunning(){return running;}
    public String token(){return token;}
    public int port(){return listener==null?0:listener.getLocalPort();}
    private static String line(InputStream in) throws IOException {
        ByteArrayOutputStream b=new ByteArrayOutputStream(); int c;
        while((c=in.read())!=-1){if(c==10)break; if(c!=13)b.write(c);if(b.size()>4096)throw new IOException("line too long");}
        if(c==-1 && b.size()==0)return null;
        return new String(b.toByteArray(),StandardCharsets.US_ASCII);
    }
    private void serve(Socket socket){
        try{
            InetAddress peer=socket.getInetAddress(), local=socket.getLocalAddress();
            if(!(peer.isSiteLocalAddress() || peer.isLoopbackAddress()) || !(local.isSiteLocalAddress() || local.isLoopbackAddress())){
                json(socket,403,"Private local network required");return;
            }
            InputStream in=new BufferedInputStream(socket.getInputStream());
            String first=line(in);if(first==null)return;
            String[] request=first.split(" "); if(request.length!=3){send(socket,400,"text/plain","Bad request".getBytes(StandardCharsets.UTF_8));return;}
            Map<String,String> headers=new HashMap<String,String>();String l;int bytes=0;
            while((l=line(in))!=null && !l.isEmpty()){
                bytes+=l.length(); if(bytes>16384)throw new IOException("headers too large");
                int colon=l.indexOf(':');if(colon<1)throw new IOException("bad header");
                String k=l.substring(0,colon).trim().toLowerCase(Locale.US);
                if(headers.containsKey(k))throw new IOException("duplicate header");
                headers.put(k,l.substring(colon+1).trim());
            }
            String host=headers.get("host"), expected=socket.getLocalAddress().getHostAddress()+":"+port();
            if(host==null || !host.equals(expected)){json(socket,403,"Invalid host");return;}
            String origin=headers.get("origin");
            if(origin!=null && !origin.equals("http://"+host)){json(socket,403,"Cross-origin access refused");return;}
            if("GET".equals(request[0]) && "/".equals(request[1])){send(socket,200,"text/html; charset=utf-8",page);return;}
            if("POST".equals(request[0]) && "/api/pair".equals(request[1])){
                String credential=pair(headers.get("authorization"));
                if(credential==null){json(socket,401,"Pairing failed. Check the code; after repeated attempts wait one minute. Codes expire after ten minutes. At most 32 devices can be remembered.");return;}
                send(socket,200,"application/json",("{\"credential\":\""+credential+"\"}").getBytes(StandardCharsets.UTF_8));return;
            }
            boolean events=request[1].matches("/api/events\\?after=[0-9]{1,18}");
            if(!request[1].equals("/api/state") && !request[1].equals("/api/edit") && !events){json(socket,404,"Not found");return;}
            String supplied=headers.get("authorization");
            if(!authenticated(supplied)){json(socket,401,"Connection code required");return;}
            if(events && "GET".equals(request[0])){
                if(!watchers.tryAcquire()){json(socket,503,"Live viewer limit reached; manual refresh remains available");return;}
                try{
                    long after=Long.parseLong(request[1].substring(request[1].indexOf('=')+1));
                    if(snapshot==null){Reply initial=handler.handle("state","{}");if(initial.status==200)publish(initial.body);}
                    String body;long deadline=System.currentTimeMillis()+20000;
                    synchronized(changes){while(running && revision==after && System.currentTimeMillis()<deadline)changes.wait(Math.max(1,deadline-System.currentTimeMillis()));body="{\"revision\":"+revision+",\"state\":"+(snapshot==null?"null":snapshot)+"}";}
                    if(!running || !authenticated(supplied)){json(socket,401,"Connection revoked");return;}
                    send(socket,200,"application/json",body.getBytes(StandardCharsets.UTF_8));
                }finally{watchers.release();}return;
            }
            Reply reply;
            if("GET".equals(request[0]) && "/api/state".equals(request[1])){
                reply=handler.handle("state", "{}");
            }else if("POST".equals(request[0]) && "/api/edit".equals(request[1])){
                if(headers.containsKey("transfer-encoding") || !"application/json".equals(headers.get("content-type"))){json(socket,400,"JSON required");return;}
                int size;try{size=Integer.parseInt(headers.get("content-length"));}catch(Exception e){json(socket,400,"Length required");return;}
                if(size<2 || size>8192){json(socket,413,"Request too large");return;}
                byte[] body=new byte[size];int offset=0,n;
                while(offset<size && (n=in.read(body,offset,size-offset))!=-1)offset+=n;
                if(offset!=size)throw new IOException("incomplete body");
                if(!running){json(socket,503,"Server stopped");return;}
                reply=handler.handle("edit",new String(body,StandardCharsets.UTF_8));
            }else{json(socket,405,"Method not allowed");return;}
            send(socket,reply.status,"application/json; charset=utf-8",reply.body.getBytes(StandardCharsets.UTF_8));
        }catch(Exception e){try{json(socket,503,"Phone unavailable. Refresh before retrying a change.");}catch(Exception ignored){}}
        finally{clients.remove(socket);try{socket.close();}catch(IOException ignored){}}
    }
    private void json(Socket s,int status,String message)throws IOException{
        send(s,status,"application/json; charset=utf-8",("{\"error\":\""+message+"\"}").getBytes(StandardCharsets.UTF_8));
    }
    private void send(Socket s,int status,String type,byte[] body)throws IOException{
        String h="HTTP/1.1 "+status+" Response\r\nContent-Type: "+type+"\r\nContent-Length: "+body.length+"\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nX-Frame-Options: DENY\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src https: data:; font-src data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'\r\nConnection: close\r\n\r\n";
        OutputStream out=s.getOutputStream();out.write(h.getBytes(StandardCharsets.US_ASCII));out.write(body);out.flush();
    }
}
