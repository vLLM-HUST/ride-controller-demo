"""CPU Controller lifecycle acceptance against an existing RIDE/Ray deployment."""
import argparse,subprocess,time,json
from urllib.request import urlopen
p=argparse.ArgumentParser();p.add_argument('--endpoint',required=True);p.add_argument('--address',default='http://127.0.0.1:19100');p.add_argument('--output',default='demo-acceptance.json');a=p.parse_args()
subprocess.run(['ride','start','controller','demo','--name','demo-main','--endpoint',a.endpoint,'--port','9012','--num-cpus','0.1','--num-gpus','0','--address',a.address],check=True)
def read():return json.load(urlopen(a.address.rstrip('/')+'/api/v1/controllers/demo-main'))
for _ in range(60):
 r=read()
 if r['ready']:break
 time.sleep(1)
assert r['ready'],r
first=r['job_id'];subprocess.run(['ride','start','controller','demo-main','--address',a.address],check=True);assert read()['job_id']==first
subprocess.run(['ride','logs','controller','demo-main','--address',a.address],check=True)
subprocess.run(['ride','stop','controller','demo-main','--address',a.address],check=True)
for _ in range(60):
 if read()['job_status']=='STOPPED':break
 time.sleep(1)
assert read()['job_status']=='STOPPED'
subprocess.run(['ride','start','controller','demo-main','--address',a.address],check=True)
for _ in range(60):
 r=read()
 if r['ready']:break
 time.sleep(1)
assert r['ready'] and r['job_id']!=first,r
report={'status':'PASS','scope':'CPU real Ray demo deployment, identity, idempotence, logs, stop and restore','record':r}
from pathlib import Path
Path(a.output).write_text(json.dumps(report,indent=2))
print(json.dumps(report))
