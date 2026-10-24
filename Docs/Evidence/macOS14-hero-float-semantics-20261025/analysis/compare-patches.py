#!/usr/bin/env python3
"""Compare independently located constant snapshot interiors, without display conversion."""
from pathlib import Path
import datetime,hashlib,json,math,sys
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert len(sys.argv)==2,'fresh output filename required'
out=Path(sys.argv[1]).resolve();assert out.parent==D and not out.exists()
g=json.loads((D/'result/geometry.json').read_text());assert g['complete'] and g['all4_directions_unique']
known={};inputs={}
for host in [13,14]:
 p=D/f'host{host}-known/analysis.json';a=json.loads(p.read_text());inputs[str(p.relative_to(D))]=sha(p)
 assert a['analysis_complete'] and a['semantic_patch_values_emitted'] and a['row_direction']=='top-down' and a['runtime_validation_passed'] and a['actual_os_major']==host
 assert a['independent_orientation_evidence']['sha256']==sha(D/'result/geometry.json')
 known[host]={x['raw_record']['key']:x for x in a['records']};assert len(known[host])==2
spec=json.loads((D/'atlas-rois.json').read_text());patches=[x['name'] for x in spec['patches']];rows=[];ramps=[]
for key in ['baseline-body-named','baseline-body-custom']:
 records={h:known[h][key] for h in [13,14]}
 for h,rec in records.items():
  geo=next(x for x in g['records'] if x['actual_os_major']==h and x['key']==key)
  assert rec['raw_record']['sha256']==geo['raw_sha256'] and geo['selected_direction']=='top-down'
  assert len(rec['grounded_direction_patch_and_ramp_statistics'])==11
 for name in patches:
  regions={h:r['grounded_direction_patch_and_ramp_statistics'][name] for h,r in records.items()};means={};bits={}
  assert regions[13]['pixel_count']==11648 and regions[14]['pixel_count']==2912
  for h,r in regions.items():
   assert r['alpha_all_numeric_exactly_one']
   for c,s in r['RGBA'].items():
    assert s['unique_uint16_bit_pattern_count']==1 and len(s['all_unique_bits_hex_if_at_most_64'])==1
    assert s['finite_count']==r['pixel_count'] and s['nan_count']==s['positive_infinity_count']==s['negative_infinity_count']==0
    assert s['finite_numeric_min']==s['finite_numeric_mean']==s['finite_numeric_max'] and math.isfinite(s['finite_numeric_mean'])
   means[h]={c:s['finite_numeric_mean'] for c,s in r['RGBA'].items()};bits[h]={c:s['all_unique_bits_hex_if_at_most_64'][0] for c,s in r['RGBA'].items()}
  delta={c:means[13][c]-means[14][c] for c in 'RGBA'}
  rows.append({'key':key,'patch':name,'sample_counts':{str(h):r['pixel_count'] for h,r in regions.items()},'bits':{str(h):bits[h] for h in bits},'values':{str(h):means[h] for h in means},'numeric_13_minus_14':delta,'same_all_RGBA_bits':bits[13]==bits[14],'same_RGB_bits':all(bits[13][c]==bits[14][c] for c in 'RGB'),'max_absolute_RGB_numeric_delta':max(abs(delta[c]) for c in 'RGB')})
 for h,r in records.items():
  region=r['grounded_direction_patch_and_ramp_statistics']['gray-ramp'];ramps.append({'host':h,'key':key,'scope':'Native-resolution aggregate region only; no paired cross-host columns or numeric resampling','raw_storage_box_half_open':region['raw_storage_box_half_open'],'pixel_count':region['pixel_count'],'RGBA':region['RGBA']})
summary=[]
for key in ['baseline-body-named','baseline-body-custom']:
 subset=[x for x in rows if x['key']==key]
 summary.append({'key':key,'constant_patch_count':len(subset),'all_RGBA_bit_identical_patch_count':sum(x['same_all_RGBA_bits'] for x in subset),'changed_patches':[x['patch'] for x in subset if not x['same_RGB_bits']],'max_absolute_RGB_numeric_delta':max(x['max_absolute_RGB_numeric_delta'] for x in subset),'mean_of30_absolute_RGB_numeric_deltas':math.fsum(abs(x['numeric_13_minus_14'][c]) for x in subset for c in 'RGB')/30})
r={'complete':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'geometry_sha256':sha(D/'result/geometry.json'),'comparator_sha256':sha(Path(__file__).resolve()),'inputs':inputs,'lane_units':'Original stored premultiplied extended-sRGB binary16 numeric values, not ICC-converted display codes or nits. Alpha is exact1; no unpremultiply operation.','scope':'Independent unique tuple geometry + separate Apple SDK lane contract permit named constant patch comparisons. Native source counts differ4x; no cross-host image resizing, sample registration, bit-depth conversion, clamp, color adjustment or acceptance threshold.','summary':summary,'constant_patches':rows,'native_ramp_aggregate_only':ramps,'not_proven':['Cause of visible main color residual','Unique OS/internal renderer causation','Full image pixel equality','WindowServer/context equivalence','HDR brightness equivalence','UI or product acceptance']}
text=json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n';assert len(text.encode())<=128*1024;out.write_text(text)
print(json.dumps({'complete':True,'summary':summary}))
