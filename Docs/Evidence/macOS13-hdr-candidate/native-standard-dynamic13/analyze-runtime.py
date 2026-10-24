from pathlib import Path
import hashlib,io,json
import numpy as np
import PIL
from PIL import Image,ImageCms
D=Path(__file__).resolve().parent; R=D/'runtime-20261024'
REPO=next((p for p in D.parents if (p/'.github/scripts/hdr-tone-probe.swift').exists()),D.parent.parent/'outputs/Bern')
report=json.loads((R/'report.json').read_text());source=json.loads((REPO/'Docs/Evidence/macOS13-hdr-candidate/color-probe13/report.json').read_text())
names=[p['name'] for p in source['patches']]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(p):
 im=Image.open(p);icc=im.info['icc_profile'];a=np.asarray(ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0));return np.asarray(im.convert('RGB')),a,hashlib.sha256(icc).hexdigest()
def crop(a,r):
 x,y,w,h=[round(r[k]) for k in ('x','y','width','height')];return a[y:y+h,x:x+w]
def summarize(a):
 assert a.shape==(360,640,3)
 patch={p['name']:a[round(p['source_rect']['y'])+8:round(p['source_rect']['y'])+112,round(p['source_rect']['x'])+8:round(p['source_rect']['x'])+120].mean(axis=(0,1)) for p in source['patches']}
 ramp=a[260:340,4:636].mean(axis=0)
 return patch,ramp
def comparison(a,b):
 pa,ra=summarize(a);pb,rb=summarize(b);delta=np.array([pa[n]-pb[n] for n in names]);rd=ra-rb
 return {'image_rgb_pixels_exactly_equal':bool(np.array_equal(a,b)),'different_rgb_pixels':int(np.any(a!=b,axis=2).sum()),'patch_mean_channel_mae_codes':float(np.abs(delta).mean()),'patch_mean_channel_max_absolute_delta_codes':float(np.abs(delta).max()),'patch_mean_rgb_delta':{n:[round(float(v),6) for v in row] for n,row in zip(names,delta)},'ramp_mean_column_channel_mae_codes':float(np.abs(rd).mean()),'ramp_mean_column_channel_max_absolute_delta_codes':float(np.abs(rd).max())}
assert report['success'] and report['completed_phase_count']==3 and report['activation_calls']==0 and report['frontmost_before']==report['frontmost_after']
assert [p['current_headroom'] for p in report['phases']]==[1,2,1]
frames={};rawframes={};rows=[]
for i,c in enumerate(report['captures']):
 assert sha(R/c['png'])==c['png_sha256'];raw,a,icc=normalized(R/c['png']);assert icc==c['capture_icc_sha256']
 entry={'index':i,'phase':c['phase'],'png':c['png'],'png_sha256':c['png_sha256'],'icc_sha256':icc,'headroom_before':c['current_headroom_before'],'headroom_after':c['current_headroom_after'],'rois':{}}
 for name,r in c['rois'].items():
  key=f'{i}/{name}';v=crop(a,r['screenshot_pixels']);rv=crop(raw,r['screenshot_pixels']);p,ramp=summarize(v);frames[key]=v;rawframes[key]=rv
  entry['rois'][name]={'geometry':r['screenshot_pixels'],'canonical_rgba8_srgb_sha256':r['rgba8_srgb_sha256'],'mean_srgb_rgb_by_patch':{n:[round(float(v),6) for v in p[n]] for n in names},'ramp_columns':len(ramp)}
 rows.append(entry)
baseline=REPO/'Docs/Evidence/macOS13-hdr-candidate/native-sdr-components13';br=json.loads((baseline/'report.json').read_text());braw,ba,bicc=normalized(baseline/'capture.png')
baselines={name:crop(ba,br['frames'][name]['screenshot_pixels']) for name in ['nsimageview-named','native-swiftui-named']}
comparisons={}
for i in range(6):
 a,b=f'{i}/nsimageview-named',f'{i}/native-swiftui-named';comparisons[f'{a} minus {b}']=comparison(frames[a],frames[b])
 for name in ['nsimageview-named','native-swiftui-named']:
  key=f'{i}/{name}';comparisons[f'{key} minus initial0/{name}']=comparison(frames[key],frames[f'0/{name}'])
  if i==0:comparisons[f'{key} minus prior-static13/{name}']=comparison(frames[key],baselines[name])
