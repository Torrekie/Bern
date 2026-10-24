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
# SDK sys/proc_info.h proc_bsdinfo, arm64: sizeof136, start timeval at120/128.
class ProcBSDInfo(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in [
        'flags', 'status', 'xstatus', 'pid', 'ppid', 'uid', 'gid', 'ruid',
        'rgid', 'svuid', 'svgid', 'rfu_1']] + [
        ('comm', ctypes.c_char * 16), ('name', ctypes.c_char * 32),
        ('nfiles', ctypes.c_uint32), ('pgid', ctypes.c_uint32),
        ('pjobc', ctypes.c_uint32), ('e_tdev', ctypes.c_uint32),
        ('e_tpgid', ctypes.c_uint32), ('nice', ctypes.c_int32),
        ('start_sec', ctypes.c_uint64), ('start_usec', ctypes.c_uint64)]
assert ctypes.sizeof(ProcBSDInfo) == 136
assert ProcBSDInfo.start_sec.offset == 120 and ProcBSDInfo.start_usec.offset == 128
libproc.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64,
                                ctypes.c_void_p, ctypes.c_int]
libproc.proc_pidinfo.restype = ctypes.c_int

def process_info(pid):
    info = ProcBSDInfo()
    size = ctypes.sizeof(info)
    count = libproc.proc_pidinfo(pid, 3, 0, ctypes.byref(info), size)  # PROC_PIDTBSDINFO
    if count != size or info.pid != pid or info.start_sec <= 0 or info.start_usec >= 1_000_000:
        return None
    return {'ppid': int(info.ppid), 'kernel_start':
            {'tv_sec': int(info.start_sec), 'tv_usec': int(info.start_usec)}}

def valid_start(row):
    stamp = row.get('kernel_start')
    return isinstance(stamp, dict) and type(stamp.get('tv_sec')) is int and \
        type(stamp.get('tv_usec')) is int and stamp['tv_sec'] > 0 and 0 <= stamp['tv_usec'] < 1_000_000

def same_process(row):
    info = process_info(int(row['pid']))
    return valid_start(row) and info is not None and info['kernel_start'] == row['kernel_start'] and \
        executable(int(row['pid'])) == row['executable_path']

def executable(pid):
    data = ctypes.create_string_buffer(4096)
    size = libproc.proc_pidpath(pid, data, len(data))
    return os.path.realpath(os.fsdecode(data.value)) if size > 0 else None

def parent(pid):
    info = process_info(pid)
    if info is None:
        raise ProcessLookupError('Kernel process identity unavailable')
    return info['ppid']

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
    if not valid_start(row):
        status, snapshot = helper('inspect')
        own = snapshot.get('own')
        if status == 0 and own and own['pid'] == row['pid']:
            row = own
    assert valid_start(row), 'Kernel process start unavailable; no launchDate fallback'
    current = process_info(int(row['pid']))
    assert current is None or current['kernel_start'] == row['kernel_start'], 'PID starttime changed'
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
    assert valid_start(row) and same_process(row) and parent(int(row['pid'])) == process.pid
    expected = row
    (sidecar / 'owned.json').write_text(json.dumps(row, indent=2) + '\n')
    report['ownership_bootstrapped_from_exact_child'] = True

try:
    status, initial = helper('inspect')
    assert status == 0 and initial['success'] is True and initial['own'] is None
    front = initial['front']
    assert front and front['pid'] > 0 and valid_start(front) and same_process(front)
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
            if expected is None or not valid_start(expected):
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
            if expected is None or not valid_start(expected):
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
                    if not front or front.get('pid') == pid:
                        raise RuntimeError('Own foreground remained after restore attempt; no blind kill')
                    if parent(pid) == process.pid and same_process(expected):
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
                        info = process_info(pid)
                        if info is not None and info['ppid'] == process.pid:
                            child = {'pid': pid, 'executable_path': path, 'kernel_start': info['kernel_start']}
                            if same_process(child) and parent(pid) == process.pid:
                                os.kill(pid, signal.SIGKILL)
                    elif path == str(app / 'Contents/MacOS/Showcase'):
                        # Covers an unregistered background child before ownership.json.
                        receipt = report.get('outer_cleanup') or report.get('cleanup_without_ownership') or report.get('bootstrap_inspect')
                        front = receipt.get('front_after') if receipt else None
                        if not front or front.get('pid') == pid:
                            cleanup_ok = False
                            report['remaining_app_child'] = {'pid': pid, 'reason': 'No verified non-own foreground; no blind kill'}
                        elif expected is not None and expected['pid'] == pid and same_process(expected) and parent(pid) == process.pid:
                            os.kill(pid, signal.SIGKILL)
                        else:
                            cleanup_ok = False
                            report['remaining_app_child'] = {'pid': pid, 'reason': 'No matching kernel-start ownership receipt; no blind kill'}
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
