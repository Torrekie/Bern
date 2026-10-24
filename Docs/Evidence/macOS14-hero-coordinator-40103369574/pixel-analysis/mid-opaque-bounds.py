from pathlib import Path
import hashlib,io,json
from PIL import Image,ImageCms,ImageChops
B=Path.cwd()/'work/native-pq-hero-coordinator-ci-40103369574'
D=Path(__file__).resolve().parent
out=D/'mid-opaque-bounds.json'
assert not out.exists()
result={'scope':'Nonwhite content bounds inside a fixed 12pt geometric root inset, excluding rounded window/frame corners; not image registration, exact flight bounds, synchronized progress, or root cause. V1 whole-root bounds include rounded/transparent corners and are not interpreted.','hosts':{}}
for major in (13,14):
 p=B/f'runtime{major}'
 report=json.loads((p/'report.json').read_text())
 caps={c['phase']:c for c in report['captures']}
 c=caps['in-flight']; f=p/c['png']; data=f.read_bytes()
 assert hashlib.sha256(data).hexdigest()==c['png_sha256']
 im=Image.open(io.BytesIO(data));im.load()
 icc=im.info['icc_profile']
 srgb=ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0)
 source=caps['before']['rois']['source']['screenshot_pixels']
 s=source['width']/320;rx=source['x']-16*s;ry=source['y']-24*s
 edges=[rx+12*s,ry+12*s,rx+(1024-12)*s,ry+(440-12)*s]
 assert all(abs(v-round(v))<1e-6 for v in edges)
 box=tuple(round(v) for v in edges)
 a=im.getchannel('A').crop(box).getextrema() if im.mode=='RGBA' else [255,255]
 assert tuple(a)==(255,255)
 crop=srgb.crop(box);mask=ImageChops.difference(crop,Image.new('RGB',crop.size,(255,255,255)))
 bb=mask.getbbox()
 rootbb=None if bb is None else [(bb[0]+box[0]-rx)/s,(bb[1]+box[1]-ry)/s,(bb[2]+box[0]-rx)/s,(bb[3]+box[1]-ry)/s]
 result['hosts'][str(major)]={'report_sha256':hashlib.sha256((p/'report.json').read_bytes()).hexdigest(),'png_sha256':hashlib.sha256(data).hexdigest(),'embedded_icc_sha256':hashlib.sha256(icc).hexdigest(),'root_inset_points':12,'root_inset_screenshot_pixels':box,'inset_alpha_extrema':a,'normalized_nonwhite_bbox_root_points':rootbb,'logical_rect_at_trigger':c['trigger_state']['flights'][0]['rect_in_root'],'trigger_progress':c['trigger_progress'],'interpretation':'The bounding box covers nonwhite pixels within the opaque inset; white atlas cells can be excluded. No pixel-to-state registration or sampling synchronization is established.'}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
for major,h in result['hosts'].items():print(major,h['normalized_nonwhite_bbox_root_points'])
