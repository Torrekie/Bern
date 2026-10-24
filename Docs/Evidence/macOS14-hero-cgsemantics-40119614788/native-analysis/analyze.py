#!/usr/bin/env python3
"""Replay complete saved native/ICC/semantics gate; byte hashes only, no pixel decode."""
import ast
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
import yaml

assert len(sys.argv) == 3, 'analyze.py COHORT OUTPUT_DIRECTORY (workspace cwd)'
ROOT = Path.cwd().resolve(); D = Path(sys.argv[1]).resolve(); OUT = Path(sys.argv[2]).resolve()
assert OUT != D and D not in OUT.parents and not (OUT / 'summary.json').exists()
package_path = OUT / 'package-verification.json'
package = json.loads(package_path.read_text())
assert package['complete'] is True
assert package['binary_sha256'] == '68974a3fe0ae28c23ef47de9657fbc6d34287bb36f50d12d6ac69d52b3eee334'
assert package['package_members_currently_hashed'] == 29 and package['source_map_currently_hashed'] == 21
inputs = {p: dict(meta, hash_stage='actual_precleanup_package_check') for p, meta in package['input_files'].items()}

def fp(path):
    data = path.read_bytes(); meta = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'hash_stage': 'current_offline_analysis'}
    inputs[str(path)] = meta; return meta

def load(path):
    fp(path)
    return json.loads(path.read_text(), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))

fp(package_path)
workflow_path = ROOT / 'outputs/Bern/.github/workflows/macos14-hero-cgsemantics-probe.yml'
workflow = workflow_path.read_bytes()
assert fp(workflow_path)['sha256'] == '8c5acfad83bf97255f10d73ba3dd2836350b53ecf0396dd65eec3e29923ccdcb'
document = yaml.safe_load(workflow)
shell = next(v['run'] for v in document['jobs']['measure']['steps'] if 'run' in v)
start = shell.index('import base64,hashlib,json,sys\n')
original = shell[start:shell.index('\nPY\n', start)]
adaptation = load(ROOT / 'work/hero-cgsemantics-validation-adaptation.json')
assert hashlib.sha256(original.encode()).hexdigest() == adaptation['original_gate_sha256']
assert adaptation['workflow_sha256'] == fp(workflow_path)['sha256']
changes = {
    "mode=sys.argv[1]; p=Path('evidence/runtime14')/mode; d=json.loads((p/'report.json').read_text())":
    "p=Path(sys.argv[1]).resolve(); mode=sys.argv[2]; major=int(sys.argv[3]); d=json.loads((p/'report.json').read_text())",
    "d['expected_os_major']==14 and d['actual_os_major']==14": "d['expected_os_major']==major and d['actual_os_major']==major"}
adapted = original
for before, after in changes.items():
    assert adapted.count(before) == 1, before
    adapted = adapted.replace(before, after)
