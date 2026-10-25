"""One supervised full-App input chain; external native gate and completion required."""
import json
import os
from pathlib import Path
import subprocess
import time

root = Path(__file__).resolve().parent
out = root.parent / 'search-native13-runtime'
assert not out.exists()
out.mkdir()
ipc = out / 'ipc'
ipc.mkdir(mode=0o700)
pack = json.loads((root / 'prepare.json').read_text())
app, cli = Path(pack['private']), Path(pack['cli'])
env = {k: v for k, v in os.environ.items() if not k.startswith('BERN_')}
env.update(BERN_IPC_DIR=str(ipc), BERN_APPEARANCE='light')
report = {'success': False, 'source_sha': pack['source_sha'], 'commands': [],
          'app': str(app), 'cli': str(cli), 'environment': {k: v for k, v in env.items() if k.startswith('BERN_')},
          'startup_cap_seconds': 18, 'external_work_cap_seconds': 180}
process = None
own = None

def save():
    (out / 'driver.json').write_text(json.dumps(report, indent=2) + '\n')

def helper(mode, *paths):
    p = subprocess.run([str(root / 'FocusGuard'), mode, str(app), *(str(x) for x in paths)],
                       capture_output=True, timeout=7)
    name = mode + '-' + str(time.monotonic_ns()) + '.json'
    (out / name).write_bytes(p.stdout)
    (out / (name + '.stderr.txt')).write_bytes(p.stderr)
    data = json.loads(p.stdout)
    assert p.returncode == 0 and data['success'], data
    return data

def profile(label):
    p = subprocess.run([str(root / 'Profile')], capture_output=True, timeout=5)
    (out / ('profile-' + label + '.json')).write_bytes(p.stdout)
    (out / ('profile-' + label + '.stderr.txt')).write_bytes(p.stderr)
    data = json.loads(p.stdout)
    assert p.returncode == 0 and len(data) == 3 and all(v is False for v in data.values()), data
    return data

def command(arguments, session=None, allow_failure=False, cutoff=None):
    argv = [str(cli)] + (['--session', session] if session else []) + arguments
    stem = 'startup-' + str(len(report['commands']) + 1).zfill(3)
    cap = min(8, max(0.01, cutoff - time.monotonic())) if cutoff else 8
    p = subprocess.run(argv, env=env, capture_output=True, timeout=cap)
    (out / (stem + '.stdout.json')).write_bytes(p.stdout)
    (out / (stem + '.stderr.txt')).write_bytes(p.stderr)
    report['commands'].append({'arguments': argv[1:], 'returncode': p.returncode,
                               'stdout': stem + '.stdout.json', 'stderr': stem + '.stderr.txt'})
    save()
    if not allow_failure:
        assert p.returncode == 0, stem
    return json.loads(p.stdout) if p.returncode == 0 and p.stdout else None

def control(rows, target, role, window):
    found = [r for r in rows if r.get('target') == target and r.get('role') == role and r.get('window') == window]
    assert len(found) == 1 and found[0]['enabled'] is True
    return found[0]

