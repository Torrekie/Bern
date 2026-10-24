#!/usr/bin/env python3
import hashlib,io,json,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageCms,ImageStat
root=Path(__file__).resolve().parents[1]
baseline=root/'native-pq-hero-baseline/runtime13'
candidate=Path(sys.argv[1]).resolve()
output=Path(sys.argv[2]).resolve()
assert not output.exists()
def load(directory):
 d=json.loads((directory/'report.json').read_text());assert d['success'] and d['cache_unchanged']
 rows={}
 for c in d['captures']:
  p=directory/c['png'];b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==c['png_sha256']
  im=Image.open(io.BytesIO(b));im.load();raw=im.convert('RGB')
  norm=ImageCms.profileToProfile(raw,ImageCms.ImageCmsProfile(io.BytesIO(im.info['icc_profile'])),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0)
  crops={}
  for name,roi in c['rois'].items():
   r=roi['screenshot_pixels'];v=[r['x'],r['y'],r['x']+r['width'],r['y']+r['height']];assert all(abs(x-round(x))<1e-5 for x in v)
   box=tuple(round(x) for x in v);crops[name]=(raw.crop(box),norm.crop(box),roi)
  rows[c['phase']]=crops
 return d,rows
bd,base=load(baseline);cd,test=load(candidate);rows=[]
for phase,rois in base.items():
 for name,(ar,an,geometry) in rois.items():
  br,bn,bg=test[phase][name];assert geometry==bg,(phase,name)
  ds=ImageStat.Stat(ImageChops.difference(an,bn));rawdiff=ImageChops.difference(ar,br)
  rows.append(dict(phase=phase,roi=name,raw_exact=rawdiff.getbbox() is None,srgb_exact=all(x[1]==0 for x in ds.extrema),srgb_mae=sum(ds.mean)/3,srgb_max=max(x[1] for x in ds.extrema)))
r=dict(scope='Observed control against original13 baseline; no general zero observer-effect guarantee.',baseline_report_sha256=hashlib.sha256((baseline/'report.json').read_bytes()).hexdigest(),candidate_report_sha256=hashlib.sha256((candidate/'report.json').read_bytes()).hexdigest(),all12_raw_and_srgb_exact=all(x['raw_exact'] and x['srgb_exact'] for x in rows),rows=rows)
output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({'all12_exact':r['all12_raw_and_srgb_exact'],'differences':[x for x in rows if not x['srgb_exact']]}))
