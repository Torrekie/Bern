from pathlib import Path
import json,hashlib,shutil,difflib
R=Path.cwd(); L=R/'work/native-pq-hero-backing-observer'; P=R/'outputs/Bern/.github/scripts/hero-float-probe'
p=json.loads((P/'source-provenance.json').read_text())
assert hashlib.sha256((P/'Driver.swift.inc').read_bytes()).hexdigest()==p['files']['Driver.swift.inc']['sha256']==hashlib.sha256((L/'Driver.before-backing.swift.inc').read_bytes()).hexdigest()
shutil.copy2(P/'source-provenance.json',P/'source-provenance.before-backing.json')
for n in ['Driver.before-backing.swift.inc','BackingObservation.swift.inc','Driver.swift.inc','backing-observer.patch','run-backing-one.py']:
 shutil.copy2(L/n,P/n)
with (P/'README.md').open('a') as f:
 f.write('''\nA separate BERN_HERO_LAYER_OBSERVE=off|on defaults off. The optional observer\nreads only public scalar view/layer/ancestor properties after every PNG and\noriginal final guard, before existing teardown. It reads the already-prepared\nactual manager overlay without preparing/reparenting it, and the two static\nroot-mounted flights. No contents/presentation/provider reads, layer/view\nsetters, forced layout/display, new layer or image retention are introduced.\nEach node call reads its optional layer once; shared ancestors may be observed\nagain. These getters may perform internal work; no zero-effect claim is made.\n\nThe manual macos14-hero-backing-probe workflow uses the same build recipe and\npackage, forces float capture off, collects fresh layer-off/on14, and validates\nscalar schema without assuming layer presence, class, or format. Samebinary13\nand prior/off/on image controls remain required offline. AutomaticAppKit or\nRGBA format strings are requested/default format observations, not proof of\nactual backing pixel storage or the source of a visible color difference.\nA root-mounted static endpoint remains distinct from an actual overlay flight.\n''')
p['runtime_backing_mode_default']='off'
p['backing_observer_stage']='post_png_post_final_guards_pre_teardown'
p['source_adaptations'].append('optional_post_png_scalar_view_layer_and_existing_actual_overlay_ancestor_observation_default_off')
p['backing_local_controls']={'binary_sha256':'b57b0d9303ba39ff60740c52a84cc34ab212694dff99692d69bb636b6c7c57a4','float-vs-backing-off13.json':json.loads((L/'float-vs-backing-off13.json').read_text())['all12_raw_and_srgb_exact'],'backing-off-vs-on13.json':json.loads((L/'backing-off-vs-on13.json').read_text())['all12_raw_and_srgb_exact'],'scope':'Observed12 raw+ICC normalized ROI controls; no general zero-observer-effect guarantee. Local compiler guards unchanged; newSDK guards remain absent.'}
p['files']={}
for f in sorted(P.rglob('*')):
 if f.is_file() and f.name!='source-provenance.json':
  raw=f.read_bytes();p['files'][str(f.relative_to(P))]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
(P/'source-provenance.json').write_text(json.dumps(p,indent=2,sort_keys=True)+'\n')
print('Prepared optional observer source; original newSDK Image/Hero and FloatCapture unchanged')
