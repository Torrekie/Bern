#!/usr/bin/env python3
"""Exact tuple geometry of retained snapshots; no color semantics or direction fitting."""
from pathlib import Path
import base64,datetime,hashlib,importlib.util,json,struct,sys,traceback,zlib
D=Path(__file__).resolve().parent
ROOT=D.parent.parent
BASE=ROOT/'outputs/Bern/Docs/Evidence/macOS14-hero-float-40091326190'
EXPECTED_POLICY='e89de719d300dc83faa46e186abd71ae4b5d19315351df87340133e3f64d48b7'
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def jload(p):
 need(p.stat().st_size<=2*1024*1024,'oversized JSON');return json.loads(p.read_bytes())
def read_input(p,expected=None):
 data=p.read_bytes();h=sha(data)
 if expected is not None:need(h==expected,'input hash '+str(p))
 inputs[str(p.relative_to(ROOT))]={'sha256':h,'bytes':len(data)};return data

def png16(p,expected):
 data=read_input(p,expected);need(data[:8]==b'\x89PNG\r\n\x1a\n','PNG signature')
 pos=8;ids=[];ihdr=None;end=False
 while pos<len(data):
  need(pos+12<=len(data),'PNG chunk truncation');n=struct.unpack_from('>I',data,pos)[0];typ=data[pos+4:pos+8];pay=data[pos+8:pos+8+n]
  need(pos+12+n<=len(data),'PNG payload truncation');crc=struct.unpack_from('>I',data,pos+8+n)[0]
  need(zlib.crc32(typ+pay)&0xffffffff==crc,'PNG CRC')
  if typ==b'IHDR':need(ihdr is None and pos==8,'PNG IHDR sequence');ihdr=struct.unpack('>IIBBBBB',pay)
  if typ==b'IDAT':ids.append(pay)
  if typ==b'IEND':need(n==0 and pos+12==len(data),'PNG end');end=True
  pos+=12+n
 need(end and ihdr==(640,360,16,6,0,0,0),'PNG 640x360 RGBA16 noninterlaced contract')
 row=640*8;length=(row+1)*360;dec=zlib.decompressobj();raw=dec.decompress(b''.join(ids),length+1)
 need(dec.eof and not dec.unused_data and not dec.unconsumed_tail and len(raw)==length,'PNG exact inflate size')
 # PNG filter method0 has5 standard per-row byte filters (W3C chapter6).
 previous=bytes(row);decoded=[];filter_counts={str(i):0 for i in range(5)}
 for y in range(360):
  typ=raw[y*(row+1)];need(0<=typ<=4,'unsupported PNG filter type');filter_counts[str(typ)]+=1
  current=bytearray(raw[y*(row+1)+1:(y+1)*(row+1)])
  for x in range(row):
   left=current[x-8] if x>=8 else 0;above=previous[x];upper_left=previous[x-8] if x>=8 else 0
   if typ==0:predictor=0
   elif typ==1:predictor=left
   elif typ==2:predictor=above
   elif typ==3:predictor=(left+above)//2
   else:
    estimate=left+above-upper_left;pa=abs(estimate-left);pb=abs(estimate-above);pc=abs(estimate-upper_left)
    predictor=left if pa<=pb and pa<=pc else (above if pb<=pc else upper_left)
   current[x]=(current[x]+predictor)&255
  previous=bytes(current);decoded.append(previous)
 active=b''.join(decoded)
 need(all(active[i:i+2]==b'\xff\xff' for i in range(6,len(active),8)),'source alpha16 not opaque')
 return active,filter_counts

