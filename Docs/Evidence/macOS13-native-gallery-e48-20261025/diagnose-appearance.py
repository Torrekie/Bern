"""One clean-start Light action, bounded readbacks and read-only owned PID sample."""
import json
import os
from pathlib import Path
import subprocess
import time

p = Path(__file__).resolve().parent
ready = json.loads((p / 'ready.json').read_text())
lock = json.loads((p / 'isolation.json').read_text())
expected = json.loads((p / 'own.json').read_text())
env = {k:v for k,v in os.environ.items() if not k.startswith('BERN_')}
env['BERN_IPC_DIR'] = ready['ipc']
rows = []

def identity():
    x = subprocess.run([str(p/'FocusGuard'),'inspect',lock['app']],capture_output=True,timeout=4)
    j = json.loads(x.stdout)
    assert x.returncode == 0 and j['own'] == expected
    return j

def command(label, args, timeout):
    start = time.monotonic()
    argv = [ready['cli'],'--session',ready['session'],*args]
    row = {'label':label,'argv':argv,'timeout_seconds':timeout}
    try:
        x = subprocess.run(argv,capture_output=True,env=env,timeout=timeout)
        row.update(returncode=x.returncode,stdout=x.stdout.decode(errors='replace'),stderr=x.stderr.decode(errors='replace'))
    except subprocess.TimeoutExpired as e:
        row.update(timed_out=True,stdout=(e.stdout or b'').decode(errors='replace'),stderr=(e.stderr or b'').decode(errors='replace'))
    row['elapsed_seconds'] = time.monotonic()-start
    rows.append(row)
    (p/'appearance-commands.json').write_text(json.dumps(rows,indent=2)+'\n')

initial = identity()
command('before-state',['state'],3)
command('light',['ui','activate','--target','main_window.light'],5)
command('after-state',['state'],3)
command('after-inspect',['ui','inspect'],3)
before_sample = identity()
sample = subprocess.run(['/usr/bin/sample',str(expected['pid']),'2','10','-file',str(p/'appearance-process-sample.txt')],capture_output=True,timeout=8)
report = {'scope':'Only clean-start Light action; no AX action or native tree request preceded this action.',
    'initial_identity':initial,'before_sample_identity':before_sample,'sample_returncode':sample.returncode,
    'sample_stdout':sample.stdout.decode(errors='replace'),'sample_stderr':sample.stderr.decode(errors='replace'),
    'rows':rows,'ready_for_single_native_capture':True}
(p/'appearance-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'sample_completed':sample.returncode,'pid':expected['pid'],'commands':[{'label':r['label'],'returncode':r.get('returncode'),'timed_out':r.get('timed_out',False)} for r in rows]}),flush=True)
end = time.monotonic()+45
while time.monotonic()<end and not (p/'capture-complete').exists():
    time.sleep(0.2)
(p/'finish').touch()
