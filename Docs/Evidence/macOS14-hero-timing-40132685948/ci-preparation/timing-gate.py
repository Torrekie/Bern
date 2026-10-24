#!/usr/bin/env python3
"""Frozen bounded scalar-trace checks; trace-only never promotes native success."""
import argparse, json, math

def inspect_flight_timing_trace(d):
    trace=d.get('flight_timing_trace')
    result={'trace_coverage_verified':False,'acquisition_reported_success':d.get('success'),
            'original_acquisition_error':d.get('error'),'strict_gate_passed':False,
            'sdr_reported_success':(d.get('flight_sdr_display') or {}).get('success'),
            'trace':trace,'structure_error':None,
            'scope':'Scalar call boundaries only; no rendered-frame, causal or responsiveness acceptance.'}
    def need(value,message):
        if not value:raise ValueError('flight_timing_trace: '+message)
    def number(value,label):
        need(type(value) in (int,float) and math.isfinite(value),label+' finite scalar required')
        return value
    def integer(value,label):
        need(type(value) is int and value>=0,label+' nonnegative integer required')
        return value
    try:
        need(isinstance(trace,dict),'missing trace')
        need(trace['kind']=='bounded_native_sampler_scalar_timing','kind')
        need(type(trace['complete']) is bool and type(trace['success']) is bool,'status types')
        need(trace['complete'] is True,'reported timing coverage incomplete')
        need(trace['frozen_before_teardown'] is True,'freeze before original teardown')
        need(trace['limits']=={'native_event_slots':3,'live_samples':2,'pending_callbacks':1},'fixed storage limits')
        need(type(trace['timer_added_count']) is int and trace['timer_added_count']==1,'one native timer registration')
        need(trace['scope']=='Monotonic scalar call boundaries only; neither rendered frames nor root cause','scope')
        need(trace['pending_callback'] is None,'two completed live rows must clear pending callback')
        need(d['expected_os_major'] in (13,14) and d['actual_os_major']==d['expected_os_major'],'default13/default14 only')
        need(d['flight_sdr_display']['requested']=='default' and d['flight_sdr_display']['selected']=='default','timing is default mode only')
        live=trace['live_samples'];events=trace['native_events']
        need(isinstance(live,list) and len(live)==2,'exactly two live rows')
        need(isinstance(events,dict) and set(events)=={'timer_added','first_tick','first_applied'},'exactly three named native event slots')
        required=('callback_entered_uptime','window_info_begin_uptime','window_info_end_uptime',
                  'scalars_begin_uptime','matching_begin_uptime','state_uptime','scalars_end_uptime')
        row_keys=set(required)|{'callback_id','sample_index','existing_first_live_observation_uptime',
                                'flight_identity','flight_started_uptime','progress'}
        samples=d['samples']
        need(isinstance(samples,list) and 0<len(samples)<=512,'original bounded sample list')
        need(all(type(s['sample_index']) is int and s['sample_index']==i for i,s in enumerate(samples)),
             'actual sample index sequence')
        earliest=[s for s in samples if s['flights']][:2]
        need(len(earliest)==2 and [r['sample_index'] for r in live]==[s['sample_index'] for s in earliest],
             'trace must bind the actual earliest two live scalar samples')
        callback_count=integer(d['execution_model']['sampler_callback_count'],'actual callback counter')
        need(callback_count>=len(samples),'callback counter cannot be below sample count')
        for index,row in enumerate(live):
            need(isinstance(row,dict) and set(row)==row_keys,'fixed live-row fields')
            times=[number(row[key],key) for key in required]
            need(times==sorted(times),'per-callback call boundary order')
            integer(row['callback_id'],'callback ID');sample_index=integer(row['sample_index'],'sample index')
            need(sample_index+1<=row['callback_id']<=callback_count,'callback ID/counter binding')
            number(row['progress'],'live progress');number(row['flight_started_uptime'],'flight start')
            number(row['existing_first_live_observation_uptime'],'original first-live stamp')
            need(isinstance(row['flight_identity'],str) and bool(row['flight_identity']),'flight identity')
            need(0<=sample_index<len(samples),'actual sample index')
            sample=samples[sample_index]
            need(sample['sample_index']==sample_index and sample['uptime']==row['state_uptime'],'actual scalar sample mapping')
            need(sample['stage']=='transition' and sample['flight_count']==1 and len(sample['flights'])==1,'actual single live sample')
            flight=sample['flights'][0]
            need(flight['view_identity']==row['flight_identity'] and flight['started_uptime']==row['flight_started_uptime'] and
                 flight['progress']==row['progress'],'actual flight scalar mapping')
        a,b=live
        need(b['callback_id']==a['callback_id']+1 and b['sample_index']==a['sample_index']+1,'first two adjacent callback/sample IDs')
        for key in ('flight_identity','flight_started_uptime','existing_first_live_observation_uptime'):
            need(a[key]==b[key],'same pinned flight/original first-live stamp')
        stamp=a['existing_first_live_observation_uptime'];started=a['flight_started_uptime']
        need(a['matching_begin_uptime']<=stamp<=a['state_uptime'],'first-row matching/first-live stamp interval')
        # Row2 deliberately reuses the old first-live stamp: no row2 matching<=stamp assertion.
        for name,event in events.items():
            keys={'key','flight_started_uptime','uptime' if name=='timer_added' else 'now_uptime'}
            if name=='first_applied':keys.add('progress')
            need(isinstance(event,dict) and set(event)==keys,'fixed '+name+' fields')
            need(event['key']=='coordinator-one' and event['flight_started_uptime']==started,'native event key/start identity')
            event_time=number(event['uptime'] if name=='timer_added' else event['now_uptime'],name)
            need(event_time>=started,'native event precedes flight start')
        need(events['first_applied']['now_uptime']>=events['first_tick']['now_uptime'],'first applied/tick existing-now order')
        number(events['first_applied']['progress'],'first applied progress')
        # No callback-entry versus timer-added order, progress-band or new deadline is imposed.
        result['trace_coverage_verified']=True
        result['reported_sampler_callback_count']=callback_count
        result['native_event_offsets_seconds']={name:(event.get('uptime',event.get('now_uptime'))-started) for name,event in events.items()}
        result['live_call_intervals_seconds']=[{
            'callback_id':row['callback_id'],'sample_index':row['sample_index'],
            'callback_entry_minus_flight_started':row['callback_entered_uptime']-started,
            'window_info':row['window_info_end_uptime']-row['window_info_begin_uptime'],
            'scalars':row['scalars_end_uptime']-row['scalars_begin_uptime'],
            'matching_minus_original_first_live_stamp':row['matching_begin_uptime']-stamp,
            'state_minus_flight_started':row['state_uptime']-started} for row in live]
    except (ValueError,KeyError,TypeError,IndexError) as error:
        result['structure_error']=str(error)
    return result

