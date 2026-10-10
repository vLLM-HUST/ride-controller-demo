"""Minimal observable Controller; no model forwarding or scheduling claims."""
import argparse,json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
p=argparse.ArgumentParser();p.add_argument('--listen',default='0.0.0.0:9012');a=p.parse_args()
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  routes={'/health':{'status':'ok'},'/identity':{'controller_type':'demo','version':'0.1.0'},'/status':{'mode':'demonstration','decisions':0}}
  if self.path not in routes:self.send_error(404);return
  body=json.dumps(routes[self.path]).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
host,port=a.listen.rsplit(':',1)
print(json.dumps({'event':'starting','controller_type':'demo','listen':a.listen}),flush=True)
ThreadingHTTPServer((host,int(port)),Handler).serve_forever()
