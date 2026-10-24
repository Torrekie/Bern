from pathlib import Path
import hashlib,json,numpy as np
D=Path(__file__).resolve().parent;repo=next(p for p in D.parents if (p/'.github/scripts/hdr-tone-probe.swift').exists());n=json.loads((D/'validation.json').read_text())
inputs={'e06-product-standard':repo/'Docs/Evidence/macOS13-hdr-candidate/standard-color-e06/validation.json','public-native-components':repo/'Docs/Evidence/macOS13-hdr-candidate/native-sdr-components13/validation.json'}
rows={};provenance={}
for group,p in inputs.items():
 d=json.loads(p.read_text());assert d['capture_success'] and set(d['current_headrooms'])=={1};provenance[group]={'path':str(p.relative_to(repo)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':d['scope'],'runtime_sha256':d.get('runtime_sha256'),'product_commit':d.get('product_commit'),'window_seconds':d['window_seconds'],'current_headrooms':d['current_headrooms'],'measurement':d['measurement']}
 for view,v in d['views'].items():
  patches=v['mean_srgb_rgb_by_patch']; names=list(patches)
  for ref in ['14/named-pq','14/ffb-icc']:
   b=n['native_mean_srgb_rgb'][ref];delta=np.array([np.array(patches[k])-np.array(b[k]) for k in names]);rows[f'{group}/{view} minus {ref}']={'patch_count':len(names),'rgb_channel_mean_absolute_delta_codes':float(np.abs(delta).mean()),'rgb_channel_max_absolute_delta_codes':float(np.abs(delta).max()),'mean_rgb_delta_by_patch':{name:[round(float(v),6) for v in row] for name,row in zip(names,delta)}}
r={'scope':'Offline10patch means only. Existing actual13 e06 Standard product helper and public components compared to same-code actual14 native allowedDynamicRange.high at currentHd1 with verified normal external profile. No new UI or product code run.','normal14_run':40062048900,'normal14_reference':{'path':'work/ci-hdr14-normal-40062048900/validation.json','sha256':hashlib.sha256((D/'validation.json').read_bytes()).hexdigest(),'profile':n['runtime14_profile']},'inputs':provenance,'comparisons':rows,'limitations':['13physicalM1 at2x potentialHd2 and14virtual at1x potentialHd1, separate ICC/display and runtime; these are completepipeline output measurements, not causal OS-only differences.','Rounded existing6decimal means reused (rounding<=0.0000005codes); no new fitting/image rescaling or color algorithm.','NSImageView was only rendered on13 and equals13nativeSwiftUI; cross-reference closeness does not establish14 NSImageView behavior or product acceptance.','10atlaspatches atcurrentHd1 only; not generalizedHDR/High/metadata/HLG/alpha/EXIF or hardwarebrightness equivalence.']}
(D/'existing13-vs-native14.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:{x:y for x,y in v.items() if x!='mean_rgb_delta_by_patch'} for k,v in rows.items() if k.endswith('14/named-pq')},indent=2))
