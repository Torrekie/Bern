#!/usr/bin/env python3
"""Private syntax checks plus offline schema checks of two existing reports."""
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
assert Path.cwd().resolve() == ROOT, 'Run from workspace root.'
workflow = HERE / 'macos14-hero-route-probe.yml'
wrapper = HERE / 'run-route-one.py'
text = workflow.read_text()
doc = yaml.safe_load(text)
assert doc['on'] == {'workflow_dispatch': None}
assert doc['permissions'] == {'contents': 'read'}
assert doc['jobs']['build']['runs-on'] == 'macos-15'
assert doc['jobs']['measure']['runs-on'] == 'macos-14'
for value in (
    'ditto .github/scripts/hero-route-probe work/probe',
    'test "$sdk" = 26.2', '-target arm64-apple-macos13.0',
    'cat work/probe/ProductHero.base.swift work/probe/FloatCapture.swift.inc work/probe/Driver.swift.inc',
    "d['kind']=='actual_existing_overlay_static_route_fixture'",
    "d['runtime_static_route_default']=='root'", "d['required_backing_and_float_selected']=='off'",
    "d['runtime_float_mode_default']=='off'", "d['runtime_backing_mode_default']=='off'",
    'for mode in root overlay; do', 'python3 probe/run-route-one.py',
    "b['requested']=='off' and b['selected']=='off'",
    "f['provider_copy_calls']==0 and f['retained_primary_peak_count']==0",
    "d['cache_before']==d['cache_after']", "d['activation_calls']==0 and 0<d['window_seconds']<7.9",
    "c['consecutive_equal_buffers']>=5", "c['owner_pid']==receipt['own_pid']",
):
    assert value in text, value
assert 'macos14-hero-backing-' not in text
assert 'hero-float-probe work/probe' not in text
ast.parse(wrapper.read_text(), filename=wrapper.name)
assert 'BERN_HERO_LAYER_OBSERVE="off",BERN_HERO_STATIC_ROUTE=mode' in wrapper.read_text()
assert 'BERN_HERO_FLOAT_CAPTURE="off"' in wrapper.read_text()
assert 'p.wait(timeout=15)' in wrapper.read_text()
checks = []
report_gate = None
for job_name, job in doc['jobs'].items():
    for index, step in enumerate(job['steps']):
        if 'run' not in step:
            continue
        shell = step['run']
        result = subprocess.run(['bash', '-n'], input=shell, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
        lines = shell.splitlines()
        count = 0
        i = 0
        while i < len(lines):
            if lines[i].lstrip().startswith('python3 ') and "<<'PY'" in lines[i]:
                start = i + 1
                end = start
                while end < len(lines) and lines[end] != 'PY':
                    end += 1
                assert end < len(lines)
                code = '\n'.join(lines[start:end]) + '\n'
                ast.parse(code, filename=f'{job_name}:{index}:{count}')
                if code.startswith('import base64,hashlib,json,math,sys\n'):
                    report_gate = code
                count += 1
                i = end
            i += 1
        checks.append({'job': job_name, 'step': index, 'bash_n': 'PASS',
                       'python_heredocs_ast': count, 'shell_body_executed': False})
assert len(checks) == 2 and sum(x['python_heredocs_ast'] for x in checks) == 4
assert report_gate is not None
fingerprint_path = ROOT / 'work/native-pq-hero-static-route13/build-fingerprint.json'
fingerprint = json.loads(fingerprint_path.read_text())
local_binary_sha = fingerprint['hashes']['HeroFloatCaptureProbe']
assert local_binary_sha == '8fb1b7f57b60de0948866bb950be07696b15196d9f89e2fda994fac1a22d3fac'
transforms = {
    "Path('evidence/runtime14')/mode": "Path('work/native-pq-hero-static-route13')/('runtime13-'+mode)",
    "d['expected_os_major']==14 and d['actual_os_major']==14": "d['expected_os_major']==13 and d['actual_os_major']==13",
    "receipt['expected_os_major']==14": "receipt['expected_os_major']==13",
    "hashlib.sha256(Path('probe/HeroFloatProbe').read_bytes()).hexdigest()": repr(local_binary_sha),
}
for before, after in transforms.items():
    assert report_gate.count(before) == 1, before
    report_gate = report_gate.replace(before, after)
ast.parse(report_gate)
inputs = {}
def record(path):
    data = path.read_bytes()
    inputs[str(path.relative_to(ROOT))] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
results = []
saved_argv = sys.argv[:]
for mode in ('root', 'overlay'):
    sys.argv = ['offline-adapted-route-gate', mode]
    exec(compile(report_gate, 'offline-adapted-route-gate', 'exec'), {})
    p = ROOT / 'work/native-pq-hero-static-route13' / ('runtime13-' + mode)
    for name in ('report.json', 'run-receipt.json'):
        record(p / name)
    results.append({'mode': mode, 'schema': 'PASS'})
sys.argv = saved_argv
record(fingerprint_path)
provenance = json.loads((HERE / 'provenance.json').read_text())
for item in provenance['base_inputs']:
    data = (HERE / item['private_original_file']).read_bytes()
    assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
for item in provenance['route_schema_inputs']:
    record(ROOT / item['path'])
    assert inputs[item['path']]['sha256'] == item['sha256']
report = {'success': True, 'scope': 'YAML/Python AST/bash syntax and offline existing-report schema only. No app/wrapper/compiler/CI execution or pixel comparison.',
          'yaml': 'PASS', 'wrapper_ast': 'PASS', 'syntax_checks': checks,
          'offline_existing_local13_schema': results, 'literal_transforms_only': transforms,
          'local_binary_check': 'Local binary was already removed. Existing receipts match the saved build-fingerprint SHA only; no current local binary rehash. Formal CI workflow retains its actual packaged-file hash check.',
          'adapted_gate_sha256': hashlib.sha256(report_gate.encode()).hexdigest(),
          'workflow_sha256': hashlib.sha256(workflow.read_bytes()).hexdigest(),
          'wrapper_sha256': hashlib.sha256(wrapper.read_bytes()).hexdigest(), 'input_files': inputs}
(HERE / 'validation.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: v for k, v in report.items() if k not in ('input_files', 'literal_transforms_only')}, sort_keys=True))
