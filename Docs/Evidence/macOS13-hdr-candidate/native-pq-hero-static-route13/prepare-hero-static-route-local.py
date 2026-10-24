from pathlib import Path
import shutil,hashlib,json,subprocess
R=Path.cwd();B=R/'work/native-pq-hero-backing-observer';A=R/'work/hero-actual-overlay-route-preparation';D=R/'work/native-pq-hero-static-route13';D.mkdir(exist_ok=False)
p=json.loads((A/'provenance.json').read_text());assert hashlib.sha256((B/'Driver.swift.inc').read_bytes()).hexdigest()==p['base_driver_sha256']
for name in ['Dependencies.swift','ProductImage.swift','ProductImage.exact.swift','ProductImage.v2.base.swift','ProductStyle.swift','ProductStyle.exact.swift','ProductHero.clock-adapted.swift','ProductHero.exact.swift','ProductHero.v2.base.swift','FloatCapture.swift.inc','sdk14-unreachable-gainmap.patch','local-sdk14-clock.patch','local-image-imports-and-sdk14.patch','fingerprint.py','verify_sources.py']:
 shutil.copy2(B/name,D/name)
shutil.copytree(B/'assets',D/'assets')
for name in ['StaticRoute.swift.inc','static-route-driver.patch']:
 shutil.copy2(A/name,D/name)
shutil.copy2(B/'Driver.swift.inc',D/'Driver.before-static-route.swift.inc');shutil.copy2(B/'Driver.swift.inc',D/'Driver.swift.inc')
subprocess.run(['patch','--batch','--forward','--directory',str(D),'-p1','--input',str(A/'static-route-driver.patch')],check=True,stdout=subprocess.PIPE)
derived=(D/'Driver.swift.inc').read_text();assert hashlib.sha256(derived.encode()).hexdigest()==p['derived_driver_without_helper_sha256']
driver=(D/'StaticRoute.swift.inc').read_text()+derived
assert hashlib.sha256(driver.encode()).hexdigest()==p['combined_helper_and_derived_driver_sha256']
(D/'Driver.swift.inc').write_text(driver)
(D/'ProductHero.swift').write_text((D/'ProductHero.clock-adapted.swift').read_text()+'\n'+(D/'FloatCapture.swift.inc').read_text()+'\n'+driver)
shutil.copy2(A/'provenance.json',D/'static-route-source-provenance.json')
build=(B/'build.sh').read_text().replace('"$fixture_dir/modules"','"$fixture_dir/../native-pq-hero-backing-observer/modules"')
(D/'build.sh').write_text(build)
wrapper=(B/'run-backing-one.py').read_text().replace("'binary named custom output off|on 13|14'","'binary named custom output root|overlay 13|14'").replace("mode in ['off','on']","mode in ['root','overlay']").replace('BERN_HERO_LAYER_OBSERVE=mode','BERN_HERO_LAYER_OBSERVE="off",BERN_HERO_STATIC_ROUTE=mode').replace('layer_observe_environment=mode','layer_observe_environment="off",static_route_environment=mode')
(D/'run-route-one.py').write_text(wrapper)
s={'kind':'actual_existing_overlay_static_route_local13','base_fixture':'post_png_backing_observer8b96b8c','route_source':p,'mode_default':'root','required_backing_and_float':'off','module_cache_scope':'Reuse the same active owned local SDK14.2 module cache; no second module cache.','generated_files':{}}
for f in sorted(D.rglob('*')):
 if f.is_file():
  b=f.read_bytes();s['generated_files'][str(f.relative_to(D))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
(D/'source-provenance.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
(D/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(D))+'\n' for f in sorted(D.rglob('*')) if f.is_file()))
print('Prepared single root/overlay route switch; no layer/pixel changes')
