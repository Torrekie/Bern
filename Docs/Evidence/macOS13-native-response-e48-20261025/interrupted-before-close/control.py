"""One private Gallery session; CLI actions plus actual readback, no pixel gates."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ready = json.loads((HERE / 'ready.json').read_text())
lock = json.loads((HERE / 'isolation.json').read_text())
assert Path(ready['ipc']).is_dir()
env = {k:v for k,v in os.environ.items() if not k.startswith('BERN_')}
env['BERN_IPC_DIR'] = ready['ipc']
label, *args = sys.argv[1:]
assert re.fullmatch(r'[a-z0-9-]+', label)
assert args
output = HERE / 'actions'
output.mkdir(exist_ok=True)
record = output / (label + '.json')
assert not record.exists(), 'Fresh action label required'
identity = subprocess.run([str(HERE.parents[1] / 'work/native-logic-gallery13-tools/FocusGuard'), 'inspect', lock['app']], capture_output=True, timeout=5)
assert identity.returncode == 0
own = json.loads(identity.stdout)['own']
expected = json.loads((HERE / 'own.json').read_text())
assert own is not None and all(own.get(k)==expected.get(k) for k in ['pid','bundle_id','executable_path','kernel_start']) and own['pid']==ready['pid'], 'Own kernel/path/bundle identity changed'
argv = [ready['cli'], '--session', ready['session'], *args]
try:
    p = subprocess.run(argv, env=env, capture_output=True, timeout=10)
except subprocess.TimeoutExpired as e:
    record.write_text(json.dumps({'argv':argv,'timeout_seconds':10,'stdout':(e.stdout or b'').decode(errors='replace'),'stderr':(e.stderr or b'').decode(errors='replace')},indent=2)+'\n')
    raise
record.write_text(json.dumps({'argv':argv,'returncode':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace'),'own_identity':own},indent=2)+'\n')
assert p.returncode == 0, p.stderr.decode(errors='replace')
if p.stdout.strip():
    data = json.loads(p.stdout)
    (output / (label + '.payload.json')).write_text(json.dumps(data,indent=2)+'\n')
    if args == ['ui', 'inspect']:
        print(json.dumps({'label':label,'controls':[{k:x.get(k) for k in ['target','role','label','enabled','value']} for x in data if x.get('target') in ['main_window.show_details','main_window.close_details','film.to_first','film.to_last','frame.volume','frame.volume_level','main_window.pages']]},ensure_ascii=False))
    elif args == ['state']:
        print(json.dumps({'label':label,'revision':data.get('revision'),'appearance':data.get('values',{}).get('appearance')}))
    else:
        print(json.dumps({'label':label,'data':data},ensure_ascii=False)[:2000])
else:
    print(label + ': acknowledged; this alone is not a visible/result pass')
