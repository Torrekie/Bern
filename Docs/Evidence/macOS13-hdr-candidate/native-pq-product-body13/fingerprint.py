from pathlib import Path
import hashlib,json,subprocess,datetime
D=Path(__file__).resolve().parent
names=['Dependencies.swift','ProductImage.exact.swift','ProductImage.swift','main.swift','prepare.py','sdk14-unreachable-gainmap.patch','build.sh','fingerprint.py','ProductBodyProbe','build.log','source-provenance.json']
hashes={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in names}
def call(args):
    p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    return {'exit_code':p.returncode,'output':p.stdout}
report={'built_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'target':'arm64-apple-macos13.0','swift_language_mode':'5','optimization':'O','warnings_as_errors':False,'warning_policy':'Exact product exhaustive-switch warning retained; do not rewrite the product slice to silence it.','hashes':hashes,'swift':call(['xcrun','swiftc','--version']),'sdk':call(['xcrun','--show-sdk-version']),'file':call(['file',str(D/'ProductBodyProbe')]),'mach_build':call(['xcrun','vtool','-show-build',str(D/'ProductBodyProbe')]),'codesign':call(['codesign','-dvvv',str(D/'ProductBodyProbe')]),'product_commit':'9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0'}
(D/'build-fingerprint.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(str(D/'ProductBodyProbe'))
