#!/usr/bin/env python3
"""One packaged actual-coordinator process; child-only default motion and SDR mode."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
assert len(sys.argv) in (5,6),'binary namedAsset output expectedOS13|14 [default|baked-pair]'
binary,asset,out=map(lambda x:Path(x).resolve(),sys.argv[1:4]);major=int(sys.argv[4]);assert major in [13,14]
assert binary.is_file() and asset.is_file()
mode_argument=sys.argv[5] if len(sys.argv)==6 else None
mode_environment=os.environ.get('BERN_HERO_FLIGHT_SDR')
mode=mode_argument if mode_argument is not None else (mode_environment if mode_environment is not None else 'default')
assert mode in ('default','baked-pair'),'BERN_HERO_FLIGHT_SDR must be default|baked-pair'
assert major!=14 or mode=='default','macOS14 collection is default only'
assert not any((out/name).exists() for name in ('report.json','run-receipt.json','runtime.log','hard-deadline.txt'))
assert not list(out.glob('*.png'))
out.mkdir(parents=True,exist_ok=True)
command=list(map(str,[binary,asset,out]));env=dict(os.environ);motion_was_present='BERN_MOTION' in env;env.pop('BERN_MOTION',None);env['BERN_HERO_EXPECT_OS']=str(major)
env['BERN_HERO_FLIGHT_SDR']=mode
r=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),named_asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),command=command,bern_motion_environment='unset',bern_motion_was_present=motion_was_present,expected_os_major=major,timeout_seconds=15)
r.update(flight_sdr_mode=mode,flight_sdr_mode_source='last_argument' if mode_argument is not None else 'environment' if mode_environment is not None else 'default',bern_hero_flight_sdr_environment=env['BERN_HERO_FLIGHT_SDR'])
began=time.monotonic()
with (out/'runtime.log').open('x') as log:
 p=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT);r['own_pid']=p.pid
 try:r['exit_code']=p.wait(timeout=15)
 except subprocess.TimeoutExpired:p.kill();r['exit_code']=p.wait();r['wrapper_timeout']=True
r['elapsed_seconds']=time.monotonic()-began;r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out/'run-receipt.json').open('x') as receipt:receipt.write(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:r[k] for k in ['own_pid','exit_code','elapsed_seconds']}))
raise SystemExit(0 if r['exit_code']==0 else 1)
