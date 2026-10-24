from pathlib import Path
import hashlib,json,shutil
R=Path.cwd();B=R/'outputs/Bern/.github/scripts/hero-float-probe';D=R/'outputs/Bern/.github/scripts/hero-route-probe';L=R/'work/native-pq-hero-static-route13'
assert not D.exists();p=json.loads((B/'source-provenance.json').read_text())
for n,m in p['files'].items():
 raw=(B/n).read_bytes();assert len(raw)==m['bytes'] and hashlib.sha256(raw).hexdigest()==m['sha256'],n
shutil.copytree(B,D)
shutil.copy2(B/'source-provenance.json',D/'source-provenance.before-static-route.json')
shutil.copy2(B/'Driver.swift.inc',D/'Driver.before-static-route.swift.inc')
for name in ['StaticRoute.swift.inc','static-route-driver.patch','Driver.swift.inc']:
 shutil.copy2(L/name,D/name)
assert hashlib.sha256((D/'Driver.swift.inc').read_bytes()).hexdigest()=='a6b483d48f468f3479d6ac36ba7b95464c037d3c792f7efe134edfc1ba9109ca'
(D/'README.md').write_text('''# Actual existing-overlay static-route comparison\n\nThis standalone diagnostic preserves the preceding hero-float/backing harness\nunchanged. It uses their original newSDK ProductImage/Hero base, actual cache,\nBernImage, Anchor.snapshot, NSImage and Flight.draw. It changes only the parent\nof the two manual same-image static p0/p1 flights: FixtureRoot(default) versus\nthe actual manager overlay already prepared by fixtureSnapshot. It never calls\nenter/leave/finish, changes manager maps/timer/visibility/bindings, creates a\nlayer, requests a contentsFormat, converts/relabels images or captures raw data.\n\nProcess-cached BERN_HERO_STATIC_ROUTE=root|overlay defaults root. This fixture\nrequires both BERN_HERO_LAYER_OBSERVE and BERN_HERO_FLOAT_CAPTURE selected off\nbefore a window is created. That requirement is why it has its own directory;\nthe original float/backing workflows and their opt-in modes remain available.\n\nOverlay mounting uses overlay.convert(originalDesiredRootRect,from:root), not\nthe source anchor rect or manual titlebar/y adjustments. Both retained flights\nare checked after mount, before every original capture sample and after PNGs:\nselected parent/same window/320x180 bounds, public roundtrip <=1e-6pt and their\nentire subtrees contain no MTKView. Their original public ROI calculation is\nunchanged. The root-only descendant check is still kept for original content.\nAfter original orderOut, only fixture-owned overlay flights are removed before\noriginal contentnil/close; unregistered views never call manager.finish.\n\nThe normal/cache/front/non-key/inactive/noManagerFlight/noTimer/stable5 and\n7.9second window /15second process bounds remain. CI builds arm64/min13 once\nwith SDK26.2 and executes fresh root/overlay14 processes. CI success means\nacquisition/schema only; separate rawRGB+ICC-normalized controls against old\nroot and between routes are required on both14 and13 using the same original\nsigned binary. No fixed overlay offset or expected pixel equality is asserted\nduring acquisition. Local SDK14.2 controls already found all12 ROIs exact for\nold→root and root→overlay; that observation does not accept another host.\n\nStatic same-opaque-image endpoints do not validate live coordinator motion,\ninterpolation, retargeting, hiding/restoration, physical HDR or whole-app parity.\nThe before-static-route source/provenance and patch preserve the exact delta.\n''')
p['kind']='actual_existing_overlay_static_route_fixture'
p['runtime_static_route_default']='root'
p['required_backing_and_float_selected']='off'
p['source_adaptations'].append('same_manual_Flight_parent_root_or_existing_actual_manager_overlay_public_coordinate_roundtrip_and_explicit_subtree_checks')
p['route_local_controls']={'binary_sha256':'8fb1b7f57b60de0948866bb950be07696b15196d9f89e2fda994fac1a22d3fac','backing-vs-route-root13.json':json.loads((L/'backing-vs-route-root13.json').read_text())['all12_raw_and_srgb_exact'],'route-root-vs-overlay13.json':json.loads((L/'route-root-vs-overlay13.json').read_text())['all12_raw_and_srgb_exact'],'local_scope':'SDK14.2 min13 with archived unused-clock/gainmap compiler guards; those guards absent from newSDK ProductImage/Hero base here. Static endpoints only.'}
p['scope']='Same manual static endpoints under root or existing actual overlay; no actual coordinated flight/lifecycle/fullapp/HDR-physics acceptance. Samebinary13/14 offline pixel controls pending.'
p['files']={}
# Wrapper added by a reviewed preparation step before publication.
for f in sorted(D.rglob('*')):
 if f.is_file() and f.name!='source-provenance.json':
  raw=f.read_bytes();p['files'][str(f.relative_to(D))]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
(D/'source-provenance.json').write_text(json.dumps(p,indent=2,sort_keys=True)+'\n')
print('Prepared dedicated route source; old float/backing harness unchanged')
