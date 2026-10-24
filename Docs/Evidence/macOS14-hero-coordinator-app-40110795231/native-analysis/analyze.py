#!/usr/bin/env python3
"""Replay the pinned native gate offline; read originals, write one small summary."""
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

assert len(sys.argv) == 3, 'analyze.py INPUT_COHORT OUTPUT_DIRECTORY (run from workspace root)'
ROOT = Path.cwd().resolve()
COHORT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
assert OUT != COHORT and COHORT not in OUT.parents
assert not (OUT / 'summary.json').exists(), 'Refuse to overwrite an existing summary'
HARNESS = 'be6eb08a91e74d900cdaccc6d8730c81aefb96bc'
WORKFLOW = '.github/workflows/macos14-hero-coordinator-app-probe.yml'
WORKFLOW_SHA = '875747591a581fde4b4381482961405ab990cb279a878929a5627adc3791c7af'
inputs = {}

def fingerprint(path):
    data = path.read_bytes()
    meta = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    inputs[str(path)] = meta
    return meta

def load(path):
    fingerprint(path)
    return json.loads(path.read_text(), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))

workflow_bytes = subprocess.run(['git', 'show', HARNESS + ':' + WORKFLOW],
                                cwd=ROOT / 'outputs/Bern', check=True, capture_output=True).stdout
assert hashlib.sha256(workflow_bytes).hexdigest() == WORKFLOW_SHA
document = yaml.safe_load(workflow_bytes)
shell = next(step['run'] for step in document['jobs']['measure']['steps'] if 'run' in step)
start = shell.index('import hashlib,json,math\n')
gate = shell[start:shell.index('\nPY\n', start)] + '\n'
original_gate_sha = hashlib.sha256(gate.encode()).hexdigest()
changes = {
    "Path('evidence/runtime14')": f"Path({str(COHORT)!r})/('runtime'+str(major))",
    "d['expected_os_major']==14 and d['actual_os_major']==14": "d['expected_os_major']==major and d['actual_os_major']==major",
    "receipt['expected_os_major']==14": "receipt['expected_os_major']==major",
    "Path('probe/HeroCoordinatorAppProbe')": f"Path({str(COHORT / 'probe/HeroCoordinatorAppProbe')!r})",
}
for before, after in changes.items():
    assert gate.count(before) == 1, before
    gate = gate.replace(before, after)
ast.parse(gate, filename='adapted-pinned-native-gate')

package = load(COHORT / 'package-verification-local.json')
BINARY_SHA = package['binary_sha256']
TAR_SHA = package['archive_sha256']
for digest in (BINARY_SHA, TAR_SHA):
    assert isinstance(digest, str) and len(digest) == 64 and set(digest) <= set('0123456789abcdef')
assert fingerprint(COHORT / 'probe/HeroCoordinatorAppProbe')['sha256'] == BINARY_SHA
assert fingerprint(COHORT / 'build/hero-coordinator-app-probe.tar.gz')['sha256'] == TAR_SHA
assert package['archive_sha256'] == TAR_SHA
manifest = COHORT / 'probe/SHA256SUMS'
assert fingerprint(manifest)['sha256'] == package['package_manifest_sha256']
members = []
for line in manifest.read_text().splitlines():
    expected, name = line.split('  ', 1)
    relative = Path(name)
    assert not relative.is_absolute() and '..' not in relative.parts
    assert fingerprint(COHORT / 'probe' / relative)['sha256'] == expected, name
    members.append(name)
assert sorted(members) == sorted(package['verified_package_members'])
provenance = load(COHORT / 'probe/source-provenance.json')
assert provenance['kind'] == 'actual_coordinator_app_loop_fixture'
assert provenance['local_compile_attempted'] is False and 'local_static_preflight' not in provenance
for name, meta in provenance['files'].items():
    assert fingerprint(COHORT / 'probe' / name)['sha256'] == meta['sha256'], name

