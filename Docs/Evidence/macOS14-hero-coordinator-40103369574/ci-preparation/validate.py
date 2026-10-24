#!/usr/bin/env python3
"""Static preparation validation only; never execute workflow bodies or native code."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
workflow = HERE / 'macos14-hero-coordinator-probe.yml'
wrapper = HERE / 'run-one.py'
text = workflow.read_text()
doc = yaml.safe_load(text)
assert doc['on'] == {'workflow_dispatch': None}
assert doc['permissions'] == {'contents': 'read'}
assert doc['jobs']['build']['runs-on'] == 'macos-15'
assert doc['jobs']['measure']['runs-on'] == 'macos-14'
assert doc['jobs']['build']['env']['DEVELOPER_DIR'] == '/Applications/Xcode_26.3.app/Contents/Developer'
for required in (
    'ditto .github/scripts/hero-coordinator-probe work/probe',
    'test "$sdk" = 26.2', '-target arm64-apple-macos13.0',
    "printf 'import AppKit\\nimport SwiftUI\\n' > work/probe/ProductHero.swift",
    'cat work/probe/ProductHero.exact.swift work/probe/Driver.swift.inc >> work/probe/ProductHero.swift',
    "d['kind']=='actual_coordinator_replacement_fixture'",
    "d['original_hero_sha256']=='8e1e90a00ff2f386a38ed8c4977af27a505571051560d50406e9e54b69ed186c'",
    "d['files']['Driver.swift.inc']['sha256']=='d8ed3e8d5716f65b00a6d14fd1007d89eaf30d5aca58446344263d59375a739b'",
    "receipt['bern_motion_environment']=='unset'",
    "c['consecutive_equal_buffers']>=5", "mid['consecutive_equal_buffers_required'] is False",
    "0.2<mid['trigger_progress']<0.8", "trigger['timer_exists'] is True",
    "d['observed_flight_identities']==identities", "sample['timer_exists'] is True",
    "d['cache_before']==d['cache_after']", "d['frontmost_before']==d['frontmost_after']",
    "resting(d['before_cleanup_state'])", "native['transition_count']==1",
    "'source_no_longer_attached','temporary_view_removed'",
    "'x':16,'y':24,'width':320,'height':180", "'x':352,'y':244,'width':320,'height':180",
):
    assert required in text, required
for excluded in ('FloatCapture.swift.inc', 'BackingObservation.swift.inc', 'StaticRoute.swift.inc',
                 'macos14-hero-route-', 'for mode in root overlay', 'Coordinator schema gate pending'):
    assert excluded not in text, excluded
assert text.count('python3 probe/run-one.py ') == 1
wrapper_text = wrapper.read_text()
ast.parse(wrapper_text, filename=wrapper.name)
assert "assert len(sys.argv)==5" in wrapper_text
assert "command=list(map(str,[binary,asset,out]))" in wrapper_text
assert "env=dict(os.environ)" in wrapper_text and "env.pop('BERN_MOTION',None)" in wrapper_text
assert "env['BERN_HERO_EXPECT_OS']=str(major)" in wrapper_text
assert 'p.wait(timeout=15)' in wrapper_text and 'except subprocess.TimeoutExpired:p.kill();' in wrapper_text
for excluded in ('BERN_HERO_FLOAT_CAPTURE', 'BERN_HERO_LAYER_OBSERVE', 'BERN_HERO_STATIC_ROUTE'):
    assert excluded not in wrapper_text
checks = []
for name, job in doc['jobs'].items():
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
                ast.parse('\n'.join(lines[start:end]) + '\n', filename=f'{name}:{index}:{count}')
                count += 1
                i = end
            i += 1
        checks.append({'job': name, 'step': index, 'bash_n': 'PASS',
                       'python_heredocs_ast': count, 'shell_body_executed': False})
assert len(checks) == 2 and sum(c['python_heredocs_ast'] for c in checks) == 4
provenance = json.loads((HERE / 'provenance.json').read_text())
base = provenance['base_workflow']
data = (HERE / base['private_original_file']).read_bytes()
assert len(data) == base['bytes'] and hashlib.sha256(data).hexdigest() == base['sha256']
driver = ROOT / 'work/hero-coordinator-preparation/Driver.swift.inc'
data = driver.read_bytes()
assert hashlib.sha256(data).hexdigest() == 'd8ed3e8d5716f65b00a6d14fd1007d89eaf30d5aca58446344263d59375a739b'
assert len(data.decode().splitlines()) == 353
report = {'success': True, 'scope': 'Static YAML/Python AST/bash syntax and frozen source hash only. No runtime report exists for schema execution; no Swift typecheck/compile, app, wrapper or CI execution by this preparation.',
          'yaml': 'PASS', 'wrapper_ast': 'PASS', 'checks': checks,
          'base_workflow_hash': 'PASS', 'driver_sha256': hashlib.sha256(data).hexdigest(),
          'driver_bytes': len(data), 'driver_lines': 353,
          'runtime_schema_execution': 'NOT PERFORMED — no actual coordinator runtime report available',
          'workflow_sha256': hashlib.sha256(workflow.read_bytes()).hexdigest(),
          'wrapper_sha256': hashlib.sha256(wrapper.read_bytes()).hexdigest()}
(HERE / 'static-validation.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps(report, sort_keys=True))
