#!/usr/bin/env python3
"""Offline review of actual downloaded14 capture; never invokes UI or CI."""
from pathlib import Path
from collections import Counter
import hashlib,json,math,struct

ROOT=Path(__file__).resolve().parent.parent.parent
OUT=Path(__file__).resolve().parent
RUN=ROOT/'work/picture-grid-width-run'
RAW=RUN/'raw'
OLD=ROOT/'work/picture-scene-observed14/raw'
CONTROL=ROOT/'outputs/Bern/Docs/Evidence/macOS14-picture-scene-control-40135147500/raw'
H='7dddc256ccdc006d746766af6ef3d7f68d887547'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def tuple4(d):return [d[k]for k in ['x','y','width','height']]
def finite_rects(d):
    n=0
    if isinstance(d,dict):
        if all(k in d for k in ['x','y','width','height']):
            assert all(isinstance(d[k],(int,float))and math.isfinite(d[k])for k in ['x','y','width','height']);n+=1
        for v in d.values():n+=finite_rects(v)
    elif isinstance(d,list):
        for v in d:n+=finite_rects(v)
    return n
def signature(e):
    g=next((x for x in e['ancestors_nearest_first']if x['class']=='SwiftUI._NSGraphicsView'),None)
    s=e['nearest_enclosing_scroll_view']
    return {k:e[k]for k in ['label','callback','resolved_size','swiftui_global_frame','environment_at_probe','probe_bounds_size_equals_resolved_size']}|{
      'probe':{k:e['probe'][k]for k in ['bounds_local','bounds_in_window_base','frame_in_superview','probe_bounds_in_node']},
      'graphics':{k:g[k]for k in ['bounds_local','bounds_in_window_base']}if g else None,
      'scroll':{key:s[key]['bounds_local']for key in ['clip_view','document_view']}if s else None}
