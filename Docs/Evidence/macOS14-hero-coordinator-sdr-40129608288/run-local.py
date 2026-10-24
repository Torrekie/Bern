"""One fresh native process per mode; require default controls before candidate."""
import datetime,hashlib,json,subprocess,sys
from pathlib import Path

assert len(sys.argv)==2 and sys.argv[1] in ('default','baked-pair')
mode=sys.argv[1]; root=Path(__file__).resolve().parent
workspace=root.parent.parent; repo=workspace/'outputs/Bern'
probe=root/'probe'; binary=probe/'HeroCoordinatorSDRProbe'
verification=json.loads((root/'package-verification-local.json').read_text())
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(binary)==verification['binary_sha256']
ready=root/'default13-ready.json'
if mode=='baked-pair':
    default=json.loads(ready.read_text());assert default['ready_for_candidate'] is True
    assert default['binary_sha256']==digest(binary)
    for name,sha in default['input_hashes'].items(): assert digest(root/name)==sha,name
runtime=root/('runtime13-'+mode); assert not runtime.exists()
runtime.mkdir(); steps=[]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def step(name,argv):
    began=now(); command=list(map(str,argv))
    run=subprocess.run(command,cwd=workspace,capture_output=True,text=True)
    (runtime/(name+'.stdout.txt')).write_text(run.stdout)
    (runtime/(name+'.stderr.txt')).write_text(run.stderr)
    result={'step':name,'argv':command,'started_utc':began,'finished_utc':now(),'exit_code':run.returncode}
    steps.append(result)
    (runtime/'root-steps.json').write_text(json.dumps(steps,indent=2,sort_keys=True)+'\n')
    assert run.returncode==0,(name,run.returncode,run.stderr[-1200:])
    print(json.dumps(result))
step('wrapper',[sys.executable,'-B',probe/'run-one.py',binary,probe/'assets/source-named-pq.png',runtime,'13',mode])
step('native-base',[sys.executable,'-B',root/'tools/run-native-base.py',runtime,'13',binary])
step('native-sdr',[sys.executable,'-B',root/'tools/flight-sdr-gate.py',runtime/'report.json',runtime/'run-receipt.json',mode,'13'])
old=repo/'Docs/Evidence/macOS14-hero-coordinator-app-40110795231'
control=old/'same-binary-13-14/runtime13' if mode=='default' else root/'runtime13-default'
output=runtime/'endpoint-controls.json'
step('endpoint-controls',[sys.executable,'-B',root/'check-endpoint-controls.py',old/'pixel-analysis/analyze.py',control,runtime,output])
assert json.loads(output.read_text())['exact_endpoint_controls'] is True
assert digest(binary)==verification['binary_sha256']
if mode=='default':
    assert not ready.exists()
    names=['runtime13-default/'+name for name in ('report.json','run-receipt.json','root-steps.json','endpoint-controls.json')]
    result={'ready_for_candidate':True,'recorded_utc':now(),'binary_sha256':digest(binary),
            'default_gates_and_endpoint_controls_all_exit_zero':True,
            'input_hashes':{name:digest(root/name) for name in names},
            'scope':'Default13 acquisition, unchanged native/execution and appended SDR gates, exact old13 corresponding endpoint controls completed before candidate launch.'}
    with ready.open('x') as f:f.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
