#!/usr/bin/env python3
"""One candidate13 capture; actual successful14 color gate is mandatory before --run."""
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

SOURCE = "ce462b3ef5d11b72d51ddf9158940d686bc7707a"
BASELINE = "e48fff46b3a92a28465ad74295bd273a9d69af7d"
KIND = "split_label_color_candidate13_capture"
LOCKS_SCHEMA = "bern_split_label_color_candidate13_locks_v1"
ORIGINAL_GUI = "d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c"
ORIGINAL_CLI = "31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5"
CI_CAPTURE_SOURCE = "fa850da24c63d6f8a543808b59ff07d5a5535d718ef2fec949b99df6f8dc9b69"
CI_GATE_SOURCE = "f8a3f035a357a211f86ba5ca70774745324db5e1778f5a7644384fc95978a618"
STYLE_SOURCE = "8219c50ec45a81eb7516b63bddbc7541211006c1a09f0069a93390707c0c6df0"
GENERATED_SOURCE = "f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653"
COLLECTOR_SOURCE_SHA = '61426976dbb557d0d8974dcb4da11337bc1611420b04cec0f856bace14bf362c'
GUARD_SOURCE_SHA = 'ab78c7d374169478a5f99c1a3000f9a6180338b78e2f250e5ff1446f7e19345d'
LOCAL_SOURCE_MANIFEST_SHA = '9e50ba1b0e22223183a0ea102d9ced851c11db52bff9adec475c9b2013299089'

def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_contract(build_path, build_sha, gate_path, gate_sha, control_path, candidate_path):
    for value in [build_sha,gate_sha]:
        assert re.fullmatch(r"[0-9a-f]{64}",value), "Root-reviewed actual digest required"
    build_path,gate_path,control_path,candidate_path = [p.resolve(strict=True) for p in [build_path,gate_path,control_path,candidate_path]]
    assert file_hash(build_path)==build_sha and file_hash(gate_path)==gate_sha
    manifest=json.loads(build_path.read_text());gate=json.loads(gate_path.read_text())
    assert manifest['schema']=='bern_split_label_color_build_v1' and manifest['success'] is True
    assert manifest['source_sha']==SOURCE and manifest['baseline_sha']==BASELINE
    assert re.fullmatch(r"[0-9]+",manifest['run_id']) and re.fullmatch(r"[0-9a-f]{40}",manifest['harness_sha'])
    assert manifest['compiled_style_sha256']==STYLE_SOURCE and manifest['compiled_generated_sha256']==GENERATED_SOURCE
    plan=manifest['build']
    assert plan['ui']=='swiftui-modern' and plan['minimum_macos']=='13.0' and plan['architecture']=='arm64'
    assert plan['app_bundle']=='Gallery.app' and plan['profile']=='release'
    gui=manifest['binaries']['Gallery.app/Contents/MacOS/Gallery'];cli=manifest['binaries']['bin/gallery']
    capture=manifest['helpers']['FrameColorCapture'];gate_helper=manifest['helpers']['FrameColorGate']
    for entry in [gui,cli,capture,gate_helper]:
        assert re.fullmatch(r"[0-9a-f]{64}",entry['sha256']) and type(entry['bytes']) is int and entry['bytes']>0
    assert capture['source_sha256']==CI_CAPTURE_SOURCE and gate_helper['source_sha256']==CI_GATE_SOURCE
    assert gate['kind']=='split_label_color14_no_effect' and gate['success'] is True
    assert gate['frame_detail']['equal'] is True and gate['frame_detail']['changed_pixels']==0
    assert gate['frame_roi_points']==[211,52,920,668]
    assert gate['build_manifest_sha256']==build_sha and gate['ci_run_id']==manifest['run_id'] and gate['harness_sha']==manifest['harness_sha']
    assert gate['collector_executable_sha256']==capture['sha256'] and gate['gate_executable_sha256']==gate_helper['sha256']
    inputs=[build_path,gate_path,control_path,candidate_path]
    for side,path,source,expected_gui,expected_cli in [
        ('control',control_path,BASELINE,ORIGINAL_GUI,ORIGINAL_CLI),
        ('candidate',candidate_path,SOURCE,gui['sha256'],cli['sha256'])]:
        assert file_hash(path)==gate[side+'_report_sha256']
        row=json.loads(path.read_text())
        assert row['success'] is True and row['source_sha']==source and row['label']==side
        assert row['expected_os']==14 and re.match(r"^Version 14\.",row['os'])
        assert row['ci_run_id']==manifest['run_id'] and row['harness_sha']==manifest['harness_sha']
        assert row['collector_executable_sha256']==capture['sha256']
        assert row['app_executable_sha256']==expected_gui and row['cli_sha256']==expected_cli
        assert row['closed_only'] is True and row['row_ledger_enabled'] is False
        assert not any(k.startswith('row_ledger') and k!='row_ledger_enabled' for k in row)
        assert row['app_still_running_after_cleanup'] is False and row['app_termination_status']==0
        assert row['deadline_seconds']==75 and row['heartbeat_ci_only'] is True and row['heartbeat_mode']=='ci-own-active'
        assert row['system_preferences']=={'increase_contrast':False,'reduce_motion':False,'reduce_transparency':False}
        context=row['final_context']
        assert context['appearance']=='Light' and context['caption'] is True and context['volume']=='closed' and context['video']=='Paused0'
        assert row['bundled_tides_sha256']=='145a1b5e572bd3ce16207e2b341c0eecb04b4d1e765bf72f5fe3809a24f34957'
        assert len(row['captures'])==1
        shot=row['captures'][0]
        assert shot['png']=='frame-closed-light.png' and shot['stable_equal_comparisons']>=4 and shot['samples']>=5
        assert shot['canvas_screen_top_left_points']['width']==920 and shot['canvas_screen_top_left_points']['height']==668
        assert shot['icc_sha256']==gate['icc_sha256']
        png=(path.parent/shot['png']).resolve(strict=True)
        assert file_hash(png)==shot['png_sha256']==gate[side+'_png_sha256']
        inputs.append(png)
    return manifest,gate,gui,cli,inputs


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run', action='store_true')
parser.add_argument('--collector', required=True, type=Path)
parser.add_argument('--focus-guard', required=True, type=Path)
parser.add_argument('--collector-sha256', required=True)
parser.add_argument('--focus-guard-sha256', required=True)
parser.add_argument('--local-sources', required=True, type=Path)
parser.add_argument('--helper-build', required=True, type=Path)
parser.add_argument('--helper-build-sha256', required=True)
parser.add_argument('--locks', required=True, type=Path)
parser.add_argument('--locks-sha256', required=True)
parser.add_argument('--build-manifest-sha256', required=True)
parser.add_argument('--color14-gate-sha256', required=True)
parser.add_argument('output', type=Path)
args = parser.parse_args()
if not args.run:
    print('Draft plan only: actual build, successful14 color gate, private candidate locks and local helper identities required before --run.')
    raise SystemExit(0)

