#!/usr/bin/env python3
import hashlib,io,json,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageCms,ImageStat
assert len(sys.argv)==4, 'baseline runtime, candidate runtime, fresh JSON output required'
baseline=Path(sys.argv[1]).resolve()
candidate=Path(sys.argv[2]).resolve()
output=Path(sys.argv[3]).resolve()
assert not output.exists()
def load(directory):
 d=json.loads((directory/'report.json').read_text());assert d['success'] and d['cache_unchanged'] and d['cache_before']==d['cache_after']
 assert d['activation_calls']==0 and d['frontmost_before']==d['frontmost_after']
 assert all(v is False for k in ['normal_before','normal_after'] for v in d[k].values())
 assert d['completed_phases']==2 and len(d['captures'])==2 and d['window_seconds']<7.9
 rows={}; d['_control_embedded_icc']={}
 for c in d['captures']:
  assert c['consecutive_equal_buffers']>=5 and c['live_metal_count']==0 and not c['key'] and not c['active']
  assert c['manager']['flight_count']==0 and c['manager']['timer_exists'] is False
  p=directory/c['png'];b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==c['png_sha256']
  im=Image.open(io.BytesIO(b));im.load();raw=im.convert('RGB')
  assert im.info.get('icc_profile') and list(im.size)==c['capture_size']
  d['_control_embedded_icc'][c['phase']]=hashlib.sha256(im.info['icc_profile']).hexdigest()
  norm=ImageCms.profileToProfile(raw,ImageCms.ImageCmsProfile(io.BytesIO(im.info['icc_profile'])),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0)
  crops={}
  for name,roi in c['rois'].items():
   r=roi['screenshot_pixels'];v=[r['x'],r['y'],r['x']+r['width'],r['y']+r['height']];assert all(abs(x-round(x))<1e-5 for x in v)
   box=tuple(round(x) for x in v)
   if im.mode=='RGBA':assert im.getchannel('A').crop(box).getextrema()==(255,255)
   crops[name]=(raw.crop(box),norm.crop(box),roi)
  assert len(crops)==6 and c['phase'] not in rows
  rows[c['phase']]=crops
 return d,rows
bd,base=load(baseline);cd,test=load(candidate);rows=[]
assert set(base)==set(test)=={'progress-0','progress-1'}
for phase,rois in base.items():
 for name,(ar,an,geometry) in rois.items():
  br,bn,bg=test[phase][name];assert geometry==bg,(phase,name)
  ds=ImageStat.Stat(ImageChops.difference(an,bn));rawdiff=ImageChops.difference(ar,br)
  rows.append(dict(phase=phase,roi=name,raw_exact=rawdiff.getbbox() is None,srgb_exact=all(x[1]==0 for x in ds.extrema),srgb_mae=sum(ds.mean)/3,srgb_max=max(x[1] for x in ds.extrema)))
r=dict(scope='Observed same-host control against explicitly supplied baseline. Twelve raw and ICC-normalized ROI comparisons, actual capture/normal/cache/front gates. No general zero observer-effect guarantee.',baseline_report_sha256=hashlib.sha256((baseline/'report.json').read_bytes()).hexdigest(),candidate_report_sha256=hashlib.sha256((candidate/'report.json').read_bytes()).hexdigest(),embedded_icc_identical=bd['_control_embedded_icc']==cd['_control_embedded_icc'],baseline_embedded_icc=bd['_control_embedded_icc'],candidate_embedded_icc=cd['_control_embedded_icc'],all12_raw_and_srgb_exact=all(x['raw_exact'] and x['srgb_exact'] for x in rows) and bd['_control_embedded_icc']==cd['_control_embedded_icc'],rows=rows)
output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({'all12_exact':r['all12_raw_and_srgb_exact'],'differences':[x for x in rows if not x['srgb_exact']]}))

raise SystemExit(0 if r['all12_raw_and_srgb_exact'] else 1)
