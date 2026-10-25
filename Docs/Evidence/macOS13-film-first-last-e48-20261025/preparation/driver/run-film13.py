#!/usr/bin/env python3
"""One original-e48 Film initial/first-Last capture; no action without --run."""
import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import platform
import plistlib
import shutil
import subprocess
import time

SOURCE = 'e48fff46b3a92a28465ad74295bd273a9d69af7d'
KIND = 'film_first_last13_capture'
CONTROL_GUI = 'd44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c'
CONTROL_CLI = '31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5'
DELIVERY_SHA = 'e6fbe8ea1c3f62dc89a5e6d56c6cc40c6b369a15eefed2d4e07dbb4c3b9a71c7'
GALLERY_BUILD_SHA = 'a76b48042bb473e4f372e26ef84d480482e543fb876d15037662a42482bd454a'
COLLECTOR_SOURCE_SHA = 'c4a1bd81e61079a75047e9cfc1f1407b2f12de1ccad7744878ff98975839ee9b'
GUARD_SOURCE_SHA = 'ab78c7d374169478a5f99c1a3000f9a6180338b78e2f250e5ff1446f7e19345d'
LOCAL_SOURCE_MANIFEST_SHA = 'fa2fe88074dad1cea738227d7925d6e1be03d8247a7f85ac1f1c8504fff10f26'

REFERENCE14_SHA = '8921655dea0938f76e49cfc808414d3278fce1deabeca1b98f5fd1d5bdfe8f50'
REFERENCE14_RESULT_SHA = '54b06d51178cf8e57d947c2de193f837b36ab0a52fa0e341357f0d6972cba0bf'
REFERENCE14_SOURCE_SHA = '6c4d5c93c9331ba4dd6427aa18799b6a1e720b6e2e006e036fb908ced4f9e635'


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_reference(path):
    path=path.resolve(strict=True)
    assert file_hash(path)==REFERENCE14_SHA
    ref=json.loads(path.read_text())
    assert ref['schema']=='bern_exact_e48_film_first_last14_reference_v1' and ref['reference_data_complete'] is True
    assert ref['source_sha']==SOURCE and ref['gui_sha256']==CONTROL_GUI and ref['cli_sha256']==CONTROL_CLI
    assert ref['build_run']==40070407306 and ref['run_id']==40165343690
    assert ref['harness_sha']=='2cff19aad748ac673fefda921b313886bb902e4b'
    assert ref['collector_source_sha256']==REFERENCE14_SOURCE_SHA
    limits=ref['limits']
    assert limits['termination_or_restored_front_receipt_available'] is False
    assert limits['old_CI_cleanup_order_stop_before_restore'] is True and limits['does_not_satisfy_local13_kernel_cleanup_gate'] is True
    children=[]
    for entry,expected_path,expected_sha in [(ref['raw_result'],'raw/result.json',REFERENCE14_RESULT_SHA),
        (ref['collector_source'],'raw/gallery-film-probe.swift',REFERENCE14_SOURCE_SHA),
        (ref['initial_setup']['png'],'raw/direct-film.png','46ae79801159c1a9b26e6a86225e51bcfc34a667bf215ec94a611c6cfe8b00d8'),
        (ref['first_last']['png'],'raw/direct-last.png','13788694f15e1d1c87111de35daac508c6fa65e7f725ae4639136504013e6522')]:
        assert entry['path']==expected_path and entry['sha256']==expected_sha
        child=(path.parent/entry['path']).resolve(strict=True)
        assert child.is_relative_to(path.parent) and file_hash(child)==expected_sha
        children.append(child)
    raw=json.loads(children[0].read_text())
    assert raw['success'] is True and raw['source_sha']==SOURCE and raw['harness_sha']==ref['harness_sha']
    assert raw['expected_os_major']==14 and raw['requested_scenario']=='direct' and raw['followup_sequence']=='last-resize'
    assert raw['system_preferences']=={'increase_contrast':False,'reduce_motion':False,'reduce_transparency':False}
    assert len(raw['cases'])==1
    case=raw['cases'][0]
    assert ref['initial_setup']['capture']==case['film'] and ref['initial_setup']['terminal_ax']==case['settled_ax']
    assert ref['first_last']['stage']=='last' and ref['first_last']['json_pointer']=='/cases/0/followup_stages/0'
    assert case['followup_stages'][0]['stage']=='last'
    assert ref['first_last']['capture']==case['followup_stages'][0]['capture'] and ref['first_last']['terminal_ax']==case['followup_stages'][0]['ax']
    return ref,[path,*children]


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run', action='store_true')
parser.add_argument('--collector', required=True, type=Path)
parser.add_argument('--focus-guard', required=True, type=Path)
parser.add_argument('--collector-sha256', required=True)
parser.add_argument('--focus-guard-sha256', required=True)
parser.add_argument('--locks', required=True, type=Path)
parser.add_argument('--locks-sha256', required=True)
parser.add_argument('--local-sources', required=True, type=Path)
parser.add_argument('--helper-build', required=True, type=Path)
parser.add_argument('--helper-build-sha256', required=True)
parser.add_argument('output', type=Path)
args = parser.parse_args()
if not args.run:
    print('Plan only: fixed actual14 Film data prerequisite; fresh Film locks and actual compiled helper receipts required before --run.')
    raise SystemExit(0)

