"""Observable non-streaming request concurrency limiter."""
import argparse,json,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
p=argparse.ArgumentParser();p.add_argument('--listen',default='0.0.0.0:9012');p.add_argument('--backend');p.add_argument('--max-concurrency',type=int,default=1);a=p.parse_args()
if a.max_concurrency<1:p.error('max-concurrency must be positive')
semaphore=threading.BoundedSemaphore(a.max_concurrency);lock=threading.Lock()
state={'active':0,'waiting':0,'completed':0,'failed':0,'peak_active':0,'queued_total':0}
class Handler(BaseHTTPRequestHandler):
 def reply(self,body,status=200):
  self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def do_GET(self):
  with lock:snapshot=dict(state)
  routes={'/health':{'status':'ok'},'/identity':{'controller_type':'demo','version':'0.1.0','backend':a.backend,'max_concurrency':a.max_concurrency},'/status':snapshot}
  if self.path not in routes:self.send_error(404);return
  self.reply(json.dumps(routes[self.path]).encode())
 def do_POST(self):
  if self.path!='/v1/chat/completions' or not a.backend:self.send_error(404);return
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<=1048576:raise ValueError('Invalid body size')
   payload=self.rfile.read(length);data=json.loads(payload)
   if data.get('stream'):raise ValueError('Streaming is not supported by this demo')
  except (ValueError,TypeError):self.reply(b'{"error":"invalid or unsupported request"}',400);return
  acquired=semaphore.acquire(blocking=False)
  if not acquired:
   with lock:state['waiting']+=1;state['queued_total']+=1
   semaphore.acquire()
   with lock:state['waiting']-=1
  with lock:state['active']+=1;state['peak_active']=max(state['peak_active'],state['active'])
  try:
   with urlopen(Request(a.backend.rstrip('/')+self.path,data=payload,headers={'Content-Type':'application/json'}),timeout=300) as response:body=response.read()
   self.reply(body)
   with lock:state['completed']+=1
  except HTTPError as error:
   self.reply(error.read(),error.code)
   with lock:state['failed']+=1
  except Exception as error:
   with lock:state['failed']+=1
   try:self.reply(json.dumps({'error':type(error).__name__}).encode(),502)
   except OSError:pass
  finally:
   with lock:state['active']-=1
   semaphore.release()
host,port=a.listen.rsplit(':',1)
print(json.dumps({'event':'starting','controller_type':'demo','listen':a.listen,'backend':a.backend,'max_concurrency':a.max_concurrency}),flush=True)
ThreadingHTTPServer((host,int(port)),Handler).serve_forever()
