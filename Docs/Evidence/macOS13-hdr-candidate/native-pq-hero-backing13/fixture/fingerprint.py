#!/usr/bin/env python3
from pathlib import Path
import datetime,hashlib,json,subprocess
D=Path(__file__).resolve().parent
p=json.loads((D/'source-provenance.json').read_text())
def call(args):
    r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    return {'argv':args,'exit_code':r.returncode,'output':r.stdout}
names=list(p['generated_files'])+['source-provenance.json','SHA256SUMS','build-environment.txt','build.log','HeroFloatCaptureProbe']
binary=str(D/'HeroFloatCaptureProbe')
r={'built_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in names},
   'target':'arm64-apple-macos13.0','language_mode':'5','optimization':'O','jobs':2,
   'swift':call(['xcrun','swiftc','--version']),'sdk':call(['xcrun','--show-sdk-version']),
   'file':call(['file',binary]),'mach_build':call(['xcrun','vtool','-show-build',binary]),
   'codesign_verify':call(['codesign','--verify','--strict',binary]),
   'codesign':call(['codesign','-dvvv',binary]),
   'source_policy':'Isolated v2 metadata fixture plus opt-in original CGImage retention/post-teardown provider export; exact localSDK14 compatibility guards.',
   'warning_policy':'Preserve actual compiler log; no warning suppression or warnings-as-errors claim.'}
assert r['codesign_verify']['exit_code']==0
(D/'build-fingerprint.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({'binary_sha256':r['hashes']['HeroFloatCaptureProbe'],'strict_signature':True}))
