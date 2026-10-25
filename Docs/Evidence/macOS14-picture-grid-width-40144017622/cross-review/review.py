#!/usr/bin/env python3
"""Offline13/14 bounded prefix comparison; no new runtime or product edits."""
from pathlib import Path
from collections import Counter
import hashlib,json,math,struct

ROOT=Path(__file__).resolve().parent.parent.parent
OUT=Path(__file__).resolve().parent
LOCAL=ROOT/'work/picture-grid-width-local13'
REMOTE=ROOT/'work/picture-grid-width-run/raw'
A2=ROOT/'work/picture-local13-ab-v2/capture-A2'
B3=ROOT/'work/picture-local13-ab-v3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def rect(d):return [d[k]for k in ['x','y','width','height']]
def finite_rects(value):
    count=0
    if isinstance(value,dict):
        if all(k in value for k in ['x','y','width','height']):
            assert all(isinstance(value[k],(int,float))and math.isfinite(value[k])for k in ['x','y','width','height']);count+=1
        for v in value.values():count+=finite_rects(v)
    elif isinstance(value,list):
        for v in value:count+=finite_rects(v)
    return count
def summary(e):
    g=next(n for n in e['ancestors_nearest_first']if n['class']=='SwiftUI._NSGraphicsView')
    s=e['nearest_enclosing_scroll_view']
    return {'callback':e['callback'],'resolved_size':e['resolved_size'],'swiftui_global_frame':rect(e['swiftui_global_frame']),
      'native_probe_local_bounds':rect(e['probe']['bounds_local']),'native_probe_window_base':rect(e['probe']['bounds_in_window_base']),
      'graphics_ancestor_local_bounds':rect(g['bounds_local']),'graphics_ancestor_window_base':rect(g['bounds_in_window_base']),
      'clip_bounds':rect(s['clip_view']['bounds_local'])if s else None,'document_bounds':rect(s['document_view']['bounds_local'])if s else None,
      'environment_at_probe':e['environment_at_probe'],'probe_size_equals_resolved':e['probe_bounds_size_equals_resolved_size']}
def prefix(d):
    rows=d['commands'];start=next(i for i,r in enumerate(rows)if 'set-language'in r['arguments']);selected=False;out=[]
    for r in rows[start:]:
        a=r['arguments'][:]
        if a[0]=='--session':a[1]='<SESSION>'
        out.append({'arguments':a,'status':r['status']})
        if '--option'in a and a[-1]=='Layout':selected=True
        if selected and a[-2:]==['window','list']:break
    return out
def packet(p,pid,window,count,scale):
    d=load(p);ev=d['events']
    assert d['pid']==pid and d['schema']=='bern_picture_public_geometry_v1'and d['end_state']=='not_observed'
    assert len(ev)==count<d['event_limit']==256 and p.stat().st_size<d['file_byte_limit']==524288
    assert [e['sequence']for e in ev]==list(range(count))and len(set(e['label']for e in ev))==21
    assert all(math.isfinite(e['observed_uptime_seconds'])and e['observed_uptime_seconds']>0 for e in ev)
    assert all(a['observed_uptime_seconds']<b['observed_uptime_seconds']for a,b in zip(ev,ev[1:]))
    assert all(e['window']['number']==window and e['window']['backing_scale_factor']==scale and e['window']['is_key']and e['window']['is_main']and e['window']['is_visible']for e in ev)
    assert all(e['probe_bounds_size_equals_resolved_size']==all(e['probe']['bounds_local'][k]==e['resolved_size'][k]for k in ['width','height'])for e in ev)
    assert len({json.dumps(e['environment_at_probe'],sort_keys=True)for e in ev})==1
    points={label:[e for e in ev if e['label']==label]for label in dict.fromkeys(e['label']for e in ev)}
    return d,points,{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size,'pid':pid,'window':window,'events':count,
      'labels':21,'finite_rectangles':finite_rects(d),'callbacks':dict(Counter(e['callback']for e in ev)),
      'probe_size_match_counts':dict(Counter(str(e['probe_bounds_size_equals_resolved_size'])for e in ev)),
      'environment':ev[0]['environment_at_probe'],'end_state':d['end_state']}
