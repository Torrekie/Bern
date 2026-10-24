from pathlib import Path
import hashlib,io,json
import numpy as np
import PIL
from PIL import Image,ImageCms
D=Path(__file__).resolve().parent;REPO=next((p for p in D.parents if (p/'.github/scripts/window-background-probe.swift').exists()),D.parent.parent/'outputs/Bern')
P13=REPO/'Docs/Evidence/macOS13-window-background/sdk26-content-stable'
if not P13.exists():P13=REPO.parent.parent/'work/ci-background-40063367959/runtime13'
paths={'13':P13,'14':D}; reports={k:json.loads((p/'report.json').read_text()) for k,p in paths.items()}
assert reports['13']['probe_swift_sha256']==reports['14']['probe_swift_sha256']=='6cf5cf53178f3028f9788755c4708a6f0f32821862e3c53d79fa804e68bbb2b4'
assert reports['13']['probe_source_sha']==reports['14']['probe_source_sha']=='a39d29faeab8ad7fd15f04a2db219d755c5ef48d'
profile=json.loads((D/'profile.json').read_text());assert profile['appearance_profile']=='normal' and all(v is False for v in profile['effective_flags'].values())
rows={};runtime={};pngs={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(a):
 v,c=np.unique(a.reshape(-1,3),axis=0,return_counts=True)
 return {'mean_rgb':a.mean(axis=(0,1)).tolist(),'mode_rgb':v[c.argmax()].tolist(),'min_rgb':a.min(axis=(0,1)).tolist(),'max_rgb':a.max(axis=(0,1)).tolist(),'unique_rgb_count':len(v)}
for os,p in paths.items():
 r=reports[os];assert r['success'] and r['activation_calls']==0 and r['frontmost_before']==r['frontmost_after'] and r['window_seconds']<9
 assert [g['name'] for g in r['groups']]==['native-nsview','swiftui-color','canvas-role','split-transparent','split-explicit-role']
 assert r['expected_os_major']==r['actual_os_major']==int(os)
 rows[os]={};pngs[os]={}
 for g in r['groups']:
  b=g['stable_buffers'];assert len(b)>=2 and len({s['rgba8_srgb_sha256'] for s in b})==1
  assert all(s['window_frame']==g['window_frame'] and not s['active'] and not s['key'] and s['frontmost_pid']==r['frontmost_before'] for s in b)
  assert g['content_bounds']=={'x':0,'y':0,'width':800,'height':520}
  f=p/g['png'];assert sha(f)==g['png_sha256'];im=Image.open(f);icc=im.info['icc_profile'];assert hashlib.sha256(icc).hexdigest()==g['capture_icc_sha256']
  a=np.asarray(ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0));raw=np.asarray(im.convert('RGB'));x,y,w,h=[round(g['roi_screenshot_pixels'][k]) for k in ('x','y','width','height')]
  roi=a[y:y+h,x:x+w];rawroi=raw[y:y+h,x:x+w]
  rows[os][g['name']]={'icc_to_srgb_roi':stats(roi),'raw_png_profile_roi':stats(rawroi),'roi_pixels':[x,y,w,h],'capture_size':g['capture_size'],'icc_sha256':g['capture_icc_sha256'],'window_frame':g['window_frame'],'content_bounds':g['content_bounds'],'resolved_srgb':g['resolved_srgb'],'root_allows_vibrancy':g['root_allows_vibrancy'],'native_effect_views':g['native_effect_views'],'stable_buffer_count':len(b),'same_pixels_and_per_variant_outer_frame':True}
  pngs[os][g['png']]={'sha256':g['png_sha256'],'bytes':f.stat().st_size}
 assert all(d['content_bounds']=={'x':0,'y':0,'width':800,'height':520} and d['content_layout_rect']=={'x':0,'y':0,'width':800,'height':520} and d['visible'] and not d['key'] and not d['app_active'] and d['frontmost_pid']==r['frontmost_before'] for d in r['diagnostics'])
 assert all(d['onscreen'] is True for d in r['diagnostics'] if d['event']=='before-shot')
 runtime[os]={k:r[k] for k in ['success','os','probe_source_sha','probe_swift_sha256','window_seconds','frontmost_before','frontmost_after','activation_calls','system_preferences_readonly','geometry_contract']};runtime[os]['diagnostic_samples']=len(r['diagnostics']);runtime[os]['all_diagnostic_content_bounds_layout_rect800x520']=True;runtime[os]['onscreen_not_yet_available_install_events']=sum(d['onscreen'] is None for d in r['diagnostics']);runtime[os]['all_before_shot_events_onscreen']=True
comparisons={n:{'icc_normalized_mean13_minus14':(np.array(rows['13'][n]['icc_to_srgb_roi']['mean_rgb'])-np.array(rows['14'][n]['icc_to_srgb_roi']['mean_rgb'])).tolist(),'mode13':rows['13'][n]['icc_to_srgb_roi']['mode_rgb'],'mode14':rows['14'][n]['icc_to_srgb_roi']['mode_rgb'],'outer_frame_equal':rows['13'][n]['window_frame']==rows['14'][n]['window_frame'],'semantic_nscolor_srgb_equal':rows['13'][n]['resolved_srgb']==rows['14'][n]['resolved_srgb']} for n in rows['13']}
v={'scope':'Same SDK26.5 arm64/min13 binary on actual13 and virtual14 normal profile. Five public inactive manually-created window backgrounds, stable content800x520 and two equal pixel buffers at each variant outer frame. Native toolbar exterior changes recorded, not repaired. Not whole Gallery App or product acceptance.','build_run':40063367959,'runtime14_run':40063500033,'expected_binary_sha256':'6a2045be05cd9fd77c99bc03c2bd2f59806b2f5de58e63417dd2df0352b5e261','runtime14_profile':profile,'runtime':runtime,'measurement':'Fixed40x40point ROI at content top-left680,430;13 80x80pixels,14 40x40pixels. Each own screenshot ICC->sRGB with Pillow ImageCms perceptual intent0 flags0; no resizing or fixed RGB adjustment.','pillow':PIL.__version__,'littlecms':ImageCms.core.littlecms_version,'groups':rows,'comparisons':comparisons,'png_manifest':pngs,'limitations':['Actual13 physical2xColorLCD and14virtual1x use different output ICC/display/desktop environments; this compares complete pipelines and does not isolate an OS-only cause.','Inactive Aqua manual NSWindow/NSHostingView only; not full Gallery SwiftUI scene or active/dark state.','14 split toolbar changes exterior548->572points at y100->113 while content/layout remain800x520; geometry contract is intentionally per-variant, not same exterior across all paths.','No native effect material/tint mechanism uniquely inferred from pixel values. Source product colors were not changed.']}
(D/'validation.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({'runtime':runtime,'comparisons':comparisons},indent=2))
