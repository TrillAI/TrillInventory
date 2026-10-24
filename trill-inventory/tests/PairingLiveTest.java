import com.harrys.scan.LocalServer;
import java.util.*;import java.util.concurrent.*;
public class PairingLiveTest {
 static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
 static String auth(String t){return "Authorization: Bearer "+t+"\r\n";}
 static String req(LocalServer s,String method,String path,String token)throws Exception{return LocalServerTest.request(s.port(),method,path,auth(token),"");}
 public static void main(String[]args)throws Exception{
  final Set<String> saved=new HashSet<>();LocalServer.TrustStore store=new LocalServer.TrustStore(){public Set<String> load(){return new HashSet<>(saved);}public void save(Set<String> v){saved.clear();saved.addAll(v);}};
  LocalServer.Handler handler=(a,b)->new LocalServer.Reply(200,"{\"items\":[]}");LocalServer s=new LocalServer(new byte[0],handler,store);ExecutorService exec=Executors.newSingleThreadExecutor();
  try{s.start(0);check(s.pairingCode().matches("[0-9]{6}"),"six digit code");
   check(req(s,"GET","/api/state",s.pairingCode()).startsWith("HTTP/1.1 401"),"short code cannot access state without validation");
   check(LocalServerTest.request(s.port(),"POST","/api/pair",auth(s.pairingCode())+"Origin: https://evil.example\r\n","").startsWith("HTTP/1.1 403"),"pairing origin protection");
   String paired=req(s,"POST","/api/pair",s.pairingCode());check(paired.startsWith("HTTP/1.1 200"),"pair accepted");String credential=paired.split("\\\"credential\\\":\\\"")[1].split("\\\"")[0];check(credential.length()==48 && saved.contains(credential),"strong remembered credential persisted");
   check(req(s,"GET","/api/state",credential).startsWith("HTTP/1.1 200"),"credential accepted");
   check(req(s,"POST","/api/pair",s.token()).startsWith("HTTP/1.1 200"),"QR secret pairs");
   s.publish("{\"items\":[],\"latestScan\":null}");final LocalServer live=s;
   Future<String> event=exec.submit(()->req(live,"GET","/api/events?after=1",credential));Thread.sleep(150);check(!event.isDone(),"long poll waits for change");long began=System.nanoTime();s.publish("{\"items\":[],\"latestScan\":{\"id\":\"scan2\"}}");String result=event.get(2,TimeUnit.SECONDS);check(result.contains("scan2") && result.contains("\"revision\":2"),"scan event delivered");check((System.nanoTime()-began)/1000000<1000,"push wakes immediately");
   for(int i=0;i<11;i++)req(s,"POST","/api/pair","invalid");check(req(s,"POST","/api/pair",s.pairingCode()).startsWith("HTTP/1.1 401"),"pairing throttled");
   s.stop();s=new LocalServer(new byte[0],handler,store);s.start(0);check(req(s,"GET","/api/state",credential).startsWith("HTTP/1.1 200"),"trust survives new server instance");s.forgetDevices();check(saved.isEmpty(),"persistent trust revoked");check(req(s,"GET","/api/state",credential).startsWith("HTTP/1.1 401"),"old browser refused");System.out.println("PAIR + LIVE OK: six digits, QR secret, origin checks, rate limit, durable trust, revocation, sub-second change notification");
  }finally{s.stop();exec.shutdownNow();}
 }
}