assert platform.mac_ver()[0].split('.')[0] == '13' and platform.machine() == 'arm64'
assert os.environ.get('CI') != 'true' and os.environ.get('GITHUB_ACTIONS') != 'true', 'Local13 cannot impersonate CI'
assert 'BERN_FRAME_ROW_LEDGER_OUTPUT_DIR' not in os.environ and 'BERN_SCROLL_TRACE_DIR' not in os.environ, 'No ledger or scroll trace environment allowed'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for value in [args.collector_sha256,args.focus_guard_sha256,args.locks_sha256,args.helper_build_sha256]:
    assert re.fullmatch(r'[0-9a-f]{64}',value), 'Root-reviewed actual digest required'
locks_path=args.locks.resolve(strict=True); assert sha(locks_path)==args.locks_sha256
locks=json.loads(locks_path.read_text())
assert set(locks)=={'schema','kind','source_sha','film','delivery_receipt','delivery_receipt_sha256','gallery_build_json','gallery_build_json_sha256','commands','scope','reference14','reference14_sha256'}
assert locks['schema']=='bern_film_first_last13_locks_v1' and locks['source_sha']==SOURCE and locks['kind']==KIND
group=locks['film']
assert set(group)=={'app','cli','bundle_id','private_gui_sha256','original_gui_sha256','cli_sha256','receipt'}
assert group['original_gui_sha256']==CONTROL_GUI and group['cli_sha256']==CONTROL_CLI
collector,guard=(p.resolve(strict=True) for p in [args.collector,args.focus_guard])
app=Path(group['app']).resolve(strict=True);cli=Path(group['cli']).resolve(strict=True)
assert collector.is_file() and guard.is_file() and cli.is_file() and app.is_dir()
assert sha(collector)==args.collector_sha256 and sha(guard)==args.focus_guard_sha256
sources=args.local_sources.resolve(strict=True);source_manifest=sources/'SHA256SUMS'
assert sha(source_manifest)==LOCAL_SOURCE_MANIFEST_SHA
source_inputs=[source_manifest]
for line in source_manifest.read_text().splitlines():
    h,name=line.split('  ',1);assert re.fullmatch(r'[0-9a-f]{64}',h)
    path=(sources/name).resolve(strict=True);assert path.parent==sources and path.is_file() and sha(path)==h
    source_inputs.append(path)
