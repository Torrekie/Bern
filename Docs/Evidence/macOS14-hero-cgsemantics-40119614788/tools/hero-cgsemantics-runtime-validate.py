import base64,hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]).resolve(); mode=sys.argv[2]; major=int(sys.argv[3]); d=json.loads((p/'report.json').read_text())
assert d['success'] is True,d.get('error')
assert d['expected_os_major']==major and d['actual_os_major']==major
assert d['completed_phases']==2 and len(d['captures'])==2
assert d['cache_unchanged'] is True and d['metal_count_before_cleanup']==0
assert d['frontmost_before']==d['frontmost_after']
assert all(v is False for k in ('normal_before','normal_after') for v in d[k].values())
assert {s['key'] for s in d['snapshots']}=={'baseline-body-named','baseline-body-custom'}
observations=d['snapshot_cgimage_observations']
assert d['snapshot_cgimage_observations_scope']=='before_existing_window_teardown'
assert len(observations)==2
assert {o['key'] for o in observations}=={'baseline-body-named','baseline-body-custom'}
assert isinstance(d['snapshot_cgimage_cleanup_observations'],list)
positive=('width','height','bits_per_component','bits_per_pixel','bytes_per_row')
nonnegative=('bitmap_info_raw','alpha_info_raw','byte_order_raw','pixel_format_raw')
flags=('wide_gamut_rgb','uses_extended_range','uses_itur2100_tf','is_pq_based','is_hlg_based')
for o in observations:
    assert o['observation_site']=='snapshot_descriptors_before_NSImage_color_metadata_after_window_teardown'
    assert o['color_space_metadata_stage']=='after_existing_window_teardown'
    assert all(type(o[n]) is int and o[n]>0 for n in positive)
    assert all(type(o[n]) is int and o[n]>=0 for n in nonnegative)
    assert type(o['float_components']) is bool and type(o['color_space_present']) is bool
    assert o['color_space_name'] is None or isinstance(o['color_space_name'],str)
    if o['color_space_present']:
        assert type(o['color_space_model_raw']) is int
        assert type(o['color_space_components']) is int and o['color_space_components']>=0
        assert all(type(o[n]) is bool for n in flags)
        assert type(o['icc_present']) is bool
        assert type(o['icc_byte_count']) is int and o['icc_byte_count']>=0
        if o['icc_present']:
            assert o['icc_byte_count']>0 and len(o['icc_sha256'])==64
            assert all(c in '0123456789abcdef' for c in o['icc_sha256'])
            if o['icc_byte_count']<=65536:
                profile=base64.b64decode(o['icc_base64'],validate=True)
                assert len(profile)==o['icc_byte_count']
                assert hashlib.sha256(profile).hexdigest()==o['icc_sha256']
                assert o['icc_base64_omitted_reason'] is None
            else:
                assert o['icc_base64'] is None
                assert o['icc_base64_omitted_reason']=='profile_exceeds_65536_bytes'
        else:
            assert o['icc_byte_count']==0 and o['icc_sha256'] is None
            assert o['icc_base64'] is None and o['icc_base64_omitted_reason']=='no_icc_profile'
    else:
        assert all(o[n] is None for n in ('color_space_model_raw','color_space_components','icc_present','icc_byte_count','icc_sha256','icc_base64','icc_base64_omitted_reason',*flags))
assert [c['phase'] for c in d['captures']]==['progress-0','progress-1']
for c in d['captures']:
    assert c['consecutive_equal_buffers']>=5 and c['live_metal_count']==0
    assert c['key'] is False and c['active'] is False
    assert c['manager']['flight_count']==0 and c['manager']['timer_exists'] is False
    assert c['capture_icc_sha256']!='absent'
