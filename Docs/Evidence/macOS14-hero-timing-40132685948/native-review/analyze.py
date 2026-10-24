#!/usr/bin/env python3
# Offline only. Do not invoke until root declares the actual cohort ready.
import argparse,ast,hashlib,json,re,subprocess,sys,tarfile,textwrap
from pathlib import Path
P=argparse.ArgumentParser()
for n in ('cohort','binary-sha','tar-sha','base-commit','overlay-files','ready-receipt'):
    P.add_argument('--'+n,required=True)
P.add_argument('--execute-ready',action='store_true',required=True)
a=P.parse_args();assert a.execute_ready
D=Path(a.cohort).resolve();O=Path(__file__).resolve().parent;assert not (O/'review.json').exists()
H=lambda b:hashlib.sha256(b).hexdigest();inputs={}
def read(p):
    p=Path(p).resolve();b=p.read_bytes();inputs[str(p)]={'bytes':len(b),'sha256':H(b)};return b
def load(p):return json.loads(read(p),parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
def relative(n):
    p=Path(n);assert not p.is_absolute() and '..' not in p.parts;return p
def command(argv):
    r=subprocess.run(argv,text=True,capture_output=True)
    return {'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
W=D/'tools/macos14-hero-timing-probe.yml';G=D/'tools/timing-gate.py'
w=read(W).decode();g=read(G).decode()
assert H(w.encode())=='4d6d9a3491d66ecabc341e51aafdeab2e901855eea59b63107359baef3cb2e08'
assert H(g.encode())=='df434f5fe79e0c048376018ccb3e5103cafa5d3e88543ff62a5c41f066ce8352'
blocks=[textwrap.dedent(v) for v in re.findall(r"(?ms)^        python3 - <<'PY'\n(.*?)^        PY\n",w)]
full=[v for v in blocks if 'midflight_sampling' in v and 'execution_model' in v];assert len(full)==1
marker='# Append-only bounded timing metadata gate; inherited native/execution/SDR gates above remain unchanged.\n'
assert full[0].count(marker)==1;prefix=full[0].split(marker)[0]
assert len(prefix.encode())==19155 and H(prefix.encode())=='db503c085d257c7102062fc209074ded13fa431aac8e0ec1395fdde0decf60a8'
def fn(source):
    n=[v for v in ast.parse(source).body if isinstance(v,ast.FunctionDef) and v.name=='validate_flight_timing_trace'];assert len(n)==1
    return ast.get_source_segment(source,n[0])
assert fn(full[0])==fn(g)
B=D/'probe/HeroTimingProbe';binary=read(B);assert H(binary)==a.binary_sha
bin_record={'path':str(B),'sha256':H(binary),'bytes':len(binary),'actual_read_before_gates':True}
checks={k:command(v) for k,v in {
 'arch':['/usr/bin/xcrun','lipo','-archs',str(B)],'build':['/usr/bin/xcrun','vtool','-show-build',str(B)],
 'signature':['/usr/bin/codesign','--verify','--strict',str(B)]}.items()}
assert all(v['exit_code']==0 for v in checks.values());assert checks['arch']['stdout'].strip()=='arm64'
assert re.search(r'\bminos\s+13\.0\b',checks['build']['stdout']) and re.search(r'\bsdk\s+26\.2\b',checks['build']['stdout'])
manifest=read(D/'probe/SHA256SUMS');members={}
for line in manifest.decode().splitlines():
    sha,name=line.split('  ',1);p=D/'probe'/relative(name);assert not p.is_symlink() and H(read(p))==sha;members[name]=sha
assert len(members)==20
for p in (D/'build/SHA256SUMS',D/'runtime14/SHA256SUMS'):assert read(p)==manifest
prov=load(D/'probe/source-provenance.json');assert len(prov['files'])==12
for n,v in prov['files'].items():assert H(read(D/'probe'/relative(n)))==v['sha256']
assembly_names=[n for n in members if n.endswith('.assembled.swift')];assert len(assembly_names)==1
assembled=b'import AppKit\nimport SwiftUI\n'+b''.join(read(D/'probe'/n) for n in ('ProductHero.swift','FlightSDR.swift.inc','Driver.swift.inc'))
assert read(D/'probe'/assembly_names[0])==assembled
archive=D/'build/hero-timing-probe.tar.gz';assert H(read(archive))==a.tar_sha
with tarfile.open(archive,'r:gz') as t:
    tf={}
    for m in t.getmembers():
        if m.isdir():continue
        assert m.isfile() and not m.issym() and not m.islnk();n=m.name.removeprefix('./');relative(n);assert n not in tf
        tf[n]=H(t.extractfile(m).read())
    assert tf==dict(members,**{'SHA256SUMS':H(manifest)})
# Bind the original git source rather than copying another package-source tree.
assert re.fullmatch('[0-9a-f]{40}',a.base_commit) and a.base_commit.startswith('4fc')
overlays=a.overlay_files.split(',');assert len(overlays)==len(set(overlays))==5
base_dir='.github/scripts/hero-coordinator-sdr-probe';base_binding={}
for n,v in prov['files'].items():
    r=subprocess.run(['git','show',a.base_commit+':'+base_dir+'/'+relative(n).as_posix()],cwd='outputs/Bern',capture_output=True)
    if n in overlays:
        base_binding[n]={'overlay':True,'current_sha256':v['sha256']}
    else:
        assert r.returncode==0 and H(r.stdout)==v['sha256'],n
        base_binding[n]={'git_base_sha256':H(r.stdout),'byte_identical':True}
for n in overlays:read(D/'probe'/relative(n))
ready=load(a.ready_receipt)
assert ready['binary_sha256']==a.binary_sha
assert ready['ready_for_observation_analysis'] is True and ready['all_steps_exit_zero'] is True
assert ready['default13_corresponding_endpoints_raw_and_icc_exact'] is True
for n,h in ready['input_hashes'].items():assert H(read(D/'runtime13'/relative(n)))==h,n
steps=load(D/'runtime13/root-steps.json');assert len(steps)==4 and all(v['exit_code']==0 for v in steps)
controls=load(D/'runtime13/endpoint-controls.json');assert controls['exact_endpoint_controls'] is True
for phase in ('before','settled'):
    c=controls['checks'][phase]
    assert c['raw']['exact'] is True and c['srgb']['exact'] is True and c['embedded_icc_identical'] is True
for n,v in controls['inputs'].items():assert H(read(n))==v['sha256'],n
root_controls={'readiness_flags_verified':True,'four_root_step_exits':[v['exit_code'] for v in steps],
 'endpoint_summary':{k:{'raw_exact':controls['checks'][k]['raw']['exact'],'srgb_exact':controls['checks'][k]['srgb']['exact'],'embedded_icc_identical':controls['checks'][k]['embedded_icc_identical']} for k in ('before','settled')},
 'scope':'Root pixel results bound to input hashes; no pixel algorithm recalculated. No candidate-order requirement in this default-only cohort.'}
processes={};adaptations={}
for major in (13,14):
    runtime=D/('runtime'+str(major))
    report_hash_before=H(read(runtime/'report.json'))
    changes={"Path('evidence/runtime14')":'Path('+repr(str(runtime))+')',
      "d['expected_os_major']==14 and d['actual_os_major']==14":f"d['expected_os_major']=={major} and d['actual_os_major']=={major}",
      "receipt['expected_os_major']==14":f"receipt['expected_os_major']=={major}",
      "Path('probe/HeroTimingProbe')":'Path('+repr(str(B))+')',
      "validate_flight_sdr(d,receipt,'default',14)":f"validate_flight_sdr(d,receipt,'default',{major})"}
    code=prefix
    for before,after in changes.items():assert code.count(before)==1,before;code=code.replace(before,after)
    ast.parse(code)
    native=command([sys.executable,'-B','-c',code]);strict=command([sys.executable,'-B',str(G),str(runtime/'report.json')])
    trace_only=command([sys.executable,'-B',str(G),str(runtime/'report.json'),'--trace-only'])
    if trace_only['exit_code']==0:assert json.loads(trace_only['stdout'])['strict_gate_passed'] is False
    report=load(runtime/'report.json');receipt=load(runtime/'run-receipt.json');assert receipt['binary_sha256']==a.binary_sha
    assert H(read(runtime/'report.json'))==report_hash_before,'Gate changed original report'
    shots=[]
    for c in report['captures']:
        assert H(read(runtime/c['png']))==c['png_sha256']
        shots.append({k:c[k] for k in ('phase','png','png_sha256','capture_icc_sha256','capture_size','capture_before_uptime','capture_after_uptime')})
    assert len(list(runtime.glob('*.png')))==len(shots)
    timing=report.get('flight_timing_trace');sdr=report['flight_sdr_display']
    coverage_result=json.loads(strict['stdout']) if strict['exit_code']==0 else json.loads(trace_only['stdout']) if trace_only is not None and trace_only['exit_code']==0 else None
    if coverage_result is not None:
        assert type(coverage_result['trace_coverage_verified']) is bool
        if strict['exit_code']!=0:assert coverage_result['strict_gate_passed'] is False
    cross_mapping={'verified':False,'scope':'Exact three-field first-row binding; separate from gate exit/coverage status.'}
    if isinstance(timing,dict) and timing.get('live_samples'):
        row=timing['live_samples'][0];mapping=sdr['flight_mapping']
        fields={'flight_identity':'flight_identity','flight_started_uptime':'flight_started_uptime','existing_first_live_observation_uptime':'first_live_observation_uptime'}
        if all(left in row and right in mapping for left,right in fields.items()):
            assert all(row[left]==mapping[right] for left,right in fields.items()),'Timing first-row/SDR mapping differs'
            cross_mapping.update(verified=True,comparisons={left:{'trace':row[left],'mapping':mapping[right],'exact':True} for left,right in fields.items()})
        else:cross_mapping['missing_fields']=[left for left,right in fields.items() if left not in row or right not in mapping]
    strict_result=json.loads(strict['stdout']) if strict['exit_code']==0 else None
    trace_result=json.loads(trace_only['stdout']) if trace_only['exit_code']==0 else None
    if trace_result is not None:
        assert type(trace_result['trace_coverage_verified']) is bool and trace_result['strict_gate_passed'] is False
        assert trace_result['acquisition_reported_success']==report['success'] and trace_result['sdr_reported_success']==sdr['success']
    if strict_result is not None:assert strict_result['trace_coverage_verified'] is True and strict_result['strict_gate_passed'] is True and strict_result['structure_error'] is None
    def brief(result):return None if result is None else {k:v for k,v in result.items() if k!='trace'}
    def gate_status(value):return {'exit_code':value['exit_code'],'stdout_sha256':H(value['stdout'].encode()),'stderr':value['stderr']}
    interval_table=None
    if isinstance(timing,dict) and len(timing.get('live_samples',[]))==2 and set(timing.get('native_events',{}))=={'timer_added','first_tick','first_applied'}:
        rows=timing['live_samples'];events=timing['native_events'];started=rows[0]['flight_started_uptime']
        interval_table={'native_offsets_seconds':{k:(v.get('uptime',v.get('now_uptime'))-started) for k,v in events.items()},
          'live_prefix_seconds':[{'callback_id':r['callback_id'],'sample_index':r['sample_index'],'progress':r['progress'],
            'entry_to_window_info_begin':r['window_info_begin_uptime']-r['callback_entered_uptime'],
            'window_info':r['window_info_end_uptime']-r['window_info_begin_uptime'],
            'window_info_end_to_scalars_begin':r['scalars_begin_uptime']-r['window_info_end_uptime'],
            'scalars':r['scalars_end_uptime']-r['scalars_begin_uptime'],
            'total_entry_to_scalars_end':r['scalars_end_uptime']-r['callback_entered_uptime'],
            'matching_begin_to_original_first_stamp_first_row_only':None if i else r['existing_first_live_observation_uptime']-r['matching_begin_uptime']} for i,r in enumerate(rows)],
          'first_scalars_end_to_first_tick_existing_now_unattributed_seconds':events['first_tick']['now_uptime']-rows[0]['scalars_end_uptime'],
          'boundary':'No callback-exit marker: remaining callback work, automatic drawing and dispatch are not separated. Existing tick now is not callback return, assignment completion or presentation time.'}
    processes[str(major)]={'native_execution_sdr_gate':native,'strict_timing_gate':gate_status(strict),'trace_only_gate':gate_status(trace_only),'strict_result':brief(strict_result),'trace_only_result':brief(trace_result),'interval_table':interval_table,
      'report_unchanged_by_all_gates':True,'report_success':report['success'],'report_error':report.get('error'),'own_pid':receipt['own_pid'],'wrapper_exit':receipt['exit_code'],
      'window_seconds':report['window_seconds'],'front':[report['frontmost_before'],report['frontmost_after']],
      'normal_before':report['normal_before'],'normal_after':report['normal_after'],'cache_unchanged':report.get('cache_unchanged'),
      'native_gates_present':'native_gates' in report,'sample_count':len(report['samples']),
      'loop_counts':{k:report['execution_model'][k] for k in ('loop_entry_count','loop_return_count','terminal_count','sampler_callback_count','stop_calls','wake_count')},
      'timing_trace':timing,'coverage_result':brief(coverage_result),'first_row_sdr_mapping_binding':cross_mapping,'snapshot_counts':{k:sdr[k] for k in ('primary_snapshot_count','conversion_count','context_create_count','helper_references_cleared')},
      'shots':shots,'coverage_is_not_native_completion':True,'pixel_analysis':False}
    adaptations[str(major)]={'five_literal_path_or_major_changes_only':changes,'adapted_prefix_sha256':H(code.encode())}
assert H(read(B))==a.binary_sha;bin_record['actual_read_after_gates']=True
both=all(v['native_execution_sdr_gate']['exit_code']==v['strict_timing_gate']['exit_code']==0 for v in processes.values())
status='strict13_and14_native_trace_pass' if both else '13_strict_pass_14_partial' if processes['13']['native_execution_sdr_gate']['exit_code']==processes['13']['strict_timing_gate']['exit_code']==0 else 'incomplete_native_or_timing'
result={'status':status,'ci_run':40132685948,'source_commit':'cc96030b22c74010df79423979aee1abf83b7cb5','harness_commit':'d72cb5f9bcec8a90fa394bca1060ed0f392ba8f3','scope':'Offline original gate/package/source checks and bounded timing extraction; no native app, compile, CI or pixel operation.',
 'workflow_sha256':H(w.encode()),'timing_gate_sha256':H(g.encode()),'original_prefix_bytes':len(prefix.encode()),'original_prefix_sha256':H(prefix.encode()),
 'timing_function_same_as_workflow':True,'gate_adaptations':adaptations,'actual_binary':bin_record,'actual_readonly_checks':checks,
 'package':{'tar_sha256':a.tar_sha,'manifest_members':20,'source_map_members':12,'assembly_sha256':H(assembled),'tar_map_exact':True},
 'git_base':{'commit':a.base_commit,'directory':base_dir,'five_overlays':overlays,'source_map_binding':base_binding},
 'root_controls':root_controls,
 'root_readiness_receipt':{'path':str(Path(a.ready_receipt).resolve()),'contents':ready,'result':'Actual readiness flags, referenced file hashes, four root exits and saved endpoint controls verified; no pixel recomputation.'},
 'processes':processes,'input_files':inputs,'pixel_acceptance':'NOT PERFORMED',
 'limits':'Trace complete is bounded coverage only. Trace-only preserves report.success and never claims strict pass. Original now/p and first-observation stamp are not presentation/matching-end timestamps. No cause or zero observer effect claim.'}
encoded=json.dumps(result,indent=2,sort_keys=True)+'\n';assert len(encoded.encode())<=65536
(O/'review.json').write_text(encoded)
print(json.dumps({'status':status,'gate_exits':{k:[v['native_execution_sdr_gate']['exit_code'],v['strict_timing_gate']['exit_code']] for k,v in processes.items()},'review_bytes':len(encoded.encode())}))
