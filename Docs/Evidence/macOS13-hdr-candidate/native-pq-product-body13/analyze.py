from pathlib import Path
import hashlib,io,json
import numpy as np
import PIL
from PIL import Image,ImageCms
D=Path(__file__).resolve().parent
REPO=next((p for p in D.parents if (p/'.github/scripts/hdr-tone-probe.swift').exists()),D.parent.parent/'outputs/Bern')
R=D/'runtime13';r=json.loads((R/'report.json').read_text())
build=json.loads((D/'build-fingerprint.json').read_text());provenance=json.loads((D/'source-provenance.json').read_text())
source=json.loads((REPO/'Docs/Evidence/macOS13-hdr-candidate/color-probe13/report.json').read_text())
base=REPO/'Docs/Evidence/macOS13-hdr-candidate/native-sdr-components13'
br=json.loads((base/'report.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(p):
 im=Image.open(p);icc=im.info['icc_profile']
 return np.asarray(im.convert('RGB')),np.asarray(ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0)),hashlib.sha256(icc).hexdigest()
def crop(a,q):
 x,y,w,h=[round(q[k]) for k in ('x','y','width','height')];return a[y:y+h,x:x+w]
def measure(a):
 assert a.shape==(360,640,3)
 patches={p['name']:a[round(p['source_rect']['y'])+8:round(p['source_rect']['y'])+112,round(p['source_rect']['x'])+8:round(p['source_rect']['x'])+120].mean(axis=(0,1)) for p in source['patches']}
 return patches,a[260:340,4:636].mean(axis=0)
def compare(a,b):
 pa,ra=measure(a);pb,rb=measure(b)
 pd=np.array([pa[n]-pb[n] for n in pa]);rd=ra-rb
 return {'image_rgb_pixels_equal':bool(np.array_equal(a,b)),'different_rgb_pixels':int(np.any(a!=b,axis=2).sum()),'patch_mean_rgb_max_delta_codes':float(np.abs(pd).max()),'patch_mean_rgb_mae_codes':float(np.abs(pd).mean()),'ramp_column_mean_rgb_max_delta_codes':float(np.abs(rd).max()),'ramp_column_mean_rgb_mae_codes':float(np.abs(rd).mean())}
assert r['success'] and r['completed_phases']==3 and len(r['captures'])==6
assert r['activation_calls']==0 and r['frontmost_before']==r['frontmost_after']==1390 and r['window_seconds']<8
assert [p['live_metal_count'] for p in r['phases']]==[0,2,0]
assert r['cache_before']==r['cache_after'] and all(p['cache_unchanged'] and p['cache']==r['cache_before'] for p in r['phases'])
assert len(r['phases'][1]['live_metal'])==2 and all(m['wants_edr'] and m['attached_to_window'] for m in r['phases'][1]['live_metal'])
ids={m['id'] for m in r['phases'][1]['live_metal']}
for held in [r['phases'][2]['held_high'],r['retained_high_final_state_before_cleanup']]:
 assert {m['id'] for m in held}==ids
 assert all(not m['attached_to_window'] and not m['wants_edr'] and m['is_paused'] for m in held)
assert r['live_metal_count_before_cleanup']==0
assert not r['image_equality_collection_gate'] and not r['high_headroom_readiness_gate']
assert all(not t['active'] and not t['key'] and t['frontmost_pid']==1390 and t['visible'] and t['onscreen'] for t in r['trajectory'])
for n,h in build['hashes'].items():
 if (D/n).exists():assert sha(D/n)==h,(n,h,sha(D/n))
assert sha(D/'ProductImage.exact.swift')==provenance['exact_slice_sha256'] and sha(D/'ProductImage.swift')==provenance['diagnostic_file_sha256']
braw,bnorm,bicc=norm(base/'capture.png');braw=crop(braw,br['frames']['native-swiftui-named']['screenshot_pixels']);bnorm=crop(bnorm,br['frames']['native-swiftui-named']['screenshot_pixels'])
comparisons={};rows=[];raw_hashes=[];norm_hashes=[]
for i,c in enumerate(r['captures']):
 assert sha(R/c['png'])==c['png_sha256'];raw,a,icc=norm(R/c['png']);assert icc==c['capture_icc_sha256']
 assert not c['active'] and not c['key'] and c['frontmost_pid']==1390
 arrays={n:crop(a,z['screenshot_pixels']) for n,z in c['rois'].items()}
 rawarrays={n:crop(raw,z['screenshot_pixels']) for n,z in c['rois'].items()}
 row={'index':i,**{k:c[k] for k in ['phase','png','png_sha256','current_headroom','potential_headroom','elapsed_seconds','capture_icc_sha256']},'rois':{}}
 for n,v in arrays.items():
  p,rm=measure(v);row['rois'][n]={'raw_profile_rgb_sha256':hashlib.sha256(rawarrays[n].tobytes()).hexdigest(),'icc_normalized_rgb_sha256':hashlib.sha256(v.tobytes()).hexdigest(),'screenshot_pixels':c['rois'][n]['screenshot_pixels'],'mean_srgb_rgb_by_patch':{k:[round(float(x),6) for x in q] for k,q in p.items()}}
  if c['phase']!='high-lifecycle':
   raw_hashes.append(row['rois'][n]['raw_profile_rgb_sha256']);norm_hashes.append(row['rois'][n]['icc_normalized_rgb_sha256'])
   comparisons[f'capture{i}/{n} minus prior-native13']=compare(v,bnorm)
   assert np.array_equal(rawarrays[n],braw)
 if c['phase']!='high-lifecycle':
  for n in ['product-named','product-custom']:
   comparisons[f'capture{i}/{n} minus own-native-oracle']=compare(arrays[n],arrays['oracle-native-named'])
 rows.append(row)
assert len(raw_hashes)==len(norm_hashes)==12 and len(set(raw_hashes))==len(set(norm_hashes))==1
assert all(c['image_rgb_pixels_equal'] for c in comparisons.values())
assert all(r['standard_before_after_equal'].values())
current=[t['current_headroom'] for t in r['trajectory']]
v={'scope':'Actual 9dd99b7 BernImage.body/.task/BernPictures cache and Legacy renderer slice, two opaque EXIFup existing PQ atlas inputs, macOS13 explicit Standard original fill320x180 then High then Standard. Identity hero only. Not whole Showcase/hero/HLG/alpha/EXIFvariant/gainmap acceptance or14 visual parity.','outcome':'All12 Standard image ROIs are identical before/after switching and to the own native oracle and prior native13 baseline, both raw profileRGB and ICC-normalized; public Metal lifecycle0->2->0, retained High views detached with EDR off before cleanup, original/derived cache unchanged.','product':provenance,'runtime':{k:r[k] for k in ['success','os','window_seconds','activation_calls','frontmost_before','frontmost_after','completed_phases']},'binary_sha256':build['hashes']['ProductBodyProbe'],'runtime_session':2596,'runtime_exit_code':0,'lifecycle':{'metal_view_count_sequence':[p['live_metal_count'] for p in r['phases']],'high_views_attached_wants_edr':True,'same_two_retained_high_ids_detached_edr_off_paused_before_cleanup':True,'held_views_still_have_superview':all(m['has_superview'] for m in r['retained_high_final_state_before_cleanup']),'deallocation_observed':False,'current_headroom_samples':current,'maximum_sampled_current':max(current),'high_capture_current':[c['current_headroom'] for c in r['captures'] if c['phase']=='high-lifecycle'],'maximum_potential_samples':sorted({t['potential_headroom'] for t in r['trajectory']}),'current_max_occurs_during':'standard-returned cooling period','high_color_acceptance':False,'draw_or_gpu_submission_instrumentation':False},'cache':{'all_phases_and_final_equal_original_ledger':True,'ledger_includes':'original/derived CGImage identity/provider/ICC; original file/bitmap/alpha/size/orientation/ratio; cached average; flags','custom_original_and_derived_distinct':r['cache_before']['source-ffb-icc.png']['image_id']!=r['cache_before']['source-ffb-icc.png']['derived_id'],'named_original_and_derived_same_object':r['cache_before']['source-named-pq.png']['image_id']==r['cache_before']['source-named-pq.png']['derived_id'],'original_custom_icc':r['cache_before']['source-ffb-icc.png']['original_icc_sha256'],'derived_custom_icc':r['cache_before']['source-ffb-icc.png']['derived_icc_sha256']},'standard_pixels':{'roi_count':12,'all_raw_profile_rgb_exact_to_own_oracle_and_prior_native13':True,'all_icc_normalized_rgb_exact_to_own_oracle_and_prior_native13':True,'all_before_after_exact':True,'raw_rgb_sha256':raw_hashes[0],'icc_normalized_rgb_sha256':norm_hashes[0],'runtime_canonical_rgba8_srgb_sha256':r['captures'][0]['rois']['product-named']['rgba8_srgb_sha256'],'patches':len(source['patches']),'gray_ramp_columns':632,'all_patch_and_ramp_delta_zero':True,'image_equality_collection_gate':False},'measurement':'Unscaled640x360 image crops; raw profileRGB and own PNG ICC->sRGB via Pillow ImageCms/LittleCMS perceptual intent0 flags0;10patch interiors112x104,632grayramp column means over80rows. Runtime canonical RGBA uses CoreGraphics separately.','pillow':PIL.__version__,'littlecms':ImageCms.core.littlecms_version,'captures':rows,'comparisons':comparisons,'prior_native13_baseline':{'directory':'../native-sdr-components13','report_sha256':sha(base/'report.json'),'capture_sha256':sha(base/'capture.png'),'capture_icc_sha256':bicc},'limitations':['High validates public surface lifecycle and request/teardown only. Actual current headroom peaks at1.470819 while cooling after High, not2. No GPU buffer or High color acceptance.','Retaining High views delays deallocation; their window detachment, EDRoff and paused state are observed, not deallocation.','Only opaque EXIFup PQ pair, original rendering and fill320x180. No HLG/alpha/orientation/contain/cover/gainmap matrix.','Hero is an identity dependency stub and excluded; no full Showcase visual parity or14 equality is claimed. Native13 still differs from14 normal on prior cool812 red.','The exact product slice is built with SDK14.2 diagnostic compiler exclusion solely for15+ gainmap decode unavailable locally; original exhaustive-switch warnings remain.']}
(D/'validation.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
print(json.dumps({'success':True,'metal_sequence':v['lifecycle']['metal_view_count_sequence'],'raw_std_12_exact':True,'normalized_std_12_exact':True,'prior_native13_exact':True,'patch_ramp_all_zero':True,'max_current':max(current),'cache_unchanged':True,'runtime_seconds':r['window_seconds'],'exe_sha256':v['binary_sha256']}))