def width(p,pid,geometry):
    d=load(p);rows=d['events'];origin=rows[0]['callback_entered_uptime_seconds']
    assert d['schema']=='bern_picture_grid_width_action_v1'and d['pid']==pid and d['end_state']=='not_observed'
    assert len(rows)==3<d['event_limit']==64 and p.stat().st_size<d['file_byte_limit']==65536 and not d['event_limit_reached']
    assert [r['sequence']for r in rows]==[0,1,2]and [r['minimum']for r in rows]==[140,192,120]
    normalized=[];relative=[]
    for r in rows:
        assert r['on_main_thread']and r['original_guard_would_pass']and r['measured_is_finite']
        assert r['old_stored_width']==0 and r['old_stored_width_bits']==struct.pack('>d',0.0).hex()
        assert r['measured_width']==719 and r['measured_width_bits']==struct.pack('>d',719.0).hex()and r['columns_captured_from_body']==1
        assert r['gap']==r['row_gap']==(12 if r['minimum']==140 else 16)
        assert all(math.isfinite(r[k])for k in ['callback_entered_uptime_seconds','recorded_after_action_uptime_seconds','minimum','gap','row_gap'])
        assert r['recorded_after_action_uptime_seconds']>=r['callback_entered_uptime_seconds']
        normalized.append({k:v for k,v in r.items()if k not in ['callback_entered_uptime_seconds','recorded_after_action_uptime_seconds']})
        relative.append({'config':[r['minimum'],r['gap'],r['row_gap']],
          'entry_ms_from_own_first_width_entry':(r['callback_entered_uptime_seconds']-origin)*1000,
          'pre_IO_record_ms_from_own_first_width_entry':(r['recorded_after_action_uptime_seconds']-origin)*1000,
          'entry_to_pre_IO_record_ms':(r['recorded_after_action_uptime_seconds']-r['callback_entered_uptime_seconds'])*1000,
          'columns_derived_from_measured_not_rendered':max(1,int((719+r['gap'])/max(1,r['minimum']+r['gap'])))})
    assert all(a['recorded_after_action_uptime_seconds']<b['callback_entered_uptime_seconds']for a,b in zip(rows,rows[1:]))
    assert rows[-1]['recorded_after_action_uptime_seconds']<geometry['events'][0]['observed_uptime_seconds']
    timeline=[{'label':e['label'],'callback':e['callback'],'sequence':e['sequence'],'ms_from_own_first_width_entry':(e['observed_uptime_seconds']-origin)*1000}for e in geometry['events']if e['label']in ['form-root','images-grid','hdr-grid']]
    return normalized,{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size,'pid':pid,'rows':relative,'no_written_cap':True,'end_state':d['end_state'],
      'geometry_key_timeline':timeline,'last_width_preIO_to_first_geometry_ms':(geometry['events'][0]['observed_uptime_seconds']-rows[-1]['recorded_after_action_uptime_seconds'])*1000}
