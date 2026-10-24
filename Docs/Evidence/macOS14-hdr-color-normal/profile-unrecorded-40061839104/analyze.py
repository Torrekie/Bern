import hashlib, io, json
from pathlib import Path
import numpy as np
import PIL
from PIL import Image, ImageCms
D=Path(__file__).resolve().parent
REPO=next(p for p in D.parents if (p/'.github/scripts/hdr-tone-probe.swift').exists())
P13=REPO/'Docs/Evidence/macOS13-hdr-candidate/color-probe13'
P14=D/'runtime14'
reports={str(k):json.loads((p/'report.json').read_text()) for k,p in [(13,P13),(14,P14)]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def box(r):
 x,y,w,h=[int(round(r[k])) for k in ('x','y','width','height')]
 assert max(abs(r[k]-v) for k,v in zip(('x','y','width','height'),(x,y,w,h)))<1e-7
 return (x,y,x+w,y+h)
def manifest(p):
 return dict((line.split(None,1)[1].strip().lstrip('*'),line.split(None,1)[0]) for line in p.read_text().splitlines())
m13=manifest(P13/'build-SHA256SUMS'); m14=manifest(P14/'build-SHA256SUMS')
assert m13==m14
assert reports['13']['harness_sha']==reports['14']['harness_sha']=='e46505c8865b0fa961e54dc0aead4d8206dd9b96'
assert reports['13']['patches']==reports['14']['patches']
source_keys=('raw_rgb16be_sha256','raw_rgba16be_sha256')
srcs={os:{s['name']:s for s in r['sources']} for os,r in reports.items()}
assert all(srcs['13'][name][k]==srcs['14'][name][k] for name in srcs['13'] for k in source_keys)
views={}; capture_checks={}
for os,p in [('13',P13),('14',P14)]:
 r=reports[os]; assert r['success'] and len(r['captures'])==4
 assert len({c['rgba8_srgb_sha256'] for c in r['captures']})==1
 assert all(not c['key'] and not c['active'] for c in r['captures'])
 assert r['frontmost_pid_before']==r['frontmost_pid_after']
 c=r['captures'][0]; im=Image.open(p/c['png']); assert sha(p/c['png'])==c['png_sha256']
 icc=im.info['icc_profile']; assert hashlib.sha256(icc).hexdigest()==c['png_color']['icc_sha256']
 rgb=ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0)
 ar=np.array(rgb,dtype=float); raw=np.array(im.convert('RGB'))
 for name,roi in c['image_rois'].items():
  x,y,x2,y2=box(roi['screenshot_pixels']); crop=ar[y:y2,x:x2]; rawcrop=raw[y:y2,x:x2]
  w,h=x2-x,y2-y; assert w/640==h/360
  patch={n:ar[b[1]:b[3],b[0]:b[2]].mean(axis=(0,1)) for n,b in [(n,box(v)) for n,v in roi['patch_sample_pixels'].items()]}
  # Each sampled output column represents the source interval 4..635, at its recorded native scale.
  sx=w/640; sy=h/360
  ix0,ix1,iy0,iy1=[int(round(v)) for v in (4*sx,636*sx,260*sy,340*sy)]
  ramp=crop[iy0:iy1,ix0:ix1].mean(axis=0)
  views[f'{os}/{name}']={'patches':patch,'ramp':ramp,'crop':crop,'raw_crop':rawcrop,'geometry':roi}
 capture_checks[os]={'os':r['os'],'native_allowed_dynamic_range_high':r['native_allowed_dynamic_range_high'],'current_headroom':[c['current_headroom'] for c in r['captures']],'potential_headroom':[c['potential_headroom'] for c in r['captures']],'frontmost_before':r['frontmost_pid_before'],'frontmost_after':r['frontmost_pid_after'],'all_inactive_nonkey':True,'four_canonical_buffers_equal':True,'all_png_bytes_equal':len({c['png_sha256'] for c in r['captures']})==1,'elapsed_seconds':r['elapsed_seconds'],'capture_pixels':[c['width'],c['height']],'screen_points':c['screen_frame'],'capture_profile':c['png_color'],'system_preferences':r.get('system_preferences','not recorded by this unchanged probe'),'image_geometry':{n:v['screenshot_pixels'] for n,v in c['image_rois'].items()}}
