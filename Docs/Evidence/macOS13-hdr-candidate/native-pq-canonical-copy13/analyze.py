from pathlib import Path
import hashlib,io,json
import numpy as np
import PIL
from PIL import Image,ImageCms
D=Path(__file__).resolve().parent;REPO=next((p for p in D.parents if (p/'.github/scripts/hdr-tone-probe.swift').exists()),D.parent.parent/'outputs/Bern')
R=D/'runtime13';report=json.loads((R/'report.json').read_text());offline=json.loads((D/'offline-result/validation.json').read_text());source=json.loads((REPO/'Docs/Evidence/macOS13-hdr-candidate/color-probe13/report.json').read_text())
names=[p['name'] for p in source['patches']];targets=['candidate-strict-cicp-pq','oracle-native-named-pq']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(p):
 im=Image.open(p);icc=im.info['icc_profile'];return np.asarray(im.convert('RGB')),np.asarray(ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0)),hashlib.sha256(icc).hexdigest()
def crop(a,r):
 x,y,w,h=[round(r[k]) for k in ('x','y','width','height')];return a[y:y+h,x:x+w]
def measurements(a):
 assert a.shape==(360,640,3)
 patches={p['name']:a[round(p['source_rect']['y'])+8:round(p['source_rect']['y'])+112,round(p['source_rect']['x'])+8:round(p['source_rect']['x'])+120].mean(axis=(0,1)) for p in source['patches']}
 return patches,a[260:340,4:636].mean(axis=0)
def compare(a,b):
 pa,ra=measurements(a);pb,rb=measurements(b);pd=np.array([pa[n]-pb[n] for n in names]);rd=ra-rb
 return {'image_rgb_pixels_equal':bool(np.array_equal(a,b)),'different_rgb_pixels':int(np.any(a!=b,axis=2).sum()),'patch_mean_rgb_mae_codes':float(np.abs(pd).mean()),'patch_mean_rgb_max_delta_codes':float(np.abs(pd).max()),'ramp_column_mean_rgb_mae_codes':float(np.abs(rd).mean()),'ramp_column_mean_rgb_max_delta_codes':float(np.abs(rd).max()),'patch_mean_rgb_delta':{n:[round(float(v),6) for v in row] for n,row in zip(names,pd)}}
assert offline['success'] and report['success'] and len(report['captures'])==6 and report['completed_phase_count']==3
assert report['offline_input_validation']==offline
assert report['activation_calls']==0 and report['frontmost_before']==report['frontmost_after']
assert [p['current_headroom'] for p in report['phases']]==[1,2,1]
assert offline['custom']['selection']=='strict-cicp-pq-color-space-copy' and offline['named']['selection']=='native-pq-original'
for n in ['custom','named']:
 x=offline[n];assert x['original_file_unchanged'] and x['layout_equal'] and x['provider_bytes_equal'] and x['source_exif_before']==x['source_exif_after']==1
 assert x['original_icc_sha256_before']==x['original_icc_sha256_after']
assert offline['derived_custom_vs_named_original_layout_equal'] and offline['derived_custom_vs_named_original_provider_bytes_equal']
arrays={};rawarrays={};rows=[]
for i,c in enumerate(report['captures']):
 assert sha(R/c['png'])==c['png_sha256'];raw,a,icc=norm(R/c['png']);assert icc==c['capture_icc_sha256']
 assert not c['active'] and not c['key'] and c['frontmost_pid']==report['frontmost_before']
 entry={k:c[k] for k in ['phase','png','png_sha256','current_headroom_before','current_headroom_after','potential_headroom','capture_icc_sha256','elapsed_seconds']};entry['index']=i;entry['rois']={}
 for n in targets:
  r=c['rois'][n];v=crop(a,r['screenshot_pixels']);rv=crop(raw,r['screenshot_pixels']);arrays[f'{i}/{n}']=v;rawarrays[f'{i}/{n}']=rv;p,rm=measurements(v)
  entry['rois'][n]={'screenshot_pixels':r['screenshot_pixels'],'canonical_rgba8_srgb_sha256':r['rgba8_srgb_sha256'],'mean_srgb_rgb_by_patch':{k:[round(float(v),6) for v in p[k]] for k in names}}
 rows.append(entry)