assert sha(sources/'FilmFirstLast.swift')==COLLECTOR_SOURCE_SHA and sha(sources/'FocusGuard.swift')==GUARD_SOURCE_SHA
helper_build_path=args.helper_build.resolve(strict=True)
assert sha(helper_build_path)==args.helper_build_sha256
helper_build=json.loads(helper_build_path.read_text())
assert helper_build['kind']=='film_first_last13_helpers_build_only' and helper_build['target']=='arm64-apple-macosx13.0'
assert helper_build['actual_min_os']=='13.0' and re.fullmatch(r'[0-9]+(?:\.[0-9]+)+',helper_build['actual_embedded_sdk'])
expected_sources={str(sources/'FilmFirstLast.swift'):COLLECTOR_SOURCE_SHA,str(sources/'FocusGuard.swift'):GUARD_SOURCE_SHA}
for key in ['source_before','source_after']:
    assert {row['path']:row['sha256'] for row in helper_build[key]}==expected_sources
for name,binary,h in [('FilmFirstLast',collector,args.collector_sha256),('FocusGuard',guard,args.focus_guard_sha256)]:
    row=helper_build['binaries'][name]
    assert Path(row['path']).resolve(strict=True)==binary and row['sha256']==h and row['bytes']==binary.stat().st_size
