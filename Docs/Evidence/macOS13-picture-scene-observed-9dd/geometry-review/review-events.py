#!/usr/bin/env python3
"""Offline bounded event schema and cross-host comparison; never invokes UI."""
from pathlib import Path
from collections import Counter
import hashlib,json,math

ROOT=Path(__file__).resolve().parent.parent.parent
OUT=Path(__file__).resolve().parent
LOCAL=ROOT/'work/picture-local13-ab-v3/events-B3/picture-observer-69534.json'
REMOTE=ROOT/'work/picture-scene-observed14/raw/observer/picture-observer-1926.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rect(d):return [d[k] for k in ['x','y','width','height']]
def finite_rects(value):
    count=0
    if isinstance(value,dict):
        if set(['x','y','width','height']).issubset(value):
            assert all(isinstance(value[k],(int,float)) and math.isfinite(value[k]) for k in ['x','y','width','height'])
            count+=1
        for child in value.values():count+=finite_rects(child)
    elif isinstance(value,list):
        for child in value:count+=finite_rects(child)
    return count

def summarize(e):
    graphics=next((n for n in e['ancestors_nearest_first'] if n['class']=='SwiftUI._NSGraphicsView'),None)
    scroll=e['nearest_enclosing_scroll_view']
    return {'sequence':e['sequence'],'callback':e['callback'],'uptime_seconds':e['observed_uptime_seconds'],
      'resolved_size':e['resolved_size'],'swiftui_global_frame':rect(e['swiftui_global_frame']),
      'native_probe_window_base':rect(e['probe']['bounds_in_window_base']),
      'native_probe_local_bounds':rect(e['probe']['bounds_local']),
      'native_probe_size_equals_resolved':e['probe_bounds_size_equals_resolved_size'],
      'nearest_graphics_ancestor_window_base':rect(graphics['bounds_in_window_base']) if graphics else None,
      'nearest_graphics_ancestor_local_bounds':rect(graphics['bounds_local']) if graphics else None,
      'clip_bounds':rect(scroll['clip_view']['bounds_local']) if scroll else None,
      'document_bounds':rect(scroll['document_view']['bounds_local']) if scroll else None,
      'environment_at_probe':e['environment_at_probe']}

def packet(path,expected_pid,expected_window,count):
    data=json.loads(path.read_text());events=data['events']
    assert data['end_state']=='not_observed' and data['schema']=='bern_picture_public_geometry_v1'
    assert data['pid']==expected_pid and len(events)==count
    assert len(events)<data['event_limit']==256 and path.stat().st_size<data['file_byte_limit']==524288
    assert [e['sequence']for e in events]==list(range(count))
    assert all(math.isfinite(e['observed_uptime_seconds']) and e['observed_uptime_seconds']>0 for e in events)
    assert all(a['observed_uptime_seconds']<b['observed_uptime_seconds'] for a,b in zip(events,events[1:]))
    assert all(all(math.isfinite(e['resolved_size'][key]) and e['resolved_size'][key]>0 for key in ['width','height']) for e in events)
    assert all(e['probe_bounds_size_equals_resolved_size']==all(e['probe']['bounds_local'][key]==e['resolved_size'][key] for key in ['width','height']) for e in events)
    assert all(e['window']['number']==expected_window and e['window']['is_visible'] and e['window']['is_main'] and e['window']['is_key']for e in events)
    assert all(e['window']['frame_in_screen_bottom_left']['width']==920 and e['window']['frame_in_screen_bottom_left']['height']==668 for e in events)
    assert all(e['ancestor_chain_truncated'] and e['ancestor_limit']==6 for e in events)
    envs={json.dumps(e['environment_at_probe'],sort_keys=True)for e in events}
    assert len(envs)==1
    labels=list(dict.fromkeys(e['label']for e in events))
    assert len(labels)==21
    points={label:[e for e in events if e['label']==label]for label in labels}
    assert all(len({e['probe']['object_id']for e in values})==1 for values in points.values())
    return data,points,{'path':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':path.stat().st_size,'pid':data['pid'],
      'event_count':len(events),'label_count':len(labels),'callbacks':dict(Counter(e['callback']for e in events)),
      'event_sequence':[0,count-1],'first_last_uptime_seconds':[events[0]['observed_uptime_seconds'],events[-1]['observed_uptime_seconds']],
      'uptime_span_seconds':events[-1]['observed_uptime_seconds']-events[0]['observed_uptime_seconds'],
      'end_state':data['end_state'],'finite_rects_checked':finite_rects(data),'all_windows_own_visible_key_main_920x668':True,
      'all_ancestor_chains_truncated_at6':True,'environment_at_all_probes':events[0]['environment_at_probe'],
      'probe_size_equals_resolved_counts':dict(Counter(str(e['probe_bounds_size_equals_resolved_size'])for e in events))}

