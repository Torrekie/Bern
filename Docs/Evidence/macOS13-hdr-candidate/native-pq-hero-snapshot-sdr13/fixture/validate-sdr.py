#!/usr/bin/env python3
"""Additive fixed-recipe assertions after unchanged native/ICC/raw semantics gates."""
from pathlib import Path
import base64,hashlib,json,math,subprocess,sys
D=Path(__file__).resolve().parent
assert len(sys.argv)==3
p=Path(sys.argv[1]).resolve();mode=sys.argv[2];assert mode in ['default','baked-named']
subprocess.run([sys.executable,'-B',str(D/'validate-base.py'),str(p),'on','13'],check=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
d=json.loads((p/'report.json').read_text());r=json.loads((p/'run-receipt.json').read_text());b=json.loads((D/'build-fingerprint.json').read_text())
assert r['mode']==mode and r['float_mode']=='on' and r['backing_mode']=='off'
assert r['binary_sha256']==b['binary_sha256']==sha(D/'HeroSnapshotSDRProbe')
assert d['activation_calls']==0 and type(d['window_seconds']) in [int,float] and math.isfinite(d['window_seconds']) and 0<d['window_seconds']<7.9
s=d['snapshot_sdr_display'];assert s['requested']==s['selected']==mode and s['success'] is True and s['error'] is None
assert s['primary_frozen'] is True and s['helper_references_cleared'] is True and s['metadata_stage']=='after_existing_window_teardown'
assert type(s['cache_hit_count']) is int and s['cache_hit_count']==0
assert type(s['cleanup_passthrough_count']) is int and s['cleanup_passthrough_count']>=0
if mode=='default':
 assert s['conversion_count']==s['context_create_count']==0 and s['records']==s['phase_checks']==[]
else:
 assert s['conversion_count']==s['context_create_count']==1 and len(s['records'])==1
 v=s['records'][0];assert v['key']=='baseline-body-named' and v['input_object_id']!=v['output_object_id']
 assert v['logical_size']==[320,180] and v['requested_tone_map_hdr_to_sdr'] is True
 assert v['actual_tone_mapping_applied']=='unknown' and v['input_color_space_override'] is False and v['deferred'] is False
 assert v['requested_output_format']=='RGBA8' and v['requested_output_color_space']=='sRGB'
 primary=next(x for x in d['snapshot_cgimage_observations'] if x['key']=='baseline-body-named')
 assert all(v['input_layout'][k]==primary[k] for k in v['input_layout'])
 w,h=primary['width'],primary['height'];assert v['input_extent']=={'x':0,'y':0,'width':w,'height':h}
 assert type(v['conversion_elapsed_seconds']) in [int,float] and math.isfinite(v['conversion_elapsed_seconds']) and 0<=v['conversion_elapsed_seconds']<d['window_seconds']
 o=v['output_metadata'];assert o['width']==w and o['height']==h and o['bits_per_component']==8 and o['bits_per_pixel']==32 and o['bytes_per_row']>=4*w and o['float_components'] is False
 assert o['color_space_present'] if 'color_space_present' in o else True
 assert o['color_space_model_raw']==1 and o['color_space_components']==3 and o['color_space_name']=='kCGColorSpaceSRGB'
 assert o['icc_present'] is True and o['icc_byte_count']>0
 profile=base64.b64decode(o['icc_base64'],validate=True);assert len(profile)==o['icc_byte_count'] and hashlib.sha256(profile).hexdigest()==o['icc_sha256']
 assert o['uses_extended_range'] is False and o['is_pq_based'] is False and o['is_hlg_based'] is False
 checks=s['phase_checks'];after=[x for x in checks if x['stage']=='after_png'];assert [x['phase'] for x in after]==[0,1]
 assert [x['phase'] for x in checks if x['stage']=='after_final_guards']==[2]
 assert {x['phase'] for x in checks if x['stage']=='before_capture'}=={0,1}
 for c in checks:
  assert c['same_from_to_display_image'] is True and c['display_nsimage_id']==v['derived_display_nsimage_id'] and c['derived_cgimage_id']==v['output_object_id']
old=D.parent.parent/'outputs/Bern/Docs/Evidence/macOS14-hero-cgsemantics-40119614788/same-binary-13-14/runtime13/on'
for key in ['named','custom']: assert (p/f'snapshot-{key}.bin').read_bytes()==(old/f'snapshot-{key}.bin').read_bytes()
for x in d['snapshot_float_capture']['records']:
 v=x['drawing_semantics'];assert v['rendering_intent_raw']==0 and v['is_mask'] is False and v['should_interpolate'] is True and v['decode_present'] is False
print(json.dumps({'mode':mode,'full_original_and_additive_native_gates':'PASS','raw_bytes_equal_frozen_on':True,'own_pid':r['own_pid'],'window_seconds':d['window_seconds'],'pixel_geometry_acceptance':'separate, not inferred from native gate','tone_mapping_applied':'unknown'}))