comparisons={}
for a,b in [('13/named-pq','13/ffb-icc'),('14/named-pq','14/ffb-icc'),('13/named-pq','14/named-pq'),('13/ffb-icc','14/ffb-icc')]:
 l,rr=views[a],views[b]; names=[p['name'] for p in reports['13']['patches']]
 delta=np.array([l['patches'][n]-rr['patches'][n] for n in names])
 ra,rb=l['ramp'],rr['ramp']; ratio=max(len(ra),len(rb))//min(len(ra),len(rb)); assert ratio*min(len(ra),len(rb))==max(len(ra),len(rb))
 # No image rescaling or phase fitting: only aggregate adjacent column means into common source intervals.
 if len(ra)>len(rb):ra=ra.reshape(len(rb),ratio,3).mean(axis=1)
 if len(rb)>len(ra):rb=rb.reshape(len(ra),ratio,3).mean(axis=1)
 rd=ra-rb
 comparisons[f'{a} minus {b}']={'patch_mean_rgb_mae_codes':float(np.abs(delta).mean()),'patch_mean_rgb_max_absolute_delta_codes':float(np.abs(delta).max()),'patch_mean_rgb_delta':{n:[round(float(v),6) for v in row] for n,row in zip(names,delta)},'ramp_column_rgb_mae_codes':float(np.abs(rd).mean()),'ramp_column_rgb_max_absolute_delta_codes':float(np.abs(rd).max()),'ramp_common_column_count':len(ra),'ramp_input_column_counts':[len(l['ramp']),len(rr['ramp'])],'ramp_method':'Aggregate adjacent native column means into common source intervals; no image resizing/interpolation/phase fit. Cross-OS 13 has2x output pixels while14 has1x.','whole_image_normalized_pixels_exactly_equal':bool(np.array_equal(l['crop'],rr['crop'])) if l['crop'].shape==rr['crop'].shape else None,'whole_image_raw_profile_pixels_exactly_equal':bool(np.array_equal(l['raw_crop'],rr['raw_crop'])) if l['raw_crop'].shape==rr['raw_crop'].shape else None}
# Reproduce the existing13 analysis as a check of ROI/method continuity.
baseline=json.loads((P13/'validation.json').read_text())
for p in baseline['patch_analysis']['patches']:
 for n,means in p['native13_srgb_mean_rgb'].items():assert np.max(np.abs(np.array(means)-views[f'13/{n}']['patches'][p['name']]))<.000001
png_manifest={f.name:{'sha256':sha(f),'bytes':f.stat().st_size} for f in P14.glob('*.png')}
summary={'scope':'Same SDK26.5 ARM64 min13 binary: actual13 native SwiftUI Image without allowedDynamicRange modifier vs14 native Image.allowedDynamicRange(.high), each at current headroom1. Two in-memory equal-code PQ atlas color-space paths; not Bern product HDR mapper or hardware HDR validation.','binary_provenance':{'build_run':39987622874,'same_build_manifest':True,'manifest':m14,'runtime_run':json.loads((D/'run.json').read_text()),'runtime_artifact':json.loads((D/'artifacts.json').read_text())['artifacts'][0]},'measurement':'Each screenshot own embedded ICC -> encoded8-bit sRGB via Pillow ImageCms/LittleCMS perceptual intent0 flags0. Means over recorded112x104 source-pixel interiors (13output112x104,14output56x52); gray ramp source4..635,y260..339. Different output scale/display/profile/OS; no OS-only causal attribution.','pillow':PIL.__version__,'littlecms':ImageCms.core.littlecms_version,'old13_patch_analysis_reproduced':True,'capture_validation':capture_checks,'sources':{os:{n:{k:v for k,v in src.items() if k!='decoded_png_bytes_per_row'} for n,src in ss.items()} for os,ss in srcs.items()},'native_mean_srgb_rgb':{k:{n:[round(float(c),6) for c in rgb] for n,rgb in v['patches'].items()} for k,v in views.items()},'comparisons':comparisons,'runtime14_png_manifest':png_manifest,'limitations':['No system_preferences flags in unchanged HDR report or exact-runtime artifact; defaults on this run are unmeasured. Separate image-run preferences cannot establish this run profile.','Actual13 2x M1 display/current1 potential2 vs14 1x virtual SDR/current1 potential1, distinct capture ICC and OS. Cross-OS measurements characterize those complete pipelines.','No product mapper/Standard/High acceptance; no headroom>1/HLG/alpha/EXIF/arbitrary metadata or unique algorithm/physical-nits inference.']}
(D/'validation.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
np.savez_compressed(D/'ramp-column-means.npz',**{k.replace('/','_'):v['ramp'] for k,v in views.items()})
print(json.dumps({'comparisons':{k:{n:v for n,v in c.items() if n not in ['patch_mean_rgb_delta','ramp_method']} for k,c in comparisons.items()},'native_mean_srgb_rgb':summary['native_mean_srgb_rgb']},indent=2))