gate_path = ROOT / 'work/hero-cgsemantics-runtime-validate.py'
adapted += '\n'  # Root's saved adapter adds one terminal LF after the two literal substitutions.
assert adapted == gate_path.read_text()
assert fp(gate_path)['sha256'] == adaptation['adapted_sha256']
ast.parse(adapted, filename='unchanged-native-ICC-semantics-gate')
processes = {}; by_host = {}; raw_comparisons = []
OLD = ROOT / 'outputs/Bern/Docs/Evidence/macOS14-hero-float-40091326190/same-binary-13-14'
for host in (13, 14):
    for mode in ('off', 'on'):
        directory = D / f'runtime{host}' / mode
        saved_argv = sys.argv[:]
        try:
            sys.argv = [str(gate_path), str(directory), mode, str(host)]
            exec(compile(adapted, str(gate_path), 'exec'), {})
        finally: sys.argv = saved_argv
        d = load(directory / 'report.json'); receipt = load(directory / 'run-receipt.json')
        assert receipt['binary_sha256'] == package['binary_sha256'] and receipt['expected_os_major'] == host
        assert receipt['mode'] == mode and receipt['timeout_seconds'] == 15 and 0 < receipt['elapsed_seconds'] < 15
        assert d['cache_before'] == d['cache_after'] and d['activation_calls'] == 0
        assert d['watchdog_seconds'] == 7.9 and d['collection_seconds'] == 7.2 and 0 < d['window_seconds'] < 7.9
        assert receipt['own_pid'] != d['frontmost_before']
        for key in ('normal_before', 'normal_after'):
            assert set(d[key]) == {'reduce_motion', 'reduce_transparency', 'increase_contrast'}
        window = d['captures'][0]['window_id']; assert type(window) is int and window > 0
        for sample in d['samples']:
            assert sample['owner_pid'] == receipt['own_pid'] and sample['window_id'] == window
            assert sample['live_metal_count'] == 0 and sample['key'] is False and sample['active'] is False
            assert sample['manager']['flight_count'] == 0 and sample['manager']['timer_exists'] is False
            assert sample['frontmost_pid'] == d['frontmost_before']
            assert sample['window_frame'] == d['captures'][0]['window_frame']
        captures = []
        for capture in d['captures']:
            assert capture['window_id'] == window
            png_path = directory / capture['png']; png = png_path.read_bytes()
            assert fp(png_path)['sha256'] == capture['png_sha256']
            assert png[:8] == b'\x89PNG\r\n\x1a\n' and png[12:16] == b'IHDR'
            assert list(struct.unpack('>II', png[16:24])) == capture['capture_size']
            trace = [v for v in d['samples'] if v['phase'] == capture['phase']]
            assert len(trace) >= 5 and all(v['raw_buffer_sha256'] == capture['raw_buffer_sha256'] for v in trace[-5:])
            captures.append({k: capture[k] for k in ('phase','png','png_sha256','raw_buffer_sha256',
                'owner_pid','window_id','window_frame','capture_size','current_headroom','potential_headroom',
                'capture_icc_sha256','consecutive_equal_buffers','live_metal_count','key','active','manager')})
        f = d['snapshot_float_capture']; details = []
        for record in f['records']:
            raw = directory / record['file']
            assert fp(raw)['sha256'] == record['sha256']
            semantics = record['drawing_semantics']
            details.append({'key': record['key'], 'raw_file': str(raw), 'raw_sha256': record['sha256'],
                'bytes': record['byte_count'], 'width': record['width'], 'height': record['height'],
                'drawing_semantics': semantics, 'provider_read_at_uptime_seconds': record['provider_read_at_uptime_seconds'],
                'released_at_uptime_seconds': f['released_at_uptime_seconds'],
                'derived_observation_timing': {
                    'provider_start_to_observation_seconds': semantics['observed_at_uptime_seconds'] - record['provider_read_at_uptime_seconds'],
                    'observation_end_to_release_seconds': f['released_at_uptime_seconds'] - semantics['observed_at_uptime_seconds'] - semantics['observation_elapsed_seconds']}})
        if mode == 'on':
            by_host[host] = {v['key']: v for v in details}
            old_directory = OLD / f'runtime{host}' / 'on'
            old = load(old_directory / 'report.json')
            old_records = {v['key']: v for v in old['snapshot_float_capture']['records']}
            for record in f['records']:
                previous = old_records[record['key']]
                previous_path = old_directory / previous['file']; before = fp(previous_path)
                assert before['sha256'] == previous['sha256'] and before['bytes'] == previous['byte_count']
                current = inputs[str(directory / record['file'])]
                raw_comparisons.append({'host': host, 'key': record['key'], 'new_path': str(directory / record['file']),
                    'old_path': str(previous_path), 'new_sha256': current['sha256'], 'old_sha256': before['sha256'],
                    'same_bytes_by_SHA_and_length': current['sha256'] == before['sha256'] and current['bytes'] == before['bytes'],
                    'new_byte_count': current['bytes'], 'old_byte_count': before['bytes']})
        observations = [{k: o[k] for k in ('key','width','height','bits_per_component','bits_per_pixel',
            'bitmap_info_raw','alpha_info_raw','byte_order_raw','pixel_format_raw','color_space_name',
            'icc_present','icc_byte_count','icc_sha256')} for o in d['snapshot_cgimage_observations']]
        processes[f'{host}-{mode}'] = {'native_ICC_semantics_gate': 'PASS', 'own_pid': receipt['own_pid'],
            'binary_sha256': receipt['binary_sha256'], 'wrapper_elapsed_seconds': receipt['elapsed_seconds'],
            'window_seconds': d['window_seconds'], 'normal_before': d['normal_before'], 'normal_after': d['normal_after'],
            'cache_before_equals_after': True, 'frontmost_before': d['frontmost_before'], 'frontmost_after': d['frontmost_after'],
            'sample_count': len(d['samples']), 'captures': captures, 'primary_descriptors_ICC': observations,
            'float_counts': {k: f[k] for k in ('primary_observation_count','cleanup_observation_count','provider_copy_calls',
                'retained_primary_peak_count','fixture_retained_images_after_export','total_raw_bytes','released_at_uptime_seconds')},
            'semantics_records': details, 'backing_observation': d['backing_observation']}
        log = directory / 'runtime.log'
        if log.is_file(): fp(log)

