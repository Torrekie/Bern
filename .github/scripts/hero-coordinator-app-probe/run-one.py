#!/usr/bin/env python3
"""One packaged actual-coordinator process; default motion in child env only."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
assert len(sys.argv)==5,'binary namedAsset output expectedOS13|14'
binary,asset,out=map(lambda x:Path(x).resolve(),sys.argv[1:4]);major=int(sys.argv[4]);assert major in [13,14]
assert binary.is_file() and asset.is_file()
assert not (out/'report.json').exists() and not (out/'run-receipt.json').exists();out.mkdir(parents=True,exist_ok=True)
command=list(map(str,[binary,asset,out]));env=dict(os.environ);motion_was_present='BERN_MOTION' in env;env.pop('BERN_MOTION',None);env['BERN_HERO_EXPECT_OS']=str(major)
r=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),named_asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),command=command,bern_motion_environment='unset',bern_motion_was_present=motion_was_present,expected_os_major=major,timeout_seconds=15)
began=time.monotonic()
with (out/'runtime.log').open('w') as log:
 p=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT);r['own_pid']=p.pid
 try:r['exit_code']=p.wait(timeout=15)
 except subprocess.TimeoutExpired:p.kill();r['exit_code']=p.wait();r['wrapper_timeout']=True
r['elapsed_seconds']=time.monotonic()-began;r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(out/'run-receipt.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:r[k] for k in ['own_pid','exit_code','elapsed_seconds']}))
raise SystemExit(0 if r['exit_code']==0 else 1)
