import hashlib, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

root = Path(__file__).resolve().parent.parent
focus = root / 'work/focus-helper'
results = []
plans = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else [
    {'name':'showcase','folder':'ci-showcase-522','run':39986051547,'source_sha':'52264541ea584745bde514ea43e98e337a24772a'},
    {'name':'gallery','folder':'ci-gallery-522-sdk262','run':39986052416,'source_sha':'52264541ea584745bde514ea43e98e337a24772a'}]
for plan in plans:
    name, folder, run = plan['name'], plan['folder'], plan['run']
    base = root / 'work' / folder / 'app'
    exe = base / (name.capitalize()+'.app') / 'Contents/MacOS' / name.capitalize()
    cli = base / 'bin' / name
    before = int(subprocess.check_output([str(focus)]))
    ipc = tempfile.mkdtemp(prefix='bern522-', dir='/tmp')
    env = dict(os.environ, BERN_IPC_DIR=ipc)
    out = root / 'work' / folder / 'launch-check'
    out.mkdir(exist_ok=True)
    started = time.monotonic()
    log = (out / 'application.log').open('w')
    app = subprocess.Popen([str(exe), '-AppleLanguages', '(en)', '-AppleLocale', 'en_US'], env=env, stdout=log, stderr=log, start_new_session=True)
    report = {'source_sha':plan['source_sha'],'run':run,'name':name,'frontmost_before':before,'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
    try:
        def call(*args):
            r = subprocess.run([str(cli), *args],env=env,text=True,capture_output=True,timeout=3)
            if r.returncode: raise RuntimeError(r.stderr)
            return json.loads(r.stdout) if r.stdout.strip() else None
        for _ in range(75):
            if app.poll() is not None: raise RuntimeError('Exited '+str(app.returncode))
            current = int(subprocess.check_output([str(focus)]))
            if current == app.pid:
                subprocess.run([str(focus),str(before)],check=True)
                report.setdefault('restored_after_seconds',time.monotonic()-started)
            try:
                sessions=call('sessions')
                if len(sessions)==1: break
            except (RuntimeError, ValueError, subprocess.TimeoutExpired): pass
            time.sleep(.08)
        else: raise RuntimeError('Session did not appear')
        session=sessions[0]['session_id']
        report['sessions']=sessions
        report['windows']=call('--session',session,'window','list')
        report['controls']=call('--session',session,'ui','inspect')
        if plan.get('frame_popover'):
            assert name == 'gallery'
            sidebar = next(c for c in report['controls'] if c['role']=='sidebar' and c['target'].endswith('.pages'))
            call('--session',session,'ui','select','--target',sidebar['target'],'--option','Frame')
            for _ in range(25):
                controls = call('--session',session,'ui','inspect')
                report['frame_last_controls']=controls
                matches = [c for c in controls if c['role']=='popover_button' and c['target'].endswith('.volume')]
                if len(matches)==1: break
                time.sleep(.03)
            else: raise RuntimeError('Frame volume did not mount')
            report['frame_volume_before']=matches[0]
            call('--session',session,'ui','activate','--target',matches[0]['target'])
            for _ in range(25):
                controls = call('--session',session,'ui','inspect')
                sliders = [c for c in controls if c['role']=='slider' and c['target'].endswith('.volume_level')]
                if len(sliders)==1: break
                time.sleep(.03)
            else: raise RuntimeError('Volume popover content did not mount')
            report['popover_volume_slider']=sliders[0]
            call('--session',session,'ui','set-number','--target',sliders[0]['target'],'--value','0.55')
            report['popover_after_edit']=call('--session',session,'ui','inspect')
            edited = next(c for c in report['popover_after_edit'] if c['target']==sliders[0]['target'])
            assert abs(float(edited['value'])-.55)<1e-9, edited
            report['frame_interaction_scope']='Actual generated app; CLI binding selects Frame, opens popover and edits draft. Does not assert physical mouse, native AX geometry, dismissal or14 visual equivalence.'
        report['success']=True
    except Exception as e:
        report['success']=False;report['error']=str(e)
    finally:
        if app.poll() is None:
            app.terminate()
            try: app.wait(timeout=4)
            except subprocess.TimeoutExpired: app.kill();app.wait()
        if int(subprocess.check_output([str(focus)])) == app.pid:
            subprocess.run([str(focus),str(before)],check=True)
        report['frontmost_after']=int(subprocess.check_output([str(focus)]))
        report['elapsed_seconds']=time.monotonic()-started
        shutil.rmtree(ipc)
        log.close()
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    results.append({k:v for k,v in report.items() if k not in ['controls','sessions','windows','frame_last_controls','popover_after_edit']})
print(json.dumps(results,indent=2))
assert all(r['success'] for r in results)
