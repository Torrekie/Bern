#!/usr/bin/env python3
from pathlib import Path
import datetime,hashlib,json,os,subprocess
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (D/'HeroCGDirectProbe').exists() and not (D/'modules').exists()
p=json.loads((D/'source-provenance.json').read_text())
for n,v in p['source_files'].items():assert sha(D/n)==v['sha256'],n
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer')
def call(argv):
 r=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 return dict(argv=argv,exit_code=r.returncode,output=r.stdout)
context={n:call(a) for n,a in {'os':['sw_vers'],'arch':['uname','-m'],'swift':['xcrun','swiftc','--version'],'sdk':['xcrun','--sdk','macosx','--show-sdk-version'],'sdk_path':['xcrun','--sdk','macosx','--show-sdk-path']}.items()}
assert all(x['exit_code']==0 for x in context.values())
assert '13.' in context['os']['output'] and '5.9.2' in context['swift']['output'] and context['sdk']['output'].strip()=='14.2'
args=['xcrun','swiftc','-O','-parse-as-library','-swift-version','5','-j','2','-target','arm64-apple-macos13.0','-module-cache-path',str(D/'modules')]+[str(D/n) for n in ['Dependencies.swift','ProductImage.swift','ProductStyle.swift','ProductHero.swift']]+sum((['-framework',n] for n in ['AppKit','SwiftUI','MetalKit','CoreImage','ColorSync','ImageIO','CryptoKit']),[])+['-o',str(D/'HeroCGDirectProbe')]
r={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'DEVELOPER_DIR':env['DEVELOPER_DIR'],'environment':context,'argv':args,'source_provenance_sha256':sha(D/'source-provenance.json')}
with (D/'build.log').open('w') as f:r['exit_code']=subprocess.run(args,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();r['build_log_sha256']=sha(D/'build.log')
if r['exit_code']==0:
 r['binary_sha256']=sha(D/'HeroCGDirectProbe')
 r['binary_bytes']=(D/'HeroCGDirectProbe').stat().st_size
 r['checks']={n:call(a) for n,a in {'file':['file',str(D/'HeroCGDirectProbe')],'mach_build':['xcrun','vtool','-show-build',str(D/'HeroCGDirectProbe')],'codesign_verify':['codesign','--verify','--strict',str(D/'HeroCGDirectProbe')],'codesign_details':['codesign','-dvvv',str(D/'HeroCGDirectProbe')]}.items()}
(D/'build-fingerprint.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:r[k] for k in ['exit_code','binary_sha256','binary_bytes'] if k in r}))
if r['exit_code']==0:assert all(x['exit_code']==0 for x in r['checks'].values())
raise SystemExit(r['exit_code'])