def validate_flight_timing_trace(d,strict=True):
    result=inspect_flight_timing_trace(d)
    result['mode']='strict' if strict else 'trace-only'
    if strict:
        trace=d.get('flight_timing_trace') or {}
        sdr=d.get('flight_sdr_display') or {}
        if not (result['trace_coverage_verified'] and d.get('success') is True and d.get('error') is None and
                trace.get('success') is True and trace.get('error') is None and
                sdr.get('success') is True and sdr.get('error') is None):
            raise ValueError('Strict timing gate failed; original native/acquisition failure is preserved: '+
                             str(result['structure_error'] or d.get('error') or trace.get('error')))
        result['strict_gate_passed']=True
    else:
        result['overall_status']='partial/native failure preserved' if d.get('success') is not True else 'trace coverage only; native gates not rerun here'
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report')
    parser.add_argument('--trace-only',action='store_true',help='Report coverage/available trace; never passes original acquisition')
    args=parser.parse_args()
    def reject(value):raise ValueError('Non-finite JSON token: '+value)
    with open(args.report) as source:d=json.load(source,parse_constant=reject)
    print(json.dumps(validate_flight_timing_trace(d,strict=not args.trace_only),indent=2,sort_keys=True,allow_nan=False))

if __name__=='__main__':main()
