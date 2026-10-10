"""RIDE adapter: configuration, process command and type-specific readiness."""
import json,shlex
from urllib.request import urlopen
class Adapter:
 @staticmethod
 def command(spec):
  if not spec.get('endpoint'):raise ValueError('Demo requires a reachable endpoint')
  return shlex.join(['python','-m','ride_controller_demo','--listen',spec.get('listen','0.0.0.0:9012')])
 @staticmethod
 def probe(spec):
  values={}
  for route in ('health','identity','status'):
   with urlopen(spec['endpoint'].rstrip('/')+'/'+route,timeout=2) as response:values[route]=json.load(response)
  return dict(values,controller_ready=values['health'].get('status')=='ok' and values['identity'].get('controller_type')=='demo')