def main():
    l,lp,lsummary=packet(LOCAL,69534,10731,21)
    r,rp,rsummary=packet(REMOTE,1926,28,49)
    assert list(lp)==list(rp)
    le,re=lsummary['environment_at_all_probes'],rsummary['environment_at_all_probes']
    differences={k:{'local13':le[k],'remote14':re[k]}for k in le if le[k]!=re[k]}
    assert differences=={'display_scale':{'local13':2,'remote14':1}}
    rows=[]
    for label,values in lp.items():
        assert len(values)==1
        rows.append({'label':label,'local13_single_event':summarize(values[0]),'remote14_first_event':summarize(rp[label][0]),'remote14_last_event':summarize(rp[label][-1]),'remote14_event_count':len(rp[label])})
    capture=json.loads((ROOT/'work/picture-local13-ab-v3/capture-B3/result.json').read_text())
    ownership=json.loads((ROOT/'work/picture-local13-ab-v3/capture-B3/ownership.json').read_text())
    layout=next(w for w in capture['windows']if w['png']=='images-layout-light.png')
    assert ownership['pid']==l['pid']==layout['pid'] and layout['window_number']==10731
    report={
      'verdict':'B3_IO_on_21_labels_native129_147_and_selected9PNG_noninterference_pass',
      'local13':lsummary,'remote14':rsummary,'own_process_binding':{'ownership_sha256':sha(ROOT/'work/picture-local13-ab-v3/capture-B3/ownership.json'),'identity':ownership,'capture_layout_window':10731},
      'environment_differences':differences,'per_label_first_last':rows,
      'narrow_observations':[
        'Local13 has exactly one attachment callback per label. All21 native background probe sizes equal the concurrently supplied resolved sizes; this is not a terminal observation.',
        'Local13 Images Grid is719x109 and its nearest reported graphics ancestor is739x129. HDR Grid is719x127 and ancestor739x147. These native observations corroborate the separately verified whole original PNG raster heights129/147.',
        'Remote14 Images Grid initially reports719x105; final callback supplies resolved719x109 while its native background probe remains719x105 and graphics ancestor739x125. HDR stays127/147. The asynchronous mismatch cannot be used as a synchronized presentation record.',
        'First three image columns have resolved height109 on both systems; width-only mark column83. All image heights90 or64 and caption height13 match. Fractional caption widths and native pixel-aligned origins can differ with display scale.',
        'Remote14 final HDR SwiftUI global y335 matches local13 y335, but remote14 native HDR probe window-base y210 differs from local13 y206 and the original remote14 PNG is4pt higher. The apparent last global-frame match is not native/raster equivalence.',
        'The public environment probes match in9 of10 fields. Only display_scale differs2vs1. Inherited nil describes the probe environment font; it does not read the internal effective Text font.',
        'Both packet end_state fields remain not_observed. No proposed size, settled state, timer duration, physical display luminance, or unique root cause is inferred. The different event spans/callback counts are not compared as animation or responsiveness timings.'
      ],
      'source_context':'The first Grid computes5columns/4children and HDR3columns/2children at width719. onGeometryChange is the SDK back-deployed API, not a Bern PreferenceKey shim.',
      'limits':'Native ancestor class descriptions are observations through public NSView traversal, not a named public card API. Six-node truncated chains omit higher ancestors. Neither host has a capture-correlated terminal geometry dump.'}
    p=OUT/'B3-14-event-cross-review.json'
    with p.open('x')as f:json.dump(report,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({'report':str(p),'sha256':sha(p),'local_events':21,'remote_events':49,'environment_differences':differences}))

if __name__=='__main__':main()
