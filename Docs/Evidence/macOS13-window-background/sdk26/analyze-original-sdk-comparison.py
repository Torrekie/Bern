from pathlib import Path
from PIL import Image, ImageCms
import PIL,numpy as np,io,json,hashlib
D=Path(__file__).resolve().parent
REPO=next(p for p in D.parents if (p/'.github/scripts/window-background-probe.swift').exists())
paths={'sdk14.2-old-source':REPO/'Docs/Evidence/macOS13-window-background','sdk26.5-public-source':D}
reports={k:json.loads((p/'report.json').read_text()) for k,p in paths.items()}
rows={}; arrays={}
def stats(a):
 v,c=np.unique(a.reshape(-1,3),axis=0,return_counts=True)
 return {'mean_rgb':a.mean(axis=(0,1)).tolist(),'mode_rgb':v[c.argmax()].tolist(),'min_rgb':a.min(axis=(0,1)).tolist(),'max_rgb':a.max(axis=(0,1)).tolist(),'unique_rgb_count':len(v)}
for k,p in paths.items():
 r=reports[k]; assert r['success'] and r['activation_calls']==0 and r['frontmost_before']==r['frontmost_after'] and len(r['groups'])==5
 rows[k]={}; arrays[k]={}
 for g in r['groups']:
  f=p/g['png']; data=f.read_bytes();assert hashlib.sha256(data).hexdigest()==g['png_sha256']
  im=Image.open(f); icc=im.info['icc_profile'];assert hashlib.sha256(icc).hexdigest()==g['capture_icc_sha256']
  srgb=ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0)
  ar=np.asarray(srgb);raw=np.asarray(im.convert('RGB')); z=g['roi_screenshot_pixels'];x,y,w,h=[round(z[n]) for n in ('x','y','width','height')]
  assert len(g['stable_buffers'])>=2 and len({b['rgba8_srgb_sha256'] for b in g['stable_buffers']})==1
  assert all(not b['active'] and not b['key'] and b['frontmost_pid']==r['frontmost_before'] for b in g['stable_buffers'])
  rows[k][g['name']]={'icc_to_srgb_roi':stats(ar[y:y+h,x:x+w]),'raw_png_profile_roi':stats(raw[y:y+h,x:x+w]),'png_sha256':g['png_sha256'],'icc_sha256':g['capture_icc_sha256'],'semantic_nscolor_srgb':g['resolved_srgb']['semantic_window_background'],'effect_view_count':len(g['native_effect_views']),'roi_pixels':[x,y,w,h]}
  arrays[k][g['name']]=ar
cmp={};a,b=paths
for name in rows[a]:
 aa,bb=arrays[a][name],arrays[b][name];changed=np.any(aa!=bb,axis=2);yy,xx=np.where(changed)
 cmp[name]={'whole_png_sha_equal':rows[a][name]['png_sha256']==rows[b][name]['png_sha256'],'whole_icc_normalized_pixels_equal':not bool(changed.any()),'changed_pixel_count':int(changed.sum()),'changed_pixels_bbox_xyxy':None if not changed.any() else [int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'fixed_roi_stats_exactly_equal':rows[a][name]['icc_to_srgb_roi']==rows[b][name]['icc_to_srgb_roi'],'window_frame_equal':next(g for g in reports[a]['groups'] if g['name']==name)['window_frame']==next(g for g in reports[b]['groups'] if g['name']==name)['window_frame']}
v={'scope':'Offline comparison of two actual13 background runs: original SDK14.2 fixture vs SDK26.5 public probe. Source hash and metadata/lifecycle differ; this is not an exact-source-only SDK test or macOS14 result.','measurement':'Fixed40x40pt content-top-left ROI680,430 (80x80 native pixels). Each own screenshot ICC to sRGB, perceptual intent0 flags0; no image resizing.','pillow':PIL.__version__,'littlecms':ImageCms.core.littlecms_version,'runtime':{k:{n:r.get(n) for n in ['os','probe_source_sha','probe_swift_sha256','window_seconds','frontmost_before','frontmost_after','activation_calls','system_preferences_readonly']} for k,r in reports.items()},'groups':rows,'comparisons':cmp,'limitations':['Both nonkey/inactive manually-created Aqua windows, not whole Gallery App scenes.','Public source has added provenance/expectedOS checks and changed collector deadline; different source hashes as well asSDK.','No prefs/wallpaper/brightness changes by the probes; desktop context could affect native transparent composition.']}
(D/'validation13-sdk.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
print(json.dumps({'comparisons':cmp,'new_roi':{k:v['icc_to_srgb_roi'] for k,v in rows[b].items()}},indent=2))