trajectory=report['trajectory'];subs=report['driver_submissions'];reads=report['driver_completed_texture_readbacks']
completed=[s for s in subs if s['event']=='gpu-completed'];committed=[s for s in subs if s['event']=='committed-present'];entered=[s for s in subs if s['event']=='draw-enter']
assert len(completed)==len(committed)==len(entered)==len(reads)==27
assert all(s['status']==4 and s['error']=='none' for s in completed)
assert all(not t['active'] and not t['key'] and t['frontmost_pid']==report['frontmost_before'] and t['visible'] and t['onscreen'] for t in trajectory)
validation={'scope':report['scope'],'result':'Completed actual currentHd1->2->1 without activation. All12 target image ROI arrays (two views,six captures) are byte-identical both in raw screenshot profileRGB and after offline ICC normalization. Native candidate stayed screenshot-constant on this atlas under this successful visible driver. This is not proof of hidden native linear-buffer/physical brightness clamping.','runtime':{k:report[k] for k in ['success','os','window_seconds','activation_calls','frontmost_before','frontmost_after','completed_phase_count','system_preferences_readonly','provider_copy_bytes_unchanged','atlas_sha256','ordering']},'collection':{'image_equality_was_not_a_gate':True,'phase_headrooms':[p['current_headroom'] for p in report['phases']],'potential_headrooms':sorted(set(t['potential_headroom'] for t in trajectory)),'sampled_current_headrooms':[t['current_headroom'] for t in trajectory],'trajectory_count':len(trajectory),'all_trajectory_nonkey_inactive_visible_onscreen_foreground_unchanged':True,'all_target_raw_profile_rgb_arrays_equal':all(np.array_equal(v,next(iter(rawframes.values()))) for v in rawframes.values()),'all_target_icc_normalized_rgb_arrays_equal':all(np.array_equal(v,next(iter(frames.values()))) for v in frames.values())},'driver_evidence':{'source':'Existing192x108 successful prototype sibling ToneView. No new map formula.','draw_count':len(entered),'committed_present_count':len(committed),'gpu_completed_count':len(completed),'all_gpu_completed_status4_no_error':True,'completed_texture_readbacks':len(reads),'real_screen_notification_count':len(report['real_screen_notifications']),'requested_high_readbacks_current2':[s for s in reads if s['intent']=='High' and s['current']==2],'initial_and_returned_readback_values':sorted({(s['left'],s['right']) for s in reads if s['intent']=='Standard' and s['current']==1}),'visibility_all_ticks':all(t['driver_visible_rect']['width']==192 and t['driver_visible_rect']['height']==108 and t['driver_attached_to_own_window'] and not t['driver_layer_hidden'] and t['driver_layer_opacity']==1 for t in trajectory)},'measurement':'Raw own WindowServer PNG ICC->encoded8-bit sRGB using Pillow ImageCms/LittleCMS perceptual intent0 flags0. Original fixed640x360 image ROIs with no resizing/phasefit.10patch112x104interior means; grayramp sourcecolumns4..635 overrows260..339.','pillow':PIL.__version__,'littlecms':ImageCms.core.littlecms_version,'captures':rows,'comparisons':comparisons,'prior_static_baseline':{'directory':str(baseline.relative_to(REPO)),'report_sha256':sha(baseline/'report.json'),'capture_sha256':sha(baseline/'capture.png'),'icc_sha256':bicc},'limitations':['Only actual13.7.8 M1/2x/current1->2->1 potential2,inactive Aqua,one namedPQ color atlas.','Both native images bare/no allowedDynamicRange modifier. No product helper/Standard/High or native14 runtime tested here.','SDR WindowServer captures can compress/clip EDR; screenshot constancy does not expose native private layer linear samples or measured panel light.','Changed request surface/visibility/parent/lifecycle vs old failed8x8 probe; success does not isolate one cause for the old failure.']}
(D/'runtime-validation.json').write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n');np.savez_compressed(D/'runtime-ramp-columns.npz',**{k.replace('/','_'):summarize(v)[1] for k,v in frames.items()})
print(json.dumps({'runtime':validation['runtime'],'collection':validation['collection'],'baseline_deltas':{k:v for k,v in comparisons.items() if 'prior-static' in k},'driver_counts':{k:v for k,v in validation['driver_evidence'].items() if k not in ['requested_high_readbacks_current2']}},indent=2))
