#!/usr/bin/env python3
"""One root-prepared private Showcase; no execution without --run."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run', action='store_true')
parser.add_argument('--collector', required=True, type=Path)
parser.add_argument('--focus-guard', required=True, type=Path)
parser.add_argument('app', type=Path)
parser.add_argument('cli', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
if not args.run:
    print('Plan only: one light full-prefix capture through Layout; root must compile/review first.')
    raise SystemExit(0)

collector, guard, app, cli = (p.resolve(strict=True) for p in
                             [args.collector, args.focus_guard, args.app, args.cli])
output = args.output.absolute()
sidecar = Path(str(output) + '.watchdog')
assert not output.exists() and not sidecar.exists(), 'Fresh output and watchdog directory required'
assert collector.is_file() and guard.is_file() and cli.is_file() and app.is_dir()
assert os.environ.get('BERN_REFERENCE_PROFILE') == 'normal'
assert re.fullmatch('[0-9a-f]{40}', os.environ.get('BERN_SOURCE_SHA', '')), 'Root must bind source identity'
sidecar.mkdir(parents=True)
report = {'success': False, 'collector_cap_seconds': 175,
          'app': str(app), 'cli': str(cli), 'output': str(output),
          'collector_sha256': hashlib.sha256(collector.read_bytes()).hexdigest(),
          'focus_guard_sha256': hashlib.sha256(guard.read_bytes()).hexdigest()}
process = None
expected = None
libproc = ctypes.CDLL('/usr/lib/libproc.dylib')
libproc.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
libproc.proc_pidpath.restype = ctypes.c_int

def executable(pid):
    data = ctypes.create_string_buffer(4096)
    size = libproc.proc_pidpath(pid, data, len(data))
    return os.path.realpath(os.fsdecode(data.value)) if size > 0 else None

def parent(pid):
    value = subprocess.check_output(['ps', '-p', str(pid), '-o', 'ppid='], timeout=2)
    return int(value.strip())

def save():
    temp = sidecar / 'watchdog.json.tmp'
    temp.write_text(json.dumps(report, indent=2) + '\n')
    temp.replace(sidecar / 'watchdog.json')

def helper(mode, *paths):
    result = subprocess.run([str(guard), mode, str(app), *(str(p) for p in paths)],
                            capture_output=True, timeout=7)
    name = 'guard-' + mode + '-' + str(time.monotonic_ns())
    (sidecar / (name + '.stdout.json')).write_bytes(result.stdout)
    (sidecar / (name + '.stderr.txt')).write_bytes(result.stderr)
    data = json.loads(result.stdout)
    return result.returncode, data

def refresh_owned():
    global expected
    ownership = output / 'ownership.json'
    if not ownership.exists():
        return
    row = json.loads(ownership.read_text())
    assert row['collector_pid'] == process.pid
    assert row['executable_path'] == str(app / 'Contents/MacOS/Showcase')
    assert row['bundle_id'] == report['private_bundle_id']
    if row.get('launch_date') is None:
        status, snapshot = helper('inspect')
        own = snapshot.get('own')
        if status == 0 and own and own['pid'] == row['pid']:
            row = own
    expected = row
    (sidecar / 'owned.json').write_text(json.dumps(row, indent=2) + '\n')

def bootstrap_owned():
    """Cover Process.run -> ownership-file failures without adopting a foreign instance."""
    global expected
    status, snapshot = helper('inspect')
    report['bootstrap_inspect'] = snapshot
    assert status == 0
    row = snapshot.get('own')
    if row is None:
        return
    assert row['bundle_id'] == report['private_bundle_id']
    assert row['executable_path'] == str(app / 'Contents/MacOS/Showcase')
    assert row['launch_date'] is not None and parent(int(row['pid'])) == process.pid
    expected = row
    (sidecar / 'owned.json').write_text(json.dumps(row, indent=2) + '\n')
    report['ownership_bootstrapped_from_exact_child'] = True

try:
    status, initial = helper('inspect')
    assert status == 0 and initial['success'] is True and initial['own'] is None
    front = initial['front']
    assert front and front['launch_date'] is not None and front['pid'] > 0
    report['private_bundle_id'] = initial['private_bundle_id']
    report['original_front'] = front
    (sidecar / 'original-front.json').write_text(json.dumps(front, indent=2) + '\n')
    env = os.environ.copy()
    env['BERN_PICTURE_FOCUS_GUARD'] = str(guard)
    env['BERN_PICTURE_WATCHDOG_FRONT'] = str(sidecar / 'original-front.json')
    # The product observer output remains supplied by root, unchanged.
    if 'BERN_PICTURE_OBSERVER_OUTPUT_DIR' in env:
        assert Path(env['BERN_PICTURE_OBSERVER_OUTPUT_DIR']).is_absolute()
    report['phase'] = 'collector'; save()
    with (sidecar / 'collector.log').open('wb') as log:
        process = subprocess.Popen([str(collector), str(app), str(cli), str(output)],
                                   env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        report['collector_pid'] = process.pid; save()
        end = time.monotonic() + 175
        while process.poll() is None and time.monotonic() < end:
            if expected is None or expected.get('launch_date') is None:
                refresh_owned()
            time.sleep(0.1)
        if process.poll() is None:
            # Freeze only the collector, leaving the app alive for restore-before-stop.
            os.kill(process.pid, signal.SIGSTOP)
            report['timeout'] = True
        else:
            report['collector_exit_code'] = process.returncode
        refresh_owned()
except BaseException as error:
    report['error'] = type(error).__name__ + ': ' + str(error)
finally:
    cleanup_ok = True
    try:
        if process is not None:
            if process.poll() is None and not report.get('timeout'):
                os.kill(process.pid, signal.SIGSTOP)
            if expected is None or expected.get('launch_date') is None:
                bootstrap_owned()
            if expected is not None:
                # Independent helper applies the same exact-instance and current-front guards.
                status, receipt = helper('cleanup', sidecar / 'original-front.json', sidecar / 'owned.json')
                report['outer_cleanup'] = receipt
                cleanup_ok = status == 0 and receipt['success'] is True
                pid = int(expected['pid'])
                if executable(pid) == str(app / 'Contents/MacOS/Showcase'):
                    # An unregistered background child cannot be foreground; fail closed otherwise.
                    front = receipt.get('front_after', {})
                    if front and front.get('pid') == pid:
                        raise RuntimeError('Own foreground remained after restore attempt; no blind kill')
                    if parent(pid) == process.pid:
                        os.kill(pid, signal.SIGKILL)
                    else:
                        raise RuntimeError('Own executable remains without verified collector parent')
            else:
                status, snapshot = helper('inspect')
                report['cleanup_without_ownership'] = snapshot
                if status != 0 or snapshot.get('own') is not None:
                    cleanup_ok = False
    except BaseException as error:
        cleanup_ok = False
        report['cleanup_error'] = type(error).__name__ + ': ' + str(error)
    finally:
        # Run even when bootstrap/restore failed, before orphaning collector children.
        if process is not None:
            try:
                rows = subprocess.check_output(['ps', '-axo', 'pid=,ppid='], timeout=3).decode().splitlines()
                for row in rows:
                    pid, ppid = map(int, row.split())
                    if ppid != process.pid:
                        continue
                    path = executable(pid)
                    if path in {str(cli), str(guard)}:
                        if parent(pid) == process.pid and executable(pid) == path:
                            os.kill(pid, signal.SIGKILL)
                    elif path == str(app / 'Contents/MacOS/Showcase'):
                        # Covers an unregistered background child before ownership.json.
                        receipt = report.get('outer_cleanup') or report.get('cleanup_without_ownership') or report.get('bootstrap_inspect')
                        front = receipt.get('front_after') if receipt else None
                        if not front or front.get('pid') == pid:
                            cleanup_ok = False
                            report['remaining_app_child'] = {'pid': pid, 'reason': 'No verified non-own foreground; no blind kill'}
                        elif parent(pid) == process.pid and executable(pid) == path:
                            os.kill(pid, signal.SIGKILL)
                report['exact_child_cleanup_attempted'] = True
            except BaseException as error:
                cleanup_ok = False
                report['child_cleanup_error'] = type(error).__name__ + ': ' + str(error)
            finally:
                try:
                    if process.poll() is None:
                        os.kill(process.pid, signal.SIGKILL)
                    process.wait(timeout=3)
                except BaseException as error:
                    cleanup_ok = False
                    report['collector_cleanup_error'] = type(error).__name__ + ': ' + str(error)
    report['cleanup_success'] = cleanup_ok
    report['success'] = cleanup_ok and report.get('collector_exit_code') == 0 and not report.get('timeout') and 'error' not in report
    save()
raise SystemExit(0 if report['success'] else 1)
