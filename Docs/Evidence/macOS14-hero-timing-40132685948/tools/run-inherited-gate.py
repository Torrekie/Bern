"""Run the complete inherited native/execution/SDR gate; timing stays separate."""
import ast,hashlib,json,sys
from pathlib import Path
import yaml
assert len(sys.argv)==4,'RUNTIME MAJOR BINARY'
directory=Path(sys.argv[1]).resolve();major=int(sys.argv[2]);binary=Path(sys.argv[3]).resolve()
document=yaml.safe_load((Path(__file__).parent/'macos14-hero-timing-probe.yml').read_text())
shell=next(s['run'] for s in document['jobs']['measure']['steps'] if 'run' in s)
start=shell.index('import hashlib,json,math\n');full=shell[start:shell.index('\nPY\n',start)]+'\n'
marker='# Append-only bounded timing metadata gate; inherited native/execution/SDR gates above remain unchanged.\n'
assert full.count(marker)==1;gate=full.split(marker)[0]
assert hashlib.sha256(gate.encode()).hexdigest()=='db503c085d257c7102062fc209074ded13fa431aac8e0ec1395fdde0decf60a8'
changes={"Path('evidence/runtime14')":'Path('+repr(str(directory))+')',
 "d['expected_os_major']==14 and d['actual_os_major']==14":"d['expected_os_major']==major and d['actual_os_major']==major",
 "receipt['expected_os_major']==14":"receipt['expected_os_major']==major",
 "Path('probe/HeroTimingProbe')":'Path('+repr(str(binary))+')',
 "validate_flight_sdr(d,receipt,'default',14)":"validate_flight_sdr(d,receipt,'default',major)"}
for before,after in changes.items():
 assert gate.count(before)==1,before
 gate=gate.replace(before,after)
ast.parse(gate);exec(compile(gate,'unchanged-inherited-gate','exec'),{'major':major})
print(json.dumps({'inherited_native_execution_sdr':'PASS','adaptations':changes,'adapted_sha256':hashlib.sha256(gate.encode()).hexdigest()},sort_keys=True))
