"""Real-model concurrency acceptance; existing RIDE, Ray and owned model required."""
import argparse,json,time,subprocess,concurrent.futures
from urllib.request import urlopen,Request
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--address',default='http://127.0.0.1:19100');p.add_argument('--backend',required=True);p.add_argument('--endpoint',required=True);p.add_argument('--model',required=True);p.add_argument('--model-service',required=True);p.add_argument('--output',required=True);a=p.parse_args()
def get(path):return json.load(urlopen(path,timeout=5))
def instance():return get(a.address+'/api/v1/controllers/npu-demo')
def cli(*args):subprocess.run(['ride',*args,'--address',a.address],check=True)
for _ in range(300):
 if get(a.address+'/api/v1/model-services/'+a.model_service)['ready']:break
 time.sleep(2)
else:raise RuntimeError('Real model not Ready')
cli('start','controller','demo','--name','npu-demo','--backend',a.backend,'--endpoint',a.endpoint,'--port','9012','--num-cpus','0.1','--num-gpus','0')
def ready():
 for _ in range(90):
  r=instance()
  if r['ready']:return r
  time.sleep(1)
 raise RuntimeError('Controller not Ready')
first=ready()['job_id']
payload=json.dumps({'model':a.model,'messages':[{'role':'user','content':'Explain why the sky is blue.'}],'max_tokens':64,'temperature':0,'stream':False}).encode()
def request(_):
 with urlopen(Request(a.endpoint+'/v1/chat/completions',data=payload,headers={'Content-Type':'application/json'}),timeout=300) as r:return json.load(r)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:responses=list(pool.map(request,range(4)))
state=get(a.endpoint+'/status')
if not(state['peak_active']==1 and state['queued_total']>=1 and state['completed']==4 and state['failed']==0):raise RuntimeError(str(state))
if not all(r['usage']['completion_tokens']>0 and r['choices'] for r in responses):raise RuntimeError('Invalid responses')
cli('stop','controller','npu-demo')
for _ in range(60):
 if instance()['job_status']=='STOPPED':break
 time.sleep(1)
if instance()['job_status']!='STOPPED':raise RuntimeError('Stop failed')
if not get(a.address+'/api/v1/model-services/'+a.model_service)['ready']:raise RuntimeError('Model stop isolation failed')
cli('start','controller','npu-demo');current=ready()
if current['job_id']==first:raise RuntimeError('Restore did not create a new Job')
restored=request(0)
report={'status':'PASS','scope':'real model request concurrency and lifecycle; no performance claim','state':state,'responses':responses,'restored_response':restored,'controller':current}
Path(a.output).write_text(json.dumps(report,indent=2));print(json.dumps(report))
