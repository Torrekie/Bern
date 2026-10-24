#!/usr/bin/env python3
"""Append-only gate for the frozen actual-coordinator flight_sdr_display schema."""
import json, math, sys

def validate_flight_sdr(d, receipt, mode, major):
    def need(value, message):
        if not value: raise ValueError('flight_sdr_display: '+message)
    def count(value, label, expected=None):
        need(type(value) is int and value>=0,label+' must be a nonnegative integer')
        if expected is not None: need(value==expected,label+' differs')
    def number(value, label):
        need(type(value) in (int,float) and math.isfinite(value) and value>=0,label+' must be finite/nonnegative')
        return value
    def identity(value, label):
        need(isinstance(value,str) and bool(value) and value!='nil',label+' missing')
        return value
    def layout(value, bits, pixels, floating, label):
        for key in ('width','height','bits_per_component','bits_per_pixel','bytes_per_row',
                    'bitmap_info_raw','alpha_info_raw','byte_order_raw','pixel_format_raw'):
            count(value[key],label+'.'+key)
        need(value['width'] in (320,640) and value['height']==value['width']*9//16,label+' extent')
        need(value['bits_per_component']==bits and value['bits_per_pixel']==pixels,label+' depth')
        need(value['float_components'] is floating and value['bytes_per_row']>=value['width']*(pixels//8),label+' storage')
    def space(value, label):
        need(value['present'] is True and value['model_raw']==1 and value['components']==3,label+' RGB3')
        need(value['stage']=='after_existing_window_teardown',label+' metadata stage')
        count(value['icc_byte_count'],label+'.icc_byte_count')
        sha=value['icc_sha256']
        need((value['icc_byte_count']==0 and sha=='absent') or
             (value['icc_byte_count']>0 and isinstance(sha,str) and len(sha)==64 and all(c in '0123456789abcdef' for c in sha)),label+' ICC record')
    need(type(major) is int and major in (13,14) and mode in ('default','baked-pair'),'mode/OS enum')
    need(mode=='default' or major==13,'baked-pair is13 only')
    need(d['success'] is True and d.get('error') is None,'original acquisition failed')
    need(d['expected_os_major']==major and d['actual_os_major']==major,'report OS')
    need(receipt['exit_code']==0 and not receipt.get('wrapper_timeout',False),'process failure/timeout')
    need(receipt['expected_os_major']==major and receipt['timeout_seconds']==15,'receipt OS/timeout')
    need(receipt['flight_sdr_mode']==mode and receipt['bern_hero_flight_sdr_environment']==mode,'receipt mode/environment')
    need(receipt['flight_sdr_mode_source'] in ('last_argument','environment','default'),'receipt mode source')
    s=d['flight_sdr_display']
    need(s['requested']==mode and s['selected']==mode,'reported mode')
    need(s['success'] is True and s['error'] is None,'helper failure; no successful fallback accepted')
    count(s['primary_snapshot_count'],'primary snapshots',2)
    count(s['cleanup_snapshot_count'],'cleanup snapshots')
    baked=mode=='baked-pair'
    for key,wanted in (('conversion_count',2 if baked else 0),('context_create_count',1 if baked else 0),
                       ('derived_cache_count_before_release',2 if baked else 0),
                       ('helper_retained_original_cgimage_count',0),('helper_original_provider_read_count',0)):
        count(s[key],key,wanted)
    need(s['primary_frozen'] is True and s['helper_references_cleared'] is True,'original cleanup/release incomplete')
    need(s['release_scope']=='Helper-owned derived cache/context/color-space and weak refs cleared; no global deallocation claim','release scope')
    records=s['records']; need(isinstance(records,list) and len(records)==2,'two actual records required')
    mapping=s['flight_mapping']
    need(mapping['from_ordinal']==1 and mapping['to_ordinal']==2,'actual snapshot ordinal mapping')
    transition=number(mapping['transition_uptime'],'transition')
    need(transition==d['transition_uptime'],'transition mismatch')
    started=number(mapping['flight_started_uptime'],'flight started')
    first=number(mapping['first_live_observation_uptime'],'first observation')
    need(transition<=started<=first,'transition/flight/observer order')
    flight_id=identity(mapping['flight_identity'],'flight identity')
    need(d['observed_flight_identities']==[flight_id] and d['native_gates']['observed_flight_identities']==[flight_id],'native flight mapping')
    need(mapping['from_nsimage_id']!=mapping['to_nsimage_id'],'independent from/to wrappers')
    previous_end=transition; derived_ids=[]
    for ordinal,record in enumerate(records,1):
        need(record['ordinal']==ordinal and record['key']=='coordinator-one','record ordinal/key')
        identity(record['anchor_identity'],'anchor identity')
        identity(record['input_object_id'],'original renderer CGImage identity')
        need(record['wrapped'] is True and record.get('error') is None,'partial snapshot/wrapper failure')
        need(record['logical_size']==[320,180],'original logical size')
        role='from' if ordinal==1 else 'to'
        need(record['flight_role']==role and record['display_nsimage_id']==mapping[role+'_nsimage_id'],'actual wrapper role')
        identity(record['display_nsimage_id'],'display wrapper identity')
        source=record['input_layout']; layout(source,16,64,True,'input')
        need((source['bitmap_info_raw'],source['alpha_info_raw'],source['byte_order_raw'],source['pixel_format_raw'])==(4353,1,4096,0),'original float layout')
        need(record['input_extent']=={'x':0,'y':0,'width':source['width'],'height':source['height']},'exact input extent')
        space(record['input_color_space'],'input space')
        timeline=[number(record[key],key) for key in ('snapshot_started_uptime','renderer_returned_uptime')]
        if baked:
            need(record['requested_tone_map_hdr_to_sdr'] is True and record['actual_tone_mapping_applied']=='unknown','requested versus actual tone mapping')
            need(record['input_color_space_override'] is False and record['deferred'] is False,'fixed recipe options')
            need(record['requested_output_format']=='RGBA8' and record['requested_output_color_space']=='sRGB','fixed output request')
            timeline += [number(record[key],key) for key in ('conversion_started_uptime','conversion_finished_uptime')]
            derived=record['derived_layout']; layout(derived,8,32,False,'derived')
            need((derived['width'],derived['height'])==(source['width'],source['height']),'exact output extent')
            space(record['derived_color_space'],'derived space')
            need(record['derived_color_space']['name']=='kCGColorSpaceSRGB','derived sRGB')
            derived_id=identity(record['derived_object_id'],'derived identity')
            need(derived_id!=record['input_object_id'],'derived output cannot be original-image fallback')
            derived_ids.append(derived_id)
        else:
            need(record['conversion_started_uptime'] is None and record['conversion_finished_uptime'] is None,'default conversion timestamps')
            for key in ('derived_object_id','derived_layout','derived_color_space','requested_tone_map_hdr_to_sdr',
                        'actual_tone_mapping_applied','requested_output_format','requested_output_color_space','deferred','input_color_space_override'):
                need(key not in record,'default unexpectedly contains conversion field '+key)
        timeline += [number(record[key],key) for key in ('nsimage_wrapped_uptime','snapshot_returning_uptime')]
        need(previous_end<=timeline[0] and timeline==sorted(timeline) and timeline[-1]<=started,'snapshot/conversion/wrapper/flight order')
        previous_end=timeline[-1]
    if baked: need(len(set(derived_ids))==2,'two independent retained derived images')
    states=list(d['samples'])+[d['before_cleanup_state']]
    for capture in d['captures']: states += [capture['state_before'],capture['state_after']]
    states += [d['midflight_sampling']['armed']['state'],d['midflight_sampling']['capture_sample']['state']]
    live_count=0
    for state in states:
        for flight in state['flights']:
            live_count+=1
            need(flight['view_identity']==flight_id and flight['started_uptime']==started,'scalar actual flight mismatch')
            need(flight['from_nsimage_id']==mapping['from_nsimage_id'] and flight['to_nsimage_id']==mapping['to_nsimage_id'],'scalar actual image mismatch')
            need(first<=number(state['uptime'],'live scalar uptime'),'observer precedes recorded state')
            need(records[0]['rect_in_overlay']==flight['from_rect'] and records[1]['rect_in_overlay']==flight['to_rect'],'snapshot rect/flight mapping')
    need(live_count>0,'no actual live scalar record')
    need(first<=d['execution_model']['terminal_uptime']<=d['execution_model']['loop_return_uptime'],'observer/normal return order')
    return {'mode':mode,'major':major,'actual_snapshots':2,'conversions':s['conversion_count'],
            'contexts':s['context_create_count'],'helper_references_cleared':True,'actual_tone_mapping_applied':'unknown' if baked else 'not requested'}

def main():
    if len(sys.argv)!=5: raise ValueError('report.json receipt.json default|baked-pair 13|14')
    def reject(value): raise ValueError('Non-finite JSON token: '+value)
    with open(sys.argv[1]) as source: d=json.load(source,parse_constant=reject)
    with open(sys.argv[2]) as source: receipt=json.load(source,parse_constant=reject)
    print(json.dumps(validate_flight_sdr(d,receipt,sys.argv[3],int(sys.argv[4])),sort_keys=True))

if __name__=='__main__': main()
