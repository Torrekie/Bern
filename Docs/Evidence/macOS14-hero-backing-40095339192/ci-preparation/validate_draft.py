#!/usr/bin/env python3
"""Parse private workflow/Python and bash -n only; never execute workflow bodies."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
workflow = HERE / 'macos14-hero-backing-probe.yml'
wrapper = HERE / 'run-backing-one.py'
text = workflow.read_text()
doc = yaml.safe_load(text)
assert doc['on'] == {'workflow_dispatch': None}
assert doc['permissions'] == {'contents': 'read'}
assert doc['jobs']['build']['runs-on'] == 'macos-15'
assert doc['jobs']['measure']['runs-on'] == 'macos-14'
assert doc['jobs']['build']['env']['DEVELOPER_DIR'] == '/Applications/Xcode_26.3.app/Contents/Developer'
assert 'BACKING_SCHEMA_VALIDATION_INSERT' not in text
for required in (
    'test "$sdk" = 26.2', '-target arm64-apple-macos13.0',
    'ditto .github/scripts/hero-float-probe work/probe',
    'cat work/probe/ProductHero.base.swift work/probe/FloatCapture.swift.inc work/probe/Driver.swift.inc',
    "d['kind']=='original_snapshot_float_capture_fixture'",
    "d['runtime_float_mode_default']=='off'", "'run-backing-one.py' in d['files']",
    'for mode in off on; do', 'python3 probe/run-backing-one.py',
    "f['requested']=='off' and f['selected']=='off'",
    "f['provider_copy_calls']==0 and f['retained_primary_peak_count']==0",
    "f['records']==[] and f['total_raw_bytes']==0",
    "b['stage']=='post_png_post_final_guards_pre_teardown'",
    "ids[1:]==root_ids", "d['cache_unchanged'] is True",
    "d['cache_before']==d['cache_after']",
    "d['activation_calls']==0 and 0<d['window_seconds']<7.9",
    "frame['width']==320 and frame['height']==180",
    "frame==c['rois'][record['role']]['host_top_left_points']",
    "d['frontmost_before']==d['frontmost_after']",
    "c['consecutive_equal_buffers']>=5", "c['owner_pid']==receipt['own_pid']",
):
    assert required in text, required
assert 'macos14-hero-float-' not in text
ast.parse(wrapper.read_text(), filename=wrapper.name)
checks = []
for job_name, job in doc['jobs'].items():
    for index, step in enumerate(job['steps']):
        if 'run' not in step:
            continue
        shell = step['run']
        result = subprocess.run(['bash', '-n'], input=shell, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
        python_blocks = 0
        lines = shell.splitlines()
        i = 0
        while i < len(lines):
            if lines[i].lstrip().startswith('python3 ') and "<<'PY'" in lines[i]:
                start = i + 1
                end = start
                while end < len(lines) and lines[end] != 'PY':
                    end += 1
                assert end < len(lines), 'Unterminated Python heredoc'
                ast.parse('\n'.join(lines[start:end]) + '\n', filename=f'{job_name}:{index}:heredoc-{python_blocks}')
                python_blocks += 1
                i = end
            i += 1
        checks.append({'job': job_name, 'step': index, 'name': step['name'],
                       'bash_n': 'PASS', 'python_heredocs_ast': python_blocks,
                       'shell_body_executed': False})
assert len(checks) == 2 and sum(c['python_heredocs_ast'] for c in checks) == 4
wrapper_text = wrapper.read_text()
assert 'BERN_HERO_FLOAT_CAPTURE="off",BERN_HERO_LAYER_OBSERVE=mode' in wrapper_text
assert 'p.wait(timeout=15)' in wrapper_text
assert 'except subprocess.TimeoutExpired:p.kill();' in wrapper_text
provenance = json.loads((HERE / 'provenance.json').read_text())
for original in provenance['base_inputs']:
    data = (HERE / original['private_original_file']).read_bytes()
    assert len(data) == original['bytes']
    assert hashlib.sha256(data).hexdigest() == original['sha256']
schema = (HERE / provenance['schema_source']['private_copy']).read_bytes()
assert len(schema) == provenance['schema_source']['bytes']
assert hashlib.sha256(schema).hexdigest() == provenance['schema_source']['sha256']
report = {'success': True, 'scope': 'Static parse and bash syntax only; no workflow body, wrapper, native app, compiler or CI execution.',
          'yaml': 'PASS', 'wrapper_ast': 'PASS', 'checks': checks,
          'source_original_hashes': 'PASS', 'schema_copy_hash': 'PASS',
          'workflow_sha256': hashlib.sha256(workflow.read_bytes()).hexdigest(),
          'wrapper_sha256': hashlib.sha256(wrapper.read_bytes()).hexdigest()}
(HERE / 'static-validation.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps(report, sort_keys=True))
