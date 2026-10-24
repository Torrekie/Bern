#!/usr/bin/env python3
"""One original-snapshot static process, own fresh output, no activation or retries."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
assert len(sys.argv)==2 and sys.argv[1] in ['control','image-view']
mode=sys.argv[1];D=Path(__file__).resolve().parent;binary=D/'HeroNativeDisplayProbe';out=D/('runtime13-'+mode)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((D/'build-fingerprint.json').read_text())
assert build['exit_code']==0 and sha(binary)==build['binary_sha256']
assert 'minos 13.0' in build['checks']['mach_build']['output'] and 'sdk 14.2' in build['checks']['mach_build']['output']
assert build['checks']['codesign_verify']['exit_code']==0
assert not out.exists();out.mkdir()
args=[str(binary),str(D/'assets/source-named-pq.png'),str(D/'assets/source-ffb-icc.png'),str(out)]
settings=dict(BERN_HERO_NATIVE_DISPLAY=mode,BERN_HERO_FLOAT_CAPTURE='off',BERN_HERO_LAYER_OBSERVE='off',BERN_HERO_STATIC_ROUTE='overlay',BERN_HERO_EXPECT_OS='13')
r=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),binary_sha256=sha(binary),command=args,mode=mode,environment=settings,timeout_seconds=15,fresh_output_directory=True)
began=time.monotonic()
with (out/'runtime.log').open('w') as log:
 p=subprocess.Popen(args,env=dict(os.environ,**settings),stdout=log,stderr=subprocess.STDOUT);r['own_pid']=p.pid
 try:r['exit_code']=p.wait(timeout=15)
 except subprocess.TimeoutExpired:p.kill();r['exit_code']=p.wait();r['wrapper_timeout']=True
r.update(elapsed_seconds=time.monotonic()-began,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
r['binary_sha256_after']=sha(binary)
r['output_files']={x.name:{'sha256':sha(x),'bytes':x.stat().st_size} for x in out.iterdir() if x.is_file()}
(out/'run-receipt.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:r[k] for k in ['mode','own_pid','exit_code','elapsed_seconds']}))
assert r['exit_code']==0 and r['binary_sha256_after']==build['binary_sha256']
report=json.loads((out/'report.json').read_text());assert report['success'] and report['native_display']['success']
assert {x.name for x in out.glob('progress-*.png')}=={'progress-0.png','progress-1.png'}
