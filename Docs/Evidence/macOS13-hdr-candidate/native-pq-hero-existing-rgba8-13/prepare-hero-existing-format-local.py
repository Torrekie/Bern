from pathlib import Path
import shutil,hashlib,json,subprocess
R=Path.cwd();B=R/'work/native-pq-hero-static-route13';A=R/'work/hero-existing-format-preparation';D=R/'work/native-pq-hero-existing-rgba8-13';D.mkdir(exist_ok=False)
p=json.loads((A/'provenance.json').read_text());assert hashlib.sha256((B/'Driver.swift.inc').read_bytes()).hexdigest()==p['base_driver_sha256']
for n in ['Dependencies.swift','ProductImage.swift','ProductImage.exact.swift','ProductImage.v2.base.swift','ProductStyle.swift','ProductStyle.exact.swift','ProductHero.clock-adapted.swift','ProductHero.exact.swift','ProductHero.v2.base.swift','FloatCapture.swift.inc','sdk14-unreachable-gainmap.patch','local-sdk14-clock.patch','local-image-imports-and-sdk14.patch','verify_sources.py']:
 shutil.copy2(B/n,D/n)
shutil.copytree(B/'assets',D/'assets')
for n in ['FormatRequest.swift.inc','format-request-driver.patch']:
 shutil.copy2(A/n,D/n)
shutil.copy2(B/'Driver.swift.inc',D/'Driver.before-format.swift.inc');shutil.copy2(B/'Driver.swift.inc',D/'Driver.swift.inc')
subprocess.run(['patch','--batch','--forward','--directory',str(D),'-p1','--input',str(A/'format-request-driver.patch')],check=True,stdout=subprocess.PIPE)
derived=(D/'Driver.swift.inc').read_text();assert hashlib.sha256(derived.encode()).hexdigest()==p['derived_driver_without_helper_sha256']
driver=(D/'FormatRequest.swift.inc').read_text()+derived
assert hashlib.sha256(driver.encode()).hexdigest()==p['composed_helper_and_driver_sha256']
(D/'Driver.swift.inc').write_text(driver)
(D/'ProductHero.swift').write_text((D/'ProductHero.clock-adapted.swift').read_text()+'\n'+(D/'FloatCapture.swift.inc').read_text()+'\n'+driver)
shutil.copy2(A/'provenance.json',D/'format-source-provenance.json')
# Use a fresh single owned cache; never write into the preceding frozen archives.
shutil.copy2(R/'work/native-pq-hero-backing-observer/build.sh',D/'build.sh')
wrapper=(R/'work/hero-route-ci-preparation/run-route-one.py').read_text()
wrapper=wrapper.replace('One exact packaged static-route process; backing and float capture off.','One fixed-overlay control or single existing-layer RGBA8 request process.')
wrapper=wrapper.replace('root|overlay 13|14','control|rgba8 13').replace("mode in ['root','overlay'] and major in [13,14]","mode in ['control','rgba8'] and major==13")
wrapper=wrapper.replace('BERN_HERO_STATIC_ROUTE=mode','BERN_HERO_STATIC_ROUTE="overlay",BERN_HERO_FORMAT_REQUEST=mode')
wrapper=wrapper.replace('static_route_environment=mode','static_route_environment="overlay",format_request_environment=mode')
(D/'run-format-one.py').write_text(wrapper)
(D/'fingerprint.py').write_text('''from pathlib import Path
import datetime,hashlib,json,subprocess
D=Path(__file__).resolve().parent;p=json.loads((D/'source-provenance.json').read_text())
def call(args):
 r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 return {'argv':args,'exit_code':r.returncode,'output':r.stdout}
names=list(p['generated_files'])+['source-provenance.json','SHA256SUMS','build-environment.txt','build.log','HeroFloatCaptureProbe'];binary=str(D/'HeroFloatCaptureProbe')
r={'built_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in names},'target':'arm64-apple-macos13.0','language_mode':'5','optimization':'O','jobs':2,'swift':call(['xcrun','swiftc','--version']),'sdk':call(['xcrun','--show-sdk-version']),'file':call(['file',binary]),'mach_build':call(['xcrun','vtool','-show-build',binary]),'codesign_verify':call(['codesign','--verify','--strict',binary]),'codesign':call(['codesign','-dvvv',binary]),'source_policy':'Fixed existing-overlay static actual Flight; control no added getters, rgba8 one existing flight layer contentsFormat request with weak identity/persistence observations. Exact archived SDK14.2 unused-clock/gainmap guards.','warning_policy':'Actual compiler log retained; no warning suppression.'}
assert r['codesign_verify']['exit_code']==0
(D/'build-fingerprint.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\\n')
print(json.dumps({'binary_sha256':r['hashes']['HeroFloatCaptureProbe'],'strict_signature':True}))
''')
s={'kind':'existing_flight_single_rgba8_request_local13','base_fixture':'Docs/Evidence/macOS13-hdr-candidate/native-pq-hero-static-route13/fixture','source_change':p,'fixed_static_route':'overlay','format_mode_default':'control','backing_and_float_required':'off','precondition_remote_route':'CI40097558084 samebinary13/14 root and overlay controls all12 raw+ICC normalized exact on each host; does not accept full flight.','generated_files':{}}
for f in sorted(D.rglob('*')):
 if f.is_file():
  b=f.read_bytes();s['generated_files'][str(f.relative_to(D))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
(D/'source-provenance.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
(D/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(D))+'\n' for f in sorted(D.rglob('*')) if f.is_file()))
print('Prepared fixed-overlay control/one existing RGBA8 request; own cache only')