assert platform.mac_ver()[0].split('.')[0] == '13' and platform.machine() == 'arm64'
assert os.environ.get('CI') != 'true' and os.environ.get('GITHUB_ACTIONS') != 'true', 'Local13 cannot impersonate CI'
assert 'BERN_FRAME_ROW_LEDGER_OUTPUT_DIR' not in os.environ, 'A ledger environment is forbidden for this candidate'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for value in [args.collector_sha256,args.focus_guard_sha256,args.locks_sha256,args.helper_build_sha256]:
    assert re.fullmatch(r'[0-9a-f]{64}',value), 'Root-reviewed actual digest required'
locks_path=args.locks.resolve(strict=True); assert sha(locks_path)==args.locks_sha256
locks=json.loads(locks_path.read_text())
assert set(locks)=={'schema','kind','source_sha','baseline_sha','candidate','build_manifest','build_manifest_sha256','color14_gate','color14_gate_sha256','control14_report','candidate14_report','ci_run_id','harness_sha','commands','scope'}
assert locks['schema']==LOCKS_SCHEMA and locks['source_sha']==SOURCE and locks['baseline_sha']==BASELINE and locks['kind']==KIND
build_path=Path(locks['build_manifest']).resolve(strict=True);gate_path=Path(locks['color14_gate']).resolve(strict=True)
assert locks['build_manifest_sha256']==args.build_manifest_sha256 and locks['color14_gate_sha256']==args.color14_gate_sha256
manifest,gate,gui_entry,cli_entry,contract_inputs=read_contract(build_path,args.build_manifest_sha256,gate_path,args.color14_gate_sha256,Path(locks['control14_report']),Path(locks['candidate14_report']))
assert locks['ci_run_id']==manifest['run_id'] and locks['harness_sha']==manifest['harness_sha']
group=locks['candidate']
assert set(group)=={'app','cli','bundle_id','private_gui_sha256','original_gui_sha256','cli_sha256','receipt'}
assert group['original_gui_sha256']==gui_entry['sha256'] and group['cli_sha256']==cli_entry['sha256']
collector,guard=(p.resolve(strict=True) for p in [args.collector,args.focus_guard])
app=Path(group['app']).resolve(strict=True);cli=Path(group['cli']).resolve(strict=True)
assert collector.is_file() and guard.is_file() and cli.is_file() and app.is_dir()
assert sha(collector)==args.collector_sha256 and sha(guard)==args.focus_guard_sha256
sources=args.local_sources.resolve(strict=True);source_manifest=sources/'SHA256SUMS'
assert sha(source_manifest)==LOCAL_SOURCE_MANIFEST_SHA
source_inputs=[source_manifest]
for line in source_manifest.read_text().splitlines():
    digest,name=line.split('  ',1)
    assert re.fullmatch(r'[0-9a-f]{64}',digest)
    source=(sources/name).resolve(strict=True)
    assert source.parent==sources and source.is_file() and sha(source)==digest
    source_inputs.append(source)