def scaled_box(rect,w,h,direction):
 vals=[]
 for value,actual,source in [(rect['x'],w,640),(rect['y'],h,360),(rect['x']+rect['width'],w,640),(rect['y']+rect['height'],h,360)]:
  need(type(value) is int and value*actual%source==0,'noninteger fixed coordinate');vals.append(value*actual//source)
 x0,y0,x1,y1=vals
 if direction=='bottom-up':y0,y1=h-y1,h-y0
 need(0<=x0<x1<=w and 0<=y0<y1<=h,'box outside active raster');return [x0,y0,x1,y1]
def rows_at(data,w,h,box):
 x0,y0,x1,y1=box;need(len(data)==w*h*8,'geometry only supports no-padding active raster')
 return [data[(y*w+x0)*8:(y*w+x1)*8] for y in range(y0,y1)]
def tuple_count(rows):return len({r[i:i+8] for r in rows for i in range(0,len(r),8)})
def evaluate(data,w,h,direction,spec,policy):
 flats=[]
 for patch in spec['patches']:
  box=scaled_box(patch['interior_source_rect'],w,h,direction);rs=rows_at(data,w,h,box);count=tuple_count(rs)
  flats.append({'source_region_name_as_geometry_label':patch['name'],'raw_box_half_open':box,'pixel_count':len(rs)*len(rs[0])//8,'distinct_complete_pixel_tuples':count,'pass':count==1})
 markers=[]
 for index,rect in enumerate(policy['ramp_marker_bands_source_rects']):
  box=scaled_box(rect,w,h,direction);rs=rows_at(data,w,h,box);same=all(row==rs[0] for row in rs)
  bins=[]
  for sx0,sx1 in policy['ramp_bin_x_source_intervals']:
   br={'x':sx0,'y':rect['y'],'width':sx1-sx0,'height':rect['height']};b=scaled_box(br,w,h,direction);first=rows_at(data,w,h,b)[0];count=tuple_count([first])
   bins.append({'source_x_interval':[sx0,sx1],'raw_box_half_open':b,'first_row_distinct_complete_tuples':count,'varies_within_predeclared_bin':count>=2})
  marker=same and all(x['varies_within_predeclared_bin'] for x in bins)
  markers.append({'source_band_index':index,'raw_box_half_open':box,'row_count':len(rs),'all_rows_bit_identical':same,'whole_band_distinct_complete_tuples':tuple_count(rs),'bins':bins,'ramp_marker_pass':marker})
 passed=all(x['pass'] for x in flats) and [x['source_band_index'] for x in markers if x['ramp_marker_pass']]==[2]
 return {'direction':direction,'pass':passed,'flat_interiors':flats,'three_fixed_bands':markers}

inputs={}
def main():
 need(len(sys.argv)==2,'usage structure.py fresh-output-child');out=Path(sys.argv[1]).resolve()
 need(out.parent==D and not out.exists(),'fresh direct child required');out.mkdir()
 result={'complete':False,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'policy_sha256':None,'direction_selection_uses_only_complete_tuple_geometry':True,'numeric_or_RGBA_semantics_emitted':False}
 try:
  policy=jload(D/'policy.json');need(sha(read_input(D/'policy.json'))==EXPECTED_POLICY,'predeclared policy changed');result['policy_sha256']=EXPECTED_POLICY
  for line in (D/'PREDECLARED-SHA256SUMS').read_text().splitlines():
   h,n=line.split('  ',1);read_input(D/n,h)
  spec=jload(D/'atlas-rois.json');read_input(D/'structure.py')
  modspec=importlib.util.spec_from_file_location('frozen_float',D/'analyze_float.py');frozen=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(frozen)
  atlas_path=ROOT/spec['provenance']['atlas_report_path'];atlas=jload(atlas_path);read_input(atlas_path,spec['provenance']['atlas_report_sha256'])
  need(atlas['success'] is True,'source atlas runtime failed');need([p['name'] for p in atlas['patches']]==[p['name'] for p in spec['patches']],'atlas patch name/order changed')
  need(all(a['source_rect']==s['source_rect'] for a,s in zip(atlas['patches'],spec['patches'])) and atlas['ramp']['source_rect']==spec['ramp']['source_rect'],'atlas geometry changed')
  sources=[];source_data=[]
  for source in spec['sources']:
   p=BASE/'same-binary-13-14/package/assets'/source['png'];data,filter_counts=png16(p,source['png_sha256']);source_data.append(data)
   candidates=[evaluate(data,640,360,x,spec,policy) for x in policy['candidates']]
   good=[x['direction'] for x in candidates if x['pass']]
   sources.append({'source_name':source['name'],'png_sha256':source['png_sha256'],'decoded_RGBA16BE_active_sha256':sha(data),'png_row_filter_counts':filter_counts,'candidates':candidates,'selected_direction':good[0] if len(good)==1 else 'unknown'})
  source_equal=source_data[0]==source_data[1];result['source_atlas']={'sources':sources,'both_active_decoded_buffers_exact':source_equal}
  need(source_equal and all(x['selected_direction']=='top-down' for x in sources),'source structure contract not verified; do not inspect snapshot data')
  old_inventory={n:h for h,n in (line.split('  ',1) for line in (BASE/'SHA256SUMS').read_text().splitlines())};read_input(BASE/'SHA256SUMS')
  records=[]
  for major in [13,14]:
   rp=BASE/f'same-binary-13-14/runtime{major}/on/report.json';rel=str(rp.relative_to(BASE));report_data=read_input(rp,old_inventory[rel]);report=json.loads(report_data)
   need(frozen.validate_runtime(report)==major,'saved runtime/host gates');capture=report['snapshot_float_capture']
   need(capture['selected']=='on' and capture['success'] and capture['error'] is None and capture['row_direction']=='unverified','actual raw export gate')
   need(capture['provider_copy_calls']==2 and capture['total_raw_bytes']<=4194304 and capture['fixture_retained_images_after_export']==0,'actual raw export bounds')
   need(len(capture['records'])==2 and {x['key'] for x in capture['records']}==set(frozen.KEYS),'raw identities')
   for source in spec['sources']:
    ledger=report['cache_before'][source['png']];need(ledger['file_sha256']==source['png_sha256'] and ledger['orientation']=='up','actual source ledger')
   for rec in capture['records']:
    obs=next(x for x in report['snapshot_cgimage_observations'] if x['key']==rec['key']);p,data=frozen.validate_record(rec,obs,rp.parent)
    read_input(p,old_inventory[str(p.relative_to(BASE))]);need(rec['bytes_per_row']==rec['width']*8,'no-padding active bytes');need(obs['color_space_name']=='kCGColorSpaceExtendedSRGB','source RGB space')
    candidates=[evaluate(data,rec['width'],rec['height'],x,spec,policy) for x in policy['candidates']];good=[x['direction'] for x in candidates if x['pass']]
    records.append({'actual_os_major':major,'key':rec['key'],'raw_sha256':rec['sha256'],'size':[rec['width'],rec['height']],'candidates':candidates,'selected_direction':good[0] if len(good)==1 else 'unknown','passing_candidate_count':len(good),'semantic_approval':'pending independent structure and lane review'})
  result.update(records=records,complete=True,all4_directions_unique=all(x['passing_candidate_count']==1 for x in records),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 except Exception as e:
  result['error']=str(e);(out/'error.log').write_text(traceback.format_exc())
 finally:
  result['inputs']=inputs;result['script_sha256']=sha((D/'structure.py').read_bytes());encoded=json.dumps(result,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n';need(len(encoded.encode())<=128*1024,'bounded structure result');(out/'geometry.json').write_text(encoded)
  (out/'INPUT-SHA256SUMS').write_text(''.join(f"{v['sha256']}  {k}\n" for k,v in sorted(inputs.items())))
 print(json.dumps({k:result[k] for k in ['complete','all4_directions_unique','error'] if k in result}))
 return 0 if result['complete'] else 1
if __name__=='__main__':raise SystemExit(main())
