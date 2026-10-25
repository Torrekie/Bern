"""Observe actual AVPlayer-backed positions; command ACK alone cannot pass."""
import json
import os
from pathlib import Path
import subprocess
import time

p=Path(__file__).resolve().parent
r=json.loads((p/'ready.json').read_text())
env={k:v for k,v in os.environ.items() if not k.startswith('BERN_')}
env['BERN_IPC_DIR']=r['ipc']
records=[]
def command(label,args):
    start=time.monotonic()
    x=subprocess.run([r['cli'],'--session',r['session'],*args],env=env,capture_output=True,timeout=4)
    row={'label':label,'args':args,'monotonic':start,'elapsed_seconds':time.monotonic()-start,'returncode':x.returncode,'stdout':x.stdout.decode(errors='replace'),'stderr':x.stderr.decode(errors='replace')}
    records.append(row)
    (p/'media-commands.json').write_text(json.dumps(records,indent=2)+'\n')
    assert x.returncode==0, label
    return json.loads(x.stdout)

player='main#1/frame.clip'
def state(label):return command(label,['media','state','--player-id',player])
initial=state('initial')
end=time.monotonic()+8
while initial['phase'] not in ['Ready','Playing','Paused'] and time.monotonic()<end:
    time.sleep(0.2)
    initial=state('wait-ready')
assert initial['error'] is None and initial['seekable'] and initial['views']>=1
command('mute-owned-player',['media','set-muted','--player-id',player,'--muted','true'])
command('seek-zero',['media','seek','--player-id',player,'--position-ms','0'])
command('play',['media','play','--player-id',player])
playing0=state('playing0')
time.sleep(1.1)
playing1=state('playing1')
command('pause',['media','pause','--player-id',player])
time.sleep(0.65)
paused0=state('paused0')
time.sleep(0.8)
paused1=state('paused1')
checks={'same_source_version':len({x['source_version'] for x in [initial,playing0,playing1,paused0,paused1]})==1,
    'forward_progress':playing1['position_ms']>playing0['position_ms'],
    'playing_observed':playing1['phase']=='Playing',
    'paused_observed':paused0['phase']=='Paused' and paused1['phase']=='Paused',
    'pause_stable':paused1['position_ms']==paused0['position_ms'],
    'view_attached':all(x['views']>=1 for x in [playing0,playing1,paused0,paused1]),
    'no_media_error':all(x['error'] is None for x in [playing0,playing1,paused0,paused1])}
result={'player_id':player,'source':'Actual AVFoundation-backed state from the unmodified e48 application, not simulated positions.',
    'scope':'Gallery declares controls:none; CLI controls are intentional. No pointer/keyboard or audio loudness claim.',
    'muted_only_this_private_player_for_check':True,'initial':initial,'playing0':playing0,'playing1':playing1,'paused0':paused0,'paused1':paused1,'checks':checks,'success':all(checks.values())}
(p/'media-progress-report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'success':result['success'],'checks':checks,'positions':[x['position_ms'] for x in [playing0,playing1,paused0,paused1]],'phases':[x['phase'] for x in [playing0,playing1,paused0,paused1]]}),flush=True)
