#!/usr/bin/env python3
"""Offline only: apply the draft report gate to root's existing local13 reports."""
import ast
import hashlib
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
fixture = ROOT / 'work/native-pq-hero-backing-observer'
workflow = HERE / 'macos14-hero-backing-probe.yml'
doc = yaml.safe_load(workflow.read_text())
shell = next(s['run'] for s in doc['jobs']['measure']['steps'] if 'run' in s)
start = shell.index('import base64,hashlib,json,math,sys\n')
end = shell.index('\nPY\n', start)
code = shell[start:end] + '\n'
transforms = {
    "Path('evidence/runtime14')/mode": "Path('work/native-pq-hero-backing-observer')/('runtime13-'+mode)",
    "d['expected_os_major']==14 and d['actual_os_major']==14": "d['expected_os_major']==13 and d['actual_os_major']==13",
    "receipt['expected_os_major']==14": "receipt['expected_os_major']==13",
    "Path('probe/HeroFloatProbe')": "Path('work/native-pq-hero-backing-observer/HeroFloatCaptureProbe')",
}
for old, new in transforms.items():
    assert code.count(old) == 1, old
    code = code.replace(old, new)
ast.parse(code, filename='adapted-local13-report-gate')
assert Path.cwd().resolve() == ROOT, 'Run from workspace root; report paths are relative.'
original_argv = sys.argv[:]
results = []
for mode in ('off', 'on'):
    sys.argv = ['adapted-local13-report-gate', mode]
    exec(compile(code, 'adapted-local13-report-gate', 'exec'), {})
    inputs = {}
    for name in ('report.json', 'run-receipt.json'):
        p = fixture / ('runtime13-' + mode) / name
        inputs[name] = {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    results.append({'mode': mode, 'schema_gate': 'PASS', 'inputs': inputs})
sys.argv = original_argv
report = {'success': True, 'scope': 'Existing local13 JSON/receipt/PNG-count and binary-hash checks only. No app/wrapper/compiler/CI execution; no PNG pixel comparison.',
          'workflow_sha256': hashlib.sha256(workflow.read_bytes()).hexdigest(),
          'adapted_gate_sha256': hashlib.sha256(code.encode()).hexdigest(),
          'literal_transforms_only': transforms, 'results': results}
(HERE / 'local13-schema-validation.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps(report, sort_keys=True))
