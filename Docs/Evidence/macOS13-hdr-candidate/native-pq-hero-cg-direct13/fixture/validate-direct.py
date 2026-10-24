#!/usr/bin/env python3
"""Additive adapter checks after the unchanged complete float/native/ICC gate."""
from pathlib import Path
import hashlib,json,math,subprocess,sys
D=Path(__file__).resolve().parent
assert len(sys.argv)==3
p=Path(sys.argv[1]).resolve();mode=sys.argv[2];assert mode in ['default','direct']
subprocess.run([sys.executable,'-B',str(D/'validate-base.py'),str(p),'on','13'],check=True)
d=json.loads((p/'report.json').read_text());r=json.loads((p/'run-receipt.json').read_text());b=json.loads((D/'build-fingerprint.json').read_text())
assert r['mode']==mode and r['float_mode']=='on' and r['backing_mode']=='off'
assert r['binary_sha256']==b['binary_sha256']==hashlib.sha256((D/'HeroCGDirectProbe').read_bytes()).hexdigest()
assert d['activation_calls']==0 and type(d['window_seconds']) in [int,float] and math.isfinite(d['window_seconds']) and 0<d['window_seconds']<7.9
x=d['cg_direct'];assert x['requested']==x['selected']==mode and x['target']=='flight-named'
assert x['success'] is True and x['error'] is None and x['prepared'] is True
assert x['checked_phases']==[0,1] and x['post_teardown_float_success'] is True
assert x['pixel_acceptance']=='not performed; issued calls and binding gates are not visible-image proof'
a=x['associations'];assert len(a)==2 and [v['key'] for v in a]==['baseline-body-named','baseline-body-custom']
for field in ['native_image_identity','original_cgimage_identity']: assert len({v[field] for v in a})==2
assert all(v['association']=='snapshot_NSImage_created_from_this_same_renderer_return_CGImage' for v in a)
assert len(x['draws'])==2 and [v['phase'] for v in x['draws']]==[0,1]
for v in x['draws']:
 phase=v['phase'];assert v['progress']==phase and v['bounds']=={'x':0,'y':0,'width':320,'height':180}
 assert v['path']==mode and v['source_over_alphas']==[1,phase]
 assert v['native_image_identity']==a[0]['native_image_identity'] and v['original_cgimage_identity']==a[0]['original_cgimage_identity']
 assert type(x['draw_callback_counts'][str(phase)]) is int and x['draw_callback_counts'][str(phase)]>0
 if mode=='direct':
  assert v['context_observed'] is True and v['cg_draw_calls_issued']==2 and v['blend_mode']=='normal_source_over'
  assert v['local_y_flip'] is True and v['state_restore']=='paired_save_defer_restore_source_path'
 else:
  assert v['context_observed'] is False
  assert not any(k in v for k in ['cg_draw_calls_issued','blend_mode','local_y_flip','state_restore'])
assert len({v['flight_identity'] for v in x['draws']})==1
old=D.parent.parent/'outputs/Bern/Docs/Evidence/macOS14-hero-cgsemantics-40119614788/same-binary-13-14/runtime13/on'
for name in ['named','custom']:
 new=p/f'snapshot-{name}.bin'; prior=old/f'snapshot-{name}.bin';assert new.read_bytes()==prior.read_bytes()
for v in d['snapshot_float_capture']['records']:
 s=v['drawing_semantics'];assert s['rendering_intent_raw']==0 and s['is_mask'] is False and s['should_interpolate'] is True and s['decode_present'] is False
print(json.dumps({'mode':mode,'full_original_and_additive_native_gates':'PASS','raw_bytes_equal_frozen_on':True,'own_pid':r['own_pid'],'window_seconds':d['window_seconds'],'pixel_geometry_acceptance':'separate, not inferred from native gate'}))