def main():
    capture=LOCAL/'capture';d=load(capture/'result.json');remote=load(REMOTE/'result.json')
    assert d['success']and d['source_sha']==remote['source_sha']=='9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0'
    assert d['harness_sha']=='unknown' # local collector is bound by separate receipts, never relabelled as remote harness
    assert len(d['commands'])==60 and len(d['windows'])==9 and len(d['checks'])==14 and all(c['passed']for c in d['checks'])
    assert [(i+1,r['status'],r['arguments'])for i,r in enumerate(d['commands'])if r['status']!=0]==[(1,3,['sessions'])]
    assert prefix(d)==prefix(load(A2/'result.json'))==prefix(remote)
    flags=['reduce_motion','reduce_transparency','increase_contrast']
    assert all(d['system_preferences'][k]==d['system_preferences_end'][k]is False for k in flags)
    images=[]
    for w in d['windows']:
        p=capture/w['png'];assert p.read_bytes()==(A2/w['png']).read_bytes()==(B3/'capture-B3'/w['png']).read_bytes()
        assert [w['pixel_width'],w['pixel_height']]==[1840,1336]
        assert w['bounds_points']['Width']==920 and w['bounds_points']['Height']==668 and w['pid']==74700
        images.append({'name':w['png'],'sha256':sha(p),'bytes':p.stat().st_size,'A2_B3_original_PNG_exact':True})
    layout=d['windows'][-1];assert layout['png']=='images-layout-light.png'and layout['window_number']==10736
    owned=load(capture/'ownership.json');clean=load(capture/'cleanup-helper.json');original=load(capture/'original-front.json')
    assert owned['pid']==74700 and clean['success']and not clean['own_instance_still_running']
    assert clean['front_after_restore_before_stop']==clean['front_after']==original and original['pid']==9292
    assert all(clean['own'][k]==owned[k]for k in ['pid','bundle_id','executable_path','kernel_start'])
    assert owned['bundle_id']==d['private_bundle_id']
    release=load(LOCAL/'desktop-release.json')['structuredContent']
    assert not release['active']and release['currentFrontmostPID']==9292 and release['cursorMovedDistance']==0
    isolation=load(LOCAL/'B4/isolation.json');build=load(ROOT/'work/picture-grid-width-run/build/observer-build.json')
    assert isolation['original_gui_sha256']==build['binaries']['Showcase.app/Contents/MacOS/Showcase']['sha256']
    assert isolation['cli_sha256']==build['binaries']['bin/showcase']['sha256']
    assert isolation['sections_and_signature_storage_sizes_normalized_equal']and isolation['originals_unchanged']and not isolation['whole_GUI_bytes_equal']
    for name,a in isolation['original_machos'].items():
        b=isolation['private_machos'][name];assert a['sections']==b['sections']and a['signature_storage_sizes_normalized_sha256']==b['signature_storage_sizes_normalized_sha256']
    helper_build=load(ROOT/'work/picture-grid-width-local13-build/build.json')
    assert helper_build['success']and all(row['whole_binary_matches_previous']and row['sha256']==row['prior_A2_B3_binary_sha256']for row in helper_build['binaries'].values())
    local_geom,lp,ls=packet(LOCAL/'events-13/picture-observer-74700.json',74700,10736,21,2)
    remote_geom,rp,rs=packet(REMOTE/'observer/picture-observer-1532.json',1532,25,49,1)
    previous=load(B3/'events-B3/picture-observer-69534.json')
    oldp={e['label']:e for e in previous['events']};assert len(oldp)==21
    assert all(len(values)==1 and summary(values[0])==summary(oldp[label])for label,values in lp.items())
    assert list(lp)==list(rp)
    envdiff={k:{'local13':ls['environment'][k],'remote14':rs['environment'][k]}for k in ls['environment']if ls['environment'][k]!=rs['environment'][k]}
    assert envdiff=={'display_scale':{'local13':2,'remote14':1}}
    perlabel=[{'label':label,'local13_attachment':summary(values[0]),'remote14_first':summary(rp[label][0]),'remote14_last':summary(rp[label][-1]),'remote14_event_count':len(rp[label])}for label,values in lp.items()]
    ln,lw=width(LOCAL/'events-13/picture-grid-width-74700.json',74700,local_geom)
    rn,rw=width(REMOTE/'observer/picture-grid-width-1532.json',1532,remote_geom)
    assert ln==rn
    report={'verdict':'bounded13_14_width_prefix_equal_new_diagnostic_noninterference_pass_card_gap_unresolved_stop_width_diagnostic',
      'source_sha':d['source_sha'],'remote_run':40144017622,
      'local_capture':{'result_sha256':sha(capture/'result.json'),'success':True,'commands':60,'first_startup_sessions3_remaining59zero':True,'checks14_all_pass':True,
        'source_prefix_normalized_equal_A2_and_remote14':True,'normal_three_flags_start_end_false':True,'reported_local_harness_sha':d['harness_sha'],'originalPNG9':images},
      'cleanup_identity':{'ownership_sha256':sha(capture/'ownership.json'),'cleanup_receipt_sha256':sha(capture/'cleanup-helper.json'),'own_pid':74700,'original_front_pid':9292,'restored_before_stop':True,'owned_instance_stopped':True,'desktop_released_cursor_unchanged':True},
      'binary_identity_scope':{'isolation_receipt_sha256':sha(LOCAL/'B4/isolation.json'),'original_GUI_sha256':isolation['original_gui_sha256'],'private_GUI_sha256':isolation['private_gui_sha256'],
        'sections_and_signature_size_normalized_bytes_match_receipt':True,'whole_GUI_bytes_equal':False,'scope':'Same compiled executable code in an isolated ad-hoc signature copy. This review validates retained receipt consistency, not a fresh post-cleanup native binary audit.',
        'collector_helper_build_receipt_sha256':sha(ROOT/'work/picture-grid-width-local13-build/build.json'),'collector_helper_whole_hashes_match_previous_receipt':helper_build['binaries']},
      'card_raster_geometry_from_original_PNG_exactness':{'local13_Images':[161,98,900,227],'local13_Images_height':129,'local13_HDR':[161,325,900,472],'local13_HDR_height':147,'remote14_Images':[161,98,900,223],'remote14_Images_height':125,'remote14_HDR':[161,321,900,468],'remote14_HDR_height':147,'no_new_threshold_resampling_or_correction':True},
      'local13_geometry':ls,'remote14_geometry':rs,'local13_all21_attachment_states_equal_previous_B3':True,'environment_differences':envdiff,
      'all21_labels_full_size_frame_caption_environment_summary':perlabel,
      'normalized_width_rows_all_nontimestamp_fields_equal':True,'normalized_width_rows':ln,
      'normalized_width_rows_sha256':hashlib.sha256(json.dumps(ln,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
      'local13_width_and_relative_timeline':lw,'remote14_width_and_relative_timeline':rw,
      'interpretation_and_stop_boundary':[
       'Both bounded action prefixes contain three matching source configurations in140→192→120 order, old+0→measured719, captured1/main/guardtrue. This does not prove complete width histories or instance/remount identity.',
       'Measured719 predicts4/3/5 columns; those are derived predictions rather than observed rendered state. The matching prefix does not explain native/raster card129vs125.',
       'All width pre-I/O record times precede retained geometry callbacks on both hosts. Relative uptimes are computed against each hosts own first-width timestamp; absolute boot uptimes are not aligned. Interval differences are not responsiveness, pure logging cost or a unique causal diagnosis.',
       'Local13 has21 attachment events with probe109/ancestor129 for Images and127/147 for HDR. Remote14 has49 callbacks and persists resolved105→109/native105/ancestor125 mismatch. Different callback counts or timing alone do not identify why.',
       'All10 public environment fields are retained; only displayScale differs2vs1. Caption width37.5vs38 for Contain, fractional origins and all other full caption fields remain explicit. Probe inherited-nil font is not internal effective Text font.',
       'Both packet end states remain not_observed. No proposed size, synchronized terminal presentation state, continuous coverage, HDR luminance or full UI equivalence is established.',
       'Stop this width-action diagnostic at the planned boundary. Do not add traces, CI, UI runs, fixed row heights, negative padding or a4pt correction from this non-distinguishing prefix. The broader port remains unaccepted with the measured first-card difference intact.'
      ],
      'reviewer_scope':'Only offline retained metadata, originalPNG hash/byte comparison and bounded packet analysis. No payload needed, UI/CI/compiler/cache/product/repo mutation.'}
    p=OUT/'review.json'
    with p.open('x')as f:json.dump(report,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({'report':str(p),'sha256':sha(p),'normalized_width_sha256':report['normalized_width_rows_sha256'],'local_last_width_to_geometry_ms':lw['last_width_preIO_to_first_geometry_ms'],'remote_last_width_to_geometry_ms':rw['last_width_preIO_to_first_geometry_ms']}))

if __name__=='__main__':main()