wanted={'source-named-pq.png':'3efb40d42933dade20c11d2654d86afd25b1e02c838d9b080bb1233faa36da5b','source-ffb-icc.png':'fa3fdc43d91518c145c08b01ba6181ec063c68158e57d312a1ff942571c2a12e'}
assert set(d['cache_before'])==set(wanted)
assert all(d['cache_before'][n]['file_sha256']==s and d['cache_before'][n]['orientation']=='up' for n,s in wanted.items())
assert len(list(p.glob('*.png')))==2
receipt=json.loads((p/'run-receipt.json').read_text())
assert receipt['exit_code']==0 and not receipt.get('wrapper_timeout',False)
assert all(c['owner_pid']==receipt['own_pid'] for c in d['captures'])
f=d['snapshot_float_capture']
assert f['requested']==mode and f['selected']==mode
assert f['primary_observation_count']==2 and f['success'] is True and f['error'] is None
assert type(f['cleanup_observation_count']) is int
assert f['fixture_retained_images_after_export']==0
assert f['provider_copy_calls']==(2 if mode=='on' else 0)
assert f['retained_primary_peak_count']==(2 if mode=='on' else 0)
records=f['records']
assert len(records)==(2 if mode=='on' else 0)
assert len(list(p.glob('*.bin')))==len(records)
if mode=='on':
    assert {r['key'] for r in records}=={'baseline-body-named','baseline-body-custom'}
    assert sum(r['byte_count'] for r in records)<=4194304
    for r in records:
        q=Path(r['file']); assert not q.is_absolute() and '..' not in q.parts
        data=(p/q).read_bytes()
        assert len(data)==r['byte_count']==r['bytes_per_row']*r['height']
        assert hashlib.sha256(data).hexdigest()==r['sha256']
        assert (r['bits_per_component'],r['bits_per_pixel'],r['bitmap_info_raw'],r['alpha_info_raw'],r['byte_order_raw'],r['pixel_format_raw'])==(16,64,4353,1,4096,0)
        assert r['float_components'] is True and r['export_stage']=='after_existing_window_teardown'

# Append-only isolation gate; all original float/native/ICC assertions above are preserved.
backing=d['backing_observation']
assert backing['requested']==backing['selected']=='off'
assert backing['success'] is True and backing['error'] is None
assert backing['records']==[] and backing['root'] is None and backing['overlay'] is None
import math,re,struct
def finite_nonnegative(value):
    assert type(value) in (int,float) and math.isfinite(value) and value>=0
if mode=='on':
    for r in records:
        s=r['drawing_semantics']
        assert isinstance(s,dict) and set(s)=={'stage','success','error','rendering_intent_raw',
            'is_mask','should_interpolate','color_space_model_raw','color_space_components',
            'decode_present','decode_count','decode_values','decode_value_bits','decode_values_read',
            'decode_nonfinite_index','observed_at_uptime_seconds','observation_elapsed_seconds'}
        assert s['stage']=='after_existing_window_teardown_before_primary_release'
        assert s['success'] is True and s['error'] is None
        assert type(s['rendering_intent_raw']) is int and s['rendering_intent_raw']>=0
        assert s['is_mask'] is False and type(s['should_interpolate']) is bool
        assert type(s['color_space_model_raw']) is int and s['color_space_model_raw']==1
        assert type(s['color_space_components']) is int and s['color_space_components']==3
        assert type(s['decode_present']) is bool
        count=6 if s['decode_present'] else 0
        assert type(s['decode_count']) is int and s['decode_count']==count
        assert type(s['decode_values_read']) is int and s['decode_values_read']==count
        assert isinstance(s['decode_values'],list) and len(s['decode_values'])==count
        assert isinstance(s['decode_value_bits'],list) and len(s['decode_value_bits'])==count
        assert s['decode_nonfinite_index'] is None
        for value,bits in zip(s['decode_values'],s['decode_value_bits']):
            assert type(value) in (int,float) and math.isfinite(value)
            assert isinstance(bits,str) and re.fullmatch(r'0x[0-9a-f]{16}',bits)
            decoded=struct.unpack('>d',struct.pack('>Q',int(bits,16)))[0]
            assert math.isfinite(decoded) and decoded==value
            # Signed zero remains in the exact bits field; JSON numeric sign is not inferred.
        for value in (s['observed_at_uptime_seconds'],s['observation_elapsed_seconds'],
                      r['provider_read_at_uptime_seconds'],f['released_at_uptime_seconds']):
            finite_nonnegative(value)
        assert s['observed_at_uptime_seconds']>=r['provider_read_at_uptime_seconds']
        assert s['observed_at_uptime_seconds']+s['observation_elapsed_seconds']<=f['released_at_uptime_seconds']

