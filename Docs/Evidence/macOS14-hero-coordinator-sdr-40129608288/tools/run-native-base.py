"""Run the preserved native/execution prefix with four path/OS substitutions."""
import ast, hashlib, json, sys
from pathlib import Path
import yaml

assert len(sys.argv)==4, 'RUNTIME_DIRECTORY MAJOR BINARY'
directory=Path(sys.argv[1]).resolve(); major=int(sys.argv[2]); binary=Path(sys.argv[3]).resolve()
here=Path(__file__).resolve().parent
document=yaml.safe_load((here/'macos14-hero-coordinator-sdr-probe.yml').read_text())
shell=next(s['run'] for s in document['jobs']['measure']['steps'] if 'run' in s)
start=shell.index('import hashlib,json,math\n')
full=shell[start:shell.index('\nPY\n',start)]+'\n'
marker='# Append-only SDR metadata gate; inherited native/execution gate above remains unchanged.\n'
assert full.count(marker)==1
gate=full.split(marker)[0]
assert hashlib.sha256(gate.encode()).hexdigest()=='e67b21226c79f7516cc603d7731fae4e6cc4c6403df72b5769608f204c3d5a44'
changes={
    "Path('evidence/runtime14')":'Path('+repr(str(directory))+')',
    "d['expected_os_major']==14 and d['actual_os_major']==14":"d['expected_os_major']==major and d['actual_os_major']==major",
    "receipt['expected_os_major']==14":"receipt['expected_os_major']==major",
    "Path('probe/HeroCoordinatorSDRProbe')":'Path('+repr(str(binary))+')'}
for before,after in changes.items():
    assert gate.count(before)==1,before
    gate=gate.replace(before,after)
ast.parse(gate)
exec(compile(gate,'adapted-unchanged-native-prefix','exec'),{'major':major})
print(json.dumps({'native_execution_prefix':'PASS','adaptations':changes,'adapted_gate_sha256':hashlib.sha256(gate.encode()).hexdigest()},sort_keys=True))
