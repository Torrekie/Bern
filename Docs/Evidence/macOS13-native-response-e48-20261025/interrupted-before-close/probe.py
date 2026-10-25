"""Bounded readback and conditional same-owned-PID sampling; no synthetic UI state."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

p=Path(__file__).resolve().parent
root=p.parents[1]
r=json.loads((p/'ready.json').read_text())
lock=json.loads((p/'isolation.json').read_text())
expected=json.loads((p/'own.json').read_text())
env={k:v for k,v in os.environ.items() if not k.startswith('BERN_')}
env['BERN_IPC_DIR']=r['ipc']
label,mode,*args=sys.argv[1:]
assert re.fullmatch(r'[a-z0-9-]+',label)
assert not (p/(label+'.json')).exists()
identity=subprocess.run([str(root/'work/native-logic-gallery13-tools/FocusGuard'),'inspect',lock['app']],capture_output=True,timeout=4)
current=json.loads(identity.stdout)
assert identity.returncode==0 and current['own'] is not None
assert all(current['own'].get(k)==expected.get(k) for k in ['pid','bundle_id','executable_path','kernel_start'])
rows=[]
def call(argv,timeout=3):
    start=time.monotonic()
    cmd=[r['cli'],'--session',r['session'],*argv]
    row={'argv':cmd,'timeout_seconds':timeout,'started_monotonic':start}
    try:
        x=subprocess.run(cmd,env=env,capture_output=True,timeout=timeout)
        row.update(returncode=x.returncode,stdout=x.stdout.decode(errors='replace'),stderr=x.stderr.decode(errors='replace'))
        row['ok']=x.returncode==0
        if row['ok'] and x.stdout.strip():row['payload']=json.loads(x.stdout)
    except subprocess.TimeoutExpired as e:
        row.update(ok=False,timed_out=True,stdout=(e.stdout or b'').decode(errors='replace'),stderr=(e.stderr or b'').decode(errors='replace'))
    row['elapsed_seconds']=time.monotonic()-start
    rows.append(row)
    return row

if mode=='call':
    last=call(args,5)
    result={'ok':last['ok'],'payload':last.get('payload'),'timed_out':last.get('timed_out',False)}
elif mode in ['wait-film','wait-frame']:
    end=time.monotonic()+8
    ok=False
    while time.monotonic()<end:
        if mode=='wait-film':
            last=call(['ui','inspect'])
            controls=last.get('payload',[])
            ok=last['ok'] and isinstance(controls,list) and any(x.get('target')=='main_window.pages' and x.get('value')=='Film' for x in controls) and any(x.get('target')=='film.to_first' and x.get('enabled') for x in controls)
        else:
            last=call(['media','state','--player-id','main#1/frame.clip'])
            state=last.get('payload',{})
            ok=last['ok'] and state.get('phase') in ['Ready','Playing','Paused'] and state.get('views',0)>=1 and state.get('error') is None
        if ok or last.get('timed_out'):break
        if not last['ok'] and 'player_not_found' not in last.get('stderr',''):break
        time.sleep(0.2)
    result={'ok':ok,'payload':last.get('payload'),'deadline_seconds':8,'timed_out':last.get('timed_out',False)}
elif mode=='sample':
    outfile=p/(label+'.sample.txt')
    argv=['/usr/bin/sample',str(expected['pid']),'2','10','-mayDie','-file',str(outfile)]
    start=time.monotonic()
    try:
        x=subprocess.run(argv,capture_output=True,timeout=120)
        result={'ok':x.returncode==0 and outfile.exists(),'argv':argv,'returncode':x.returncode,'stdout':x.stdout.decode(errors='replace'),'stderr':x.stderr.decode(errors='replace')}
    except subprocess.TimeoutExpired as e:
        result={'ok':False,'argv':argv,'timed_out':True,'stdout':(e.stdout or b'').decode(errors='replace'),'stderr':(e.stderr or b'').decode(errors='replace')}
    result.update(elapsed_seconds=time.monotonic()-start,timeout_seconds=120,stack_file_exists=outfile.exists(),stack_file_bytes=outfile.stat().st_size if outfile.exists() else 0)
else:
    raise ValueError(mode)
result.update(label=label,mode=mode,own_identity=current['own'],rows=rows)
(p/(label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
summary={k:result[k] for k in ['label','mode','ok','timed_out','payload','stack_file_exists','stack_file_bytes','elapsed_seconds'] if k in result}
print(json.dumps(summary),flush=True)
