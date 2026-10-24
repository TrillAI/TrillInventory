import com.harrys.scan.LocalServer;
import java.net.*;import java.io.*;import java.nio.charset.StandardCharsets;import java.util.concurrent.atomic.AtomicInteger;
public class LocalServerTest {
 static void check(boolean value,String msg){if(!value)throw new AssertionError(msg);}
 static String request(int port,String method,String path,String headers,String body)throws Exception{
  Socket socket=new Socket("127.0.0.1",port);socket.setSoTimeout(10000);
  String text=method+" "+path+" HTTP/1.1\r\nHost: 127.0.0.1:"+port+"\r\n"+headers+"Connection: close\r\n\r\n"+body;
  socket.getOutputStream().write(text.getBytes(StandardCharsets.UTF_8));ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] b=new byte[4096];int n;while((n=socket.getInputStream().read(b))!=-1)bytes.write(b,0,n);socket.close();return bytes.toString("UTF-8");
 }
 public static void main(String[] args)throws Exception{
  final AtomicInteger edits=new AtomicInteger();
  LocalServer server=new LocalServer("<h1>Trill</h1>".getBytes(StandardCharsets.UTF_8),(action,body)->{
   if(action.equals("edit")){edits.incrementAndGet();check(body.equals("{\"qty\":3}"),"body parsing");}
   return new LocalServer.Reply(200,"{\"items\":[]}");
  });
  try{
   server.start(0);int port=server.port();String token=server.token(),auth="Authorization: Bearer "+token+"\r\n";
   check(token.length()==48,"strong random code");
   check(request(port,"GET","/","","").startsWith("HTTP/1.1 200"),"dashboard accessible");
   check(request(port,"GET","/api/state","","").startsWith("HTTP/1.1 401"),"data requires auth");
   check(request(port,"GET","/api/state","Authorization: Bearer wrong\r\n","").startsWith("HTTP/1.1 401"),"wrong code rejected");
   check(request(port,"GET","/api/state",auth,"").contains("{\"items\":[]}"),"state authenticated");
   check(request(port,"GET","/api/state",auth+"Origin: https://evil.example\r\n","").startsWith("HTTP/1.1 403"),"cross-origin denied");
   check(request(port,"GET","/../../etc/passwd",auth,"").startsWith("HTTP/1.1 404"),"no filesystem routes");
   String body="{\"qty\":3}";
   check(request(port,"POST","/api/edit",auth+"Content-Type: application/json\r\nContent-Length: "+body.length()+"\r\n",body).startsWith("HTTP/1.1 200"),"authorized edit");
   check(edits.get()==1,"one edit");
   check(request(port,"POST","/api/edit",auth+"Content-Type: text/plain\r\nContent-Length: 2\r\n","{}").startsWith("HTTP/1.1 400"),"bad content type");
   check(request(port,"POST","/api/edit",auth+"Content-Type: application/json\r\nContent-Length: 9000\r\n","").startsWith("HTTP/1.1 413"),"oversize denied");
   check(request(port,"GET","/api/state",auth+"Host: evil.example\r\n","").startsWith("HTTP/1.1 503"),"duplicate host denied");
   server.stop();server.start(0);check(!token.equals(server.token()),"restart rotates token");
   check(request(server.port(),"GET","/api/state",auth,"").startsWith("HTTP/1.1 401"),"old token revoked");
   System.out.println("LAN HTTP OK: real sockets, auth, origin, route restrictions, JSON, limits, stop/restart token revocation");
  }finally{server.stop();}
 }
}
