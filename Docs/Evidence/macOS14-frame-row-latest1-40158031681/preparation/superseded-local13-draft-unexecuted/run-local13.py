#!/usr/bin/env python3
"""One root-prepared private Gallery; no execution without --run."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import platform
import plistlib
import shutil
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run', action='store_true')
parser.add_argument('--collector', required=True, type=Path)
parser.add_argument('--focus-guard', required=True, type=Path)
parser.add_argument('--collector-sha256', required=True)
parser.add_argument('--focus-guard-sha256', required=True)
parser.add_argument('--locks', required=True, type=Path)
parser.add_argument('--variant', required=True, choices=['control','observer'])
parser.add_argument('--macos14-gate', required=True, type=Path)
parser.add_argument('--macos14-gate-sha256', required=True)
parser.add_argument('output', type=Path)
args = parser.parse_args()
if not args.run:
    print('Plan only: one local13 closed Frame. Root must review/compile adapters and pass real14 gate first.')
    raise SystemExit(0)

assert platform.mac_ver()[0].split('.')[0] == '13' and platform.machine() == 'arm64'
assert os.environ.get('CI') != 'true' and os.environ.get('GITHUB_ACTIONS') != 'true', 'Local13 cannot impersonate CI'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
locks_path=args.locks.resolve(strict=True); locks=json.loads(locks_path.read_text())
assert locks['schema']=='bern_frame_row_local13_locks_v1' and locks['source_sha']=='e48fff46b3a92a28465ad74295bd273a9d69af7d'
group=locks['groups'][args.variant]
collector,guard=(p.resolve(strict=True) for p in [args.collector,args.focus_guard])
app=Path(group['app']).resolve(strict=True);cli=Path(group['cli']).resolve(strict=True)
assert collector.is_file() and guard.is_file() and cli.is_file() and app.is_dir()
assert sha(collector)==args.collector_sha256 and sha(guard)==args.focus_guard_sha256
assert sha(Path(__file__).with_name('FrameClosed.swift'))=='9e39b58ebbd4f51f89f2cb5874bacd02bdb6080ba921c3ecbe25e7e8ec8b5bc3'
assert sha(Path(__file__).with_name('FocusGuard.swift'))=='ab78c7d374169478a5f99c1a3000f9a6180338b78e2f250e5ff1446f7e19345d'
assert sha(app/'Contents/MacOS/Gallery')==group['private_gui_sha256'] and sha(cli)==group['cli_sha256']
assert re.fullmatch(r'dev\.bern\.frame13\.(control|observer)\.[0-9a-f]{32}',group['bundle_id'])
assert plistlib.loads((app/'Contents/Info.plist').read_bytes())['CFBundleIdentifier']==group['bundle_id']
isolation=json.loads(Path(group['receipt']).read_text())
def bundle_members(folder):
    assert not any(p.is_symlink() for p in folder.rglob('*'))
    return {str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
assert bundle_members(app)==isolation['private_members']
assert bundle_members(Path(isolation['original_app']))==isolation['original_members']
assert sha(Path(locks['observer_build_receipt']))==locks['observer_build_sha256']
gate_path=args.macos14_gate.resolve(strict=True);assert sha(gate_path)==args.macos14_gate_sha256
gate=json.loads(gate_path.read_text());assert gate['success'] is True and gate['frame_detail']['equal'] is True
for side,letter in [('control','a'),('observer','b')]:
    path=gate_path.parent/letter/'report.json';assert sha(path)==gate[side+'_report_sha256']
    data=json.loads(path.read_text())
    assert data['success'] is True and data['expected_os']==14 and data['source_sha']==locks['source_sha']
    assert data['app_executable_sha256']==locks['groups'][side]['original_gui_sha256']
output=args.output.resolve();sidecar=Path(str(output)+'.watchdog')
assert not output.exists() and not sidecar.exists(), 'Fresh output/watchdog required'
assert app not in output.parents and output not in app.parents and output != app
sidecar.mkdir(parents=True)
for name,path in [('collector',collector),('focus-guard',guard),('private-app',app),('cli',cli)]:
    result=subprocess.run(['codesign','--verify','--strict',str(path)],capture_output=True,timeout=15)
    (sidecar/(name+'-signature.txt')).write_bytes(result.stdout+result.stderr)
    assert result.returncode==0, name+' signature verification failed'
report={'success':False,'collector_cap_seconds':95,'variant':args.variant,'source_sha':locks['source_sha'],
        'app':str(app),'cli':str(cli),'output':str(output),'collector_sha256':sha(collector),'focus_guard_sha256':sha(guard),
        'collector_source_sha256':sha(Path(__file__).with_name('FrameClosed.swift')),
        'focus_guard_source_sha256':sha(Path(__file__).with_name('FocusGuard.swift')),
        'helper_scope':'same local-only kernel-cleanup adapter for13 control/observer; differs from14 collector cleanup only',
        'macos14_gate_sha256':sha(gate_path),'locks_sha256':sha(locks_path)}
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
    if expected is None:
        bootstrap_owned()


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
    assert row['executable_path'] == str(app / 'Contents/MacOS/Gallery')
    assert valid_start(row) and same_process(row) and parent(int(row['pid'])) == process.pid
    expected = row
    row['collector_pid'] = process.pid
    (sidecar / 'owned.json').write_text(json.dumps(row, indent=2) + '\n')
    (output / 'ownership.json').write_text(json.dumps(row, indent=2) + '\n')
    report['ownership_bootstrapped_from_exact_child'] = True

try:
    status, initial = helper('inspect')
    assert status == 0 and initial['success'] is True and initial['own'] is None
    front = initial['front']
    assert front and front['pid'] > 0 and valid_start(front) and same_process(front)
    assert initial['private_bundle_id'] == group['bundle_id']
    report['private_bundle_id'] = initial['private_bundle_id']
    report['original_front'] = front
    (sidecar / 'original-front.json').write_text(json.dumps(front, indent=2) + '\n')
    output.mkdir(parents=True)
    env = os.environ.copy()
    for key in ['CI','GITHUB_ACTIONS','GITHUB_SHA','BERN_IPC_DIR','BERN_SNAPSHOT_DIR','BERN_MOTION','BERN_FRAME_ROW_LEDGER_OUTPUT_DIR']:
        env.pop(key,None)
    env['BERN_FRAME_LOCAL_EVENTS']='own-pid-active13'
    env['BERN_SOURCE_SHA']=locks['source_sha']
    if args.variant=='observer':
        (output/'ledger').mkdir()
        env['BERN_FRAME_ROW_LEDGER_OUTPUT_DIR']=str(output/'ledger')
    env['BERN_PICTURE_FOCUS_GUARD'] = str(guard)
    env['BERN_PICTURE_WATCHDOG_FRONT'] = str(sidecar / 'original-front.json')
    report['phase'] = 'collector'; save()
    with (sidecar / 'collector.log').open('wb') as log:
        process = subprocess.Popen([str(collector), str(app), str(cli), str(output),'13',args.variant,locks['source_sha']],
                                   env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        report['collector_pid'] = process.pid; save()
        end = time.monotonic() + 95
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
                observed=json.loads((output/'report.json').read_text())
                if observed.get('frontmost_before') != report['original_front']['pid']:
                    status,snapshot=helper('inspect')
                    assert status==0 and (snapshot.get('front') or {}).get('pid') != expected['pid'], 'Collector original-front mismatch; refusing blind foreground stop'
                # Independent helper applies the same exact-instance and current-front guards.
                status, receipt = helper('cleanup', sidecar / 'original-front.json', sidecar / 'owned.json')
                report['outer_cleanup'] = receipt
                cleanup_ok = status == 0 and receipt['success'] is True
                pid = int(expected['pid'])
                if executable(pid) == str(app / 'Contents/MacOS/Gallery'):
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
                    elif path == str(app / 'Contents/MacOS/Gallery'):
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
    # Only the fresh private domain and collector-reported own IPC path are cleanup targets.
    try:
        assert expected is None or not same_process(expected), 'Owned child still live; no preferences/IPC cleanup'
        identifier=group['bundle_id']
        prefs=Path(isolation['preferences_path']);state=Path(isolation['saved_state_path'])
        assert prefs==Path.home()/'Library/Preferences'/(identifier+'.plist')
        assert state==Path.home()/'Library/Saved Application State'/(identifier+'.savedState')
        result=subprocess.run(['defaults','delete',identifier],capture_output=True,timeout=5)
        report['private_preferences_delete_status']=result.returncode
        if prefs.is_symlink() or prefs.is_file(): prefs.unlink()
        if state.is_symlink(): state.unlink()
        elif state.exists(): shutil.rmtree(state)
        data=json.loads((output/'report.json').read_text()) if (output/'report.json').exists() else {}
        ipc=data.get('ipc_directory') or data.get('ipc_preserved_for_live_child')
        if ipc:
            path=Path(ipc)
            assert path.is_absolute() and path.name.startswith('bern-frame-'+str(process.pid)+'-') and path.parent.resolve()==Path('/tmp').resolve()
            assert not path.is_symlink()
            if path.exists(): shutil.rmtree(path)
        report['private_preferences_absent_at_check']=not prefs.exists() and not state.exists()
        report['ipc_cleanup_scope']='exact collector-reported path only; timeout before cleanup receipt may require root inspection'
        assert bundle_members(app)==isolation['private_members']
        assert bundle_members(Path(isolation['original_app']))==isolation['original_members'] and sha(cli)==group['cli_sha256']
        report['originals_unchanged']=True
        if report.get('collector_exit_code')==0:
            assert data['success'] is True and data['expected_os']==13 and data['source_sha']==locks['source_sha']
            assert data['heartbeat_ci_only'] is False and data['heartbeat_mode']=='local-own-active13' and data['local_events_requested']=='own-pid-active13'
            assert data['local_cleanup_adapter']=='kernel_guard_before_stop_v1' and data['app_still_running_after_cleanup'] is False
            assert data['row_ledger_enabled'] is (args.variant=='observer')
            report['collector_success']=True
    except BaseException as error:
        cleanup_ok=False
        report['post_cleanup_error']=type(error).__name__+': '+str(error)
    report['cleanup_success'] = cleanup_ok
    report['success'] = cleanup_ok and report.get('collector_exit_code') == 0 and not report.get('timeout') and 'error' not in report
    save()
raise SystemExit(0 if report['success'] else 1)
