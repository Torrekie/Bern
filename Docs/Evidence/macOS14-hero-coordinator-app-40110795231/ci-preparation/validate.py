#!/usr/bin/env python3
"""Static preparation validation only; do not execute workflow/native bodies."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
workflow = HERE / 'macos14-hero-coordinator-app-probe.yml'
wrapper = HERE / 'run-one.py'
text = workflow.read_text()
doc = yaml.safe_load(text)
provenance = json.loads((HERE / 'provenance.json').read_text())
assert doc['on'] == {'workflow_dispatch': None}
assert doc['permissions'] == {'contents': 'read'}
assert doc['jobs']['build']['runs-on'] == 'macos-15'
assert doc['jobs']['measure']['runs-on'] == 'macos-14'
assert doc['jobs']['build']['env']['DEVELOPER_DIR'] == '/Applications/Xcode_26.3.app/Contents/Developer'
assert 'PENDING' not in text and 'PLACEHOLDER' not in text
assert text.count('python3 probe/run-one.py ') == 1
for identity in ('ditto .github/scripts/hero-coordinator-app-probe work/probe',
                 'HeroCoordinatorAppProbe', 'hero-coordinator-app-probe.tar.gz',
                 'macos14-hero-coordinator-app-probe-build', 'macos14-hero-coordinator-app-evidence'):
    assert identity in text, identity
for excluded in ('HeroCoordinatorDelayProbe', 'hero-coordinator-delay-probe', 'FloatCapture.swift.inc',
                 'BackingObservation.swift.inc', 'StaticRoute.swift.inc'):
    assert excluded not in text, excluded
for required in ('test "$sdk" = 26.2', '-target arm64-apple-macos13.0',
                 "d['kind']=='actual_coordinator_app_loop_fixture'",
                 "'local_static_preflight' not in d and d['local_compile_attempted'] is False",
                 "d['files']['Driver.swift.inc']['sha256']=='" + provenance['driver_sha256'] + "'",
                 "execution['kind']=='nsapplication_run_delegate_default_timer'",
                 "execution['sampler_observed_modes']==[execution['sampler_mode']]",
                 "execution['sampler_interval_seconds']==1/60",
                 "execution['wake_type']=='applicationDefined'",
                 "execution['sampler_invalidated_before_stop'] is True",
                 "execution['wake_after_terminal'] is True and execution['wake_posted_to_own_app_queue'] is True"):
    assert required in text, required

def python_blocks(shell):
    lines = shell.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith('python3 ') and "<<'PY'" in lines[i]:
            start = i + 1
            end = start
            while end < len(lines) and lines[end] != 'PY':
                end += 1
            assert end < len(lines)
            yield '\n'.join(lines[start:end]) + '\n'
            i = end
        i += 1

old_doc = yaml.safe_load((HERE / 'delay-workflow.original.yml').read_text())
old_gate = list(python_blocks(next(s['run'] for s in old_doc['jobs']['measure']['steps'] if 'run' in s)))[-1]
new_gate = list(python_blocks(next(s['run'] for s in doc['jobs']['measure']['steps'] if 'run' in s)))[-1]
native, metadata = new_gate.split('# Append-only app-loop metadata gate;', 1)
expected_native = old_gate.replace('HeroCoordinatorDelayProbe', 'HeroCoordinatorAppProbe')
assert native == expected_native, 'Inherited delay native gate changed'
assert metadata and "capture_sample_progress']<0.8" not in new_gate

wrapper_text = wrapper.read_text()
ast.parse(wrapper_text, filename=wrapper.name)
assert hashlib.sha256(wrapper.read_bytes()).hexdigest() == '9ab93068745f9338c076328bfe28ceb1814b55b011972af34be1999736c5acf6'
assert "assert len(sys.argv)==5" in wrapper_text
assert "command=list(map(str,[binary,asset,out]))" in wrapper_text
assert "env.pop('BERN_MOTION',None)" in wrapper_text and 'p.wait(timeout=15)' in wrapper_text

checks = []
for name, job in doc['jobs'].items():
    for index, step in enumerate(job['steps']):
        if 'run' not in step:
            continue
        shell = step['run']
        result = subprocess.run(['bash', '-n'], input=shell, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
        blocks = list(python_blocks(shell))
        for number, block in enumerate(blocks):
            ast.parse(block, filename=f'{name}:{index}:{number}')
        checks.append({'job': name, 'step': index, 'bash_n': 'PASS',
                       'python_heredocs_ast': len(blocks), 'shell_body_executed': False})
assert len(checks) == 2 and sum(c['python_heredocs_ast'] for c in checks) == 4
for base in provenance['base_inputs']:
    data = (HERE / base['private_file']).read_bytes()
    assert len(data) == base['bytes'] and hashlib.sha256(data).hexdigest() == base['sha256']
source = provenance['source_provenance_input']
sp = ROOT / source['path']
assert hashlib.sha256(sp.read_bytes()).hexdigest() == source['sha256']
package = json.loads(sp.read_text())
assert package['kind'] == 'actual_coordinator_app_loop_fixture'
assert package['local_compile_attempted'] is False and 'local_static_preflight' not in package
for name, member in package['files'].items():
    assert hashlib.sha256((sp.parent / name).read_bytes()).hexdigest() == member['sha256'], name
assert (sp.parent / 'run-one.py').read_bytes() == wrapper.read_bytes()
driver = ROOT / provenance['driver_path']
data = driver.read_bytes()
assert hashlib.sha256(data).hexdigest() == provenance['driver_sha256']
assert package['files']['Driver.swift.inc']['sha256'] == provenance['driver_sha256']
assert (sp.parent / 'Driver.swift.inc').read_bytes() == data
driver_text = data.decode()
for required in ('RunLoop.main.add(timer, forMode: .default)',
                 'guard RunLoop.current.currentMode == .default',
                 '"sampler_mode": RunLoop.Mode.default.rawValue',
                 'app.delegate = state; state.noteLoopEntry(); app.run(); state.noteLoopReturn()',
                 'sampler?.invalidate(); sampler = nil; samplerStopped = true',
                 'stopCalls += 1; NSApplication.shared.stop(nil)',
                 'wakeAfterTerminal = terminal; NSApplication.shared.postEvent(wake, atStart: false)'):
    assert required in driver_text, required
assert driver_text.count('Task {') == 1, 'Expected only the original asynchronous preload task'
assert 'RunLoop.current.run(mode:' not in driver_text
report = {'success': True,
          'scope': 'Static YAML/Python AST/bash syntax, inherited gate exact-prefix proof and source hashes only; no Swift typecheck, compilation, app, wrapper, workflow or runtime-schema execution.',
          'yaml': 'PASS', 'wrapper_ast': 'PASS', 'checks': checks,
          'base_workflow_hash': 'PASS', 'inherited_delay_native_gate': 'PASS — exact prefix except binary identity',
          'driver_sha256': provenance['driver_sha256'], 'driver_bytes': len(data),
          'driver_lines': len(driver_text.splitlines()), 'source_map_members_verified': len(package['files']),
          'new_driver_local_compile_attempted': False,
          'runtime_schema_execution': 'NOT PERFORMED — no actual app-loop runtime report used',
          'workflow_sha256': hashlib.sha256(workflow.read_bytes()).hexdigest(),
          'wrapper_sha256': hashlib.sha256(wrapper.read_bytes()).hexdigest()}
(HERE / 'static-review.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps(report, sort_keys=True))
