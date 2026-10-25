#!/usr/bin/env python3
"""Root-only bounded native Scene pair driver; capture completion supplied externally."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('app', type=Path)
p.add_argument('mode', choices=['true', 'false'])
p.add_argument('output', type=Path)
a = p.parse_args()
app = a.app.resolve(strict=True)
out = a.output.absolute()
assert not out.exists(), 'Fresh output required'
out.mkdir()
guard = Path(__file__).resolve().parent / 'FocusGuard'
report = {'success': False, 'app': str(app), 'mode': a.mode,
          'app_executable_sha256': hashlib.sha256((app / 'Contents/MacOS/Showcase').read_bytes()).hexdigest(),
          'focus_guard_sha256': hashlib.sha256(guard.read_bytes()).hexdigest(), 'capture_cap_seconds': 75}
proc = None
own = None

def save():
    (out / 'driver.json').write_text(json.dumps(report, indent=2) + '\n')

def helper(mode, *paths):
    r = subprocess.run([str(guard), mode, str(app), *(str(v) for v in paths)],
                       capture_output=True, timeout=7)
    name = mode + '-' + str(time.monotonic_ns())
    (out / (name + '.json')).write_bytes(r.stdout)
    (out / (name + '.stderr.txt')).write_bytes(r.stderr)
    data = json.loads(r.stdout)
    assert r.returncode == 0 and data['success'], data
    return data

try:
    initial = helper('inspect')
    assert initial['own'] is None and initial['front']['kernel_start'] is not None
    (out / 'original-front.json').write_text(json.dumps(initial['front'], indent=2) + '\n')
    report['original_front'] = initial['front']
    env = os.environ.copy()
    env['BERN_TOOLBAR_PROBE_OUTPUT'] = str(out)
    with (out / 'app.stdout.txt').open('wb') as stdout, (out / 'app.stderr.txt').open('wb') as stderr:
        proc = subprocess.Popen([str(app / 'Contents/MacOS/Showcase'), a.mode],
                                env=env, stdout=stdout, stderr=stderr)
        report['child_pid'] = proc.pid
        report['phase'] = 'wait-ready'; save()
        end = time.monotonic() + 20
        while time.monotonic() < end and not (out / 'ready.json').exists() and proc.poll() is None:
            time.sleep(0.1)
        state = helper('inspect')
        own = state['own']
        assert own and own['pid'] == proc.pid and own['kernel_start'] is not None
        assert own['executable_path'] == str(app / 'Contents/MacOS/Showcase')
        (out / 'owned.json').write_text(json.dumps(own, indent=2) + '\n')
        assert (out / 'ready.json').is_file() and proc.poll() is None, 'No ready window'
        ready = json.loads((out / 'ready.json').read_text())
        assert ready['ready'] is True and ready['pid'] == proc.pid and ready['mode'] == a.mode
        assert type(ready['windowNumber']) is int and ready['windowNumber'] > 0
        assert ready['visible'] and ready['key'] and ready['main'] and ready['frontmost_pid'] == proc.pid
        report['ready'] = ready
        report['phase'] = 'capture-ready'; report['own'] = own; save()
        print(json.dumps({'ready': True, 'pid': own['pid'], 'mode': a.mode, 'output': str(out)}), flush=True)
        end = time.monotonic() + 75
        while time.monotonic() < end and not (out / 'capture.done').exists() and proc.poll() is None:
            time.sleep(0.1)
        report['capture_completed'] = (out / 'capture.done').is_file()
        assert report['capture_completed'] and proc.poll() is None, 'Capture cap reached or app exited'
        report['success'] = True
except Exception as e:
    report['error'] = str(e)
finally:
    try:
        if own is None and proc is not None:
            state = helper('inspect')
            candidate = state.get('own')
            if candidate and candidate['pid'] == proc.pid and candidate['kernel_start'] is not None:
                own = candidate
                (out / 'owned.json').write_text(json.dumps(own, indent=2) + '\n')
        if own is not None:
            report['cleanup'] = helper('cleanup', out / 'original-front.json', out / 'owned.json')
        elif proc is not None and proc.poll() is None:
            raise RuntimeError('Own application identity unavailable; refusing blind stop')
        if proc is not None:
            proc.wait(timeout=3)
            report['app_exit_code'] = proc.returncode
    except Exception as e:
        report['cleanup_error'] = str(e)
        report['success'] = False
    report['phase'] = 'finished'; save()
    print(json.dumps({'success': report['success'], 'output': str(out), 'error': report.get('error'),
                      'cleanup_error': report.get('cleanup_error')}), flush=True)
raise SystemExit(0 if report['success'] else 1)
