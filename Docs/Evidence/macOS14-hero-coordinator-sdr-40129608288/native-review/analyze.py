#!/usr/bin/env python3
# Offline only. Run after root explicitly declares the three actual runtimes ready.
import argparse,ast,datetime,hashlib,json,re,subprocess,sys,tarfile,textwrap
from pathlib import Path

p=argparse.ArgumentParser(description='Offline native gate and input provenance review; no native app execution or pixel decoding.')
for name in ('cohort','workflow','workflow-sha','additive-gate','additive-sha','binary-sha','tar-sha','runtime13-default','runtime13-baked','runtime14-default','root-control-receipt'):
    p.add_argument('--'+name,required=True)
p.add_argument('--execute-ready',action='store_true',required=True)
a=p.parse_args(); assert a.execute_ready
OUT=Path(__file__).resolve().parent; assert not (OUT/'review.json').exists(),'Refuse to overwrite review'
D=Path(a.cohort).resolve();inputs={}
def digest(b): return hashlib.sha256(b).hexdigest()
def read(path):
    path=Path(path).resolve();b=path.read_bytes();inputs[str(path)]={'bytes':len(b),'sha256':digest(b)};return b
def load(path):
    return json.loads(read(path),parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
def relpath(value):
    q=Path(value);assert not q.is_absolute() and '..' not in q.parts;return q
def pyblocks(workflow):
    return [textwrap.dedent(m) for m in re.findall(r"(?ms)^        python3 - <<'PY'\n(.*?)^        PY\n",workflow)]
def gate_source(workflow):
    candidates=[v for v in pyblocks(workflow) if 'midflight_sampling' in v and 'execution_model' in v]
    assert len(candidates)==1;return candidates[0]
def function_source(code,name):
    tree=ast.parse(code);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(nodes)==1;return ast.get_source_segment(code,nodes[0])
def check_cmd(argv):
    c=subprocess.run(argv,text=True,capture_output=True);assert c.returncode==0,(argv,c.stdout,c.stderr)
    return {'argv':argv,'exit_code':c.returncode,'stdout':c.stdout,'stderr':c.stderr}

workflow=read(a.workflow).decode();assert digest(workflow.encode())==a.workflow_sha and 'PENDING_' not in workflow
full=gate_source(workflow)
marker='# Append-only SDR metadata gate; inherited native/execution gate above remains unchanged.\n'
assert full.count(marker)==1;prefix=full.split(marker)[0]
old=gate_source(read('outputs/Bern/.github/workflows/macos14-hero-coordinator-app-probe.yml').decode())
assert prefix==old.replace('HeroCoordinatorAppProbe','HeroCoordinatorSDRProbe'),'Old native/execution assertions differ'
additive=read(a.additive_gate).decode();assert digest(additive.encode())==a.additive_sha
assert function_source(full,'validate_flight_sdr')==function_source(additive,'validate_flight_sdr'),'Embedded and standalone additive functions differ'
B=D/'probe/HeroCoordinatorSDRProbe';binary=read(B);assert digest(binary)==a.binary_sha
actual_binary={'path':str(B),'bytes':len(binary),'sha256':digest(binary),'actual_bytes_read_before_gates':True}
checks={
 'arch':check_cmd(['/usr/bin/xcrun','lipo','-archs',str(B)]),
 'mach_build':check_cmd(['/usr/bin/xcrun','vtool','-show-build',str(B)]),
 'signature_verify':check_cmd(['/usr/bin/codesign','--verify','--strict',str(B)]),
 'signature_details':check_cmd(['/usr/bin/codesign','-dvvv',str(B)])}
assert checks['arch']['stdout'].strip()=='arm64'
assert re.search(r'\bminos\s+13\.0\b',checks['mach_build']['stdout'])
assert re.search(r'\bsdk\s+26\.2\b',checks['mach_build']['stdout'])
manifest=read(D/'probe/SHA256SUMS').decode();members={}
for line in manifest.splitlines():
    expected,name=line.split('  ',1);relative=relpath(name);target=D/'probe'/relative
    assert not target.is_symlink() and digest(read(target))==expected,name;members[name]=expected
for path in (D/'build/SHA256SUMS',D/'runtime14/SHA256SUMS'):
    if path.exists():assert read(path)==manifest.encode(),path
provenance=load(D/'probe/source-provenance.json');assert provenance['kind']=='actual_coordinator_sdr_fixture'
for name,v in provenance['files'].items():assert digest(read(D/'probe'/relpath(name)))==v['sha256'],name
assembly=b'import AppKit\nimport SwiftUI\n'+b''.join(read(D/'probe'/n) for n in ('ProductHero.swift','FlightSDR.swift.inc','Driver.swift.inc'))
assert read(D/'probe/CoordinatorSDR.assembled.swift')==assembly
archive=D/'build/hero-coordinator-sdr-probe.tar.gz';assert digest(read(archive))==a.tar_sha
with tarfile.open(archive,'r:gz') as tar:
    files={}
    for member in tar.getmembers():
        if member.isdir():continue
        assert member.isfile() and not member.issym() and not member.islnk(),member.name
        name=member.name.removeprefix('./');relpath(name);assert name not in files,name
        files[name]=digest(tar.extractfile(member).read())
    assert files==dict(members,**{'SHA256SUMS':digest(manifest.encode())})
control=load(a.root_control_receipt)
assert control['binary_sha256']==a.binary_sha and control['default_gates_and_endpoint_controls_all_exit_zero'] is True and control['ready_for_candidate'] is True
for name,expected in control['input_hashes'].items():assert digest(read(D/relpath(name)))==expected,name
package_receipt=load(D/'package-verification-local.json')
assert package_receipt['binary_sha256']==a.binary_sha and package_receipt['archive_sha256']==a.tar_sha
assert package_receipt['assembly_sha256']==digest(assembly)
assert package_receipt['package_manifest_sha256']==digest(manifest.encode())
assert sorted(package_receipt['verified_package_members'])==sorted(members)
for folder in ('build','runtime14'):
    assert read(D/folder/'source-provenance.json')==read(D/'probe/source-provenance.json')
    read(D/folder/'binary.txt');read(D/folder/'signature.txt')
read(D/'build/environment.txt')

processes={};adaptations={};endpoint_records={}
for key,major,mode,directory in [('13-default',13,'default',a.runtime13_default),('13-baked-pair',13,'baked-pair',a.runtime13_baked),('14-default',14,'default',a.runtime14_default)]:
    directory=Path(directory).resolve()
    changes={
     "Path('evidence/runtime14')":'Path('+repr(str(directory))+')',
     "d['expected_os_major']==14 and d['actual_os_major']==14":f"d['expected_os_major']=={major} and d['actual_os_major']=={major}",
     "receipt['expected_os_major']==14":f"receipt['expected_os_major']=={major}",
     "Path('probe/HeroCoordinatorSDRProbe')":'Path('+repr(str(B))+')'}
    code=prefix
    for before,after in changes.items():assert code.count(before)==1,before;code=code.replace(before,after)
    ast.parse(code)
    # The complete original prefix executes unchanged except the recorded four literals.
    native=subprocess.run([sys.executable,'-B','-c',code],text=True,capture_output=True)
    additive_argv=[sys.executable,'-B',str(Path(a.additive_gate).resolve()),str(directory/'report.json'),str(directory/'run-receipt.json'),mode,str(major)]
    extra=subprocess.run(additive_argv,text=True,capture_output=True)
    native_result={'exit_code':native.returncode,'stdout':native.stdout,'stderr':native.stderr,'invocation':'current Python -B -c <four-literal-adapted complete native/execution prefix>'}
    additive_result={'argv':additive_argv,'exit_code':extra.returncode,'stdout':extra.stdout,'stderr':extra.stderr}
    if major==13:
        assert native.returncode==extra.returncode==0,(key,native_result,additive_result)
    else:
        assert native.returncode!=0 and extra.returncode!=0,'14 partial unexpectedly accepted by an unchanged gate'
    d=load(directory/'report.json');r=load(directory/'run-receipt.json');assert r['binary_sha256']==a.binary_sha
    if major==13:assert d['success'] is True and r['exit_code']==0
    else:
        assert d['success'] is False and r['exit_code']==1 and not r.get('wrapper_timeout',False)
        assert 'Collection entry deadline/sample bound; incomplete' in d['error']
        assert d['midflight_sampling']['armed'] is None and d['midflight_sampling']['capture_sample'] is None
        assert d['midflight_sampling']['capture_attempted'] is False and d['midflight_sampling']['next_sample_captured'] is False
        assert 'native_gates' not in d and 'cache_after' not in d and 'cache_unchanged' not in d
    captures=[]
    for c in d['captures']:
        assert digest(read(directory/c['png']))==c['png_sha256']
        fields=('phase','png','png_sha256','raw_buffer_sha256','owner_pid','window_id','window_frame','capture_size','rois','capture_icc_sha256','current_headroom','potential_headroom','capture_before_uptime','capture_after_uptime')
        x={k:c[k] for k in fields}
        x['brackets']={k:{'uptime':c[k]['uptime'],'timer_exists':c[k]['timer_exists'],'flights':c[k]['flights']} for k in ('state_before','state_after')}
        x['consecutive_equal_buffers']=c.get('consecutive_equal_buffers')
        captures.append(x)
    assert len(list(directory.glob('*.png')))==len(captures)
    if major==14:assert [c['phase'] for c in captures]==['before']
    sampling=d['midflight_sampling'];armed=sampling['armed'];captured=sampling['capture_sample'];s=d['flight_sdr_display'];mapping=s['flight_mapping']
    timing={'transition_to_started_seconds':mapping['flight_started_uptime']-mapping['transition_uptime'],
            'transition_to_first_live_observation_seconds':mapping['first_live_observation_uptime']-mapping['transition_uptime'],
            'started_to_first_live_observation_seconds':mapping['first_live_observation_uptime']-mapping['flight_started_uptime'],
            'arm_capture_index_gap':None if armed is None or captured is None else captured['sample_index']-armed['sample_index'],
            'arm_capture_uptime_gap':None if armed is None or captured is None else captured['uptime']-armed['uptime'],
            'snapshots':[{'ordinal':v['ordinal'],'role':v['flight_role'],'renderer_seconds':v['renderer_returned_uptime']-v['snapshot_started_uptime'],
                          'conversion_seconds':None if v['conversion_started_uptime'] is None else v['conversion_finished_uptime']-v['conversion_started_uptime'],
                          'whole_snapshot_seconds':v['snapshot_returning_uptime']-v['snapshot_started_uptime']} for v in s['records']]}
    live=[]
    for v in d['samples']:
        if v['flights']:
            live.append({'sample_index':v['sample_index'],'uptime':v['uptime'],'stage':v['stage'],'timer_exists':v['timer_exists'],
                         'flights':[{k:f[k] for k in ('view_identity','progress','frame','started_uptime','from_nsimage_id','to_nsimage_id')} for f in v['flights']]})
    scalar_samples={name:None if value is None else {k:value[k] for k in ('sample_index','uptime','progress','flight_identity')} for name,value in [('armed',armed),('capture',captured)]}
    processes[key]={'status':'native_and_additive_pass' if major==13 else 'partial_failed_unchanged_gates',
      'complete_original_native_execution_gate':native_result,'unchanged_additive_gate':additive_result,
      'receipt':r,'success':d['success'],'error':d.get('error'),'window_seconds':d['window_seconds'],
      'normal_before':d['normal_before'],'normal_after':d['normal_after'],'frontmost_before':d['frontmost_before'],'frontmost_after':d['frontmost_after'],
      'cache_after_present':'cache_after' in d,'cache_unchanged':d.get('cache_unchanged'),
      'cache_before_equals_after':None if 'cache_after' not in d else d['cache_before']==d['cache_after'],
      'native_gates_present':'native_gates' in d,'native_gates':d.get('native_gates'),'before_cleanup_state':d['before_cleanup_state'],
      'execution_model_reported':d['execution_model'],'flight_sdr_display':s,'derived_timing':timing,
      'sample_count':len(d['samples']),'live_samples':live,'armed_capture_samples':scalar_samples,
      'midflight_sampling_flags':{k:v for k,v in sampling.items() if k not in ('armed','capture_sample')},
      'captures':captures,'pixel_analysis_performed':False,
      'interpretation':'Original acquisition and additive gates passed; pixel/latency acceptance remains separate.' if major==13 else 'The complete original gate and unchanged additive both failed. Reported loop return/cleanup/resting values and two snapshot records do not turn incomplete acquisition into acceptance.'}
    adaptations[key]={'four_literal_path_or_major_changes_only':changes,'adapted_gate_sha256':digest(code.encode())}
    if major==13:
        steps=load(directory/'root-steps.json');assert [v['step'] for v in steps]==['wrapper','native-base','native-sdr','endpoint-controls']
        assert all(v['exit_code']==0 for v in steps)
        endpoint=load(directory/'endpoint-controls.json');assert endpoint['exact_endpoint_controls'] is True
        for phase in ('before','settled'):
            v=endpoint['checks'][phase];assert v['status']=='performed' and v['raw']['exact'] is True and v['srgb']['exact'] is True and v['embedded_icc_identical'] is True
        for name,meta in endpoint['inputs'].items():assert digest(read(name))==meta['sha256'],name
        endpoint_records[key]={'root_steps':steps,'root_endpoint_controls':endpoint,'scope':'Saved root pixel computations, source-input hashes independently bound; no pixel decoding or recomputation by this review.'}
end=datetime.datetime.fromisoformat(processes['13-default']['receipt']['finished_utc'])
ready=datetime.datetime.fromisoformat(control['recorded_utc']);begin=datetime.datetime.fromisoformat(processes['13-baked-pair']['receipt']['started_utc'])
assert end<=ready<=begin
assert all(datetime.datetime.fromisoformat(v['finished_utc'])<=ready for v in endpoint_records['13-default']['root_steps'])
assert digest(read(B))==a.binary_sha;actual_binary['actual_bytes_read_after_gates']=True
result={'status':'two13_native_pass_14_partial','scope':'Offline native/package/source and timing extraction only; no native app, compile, CI or pixel operation.',
 'ci_run':40129608288,'source_commit':'dcf1fdb3ef1a3f689898d08af4e3065b0646b481','harness_commit':'ac426048bcea23eafa8aefe75c4620590e140dc5',
 'workflow':{'path':str(Path(a.workflow).resolve()),'sha256':a.workflow_sha,'original_native_prefix_sha256':digest(prefix.encode())},
 'additive':{'path':str(Path(a.additive_gate).resolve()),'sha256':a.additive_sha,'same_function_as_workflow':True},
 'exact_gate_adaptations':adaptations,'actual_binary':actual_binary,'actual_readonly_binary_checks':checks,
 'package':{'tar_sha256':a.tar_sha,'package_manifest_members_verified':len(members),'source_map_members_verified':len(provenance['files']),'assembly_sha256':digest(assembly),'tar_member_map_exact':True,'saved_package_verification':package_receipt},
 'root_endpoint_control_receipt':{'path':str(Path(a.root_control_receipt).resolve()),'contents':control,'all_referenced_input_hashes_checked':True},
 'root_endpoint_control_records':endpoint_records,'default13_ready_before_candidate_started':True,'processes':processes,'input_files':inputs,
 'pixel_acceptance':'NOT PERFORMED','limits':'Two13 native/schema gates passed;14 is explicitly incomplete, with unchanged gates failing. First live observation and scalar samples are not presentation timestamps. No actual tone-map execution, visibility/color equivalence, unique cause or zero observer effect claim.'}
encoded=json.dumps(result,indent=2,sort_keys=True)+'\n';assert len(encoded.encode())<=196608,'Bounded review exceeded'
(OUT/'review.json').write_text(encoded)
print(json.dumps({'status':result['status'],'gate_exits':{k:[v['complete_original_native_execution_gate']['exit_code'],v['unchanged_additive_gate']['exit_code']] for k,v in processes.items()},'binary_sha256':a.binary_sha,'package_members':len(members),'source_map_members':len(provenance['files']),'pixel_analysis':'NOT PERFORMED','review_bytes':len(encoded.encode())}))