try:
    report['normal_start'] = profile('start')
    initial = helper('inspect')
    assert initial['own'] is None and initial['front']['kernel_start'] is not None
    (out / 'original-front.json').write_text(json.dumps(initial['front'], indent=2) + '\n')
    report['original_front'] = initial['front']
    with (out / 'application.stdout.txt').open('wb') as stdout, (out / 'application.stderr.txt').open('wb') as stderr:
        process = subprocess.Popen([str(app / 'Contents/MacOS/Showcase'), '-AppleLanguages', '(en)', '-AppleLocale', 'en_US'],
                                   env=env, stdout=stdout, stderr=stderr)
        report['pid'] = process.pid
        started = time.monotonic()
        end = started + 18
        report['phase'] = 'ipc-readiness'; save()
        session, main = None, None
        while time.monotonic() < end and process.poll() is None:
            if session is None:
                sessions = command(['sessions'], allow_failure=True, cutoff=end) or []
                assert len(sessions) <= 1
                if sessions:
                    session = sessions[0]['session_id']
            if session:
                windows = command(['window', 'list'], session, allow_failure=True, cutoff=end) or []
                mains = [w for w in windows if w.get('kind') == 'main']
                assert len(mains) <= 1
                if mains:
                    main = mains[0]['window']; break
            time.sleep(0.15)
        assert session and main and process.poll() is None and time.monotonic() < end
        own = helper('inspect')['own']
        assert own and own['pid'] == process.pid and own['kernel_start'] is not None
        assert own['bundle_id'] == pack['private_identifier']
        (out / 'owned.json').write_text(json.dumps(own, indent=2) + '\n')
        report.update(session=session, window=main, own=own, phase='wait-native-gate')
        (out / 'ipc-ready.json').write_text(json.dumps({'pid': process.pid, 'session': session, 'window': main,
            'bundle_id': own['bundle_id'], 'launch_monotonic': started, 'startup_deadline_monotonic': end}, indent=2) + '\n')
        save()
        print(json.dumps({'phase': 'wait-native-gate', 'pid': process.pid, 'output': str(out)}), flush=True)
        while time.monotonic() < end and not (out / 'native-ready.json').exists() and process.poll() is None:
            time.sleep(0.05)
        gate = json.loads((out / 'native-ready.json').read_text())
        assert time.monotonic() < end and gate['pid'] == process.pid and gate['success'] is True
        assert type(gate['window_id']) is int and gate['window_id'] > 0
        report['native_window_id'] = gate['window_id']
        report['joint_ready_elapsed_seconds'] = time.monotonic() - started
        command(['ui', 'set-language', '--language', 'en'], session)
        command(['window', 'resize', '--window', main, '--width', '920', '--height', '668'], session)
        rows = command(['ui', 'inspect'], session)
        assert control(rows, 'main_window.pages', 'sidebar', main)['value'] == 'Text'
        assert control(rows, 'main_window.sidebar_search', 'search', main)['value'] == ''
        assert not any(r.get('target') == 'library_page.library_results' for r in rows)
        ready = {'pid': process.pid, 'session': session, 'window': main, 'native_window_id': gate['window_id'],
                 'ipc_dir': str(ipc), 'cli': str(cli), 'bundle_id': own['bundle_id'], 'ready': True}
        (out / 'ready.json').write_text(json.dumps(ready, indent=2) + '\n')
        report['phase'] = 'external-input-ready'; save()
        print(json.dumps({'phase': 'external-input-ready', **ready}), flush=True)
        end = time.monotonic() + 180
        while time.monotonic() < end and not (out / 'finish.json').exists() and process.poll() is None:
            time.sleep(0.1)
        finish = json.loads((out / 'finish.json').read_text())
        assert time.monotonic() < end
        assert process.poll() is None and finish['pid'] == process.pid
        report['external_result'] = finish
        report['success'] = finish['success'] is True
except Exception as e:
    report['error'] = str(e)
finally:
    try:
        if own is None and process is not None:
            candidate = helper('inspect').get('own')
            if candidate and candidate['pid'] == process.pid and candidate['kernel_start'] is not None:
                own = candidate
                (out / 'owned.json').write_text(json.dumps(own, indent=2) + '\n')
        if own:
            report['cleanup'] = helper('cleanup', out / 'original-front.json', out / 'owned.json')
        elif process is not None and process.poll() is None:
            raise RuntimeError('No exact registered own identity; refusing blind stop')
        if process is not None:
            process.wait(timeout=3)
            report['app_exit_code'] = process.returncode
        report['normal_end'] = profile('end')
    except Exception as e:
        report['cleanup_error'] = str(e); report['success'] = False
    report['phase'] = 'finished'; save()
    print(json.dumps({'success': report['success'], 'error': report.get('error'),
                      'cleanup_error': report.get('cleanup_error')}), flush=True)
raise SystemExit(0 if report['success'] else 1)
