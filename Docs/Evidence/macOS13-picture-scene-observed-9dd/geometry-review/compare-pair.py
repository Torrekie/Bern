#!/usr/bin/env python3
"""Read-only verification of the original local13 selected PNG cohort."""
from pathlib import Path
import argparse, hashlib, importlib.util, json

ROOT=Path(__file__).resolve().parent.parent.parent
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('picture_geometry_review',OUT/'review.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('candidate',type=Path)
    ap.add_argument('scope',choices=['modifiers-present_log-off','modifiers-present_IO-on'])
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    control=ROOT/'work/picture-local13-ab-v2/capture-A2'
    candidate=args.candidate.resolve(strict=True)
    a,b=load(control/'result.json'),load(candidate/'result.json')
    assert a['success'] and b['success']
    assert a['source_sha']==b['source_sha']=='9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0'
    assert a['os']==b['os']=='Version 13.7.8 (Build 22H730)'
    assert mod.normalized_prefix(a)==mod.normalized_prefix(b)
    assert len(a['windows'])==len(b['windows'])==9
    pngs=[]
    for aw,bw in zip(a['windows'],b['windows']):
        assert aw['png']==bw['png']
        assert aw['pixel_width']==bw['pixel_width']==1840
        assert aw['pixel_height']==bw['pixel_height']==1336
        assert aw['bounds_points']==bw['bounds_points']
        assert aw['session_windows'][0]['focused'] and bw['session_windows'][0]['focused']
        p,q=control/aw['png'],candidate/bw['png']
        same=p.read_bytes()==q.read_bytes()
        assert same
        pngs.append({'name':aw['png'],'A2_sha256':sha(p),'candidate_sha256':sha(q),'PNG_bytes_equal':same})
    metadata=[]
    for lab,folder,d in [('A2',control,a),('candidate',candidate,b)]:
        original=load(folder/'original-front.json')
        cleanup=load(folder/'cleanup-helper.json')
        ownership=load(folder/'ownership.json')
        assert cleanup['success'] and not cleanup['own_instance_still_running']
        assert cleanup['front_after_restore_before_stop']==original==cleanup['front_after']
        assert ownership['pid']==d['windows'][-1]['pid']
        assert cleanup['own']['pid']==ownership['pid']
        assert cleanup['own']['bundle_id']==ownership['bundle_id']==d['private_bundle_id']
        assert cleanup['own']['executable_path']==ownership['executable_path']
        assert cleanup['own']['kernel_start']==ownership['kernel_start']
        flags=['increase_contrast','reduce_motion','reduce_transparency']
        assert all(d['system_preferences'][key]==d['system_preferences_end'][key] is False for key in flags)
        assert all(row['passed'] for row in d['checks']) and len(d['checks'])==14
        nonzero=[(i+1,row['arguments'],row['status']) for i,row in enumerate(d['commands']) if row['status']!=0]
        assert nonzero==[(1,['sessions'],3)]
        metadata.append({'label':lab,'path':str(folder.relative_to(ROOT)),'result_sha256':sha(folder/'result.json'),
          'commands':len(d['commands']),'checks':14,'startup_nonzero':nonzero,'all_remaining_commands_zero':True,
          'three_accessibility_flags_start_end_false':True,'end_accent_not_collected':True,'success':d['success'],'cleanup_success':cleanup['success'],
          'original_front':original,'owned_identity':ownership,'restored_before_stop':True,'own_instance_still_running':False,
          'cleanup_helper_sha256':sha(folder/'cleanup-helper.json'),'ownership_sha256':sha(folder/'ownership.json')})
    report={'verdict':'selected_9_PNGs_exact_normalized_prefix_context_cleanup_pass','scope':args.scope,
      'source_sha':a['source_sha'],'selected_PNGs':pngs,'metadata':metadata,
      'geometry_inference_from_PNG_exactness':{'first_card_half_open_points':[161,98,900,227],'first_card_height':129,
        'HDR_card_half_open_points':[161,325,900,472],'HDR_card_height':147,
        'sidebar_boundary_points':[140,141],'first_Grid_columns_children':[5,4],'HDR_Grid_columns_children':[3,2]},
      'limits':'Bounded selected static PNG/CLI sequence. No physical input, animation timing, full UI equivalence, global runtime noninterference or causal attribution. Overall failed v1 A is kept separately and is not relabelled successful. Observer IO-on requires independent event existence/validity evidence; this report scope is the supplied cohort identity.'}
    target=args.output.absolute()
    with target.open('x') as f:json.dump(report,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({'report':str(target),'sha256':sha(target),'PNG_count':9,'all_equal':True,'scope':args.scope}))

if __name__=='__main__':main()
