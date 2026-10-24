"""One default13 process, unchanged inherited gates, new strict trace and control."""
import datetime,hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent;workspace=root.parent.parent;repo=workspace/'outputs/Bern'
probe=root/'probe';binary=probe/'HeroTimingProbe';runtime=root/'runtime13'
verification=json.loads((root/'package-verification-local.json').read_text())
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(binary)==verification['binary_sha256'] and not runtime.exists()
runtime.mkdir();steps=[]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def step(name,args):
    command=list(map(str,args));began=now()
    r=subprocess.run(command,cwd=workspace,capture_output=True,text=True)
    (runtime/(name+'.stdout.txt')).write_text(r.stdout);(runtime/(name+'.stderr.txt')).write_text(r.stderr)
    steps.append({'name':name,'argv':command,'started_utc':began,'finished_utc':now(),'exit_code':r.returncode})
    (runtime/'root-steps.json').write_text(json.dumps(steps,indent=2,sort_keys=True)+'\n')
    assert r.returncode==0,(name,r.returncode,r.stderr[-1200:]);print(json.dumps(steps[-1]))
py=[sys.executable,'-B']
step('wrapper',py+[probe/'run-one.py',binary,probe/'assets/source-named-pq.png',runtime,'13','default'])
step('inherited-gate',py+[root/'tools/run-inherited-gate.py',runtime,'13',binary])
step('strict-timing',py+[root/'tools/timing-gate.py',runtime/'report.json'])
old=repo/'Docs/Evidence/macOS14-hero-coordinator-sdr-40129608288'
analyzer=repo/'Docs/Evidence/macOS14-hero-coordinator-app-40110795231/pixel-analysis/analyze.py'
step('endpoint-controls',py+[old/'check-endpoint-controls.py',analyzer,old/'runtime13-default',runtime,runtime/'endpoint-controls.json'])
assert json.loads((runtime/'endpoint-controls.json').read_text())['exact_endpoint_controls'] is True
assert digest(binary)==verification['binary_sha256']
ready={'ready_for_observation_analysis':True,'recorded_utc':now(),'binary_sha256':digest(binary),
       'all_steps_exit_zero':True,'default13_corresponding_endpoints_raw_and_icc_exact':True,
       'input_hashes':{name:digest(runtime/name) for name in ('report.json','run-receipt.json','root-steps.json','endpoint-controls.json')}}
(root/'local13-ready.json').write_text(json.dumps(ready,indent=2,sort_keys=True)+'\n')
