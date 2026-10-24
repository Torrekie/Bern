#!/usr/bin/env python3
"""Private static syntax/preservation proof only; never execute workflow bodies."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
workflow = HERE / 'macos14-hero-cgsemantics-probe.yml'
text = workflow.read_text()
old = yaml.safe_load((HERE / 'float-workflow.original.yml').read_text())
new = yaml.safe_load(text)
assert new['on'] == {'workflow_dispatch': None}
assert new['permissions'] == {'contents': 'read'}
assert new['jobs']['build']['runs-on'] == 'macos-15'
assert new['jobs']['measure']['runs-on'] == 'macos-14'
assert new['jobs']['build']['env'] == old['jobs']['build']['env']
checks = []
programs = {}
for name, job in new['jobs'].items():
    for index, step in enumerate(job['steps']):
        if 'run' not in step: continue
        shell = step['run']
        result = subprocess.run(['bash', '-n'], input=shell, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
        lines = shell.splitlines(); blocks = []; i = 0
        while i < len(lines):
            if lines[i].lstrip().startswith('python3 ') and "<<'PY'" in lines[i]:
                start = i + 1; end = start
                while end < len(lines) and lines[end] != 'PY': end += 1
                assert end < len(lines)
                code = '\n'.join(lines[start:end]) + '\n'
                ast.parse(code, filename=f'{name}:{index}:{len(blocks)}')
                blocks.append(code); i = end
            i += 1
        programs[name] = blocks
        checks.append({'job': name, 'bash_n': 'PASS', 'python_heredocs_ast': len(blocks), 'shell_body_executed': False})
assert len(checks) == 2 and sum(c['python_heredocs_ast'] for c in checks) == 4
old_shell = next(s['run'] for s in old['jobs']['measure']['steps'] if 'run' in s)
start = old_shell.index('import base64,hashlib,json,sys\n')
old_gate = old_shell[start:old_shell.index('\nPY\n', start)] + '\n'
gate = programs['measure'][-1]
prefix, appended = gate.split('# Append-only isolation gate;', 1)
assert prefix == old_gate.replace('HeroFloatProbe', 'HeroCGSemanticsProbe')
assert appended
before = (HERE / 'run-one.original.py').read_text()
after = (HERE / 'run-one.py').read_text()
assert after == before.replace('env=dict(os.environ,BERN_HERO_FLOAT_CAPTURE=mode,BERN_HERO_EXPECT_OS=str(major))',
    "env=dict(os.environ,BERN_HERO_FLOAT_CAPTURE=mode,BERN_HERO_EXPECT_OS=str(major),BERN_HERO_LAYER_OBSERVE='off')")
ast.parse(after, filename='run-one.py')
for key in ('product_source_commit', 'fixture_base_commit'):
    value = json.loads((HERE / 'provenance.json').read_text())[key]
    assert f"d['{key}']=='{value}'" in text
assert "d['kind']=='original_snapshot_cg_drawing_semantics_fixture'" in text
for required in ('hero-cgsemantics-probe.tar.gz', 'ditto .github/scripts/hero-cgsemantics-probe work/probe',
                 'macos14-hero-cgsemantics-probe-build', 'macos14-hero-cgsemantics-evidence'):
    assert required in text, required
provenance = json.loads((HERE / 'provenance.json').read_text())
for base in provenance['base_inputs']:
    data = (HERE / base['private_file']).read_bytes()
    assert len(data) == base['bytes'] and hashlib.sha256(data).hexdigest() == base['sha256']
    assert Path(base['path']).read_bytes() == data, 'Original source changed'
assert 'PENDING' not in text, 'Final drawing_semantics contract still pending'
for required in ("s=r['drawing_semantics']", "s['stage']=='after_existing_window_teardown_before_primary_release'",
                 "type(s['rendering_intent_raw']) is int and s['rendering_intent_raw']>=0",
                 "s['is_mask'] is False and type(s['should_interpolate']) is bool",
                 "count=6 if s['decode_present'] else 0", "s['decode_nonfinite_index'] is None",
                 "re.fullmatch(r'0x[0-9a-f]{16}',bits)", "struct.unpack('>d',struct.pack('>Q',int(bits,16)))[0]",
                 "s['observed_at_uptime_seconds']>=r['provider_read_at_uptime_seconds']",
                 "s['observed_at_uptime_seconds']+s['observation_elapsed_seconds']<=f['released_at_uptime_seconds']"):
    assert required in appended, required
result = {'success': True, 'scope': 'Static syntax, original full native/ICC gate exact-prefix and single-wrapper-environment-change proof only; no native/runtime-schema/CI/compiler/UI execution.',
    'yaml': 'PASS', 'wrapper_ast': 'PASS', 'checks': checks,
    'original_native_ICC_gate': 'PASS — exact prefix except binary identity',
    'wrapper_delta': 'PASS — only explicit backing off added',
    'workflow_sha256': hashlib.sha256(workflow.read_bytes()).hexdigest(),
    'wrapper_sha256': hashlib.sha256((HERE / 'run-one.py').read_bytes()).hexdigest(),
    'runtime_schema_execution': 'NOT PERFORMED'}
(HERE / 'static-review.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
