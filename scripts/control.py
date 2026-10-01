"""Run inside the container: python scripts/control.py status|preview|sync."""
import os,sys,json,httpx
command=sys.argv[1] if len(sys.argv)>1 else 'status'
if command not in {'status','preview','sync'}:raise SystemExit('Use status, preview, or sync')
headers={'Authorization':'Bearer '+os.environ['WATCHKEEPER_API_TOKEN']}
r=httpx.request('GET' if command=='status' else 'POST','http://127.0.0.1:8765/'+command,headers=headers,timeout=300)
r.raise_for_status();print(json.dumps(r.json(),indent=2))