base=REPO/'Docs/Evidence/macOS13-hdr-candidate/native-sdr-components13';br=json.loads((base/'report.json').read_text());braw,ba,bicc=norm(base/'capture.png');b=crop(ba,br['frames']['native-swiftui-named']['screenshot_pixels']);rawb=crop(braw,br['frames']['native-swiftui-named']['screenshot_pixels'])
comparisons={}
for i in range(6):
 comparisons[f'capture{i}/candidate minus oracle']=compare(arrays[f'{i}/{targets[0]}'],arrays[f'{i}/{targets[1]}'])
 for n in targets:comparisons[f'capture{i}/{n} minus prior-static13-native']=compare(arrays[f'{i}/{n}'],b)
assert all(v['image_rgb_pixels_equal'] for v in comparisons.values())
raw_all=all(np.array_equal(v,rawb) for v in rawarrays.values());assert raw_all
trajectory=report['trajectory'];subs=report['driver_submissions'];reads=report['driver_completed_texture_readbacks'];complete=[s for s in subs if s['event']=='gpu-completed'];committed=[s for s in subs if s['event']=='committed-present'];draws=[s for s in subs if s['event']=='draw-enter']
assert len(complete)==len(committed)==len(draws)==len(reads)>0 and all(s['status']==4 and s['error']=='none' for s in complete)
assert any(s['current']==2 and s['requests_edr'] and s['right']>1 for s in reads)
assert all(not t['active'] and not t['key'] and t['frontmost_pid']==report['frontmost_before'] and t['visible'] and t['onscreen'] and t['driver_attached_to_own_window'] and t['driver_visible_rect']['width']==192 and t['driver_visible_rect']['height']==108 for t in trajectory)
v={'scope':'Actual13 protocol-PQ derived color-space-only CGImage copy vs original namedPQ native oracle, both bare SwiftUI Image during real1->2->1 headroom. No product BernImage/hero/HLG/EXIFvariant/alpha/gainmap or physicalpanel acceptance.','outcome':'All12 image ROIs match each other and the prior named native13 baseline exactly before and after ICC normalization. Strict CICP normalization changes display interpretation without changing original source/ICC/provider/layout.','offline_validation':offline,'runtime':{k:report[k] for k in ['success','os','window_seconds','activation_calls','frontmost_before','frontmost_after','completed_phase_count','system_preferences_readonly','ordering']},'capture_sequence':{'headrooms':[p['current_headroom'] for p in report['phases']],'sampled_current_headrooms':[t['current_headroom'] for t in trajectory],'trajectory_count':len(trajectory),'potential_headrooms':sorted(set(t['potential_headroom'] for t in trajectory)),'image_equality_was_not_a_gate':True,'all12_raw_profile_rgb_arrays_equal_prior_native':raw_all,'all12_icc_normalized_arrays_equal_prior_native':True},'driver':{'draws':len(draws),'committed_present':len(committed),'gpu_completed_status4_no_error':len(complete),'texture_readbacks':len(reads),'real_screen_notifications':len(report['real_screen_notifications']),'high_current2_texture_readbacks':[s for s in reads if s['current']==2 and s['requests_edr']]},'measurement':'Fixed640x360 native image ROIs; raw profileRGB and own PNG ICC->sRGB via Pillow ImageCms/LittleCMS perceptual intent0 flags0.10patch112x104interiors and632 grayramp column means over80rows; no rescaling/fitting.','pillow':PIL.__version__,'littlecms':ImageCms.core.littlecms_version,'captures':rows,'comparisons':comparisons,'prior_named_native13_baseline':{'report_sha256':sha(base/'report.json'),'capture_sha256':sha(base/'capture.png'),'icc_sha256':bicc},'limitations':['Native13 remains different from normal14 on some colors (prior cool812 red≈92.49 vs119). No color formula fitted or14 parity claimed.','Inputs are existing opaque EXIFup PQ pair. Source orientation/layout preservation is not visual EXIFvariant/alpha coverage.','WindowServer SDR constancy does not inspect private native linear image buffers or measure physicalpanel clipping.','Bare Image diagnostic does not validate full BernImage fit/wrappers, hero output or product code.']}
(D/'validation.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');np.savez_compressed(D/'ramp-column-means.npz',**{k.replace('/','_'):measurements(a)[1] for k,a in arrays.items()});print(json.dumps({'runtime':v['runtime'],'sequence':v['capture_sequence'],'driver':v['driver'],'roi_comparisons_all_zero':all(z['patch_mean_rgb_max_delta_codes']==0 and z['ramp_column_mean_rgb_max_delta_codes']==0 for z in comparisons.values())}))