assert sha(sources/'FrameColorCapture.swift')==COLLECTOR_SOURCE_SHA and sha(sources/'FocusGuard.swift')==GUARD_SOURCE_SHA
proof=json.loads((sources/'source-proof.json').read_text())
assert proof['only_final_run_cleanup_defer_changed'] is True and proof['exact_inverse_restores_full_fa850_baseline'] is True and proof['guard_byte_identical_to_ab78'] is True
helper_build_path=args.helper_build.resolve(strict=True)
assert sha(helper_build_path)==args.helper_build_sha256
helper_build=json.loads(helper_build_path.read_text())
assert helper_build['kind']=='local13_candidate_color_helpers_build_only' and helper_build['target']=='arm64-apple-macosx13.0'
assert helper_build['actual_min_os']=='13.0' and helper_build['actual_embedded_sdk']=='13.0'
expected_sources={str(sources/'FrameColorCapture.swift'):COLLECTOR_SOURCE_SHA,str(sources/'FocusGuard.swift'):GUARD_SOURCE_SHA}
for key in ['source_before','source_after']:
    assert {row['path']:row['sha256'] for row in helper_build[key]}==expected_sources
for name,binary,digest in [('FrameColorCapture',collector,args.collector_sha256),('FocusGuard',guard,args.focus_guard_sha256)]:
    row=helper_build['binaries'][name]
    assert Path(row['path']).resolve(strict=True)==binary and row['sha256']==digest and row['bytes']==binary.stat().st_size
assert all(row['exit_code']==0 for row in helper_build['commands'])
assert sha(app/'Contents/MacOS/Gallery')==group['private_gui_sha256'] and sha(cli)==group['cli_sha256']
assert re.fullmatch(r'dev\.bern\.frame13\.candidate\.[0-9a-f]{32}',group['bundle_id'])
assert plistlib.loads((app/'Contents/Info.plist').read_bytes())['CFBundleIdentifier']==group['bundle_id']
isolation_path=Path(group['receipt']).resolve(strict=True)
isolation=json.loads(isolation_path.read_text())
for key in ['kind','source_sha','baseline_sha','build_manifest','build_manifest_sha256','color14_gate','color14_gate_sha256','control14_report','candidate14_report','ci_run_id','harness_sha']:
    assert isolation[key]==locks[key]
