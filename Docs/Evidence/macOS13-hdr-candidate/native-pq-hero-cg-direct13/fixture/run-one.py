#!/usr/bin/env python3
"""One exact packaged probe process; no retries or preference/permission changes."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
assert len(sys.argv)==7,'binary named custom output default|direct 13'
binary,named,custom,out=map(lambda x:Path(x).resolve(),sys.argv[1:5]);mode=sys.argv[5];major=int(sys.argv[6]);assert mode in ['default','direct'] and major == 13
assert binary.is_file() and named.is_file() and custom.is_file()
assert not (out/'report.json').exists() and not (out/'run-receipt.json').exists();out.mkdir(parents=True,exist_ok=True)
command=list(map(str,[binary,named,custom,out]));env=dict(os.environ,BERN_HERO_FLOAT_CAPTURE='on',BERN_HERO_EXPECT_OS=str(major),BERN_HERO_LAYER_OBSERVE='off',BERN_HERO_CG_DIRECT=mode)
r=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),command=command,mode=mode,float_mode='on',backing_mode='off',expected_os_major=major,timeout_seconds=15)
began=time.monotonic()
with (out/'runtime.log').open('w') as log:
 p=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT);r['own_pid']=p.pid
 try:r['exit_code']=p.wait(timeout=15)
 except subprocess.TimeoutExpired:p.kill();r['exit_code']=p.wait();r['wrapper_timeout']=True
r['elapsed_seconds']=time.monotonic()-began;r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(out/'run-receipt.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:r[k] for k in ['mode','own_pid','exit_code','elapsed_seconds']}))
raise SystemExit(0 if r['exit_code']==0 else 1)
