from pathlib import Path
import hashlib,io,json,math
from PIL import Image,ImageCms,ImageChops,ImageStat
B=Path.cwd()/'work/native-pq-hero-coordinator-ci-40103369574';D=Path(__file__).resolve().parent
assert not (D/'summary.json').exists()
result={'scope':'Original PNG/ICC/opaque endpoint ROI comparison and midflight visible-pixel bounds only; no synchronized frame/color/whole-animation acceptance or root-cause attribution.','hosts':{}}
for major in [13,14]:
 P=B/f'runtime{major}';report=json.loads((P/'report.json').read_text());rows={};inputhash={}
 for c in report['captures']:
  f=P/c['png'];raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();assert h==c['png_sha256'];inputhash[str(f)]=h
  im=Image.open(io.BytesIO(raw));im.load();icc=im.info.get('icc_profile');assert icc
  rgb=im.convert('RGB');norm=ImageCms.profileToProfile(rgb,ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0)
  rows[c['phase']]={'capture':c,'raw':rgb,'srgb':norm,'image':im,'icc':hashlib.sha256(icc).hexdigest()}
 def box(r):
  edges=[r['x'],r['y'],r['x']+r['width'],r['y']+r['height']];assert all(abs(v-round(v))<1e-6 for v in edges);return tuple(round(v) for v in edges)
 before=rows['before'];after=rows['settled'];bp=box(before['capture']['rois']['source']['screenshot_pixels']);ap=box(after['capture']['rois']['destination']['screenshot_pixels']);assert bp[2]-bp[0]==ap[2]-ap[0] and bp[3]-bp[1]==ap[3]-ap[1]
 def opaque(row,b):return row['image'].mode!='RGBA' or row['image'].getchannel('A').crop(b).getextrema()==(255,255)
 def nonwhite(im):
  pixels=list(im.getdata());count=sum(p!=(255,255,255) for p in pixels)
  return {'nonwhite_pixels':count,'total_pixels':len(pixels),'fraction':count/len(pixels),'rgb_stddev':ImageStat.Stat(im).stddev}
 endpoint={}
 for mode in ['raw','srgb']:
  x=before[mode].crop(bp);y=after[mode].crop(ap);df=ImageChops.difference(x,y);st=ImageStat.Stat(df)
  endpoint[mode]={'mae':sum(st.mean)/3,'max':max(v[1] for v in st.extrema),'exact':df.getbbox() is None,'before':nonwhite(x),'settled':nonwhite(y)}
 mid=rows['in-flight'];cap=mid['capture'];scale=before['capture']['rois']['source']['screenshot_pixels']['width']/320
 # Root content starts at the source's known root-point offset, using actual conversion.
 bpr=before['capture']['rois']['source']['screenshot_pixels'];rx=bpr['x']-16*scale;ry=bpr['y']-24*scale
 rootbox=(round(rx),round(ry),round(rx+1024*scale),round(ry+440*scale));content=mid['srgb'].crop(rootbox)
 bbox=ImageChops.difference(content,Image.new('RGB',content.size,(255,255,255))).getbbox()
 flight=cap['rois']['flight']['screenshot_pixels'];inset=8*scale
 interior=(math.ceil(flight['x']+inset),math.ceil(flight['y']+inset),math.floor(flight['x']+flight['width']-inset),math.floor(flight['y']+flight['height']-inset))
 trace=[{'uptime':s['uptime'],'progress':s['flights'][0]['progress'],'rect_in_root':s['flights'][0]['rect_in_root']} for s in report['samples'] if s['flights']]
 result['hosts'][str(major)]={'report_sha256':hashlib.sha256((P/'report.json').read_bytes()).hexdigest(),'png_hashes':inputhash,'embedded_icc_before_settled_identical':before['icc']==after['icc'],'endpoint_size_pixels':[bp[2]-bp[0],bp[3]-bp[1]],'opaque_before_settled':opaque(before,bp) and opaque(after,ap),'endpoint_comparison':endpoint,'midflight':{'trigger_progress':cap['trigger_progress'],'before_uptime':cap['capture_before_uptime'],'after_uptime':cap['capture_after_uptime'],'trigger_flights':cap['trigger_state']['flights'],'before_flights':cap['state_before']['flights'],'after_flights':cap['state_after']['flights'],'root_content_pixel_box':rootbox,'nonwhite_bbox_in_root_pixels':bbox,'nonwhite_bbox_root_points':None if bbox is None else [v/scale for v in bbox],'logical_flight_interior_pixel_box_inset8pt':interior,'logical_flight_interior':nonwhite(mid['srgb'].crop(interior)),'interpretation':'Nonwhite bounds depend on image content and color transform; they are not exact flight bounds or a fitted image registration.'},'first_live_trace':trace[:12]}
(D/'summary.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
for major,h in result['hosts'].items():print(major,'endpoint',h['endpoint_comparison']['srgb']['mae'],h['endpoint_comparison']['srgb']['max'],'mid content bbox points',h['midflight']['nonwhite_bbox_root_points'],'mid logical interior nonwhite',h['midflight']['logical_flight_interior']['fraction'])