semantic_fields = ('rendering_intent_raw','is_mask','should_interpolate','decode_present','decode_count',
    'decode_values','decode_value_bits','decode_values_read','decode_nonfinite_index','color_space_model_raw','color_space_components')
comparisons = []
for key in ('baseline-body-named', 'baseline-body-custom'):
    values = {str(host): {k: by_host[host][key]['drawing_semantics'][k] for k in semantic_fields} for host in (13,14)}
    comparisons.append({'key': key, 'attributes_and_decode_by_host': values, 'all_reported_attributes_equal': values['13'] == values['14'],
        'limits': 'Equality covers these two retained original images per key at post-teardown observation only; no rendered-context/storage/visible-output cause follows.'})
control_receipts = []
for path in sorted((D / 'controls').glob('*.json')):
    control_receipts.append({'path': str(path), **fp(path), 'scope': 'Root pixel-control receipt fingerprint only; pixel algorithms not rerun and not native gates.'})
result = {'complete': True, 'ci_run': 40119614788, 'source_commit': '3c137f307576a44ffc58543def3cfec5b310c9d7',
    'harness_commit': '9989b904fe3bd2018d53ce91eec08bc52573fcc6',
    'scope': 'Offline original full native/ICC/semantics gate, retained-file hash and metadata comparison. No pixel decode/conversion, provider API, native/compiler/CI execution or source change.',
    'gate_verification': {'original_gate_sha256': adaptation['original_gate_sha256'], 'adapted_gate_sha256': adaptation['adapted_sha256'],
        'only_literal_changes': changes, 'serialization_only_extra_terminal_LF': True,
        'root_adaptation_metadata_matches': True},
    'precleanup_package_verification_path': str(package_path), 'package_counts': {'package': 29, 'source': 21},
    'processes': processes, 'crosshost_semantics': comparisons, 'same_host_old_float_raw_comparisons': raw_comparisons,
    'root_control_receipts_hashed_only': control_receipts, 'input_files': inputs,
    'input_stage_note': 'Actual binary/tar/full package hashes captured before root cleanup; current native/raw/PNG inputs hashed here. Per-entry hash_stage distinguishes them; no fresh signing claim.',
    'raw_window_buffer_scope': 'PNG/raw export file SHA independently checked; five-equal WindowServer-buffer hashes are report consistency evidence, no WindowServer recapture or pixel decoding.',
    'not_proven': ['Pixel/UI/full-flight acceptance','Unique rendering cause','Context/storage equivalence','General zero observer effect','Decode-present behavior when all actual decodes are nil']}
encoded = json.dumps(result, indent=2, sort_keys=True) + '\n'
assert len(encoded.encode()) <= 131072
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'summary.json').write_text(encoded)
(OUT / 'INPUT-SHA256SUMS').write_text(''.join(v['sha256'] + '  ' + path + '\n' for path, v in sorted(inputs.items())))
print(json.dumps({'complete': True, 'native_gates': {k: v['native_ICC_semantics_gate'] for k,v in processes.items()},
    'attrs_equal': {v['key']: v['all_reported_attributes_equal'] for v in comparisons},
    'raw_same_old': [v['same_bytes_by_SHA_and_length'] for v in raw_comparisons], 'input_files': len(inputs), 'bytes': len(encoded.encode())}, sort_keys=True))