def main():
    result=load(RAW/'result.json');baseline=load(OLD/'result.json')
    assert result['success']and result['source_sha']=='9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0'and result['harness_sha']==H
    assert result['os']=='Version 14.8.9 (Build 23J631)'and result['appearance_profile']=='normal'
    assert not any(result['system_preferences'][k]for k in ['reduce_motion','reduce_transparency','increase_contrast'])
    assert len(result['windows'])==13 and len(result['checks'])==18 and all(c['passed']for c in result['checks'])
    assert len(result['commands'])==80
    assert [(i+1,r['status'])for i,r in enumerate(result['commands'])if r['status']!=0]==[(1,3),(72,3)]
    assert all(result['commands'][i-1]['arguments']==['sessions']for i in [1,72])
    pngs=[]
    for w in result['windows']:
        assert w['bounds_points']['Width']==920 and w['bounds_points']['Height']==668
        assert [w['pixel_width'],w['pixel_height']]==[920,668]
        name=w['png'];raw=(RAW/name).read_bytes()
        assert raw==(OLD/name).read_bytes()==(CONTROL/name).read_bytes()
        pngs.append({'name':name,'sha256':sha(RAW/name),'bytes':len(raw),'old_observed_and_control_exact':True})
    layout=next(w for w in result['windows']if w['png']=='images-layout-light.png')
    assert layout['pid']==1532 and layout['window_number']==25 and layout['session_windows'][0]['focused']
    geometry_path=RAW/'observer/picture-observer-1532.json';geometry=load(geometry_path);events=geometry['events']
    old_geometry=load(OLD/'observer/picture-observer-1926.json');old_events=old_geometry['events']
    assert geometry['schema']=='bern_picture_public_geometry_v1'and geometry['end_state']=='not_observed'and geometry['pid']==1532
    assert len(events)==49<geometry['event_limit']==256 and geometry_path.stat().st_size<geometry['file_byte_limit']==524288
    assert [e['sequence']for e in events]==list(range(49))
    assert len(set(e['label']for e in events))==21
    assert all(math.isfinite(e['observed_uptime_seconds'])and e['observed_uptime_seconds']>0 for e in events)
    assert all(a['observed_uptime_seconds']<b['observed_uptime_seconds']for a,b in zip(events,events[1:]))
    assert all(e['window']['number']==25 and e['window']['is_key']and e['window']['is_main']and e['window']['is_visible']and e['window']['backing_scale_factor']==1 for e in events)
    assert all([e['window']['frame_in_screen_bottom_left'][k]for k in ['width','height']]==[920,668]for e in events)
    assert all(e['probe_bounds_size_equals_resolved_size']==all(e['probe']['bounds_local'][k]==e['resolved_size'][k]for k in ['width','height'])for e in events)
    assert len({json.dumps(e['environment_at_probe'],sort_keys=True)for e in events})==1
    keyed={(e['label'],e['callback']):signature(e)for e in events};old_keyed={(e['label'],e['callback']):signature(e)for e in old_events}
    assert len(keyed)==len(old_keyed)==49 and keyed==old_keyed
    changed_order=[{'sequence':i,'new_label':a['label'],'old_label':b['label'],'callback':a['callback']}for i,(a,b)in enumerate(zip(events,old_events))if (a['label'],a['callback'])!=(b['label'],b['callback'])]
    width_path=RAW/'observer/picture-grid-width-1532.json';width=load(width_path);rows=width['events']
    assert width['schema']=='bern_picture_grid_width_action_v1'and width['pid']==1532 and width['end_state']=='not_observed'
    assert len(rows)==3<width['event_limit']==64 and width_path.stat().st_size<width['file_byte_limit']==65536 and not width['event_limit_reached']
    assert [r['sequence']for r in rows]==[0,1,2]and [r['minimum']for r in rows]==[140,192,120]
    origin=rows[0]['callback_entered_uptime_seconds']
    wsummary=[]
    for r in rows:
        assert r['old_stored_width']==0 and r['old_stored_width_bits']=='0000000000000000'
        assert r['measured_width']==719 and r['measured_width_bits']==struct.pack('>d',719.0).hex()
        assert r['measured_is_finite']and r['original_guard_would_pass']and r['on_main_thread']and r['columns_captured_from_body']==1
        assert all(math.isfinite(r[k])for k in ['callback_entered_uptime_seconds','recorded_after_action_uptime_seconds','minimum','gap','row_gap'])
        assert r['callback_entered_uptime_seconds']<=r['recorded_after_action_uptime_seconds']
        assert r['gap']==r['row_gap']==(12 if r['minimum']==140 else 16)
        derived=max(1,int((719+r['gap'])/max(1,r['minimum']+r['gap'])))
        wsummary.append(r|{'entry_ms_from_first_width_entry':(r['callback_entered_uptime_seconds']-origin)*1000,
          'pre_IO_record_ms_from_first_width_entry':(r['recorded_after_action_uptime_seconds']-origin)*1000,
          'entry_to_pre_IO_record_ms':(r['recorded_after_action_uptime_seconds']-r['callback_entered_uptime_seconds'])*1000,
          'columns_derived_from_measured_not_observed':derived})
    assert all(a['recorded_after_action_uptime_seconds']<b['callback_entered_uptime_seconds']for a,b in zip(rows,rows[1:]))
    assert rows[-1]['recorded_after_action_uptime_seconds']<events[0]['observed_uptime_seconds']
    timeline=[]
    for e in events:
        if e['label']in ['form-root','images-grid','hdr-grid']:
            g=next(x for x in e['ancestors_nearest_first']if x['class']=='SwiftUI._NSGraphicsView')
            timeline.append({'sequence':e['sequence'],'label':e['label'],'callback':e['callback'],
              'uptime_seconds':e['observed_uptime_seconds'],'ms_from_first_width_entry':(e['observed_uptime_seconds']-origin)*1000,
              'resolved_size':e['resolved_size'],'swiftui_global_frame':tuple4(e['swiftui_global_frame']),
              'native_probe_window_base':tuple4(e['probe']['bounds_in_window_base']),
              'nearest_graphics_ancestor_window_base':tuple4(g['bounds_in_window_base']),
              'probe_size_equals_resolved':e['probe_bounds_size_equals_resolved_size']})
    receipts=[]
    for name,job in [('build','build-job.log'),('raw','capture-job.log')]:
        p=RUN/(name+'.download.json');d=load(p);artifact=d['artifact'];log=(RUN/job).read_text()
        assert d['api_digest_verified']and d['archive_deleted']and d['outer_zip_digest']==artifact['digest']
        assert d['outer_zip_bytes']==artifact['size_in_bytes']
        assert artifact['workflow_run']['id']==40144017622 and artifact['workflow_run']['head_sha']==H
        assert artifact['digest'].removeprefix('sha256:')in log and str(artifact['id'])in log
        receipts.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'artifact':artifact,'outer_zip_bytes':d['outer_zip_bytes'],'outer_zip_digest':d['outer_zip_digest'],
          'api_digest_verified_in_actual_root_receipt':True,'server_upload_log_digest_matches':True,'reviewer_rehashed_deleted_ZIP':False})
    report={
      'verdict':'actual14_selected13PNG_125_147_and_21point_plus_width_prefix_gates_pass',
      'run_id':40144017622,'harness_sha':H,'result_sha256':sha(RAW/'result.json'),
      'normal_three_flags_false':True,'commands':80,'startup_sessions_status3_indices':[1,72],'remaining78_commands_zero':True,'checks18_all_pass':True,
      'PNG_originals':pngs,'card_geometry_from_exact_original_baseline':{'images_half_open_points':[161,98,900,223],'images_height':125,'HDR_half_open_points':[161,321,900,468],'HDR_height':147,'new_threshold_or_resampling':False},
      'artifact_download_receipts':receipts,
      'geometry_packet':{'path':str(geometry_path.relative_to(ROOT)),'sha256':sha(geometry_path),'bytes':geometry_path.stat().st_size,'events':49,'labels':21,'finite_rectangles_checked':finite_rects(geometry),
        'callbacks':dict(Counter(e['callback']for e in events)),'end_state':geometry['end_state'],'per_label_callback_geometry_matches_old':True,
        'global_sequence_changes_from_old':changed_order,'environment':events[0]['environment_at_probe'],
        'probe_size_match_counts':dict(Counter(str(e['probe_bounds_size_equals_resolved_size'])for e in events))},
      'width_packet':{'path':str(width_path.relative_to(ROOT)),'sha256':sha(width_path),'bytes':width_path.stat().st_size,'events':3,'pid':1532,'no_written_cap':True,'end_state':width['end_state'],'rows':wsummary},
      'geometry_timeline_relative_to_first_width_entry':timeline,
      'last_width_pre_IO_record_to_first_geometry_ms':(events[0]['observed_uptime_seconds']-rows[-1]['recorded_after_action_uptime_seconds'])*1000,
      'interpretation_limits':[
       'Three records are one bounded successful serialized prefix. Configurations hint at three source callsites; no instance/remount identity or terminal coverage is available.',
       'Body-captured columns1 are consistent with initialwidth0, while measured719 predicts4/3/5. Those predictions are derived, not observed rendered column counts or evidence of a later body evaluation.',
       'All width pre-IO record timestamps precede all retained geometry attachment callbacks. This bounds observer callback ordering in this process, not when SwiftUI performed its internal layout, committed a presentation frame, or captured the PNG.',
       'Entry-to-record intervals include original state action, singleton setup/lock and scheduling before serialization. They are not complete I/O cost, closure-return latency, animation timing or a cross-host responsiveness comparison.',
       'New and old14 per-label/callback geometry states are equal, but late Gainmap/PQ update groups switch global order. The13PNG files remain byte-identical; this ordering difference alone cannot identify the card-height cause.',
       'The14 first-grid resolved105→109/native105 mismatch persists. Last HDR global335 does not turn native higher geometry into equivalence. Both packets retain end_state not_observed and no synchronized terminal/presentation state.',
       'Outer ZIP verification is grounded in actual root download receipts cross-checked against server upload logs. DeletedZIP bytes were not independently rehashed by this reviewer. Native binary/source audit belongs to the separate reviewer.',
       'No13 width-trace result has been reviewed here yet. Equal or different future width histories cannot by themselves establish a unique root cause.'
      ],
      'reviewer_scope':'Offline original hashes/JSON/logs only. No UI, CI, compiler, source changes, new pixel thresholds or large copy.'}
    p=OUT/'review.json'
    with p.open('x')as f:json.dump(report,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({'report':str(p),'sha256':sha(p),'verdict':report['verdict'],'width_post_to_geometry_ms':report['last_width_pre_IO_record_to_first_geometry_ms']}))

if __name__=='__main__':main()