assert isolation['private_app']==str(app) and isolation['private_bundle_id']==group['bundle_id']
assert isolation['original_gui_sha256']==gui_entry['sha256'] and isolation['private_gui_sha256']==group['private_gui_sha256']
assert isolation['cli']==str(cli) and isolation['cli_sha256']==group['cli_sha256']
assert isolation['sections_and_signature_storage_sizes_normalized_equal'] is True and isolation['originals_unchanged'] is True
def bundle_members(folder):
    assert not any(p.is_symlink() for p in folder.rglob('*'))
    return {str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
original_app=Path(isolation['original_app']).resolve(strict=True)
assert bundle_members(app)==isolation['private_members']
assert bundle_members(original_app)==isolation['original_members']
assert sha(original_app/'Contents/MacOS/Gallery')==gui_entry['sha256']

assert isolation['original_members']=={name:row['sha256'] for name,row in manifest['app_members'].items()}
output=args.output.resolve();sidecar=Path(str(output)+'.watchdog')
assert not output.exists() and not sidecar.exists(), 'Fresh output/watchdog required'
inputs=[locks_path,collector,guard,app,cli,isolation_path,original_app,helper_build_path,sources,
        Path(__file__).resolve(),*source_inputs,*contract_inputs]
assert all(dst!=p and dst not in p.parents and p not in dst.parents for dst in [output,sidecar] for p in inputs), 'Output/watchdog and inputs must not overlap in either direction'
pinned_inputs={str(p):sha(p) for p in [locks_path,isolation_path,collector,guard,helper_build_path,Path(__file__).resolve(),*source_inputs,*contract_inputs]}
sidecar.mkdir(parents=True)
for name,path in [('collector',collector),('focus-guard',guard),('private-app',app),('cli',cli)]:
    result=subprocess.run(['codesign','--verify','--strict',str(path)],capture_output=True,timeout=15)
    (sidecar/(name+'-signature.txt')).write_bytes(result.stdout+result.stderr)
    assert result.returncode==0, name+' signature verification failed'
report={'success':False,'kind':KIND,'outer_wait_cap_seconds':95,'collector_deadline_seconds':75,'source_sha':SOURCE,
        'scope':'One generic SplitButton color candidate13 closed Frame capture after actual14 no-effect; no color acceptance or layout-ledger gate claim',
        'app':str(app),'cli':str(cli),'output':str(output),'collector_sha256':sha(collector),'focus_guard_sha256':sha(guard),
        'collector_source_sha256':COLLECTOR_SOURCE_SHA,'focus_guard_source_sha256':GUARD_SOURCE_SHA,
        'helper_scope':'local-only kernel-cleanup adapter; acquisition differs from14 only in final cleanup',
        'ci_run_id':manifest['run_id'],'harness_sha':manifest['harness_sha'],
        'locks_sha256':sha(locks_path),'build_manifest_sha256':args.build_manifest_sha256,'color14_gate_sha256':args.color14_gate_sha256,
        'helper_build_sha256':args.helper_build_sha256,'local_source_manifest_sha256':LOCAL_SOURCE_MANIFEST_SHA,
        'ipc_cleanup_verified':False,'exact_child_cleanup_verified':False,'bound_input_sha256':pinned_inputs}
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
    for key in ['CI','GITHUB_ACTIONS','GITHUB_SHA','GITHUB_RUN_ID','BERN_IPC_DIR','BERN_SNAPSHOT_DIR','BERN_MOTION','BERN_FRAME_ROW_LEDGER_OUTPUT_DIR']:
        env.pop(key,None)
    env['BERN_FRAME_LOCAL_EVENTS']='own-pid-active13'
    env['BERN_SOURCE_SHA']=locks['source_sha']
    assert 'BERN_FRAME_ROW_LEDGER_OUTPUT_DIR' not in env
    env['BERN_PICTURE_FOCUS_GUARD'] = str(guard)
    env['BERN_PICTURE_WATCHDOG_FRONT'] = str(sidecar / 'original-front.json')
    report['phase'] = 'collector'; save()
    with (sidecar / 'collector.log').open('wb') as log:
        process = subprocess.Popen([str(collector), str(app), str(cli), str(output),'13','candidate',locks['source_sha']],
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
            assert data['label']=='candidate' and data['ci_run_id']=='local' and data['collector_executable_sha256']==args.collector_sha256
            assert all(sha(Path(name))==digest for name,digest in pinned_inputs.items())
            report['collector_success']=True
    except BaseException as error:
        cleanup_ok=False
        report['post_cleanup_error']=type(error).__name__+': '+str(error)
    report['cleanup_success'] = cleanup_ok
    report['success'] = cleanup_ok and report.get('collector_exit_code') == 0 and not report.get('timeout') and 'error' not in report
    save()
raise SystemExit(0 if report['success'] else 1)
