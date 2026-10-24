import hashlib,json,os,shutil,subprocess,tempfile,time
from pathlib import Path
root=Path(__file__).resolve().parent.parent
base=root/'work/native-standard-full-app-9dd';out=base/'startup-window-gate';assert not out.exists();out.mkdir()
helper=root/'work/focus-helper';app=base/'app/Showcase.app/Contents/MacOS/Showcase';cli=base/'app/bin/showcase'
focus=lambda:int(subprocess.check_output([str(helper)],text=True,timeout=2))
before=focus();began=time.monotonic();deadline=began+25;ipc=tempfile.mkdtemp(prefix='bern9dd-',dir='/tmp');env=dict(os.environ,BERN_IPC_DIR=ipc)
report={'source_sha':'9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0','build_run':40066468884,'scope':'isolated bundle startup/window/control smoke only; no Standard picture visual or active-window acceptance','harness_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'frontmost_before':before,'executable_sha256':hashlib.sha256(app.read_bytes()).hexdigest(),'calls':[],'readiness':[]}
log=(out/'application.log').open('w');p=subprocess.Popen([str(app),'-AppleLanguages','(en)','-AppleLocale','en_US'],env=env,stdout=log,stderr=log,start_new_session=True);report['pid']=p.pid
try:
 def call(*args):
  remaining=deadline-time.monotonic()
  if remaining<=0:raise RuntimeError('25-second absolute startup deadline')
  stem=f'{len(report["calls"])+1:03d}';t=time.monotonic()
  try:
   r=subprocess.run([str(cli),*args],env=env,text=True,capture_output=True,timeout=min(3,remaining))
  except subprocess.TimeoutExpired as e:
   (out/(stem+'-stdout.txt')).write_text((e.stdout or b'').decode(errors='replace') if isinstance(e.stdout,bytes) else e.stdout or '')
   (out/(stem+'-stderr.txt')).write_text((e.stderr or b'').decode(errors='replace') if isinstance(e.stderr,bytes) else e.stderr or '')
   report['calls'].append({'arguments':args,'seconds':time.monotonic()-t,'timeout':True,'stdout':stem+'-stdout.txt','stderr':stem+'-stderr.txt'});raise
  (out/(stem+'-stdout.json')).write_text(r.stdout);(out/(stem+'-stderr.txt')).write_text(r.stderr)
  report['calls'].append({'arguments':args,'seconds':time.monotonic()-t,'status':r.returncode,'stdout':stem+'-stdout.json','stderr':stem+'-stderr.txt'})
  if r.returncode:raise RuntimeError('CLI failed '+str(args))
  return json.loads(r.stdout) if r.stdout.strip() else None
 session=None;ready_until=began+18
 while time.monotonic()<ready_until:
  if p.poll() is not None:raise RuntimeError('App exited '+str(p.returncode))
  current=focus()
  if current==p.pid:
   subprocess.run([str(helper),str(before)],check=True,timeout=2);report.setdefault('restore_elapsed',time.monotonic()-began)
  try:
   sessions=call('sessions')
   windows=[]
   if len(sessions)==1:
    session=sessions[0]['session_id'];windows=call('--session',session,'window','list')
   native=json.loads(subprocess.check_output([str(helper),'--windows',str(p.pid)],text=True,timeout=2))
   visible=[w for w in native if w.get('kCGWindowAlpha',0)>=.99 and w.get('kCGWindowIsOnscreen') and w.get('kCGWindowBounds',{}).get('Width',0)>120]
   report['readiness'].append({'elapsed':time.monotonic()-began,'sessions':sessions,'windows':windows,'own_native_windows':native,'frontmost':current})
   if windows and visible:break
  except (RuntimeError,ValueError,subprocess.TimeoutExpired) as e:
   report['readiness'].append({'elapsed':time.monotonic()-began,'error':str(e)})
  time.sleep(min(.08,max(0,ready_until-time.monotonic())))
 else:raise RuntimeError('Session did not register a main window and visible owned CG window within18 seconds')
 controls=call('--session',session,'ui','inspect')
 if not controls:raise RuntimeError('No registered controls after window ready')
 report.update(success=True,control_count=len(controls),window_count=len(windows),controls=controls)
except Exception as e:report.update(success=False,error=str(e))
finally:
 if p.poll() is None:
  p.terminate()
  try:p.wait(timeout=4)
  except subprocess.TimeoutExpired:p.kill();p.wait()
 if focus()==p.pid:subprocess.run([str(helper),str(before)],check=True,timeout=2)
 report['frontmost_after']=focus();report['elapsed_seconds']=time.monotonic()-began
 log.close();shutil.rmtree(ipc);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report.get(k) for k in ['success','error','pid','control_count','window_count','frontmost_before','frontmost_after','elapsed_seconds']},indent=2))
raise SystemExit(0 if report['success'] else 1)