assert all(row['exit_code']==0 for row in helper_build['commands'])
assert sha(app/'Contents/MacOS/Gallery')==group['private_gui_sha256'] and sha(cli)==CONTROL_CLI
assert re.fullmatch(r'dev\.bern\.frame13\.film\.[0-9a-f]{32}',group['bundle_id'])
assert plistlib.loads((app/'Contents/Info.plist').read_bytes())['CFBundleIdentifier']==group['bundle_id']
isolation_path=Path(group['receipt']).resolve(strict=True)
isolation=json.loads(isolation_path.read_text())
assert isolation['kind']==KIND and isolation['source_sha']==SOURCE
assert isolation['reference14']==locks['reference14'] and isolation['reference14_sha256']==locks['reference14_sha256']==REFERENCE14_SHA
assert isolation['private_app']==str(app) and isolation['private_bundle_id']==group['bundle_id']
assert isolation['original_gui_sha256']==CONTROL_GUI and isolation['private_gui_sha256']==group['private_gui_sha256']
assert isolation['cli']==str(cli) and isolation['cli_sha256']==CONTROL_CLI
assert isolation['sections_and_signature_storage_sizes_normalized_equal'] is True and isolation['originals_unchanged'] is True
def bundle_members(folder):
    assert not any(p.is_symlink() for p in folder.rglob('*'))
    return {str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
original_app=Path(isolation['original_app']).resolve(strict=True)
assert bundle_members(app)==isolation['private_members']
assert bundle_members(original_app)==isolation['original_members']
assert sha(original_app/'Contents/MacOS/Gallery')==CONTROL_GUI

delivery_path=Path(locks['delivery_receipt']).resolve(strict=True)
build_path=Path(locks['gallery_build_json']).resolve(strict=True)
assert sha(delivery_path)==locks['delivery_receipt_sha256']==DELIVERY_SHA
assert sha(build_path)==locks['gallery_build_json_sha256']==GALLERY_BUILD_SHA
assert isolation['delivery_receipt']==str(delivery_path) and isolation['delivery_receipt_sha256']==DELIVERY_SHA
assert isolation['gallery_build_json']==str(build_path) and isolation['gallery_build_json_sha256']==GALLERY_BUILD_SHA
delivery=json.loads(delivery_path.read_text());build=json.loads(build_path.read_text())
assert delivery['source_sha']==SOURCE and delivery['build_run']==40070407306 and delivery['strict_signatures_after_move'] is True
assert delivery['delivered_gui_sha256']==CONTROL_GUI and delivery['delivered_cli_sha256']==CONTROL_CLI
assert isolation['original_members']=={row['path']:row['sha256'] for row in delivery['original_archive_app_members_verified_after_move']}
assert build['source_sha']==SOURCE and build['architecture']=='arm64' and build['minimum_macos']=='13.0' and build['sdk']=='26.2'
assert build['executable_sha256']==CONTROL_GUI and build['cli_sha256']==CONTROL_CLI
assert (build_path.parent/build['delivery_receipt']).resolve(strict=True)==delivery_path

reference_path=Path(locks['reference14']).resolve(strict=True)
reference,reference_inputs=read_reference(reference_path)

output=args.output.resolve();sidecar=Path(str(output)+'.watchdog')
assert not output.exists() and not sidecar.exists(), 'Fresh output/watchdog required'
inputs=[locks_path,collector,guard,app,cli,isolation_path,original_app,delivery_path,build_path,sources,helper_build_path,reference_path.parent,
        Path(__file__).resolve().parent,Path(__file__).resolve(),*source_inputs,*reference_inputs]
pinned_inputs={str(p):sha(p) for p in [locks_path,isolation_path,helper_build_path,Path(__file__).resolve(),*source_inputs,*reference_inputs]}
assert all(dst!=p and dst not in p.parents and p not in dst.parents for dst in [output,sidecar] for p in inputs), 'Output/watchdog and inputs must not overlap in either direction'
sidecar.mkdir(parents=True)
for name,path in [('collector',collector),('focus-guard',guard),('private-app',app),('cli',cli)]:
    result=subprocess.run(['codesign','--verify','--strict',str(path)],capture_output=True,timeout=15)
    (sidecar/(name+'-signature.txt')).write_bytes(result.stdout+result.stderr)
    assert result.returncode==0, name+' signature verification failed'
report={'success':False,'kind':KIND,'outer_wait_cap_seconds':95,'collector_deadline_seconds':75,'source_sha':SOURCE,
        'scope':'Original-e48 Film initial and first Last only; actual14 data prerequisite is not strong cleanup or cross-OS acceptance',
        'app':str(app),'cli':str(cli),'output':str(output),'collector_sha256':sha(collector),'focus_guard_sha256':sha(guard),
        'collector_source_sha256':COLLECTOR_SOURCE_SHA,'focus_guard_source_sha256':GUARD_SOURCE_SHA,
        'helper_scope':'Local Film adaptation with separately documented startup/heartbeat/sampling timing; not the same collector as14',
        'reference14_sha256':REFERENCE14_SHA,'helper_build_sha256':args.helper_build_sha256,'local_source_manifest_sha256':LOCAL_SOURCE_MANIFEST_SHA,
        'locks_sha256':sha(locks_path),'delivery_receipt_sha256':DELIVERY_SHA,'gallery_build_json_sha256':GALLERY_BUILD_SHA,
        'ipc_cleanup_verified':False,'exact_child_cleanup_verified':False,
        'bound_input_sha256':pinned_inputs}
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

def exact_instance_absent(row):
    """A changed image/path alone is not evidence that this kernel instance ended."""
    if not valid_start(row):
        return False
    pid=int(row['pid']);info=process_info(pid)
    if info is not None:
        return info['kernel_start'] != row['kernel_start']
    try:
        os.kill(pid,0)
    except ProcessLookupError:
        return True
    except PermissionError:
        pass
    return False

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
    for path in [sidecar/'owned.json',output/'ownership.json']:
        temp=path.with_suffix('.tmp');temp.write_text(json.dumps(row,indent=2)+'\n');temp.replace(path)
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
    for key in ['CI','GITHUB_ACTIONS','GITHUB_SHA','GITHUB_RUN_ID','BERN_IPC_DIR','BERN_SNAPSHOT_DIR','BERN_MOTION','BERN_FRAME_ROW_LEDGER_OUTPUT_DIR','BERN_SCROLL_TRACE_DIR']:
        env.pop(key,None)
    env['BERN_FRAME_LOCAL_EVENTS']='own-pid-active13'
    env['BERN_SOURCE_SHA']=locks['source_sha']
    assert 'BERN_FRAME_ROW_LEDGER_OUTPUT_DIR' not in env
    env['BERN_PICTURE_FOCUS_GUARD'] = str(guard)
    env['BERN_PICTURE_WATCHDOG_FRONT'] = str(sidecar / 'original-front.json')
    report['phase'] = 'collector'; save()
    with (sidecar / 'collector.log').open('wb') as log:
        process = subprocess.Popen([str(collector), str(app), str(cli), str(output)],
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
    exact_child_cleanup_verified = False
    try:
        if process is not None:
            if process.poll() is None and not report.get('timeout'):
                os.kill(process.pid, signal.SIGSTOP)
            if expected is None or not valid_start(expected):
                bootstrap_owned()
            if expected is not None:
                observed=json.loads((output/'report.json').read_text())
                original=report['original_front']
                assert observed.get('frontmost_before')==original['pid'] and valid_start(original) and same_process(original), 'Collector original front is not correlated with the still-matching outer kernel receipt; no restore/stop request'
                report['collector_original_front_correlated_before_outer_cleanup']=True
                # Independent helper applies the same exact-instance and current-front guards.
                status, receipt = helper('cleanup', sidecar / 'original-front.json', sidecar / 'owned.json')
                report['outer_cleanup'] = receipt
                cleanup_ok = status == 0 and receipt['success'] is True
                pid = int(expected['pid'])
                if executable(pid) == str(app / 'Contents/MacOS/Gallery'):
                    # An unregistered background child cannot be foreground; fail closed otherwise.
                    front = receipt.get('front_after', {})
                    if not front or front.get('pid') == pid or not valid_start(front) or not same_process(front):
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
                cleanup_ok = False  # No exact ownership receipt: absence is not verified cleanup.
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
                        status,snapshot=helper('inspect')
                        front=snapshot.get('front')
                        if status != 0 or not front or front.get('pid') == pid or not valid_start(front) or not same_process(front):
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
        if expected is not None:
            end=time.monotonic()+0.5
            while not exact_instance_absent(expected) and time.monotonic()<end:
                time.sleep(0.02)
            exact_child_cleanup_verified=cleanup_ok and exact_instance_absent(expected) and not report.get('remaining_app_child')
        report['exact_child_cleanup_verified']=exact_child_cleanup_verified
        if process is not None and not exact_child_cleanup_verified:
            cleanup_ok=False
    # Only the fresh private domain and collector-reported own IPC path are cleanup targets.
    try:
        assert cleanup_ok and exact_child_cleanup_verified and expected is not None and exact_instance_absent(expected), 'Exact child cleanup not verified; no preferences/IPC cleanup'
        data=json.loads((output/'report.json').read_text()) if (output/'report.json').exists() else {}
        ipc=data.get('ipc_directory') or data.get('ipc_preserved_for_live_child')
        report['ipc_cleanup_verified']=False
        assert ipc is not None, 'No exact collector IPC receipt; IPC cleanup remains unverified'
        path=Path(ipc)
        assert path.is_absolute() and path.name.startswith('bern-frame-'+str(process.pid)+'-') and path.parent.resolve()==Path('/tmp').resolve()
        assert not path.is_symlink()
        if path.exists():
            assert path.is_dir()
            shutil.rmtree(path)
        report['ipc_cleanup_verified']=not path.exists() and not path.is_symlink()
        assert report['ipc_cleanup_verified']
        identifier=group['bundle_id']
        prefs=Path(isolation['preferences_path']);state=Path(isolation['saved_state_path'])
        assert prefs==Path.home()/'Library/Preferences'/(identifier+'.plist')
        assert state==Path.home()/'Library/Saved Application State'/(identifier+'.savedState')
        result=subprocess.run(['defaults','delete',identifier],capture_output=True,timeout=5)
        report['private_preferences_delete_status']=result.returncode
        if prefs.is_symlink() or prefs.is_file(): prefs.unlink()
        if state.is_symlink(): state.unlink()
        elif state.exists(): shutil.rmtree(state)
        report['private_preferences_absent_at_check']=not prefs.exists() and not state.exists()
        assert report['private_preferences_absent_at_check'] and not prefs.is_symlink() and not state.is_symlink(), 'Private preferences/state remain after cleanup'
        report['ipc_cleanup_scope']='exact collector-reported path after verified exact child cleanup; missing receipt fails closed'
        assert bundle_members(app)==isolation['private_members']
        assert bundle_members(Path(isolation['original_app']))==isolation['original_members'] and sha(cli)==group['cli_sha256']
        report['originals_unchanged']=True
        if report.get('collector_exit_code')==0:
            assert data['success'] is True and data['expected_os']==13 and data['source_sha']==locks['source_sha']
            assert data['heartbeat_ci_only'] is False and data['heartbeat_mode']=='local-own-active13' and data['local_events_requested']=='own-pid-active13'
            assert data['local_cleanup_adapter']=='kernel_guard_before_stop_v1' and data['app_still_running_after_cleanup'] is False
            binding=data['local_original_front_binding']
            assert binding['matched'] is True and binding['pid']==report['original_front']['pid'] and binding['outer_front_receipt_sha256']==sha(sidecar/'original-front.json')
            report['collector_defer_original_front_binding_verified']=True
            assert data['row_ledger_enabled'] is False
            assert 'row_ledger' not in data and 'row_ledger_arm' not in data
            assert not (output/'ledger').exists() and not (output/'ledger').is_symlink()
            assert data['kind']==KIND and data['label']=='film-first-last' and data['ci_run_id']=='local' and data['collector_executable_sha256']==args.collector_sha256
            assert data['deadline_seconds']==75 and data['scenario']=='direct' and data['followup_sequence']=='first-last-only' and data['scroll_trace_enabled'] is False
            assert data['system_preferences']=={'increase_contrast':False,'reduce_motion':False,'reduce_transparency':False}
            assert data['final_context']=={'appearance':'Light','page':'Film','requested_action':'first Last only','terminal_states':2}
            assert data['app_executable_sha256']==group['private_gui_sha256'] and data['cli_sha256']==CONTROL_CLI
            assert data['app_termination_status']==0 and data['kernel_guard_cleanup']['success'] is True
            assert [row['stage'] for row in data['stages']]==['initial','last']
            shots=[data['setup_patterns']]
            for stage,name in zip(data['stages'],['direct-film.png','direct-last.png']):
                assert stage['pid']==expected['pid'] and stage['capture']['png']==name and stage['ax']['truncated'] is False
                images=[e for e in stage['ax']['elements'] if e['role']=='AXImage' and e['text'] in ['Gingham','Tartan','Madras','Glen','Houndstooth','Windowpane']]
                assert len(images)==6 and len({e['text'] for e in images})==6
                assert all(all(math.isfinite(e['frame'][k]) for k in ['x','y','width','height']) and e['frame']['width']>0 and e['frame']['height']>0 for e in images)
                shots.append(stage['capture'])
            assert shots[0]['png']=='setup-patterns.png'
            for shot in shots:
                assert shot['equal_comparisons']>=4 and shot['samples']>=5 and shot['bounds_points']['Width']==920 and shot['bounds_points']['Height']==668
                assert (output/shot['png']).is_file()
            assert all(sha(Path(name))==h for name,h in pinned_inputs.items())
            assert sha(delivery_path)==DELIVERY_SHA and sha(build_path)==GALLERY_BUILD_SHA
            report['collector_success']=True
    except BaseException as error:
        cleanup_ok=False
        report['post_cleanup_error']=type(error).__name__+': '+str(error)
    report['cleanup_success'] = cleanup_ok
    report['success'] = cleanup_ok and report.get('collector_exit_code') == 0 and not report.get('timeout') and 'error' not in report
    save()
raise SystemExit(0 if report['success'] else 1)