processes = {}
for major in (13, 14):
    # Exact original assertions, with only the four recorded path/OS substitutions.
    exec(compile(gate, 'adapted-pinned-native-gate', 'exec'), {'major': major})
    directory = COHORT / ('runtime' + str(major))
    report = load(directory / 'report.json')
    receipt = load(directory / 'run-receipt.json')
    assert receipt['binary_sha256'] == BINARY_SHA
    captures = []
    for capture in report['captures']:
        assert fingerprint(directory / capture['png'])['sha256'] == capture['png_sha256']
        value = {key: capture[key] for key in (
            'phase', 'png', 'png_sha256', 'raw_buffer_sha256', 'owner_pid', 'window_id',
            'window_frame', 'capture_size', 'rois', 'capture_icc_sha256', 'current_headroom',
            'potential_headroom', 'key', 'active', 'live_metal_count',
            'capture_before_uptime', 'capture_after_uptime')}
        if capture['phase'] == 'in-flight':
            value['consecutive_equal_buffers_required'] = capture['consecutive_equal_buffers_required']
            value['state_before'] = capture['state_before']
            value['state_after'] = capture['state_after']
        else:
            value['consecutive_equal_buffers'] = capture['consecutive_equal_buffers']
            value['bracket_counts'] = {key: {field: capture[key][field] for field in (
                'uptime', 'flight_count', 'timer_exists', 'temporary_flight_view_count')}
                for key in ('state_before', 'state_after')}
        captures.append(value)
    sampling = report['midflight_sampling']
    armed, captured = sampling['armed'], sampling['capture_sample']
    mid = report['captures'][1]
    live_samples = [sample for sample in report['samples'] if sample['flights']]
    processes[str(major)] = {
        'native_gate': 'PASS', 'execution_model_gate': 'PASS', 'report_path': str(directory / 'report.json'),
        'receipt_path': str(directory / 'run-receipt.json'), 'own_pid': receipt['own_pid'],
        'binary_sha256': receipt['binary_sha256'], 'wrapper_exit_code': receipt['exit_code'],
        'wrapper_elapsed_seconds': receipt['elapsed_seconds'], 'window_seconds': report['window_seconds'],
        'normal_before': report['normal_before'], 'normal_after': report['normal_after'],
        'frontmost_before': report['frontmost_before'], 'frontmost_after': report['frontmost_after'],
        'activation_calls': report['activation_calls'], 'cache_unchanged': report['cache_unchanged'],
        'cache_before_equals_after': report['cache_before'] == report['cache_after'],
        'default_motion_environment': receipt['bern_motion_environment'],
        'execution_model': report['execution_model'],
        'derived_execution_durations': {
            'loop_elapsed_seconds': report['execution_model']['loop_return_uptime'] - report['execution_model']['loop_entry_uptime'],
            'launch_after_loop_entry_seconds': report['execution_model']['launch_completed_uptime'] - report['execution_model']['loop_entry_uptime'],
            'preload_seconds': report['execution_model']['preload_completed_uptime'] - report['execution_model']['preload_started_uptime'],
            'terminal_to_loop_return_seconds': report['execution_model']['loop_return_uptime'] - report['execution_model']['terminal_uptime']},
        'native_gates': report['native_gates'], 'before_cleanup_state': report['before_cleanup_state'],
        'observed_flight_identities': report['observed_flight_identities'],
        'sample_count': len(report['samples']), 'live_sample_count': len(live_samples),
        'midflight_sampling': sampling, 'flat_mid_fields_crosschecked_by_original_gate': True,
        'trigger_refers_to': mid['trigger_refers_to'],
        'derived_sampling_gaps': {
            'sample_index_gap': captured['sample_index'] - armed['sample_index'],
            'uptime_gap_seconds': captured['uptime'] - armed['uptime'],
            'progress_gap': captured['progress'] - armed['progress'],
            'capture_call_elapsed_seconds': mid['capture_after_uptime'] - mid['capture_before_uptime'],
            'armed_to_capture_before_seconds': mid['capture_before_uptime'] - armed['uptime'],
            'capture_sample_to_capture_before_seconds': mid['capture_before_uptime'] - captured['uptime']},
        'captures': captures, 'pixel_acceptance': report['pixel_acceptance'],
        'pixel_analysis_performed': False}

result = {
    'success': True, 'scope': 'Offline native-gate/input-hash review only; no UI, compile, CI, source/image copy or pixel algorithm execution.',
    'ci_run': 40110795231, 'harness_commit': HARNESS,
    'parent_product_checkpoint_commit': 'ace6e1ee4acda71e26616ef0a21a3fc94d085829',
    'workflow_source': {'commit': HARNESS, 'path': WORKFLOW, 'sha256': WORKFLOW_SHA},
    'exact_gate_adaptation': {'original_gate_sha256': original_gate_sha, 'literal_changes_only': changes,
                             'adapted_gate_sha256': hashlib.sha256(gate.encode()).hexdigest()},
    'package_verification': {'current_binary_sha256': BINARY_SHA, 'current_tar_sha256': TAR_SHA,
                             'package_members_verified': len(members), 'source_map_members_verified': len(provenance['files']),
                             'original_product_source_commit': provenance['product_source_commit'],
                             'signature_scope': 'Saved root verification receipt; no fresh signing command.'},
    'processes': processes, 'pixel_acceptance': 'NOT PERFORMED',
    'interpretation': 'Full native and app-loop metadata gates pass only acquisition. Armed/capture are adjacent observer callbacks under NSApplication.run, not presentation timestamps. Terminal own-queue applicationDefined wake is not physical input, a sampling action, animation flush or presentation fence. Invalidation flag records a source path, not an independent Timer.isValid getter. No pixel/state synchrony, visibility, color equality, fix/cause or zero-observer-effect claim.',
    'input_files': inputs}
encoded = json.dumps(result, indent=2, sort_keys=True) + '\n'
assert len(encoded.encode()) <= 131072, 'Bounded output exceeded'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'summary.json').write_text(encoded)
print(json.dumps({'success': True, 'native_gates': {key: value['native_gate'] for key, value in processes.items()},
                  'sample_indices': {key: [value['midflight_sampling']['armed']['sample_index'], value['midflight_sampling']['capture_sample']['sample_index']] for key, value in processes.items()},
                  'progress': {key: [value['midflight_sampling']['armed']['progress'], value['midflight_sampling']['capture_sample']['progress']] for key, value in processes.items()},
                  'summary_bytes': len(encoded.encode()), 'input_files': len(inputs), 'pixel_analysis': 'NOT PERFORMED'}, sort_keys=True))
