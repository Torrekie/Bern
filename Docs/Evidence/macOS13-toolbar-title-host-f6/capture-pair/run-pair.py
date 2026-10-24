"""Task-local Showcase A/B wrapper. No actions without explicit --run."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import subprocess
import time
import traceback
import uuid

# Reused unchanged: reviewed ABBA Mach-O helper.
import hashlib
import struct

def sha(data):
    return hashlib.sha256(data).hexdigest()

def macho(path):
    raw = path.read_bytes()
    header = struct.unpack_from('<8I', raw)
    assert header[0] == 0xfeedfacf and header[1] == 0x100000c
    sections, segments, signature, offset = [], [], None, 32
    for _ in range(header[4]):
        command, size = struct.unpack_from('<II', raw, offset)
        assert size >= 8 and offset+size <= len(raw)
        if command == 0x1d:
            data_offset, data_size = struct.unpack_from('<II', raw, offset+8)
            signature = dict(command_offset=offset, command_size=size,
                             data_offset=data_offset, data_size=data_size)
        if command == 0x19:
            name = raw[offset+8:offset+24].rstrip(b'\0').decode()
            values = struct.unpack_from('<4Q', raw, offset+24)
            segments.append(dict(name=name, command_offset=offset,
                                 vmaddr=values[0], vmsize=values[1], fileoff=values[2], filesize=values[3]))
            count = struct.unpack_from('<I', raw, offset+64)[0]
            for index in range(count):
                values = struct.unpack_from('<16s16sQQIIIIIIII', raw, offset+72+80*index)
                section, segment, address, length, start = values[:5]
                zero = values[8] & 255 in (1, 0xc, 0x12)
                data = b'' if zero else raw[start:start+length]
                assert zero or len(data) == length
                sections.append(dict(segment=segment.rstrip(b'\0').decode(),
                    section=section.rstrip(b'\0').decode(), address=address, size=length,
                    file_offset=start, zero_fill=zero, sha256=None if zero else sha(data)))
        offset += size
    assert offset == 32+header[5] and signature
    lo = signature['command_offset']; hi = lo+signature['command_size']
    start = signature['data_offset']; end = start+signature['data_size']
    assert hi <= start and end <= len(raw)
    strict = sha(raw[:lo]+raw[hi:start]+raw[end:])
    normalized = bytearray(raw)
    for segment in segments:
        if segment['name'] == '__LINKEDIT':
            n = segment['command_offset']
            normalized[n+32:n+40] = bytes(8)
            normalized[n+48:n+56] = bytes(8)
    return dict(path=str(path), bytes=len(raw), sha256=sha(raw), signature=signature,
        segments=segments, sections=sections,
        signature_command_blob_excluded_sha256=strict,
        signature_storage_sizes_normalized_sha256=sha(normalized[:lo]+normalized[hi:start]+normalized[end:]))

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
A_SOURCE = '9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0'
B_SOURCE = 'f6be9bd95253970ad82429f8b6df107d4447e647'
A_GUI = 'cc267abcafeec30112c2796b3c0ea7699a6836a0f09a1caa73f66ea48bfa1c1b'
A_CLI = '963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170'
ALLOWED = {'Contents/Info.plist', 'Contents/MacOS/Showcase', 'Contents/_CodeSignature/CodeResources'}


def members(app):
    assert not any(p.is_symlink() for p in app.rglob('*')), 'Unexpected app symlink'
    return {str(p.relative_to(app)): sha(p.read_bytes()) for p in sorted(app.rglob('*')) if p.is_file()}


def app_machos(app):
    result = {}
    for p in sorted(app.rglob('*')):
        if p.is_file():
            with p.open('rb') as stream: magic = stream.read(4)
            if magic == b'\xcf\xfa\xed\xfe': result[str(p.relative_to(app))] = macho(p)
            else: assert magic not in [b'\xfe\xed\xfa\xcf', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca',
                                      b'\xca\xfe\xba\xbf', b'\xbf\xba\xfe\xca', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xce']
    assert 'Contents/MacOS/Showcase' in result
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--locks', type=Path, default=ROOT/'run-locks.json')
    args = parser.parse_args()
    if not args.run:
        print(json.dumps(dict(plan_only=True, locks=str(args.locks), order=['A', 'B'],
            note='No app reads, subprocesses, copies, signing, UI or cleanup without --run.',
            observer_cap_seconds=120, wrapper_work_cap_seconds=330), indent=2))
        return 0
    locks = json.loads(args.locks.read_text())
    for side, source in [('A', A_SOURCE), ('B', B_SOURCE)]:
        assert locks[side]['source_sha'] == source
        for key in ['gui_sha256', 'cli_sha256']:
            value = locks[side][key]
            assert isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)
    assert locks['A']['gui_sha256'] == A_GUI and locks['A']['cli_sha256'] == A_CLI
    assert Path(locks['A']['app']).resolve() == WORKSPACE/'outputs/macOS13/Showcase.app'
    assert Path(locks['A']['cli']).resolve() == WORKSPACE/'outputs/macOS13/bin/showcase'
    assert Path(locks['B']['app']).resolve() == ROOT/'exact/Showcase.app'
    assert Path(locks['B']['cli']).resolve() == ROOT/'exact/bin/showcase'
    observer = Path(locks['observer']['binary']).resolve()
    observer_work = ROOT/'observer-work'
    assert observer == observer_work/'ToolbarProbe' and locks['observer']['cleanup_owned_work'] is True
    observer_source = Path(locks['observer']['source']).resolve()
    assert sha(observer.read_bytes()) == locks['observer']['binary_sha256']
    assert sha(observer_source.read_bytes()) == locks['observer']['source_sha256']
    out, scratch = ROOT/'capture-pair', ROOT/'runtime-work'
    assert not out.exists() and not scratch.exists()
    out.mkdir(); scratch.mkdir()
    deadline = time.monotonic()+330
    report = dict(schema=1, success=False, order=['A', 'B'], locks=locks, groups=[],
        observer_cap_seconds=120, wrapper_work_cap_seconds=330,
        scope='Two isolated Showcase copies, one root-built observer, active13 four-page sequence; no preferences/TCC changes beyond new own identity domains.')
    originals, identities = {}, []
    owned = {str(observer)}
    lib = ctypes.CDLL('/usr/lib/libproc.dylib')
    lib.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    lib.proc_pidpath.restype = ctypes.c_int

    def save():
        temp = out/'summary.json.tmp'; temp.write_text(json.dumps(report, indent=2)+'\n'); temp.replace(out/'summary.json')

    def command(argv, log, cap=30, check=True):
        remaining = deadline-time.monotonic()-15; assert remaining > 0, 'Wrapper work deadline exhausted'
        try:
            p = subprocess.run([str(v) for v in argv], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               timeout=min(cap, remaining))
        except subprocess.TimeoutExpired as error:
            log.write_bytes(error.stdout or b''); raise
        log.write_bytes(p.stdout)
        if check: assert p.returncode == 0, 'Command failed: '+str(log)
        return p

    def processes():
        rows = subprocess.check_output(['ps', '-ww', '-axo', 'pid=,comm='], timeout=5).decode().splitlines()
        matches = []
        for row in rows:
            parts = row.strip().split(None, 1)
            if len(parts) != 2: continue
            pid = int(parts[0]); buffer = ctypes.create_string_buffer(4096)
            length = lib.proc_pidpath(pid, buffer, len(buffer))
            if length > 0:
                path = buffer.value.decode()
                if path in owned: matches.append((pid, path))
            elif parts[1] in owned:
                try: os.kill(pid, 0)
                except ProcessLookupError: continue
                raise RuntimeError('Cannot verify still-live own executable')
        return matches

    def read_collector(group, directory):
        path = directory/'runtime/result.json'
        if path.exists():
            data = json.loads(path.read_text())
            group['front_before'] = data.get('original_front')
            group['front_after'] = data.get('front_restore', {}).get('after')
            group['normal_profile_start'] = data.get('normal_profile_start')
            group['normal_profile_end'] = data.get('normal_profile_end')
            group['collector_success'] = data.get('success')
            return data
        group['collector_report_missing'] = True
        return None

    save()
    try:
        assert not processes(), 'Own observer path already running'
        assert command(['sw_vers', '-productVersion'], out/'os.txt').stdout.decode().split('.')[0] == '13'
        assert command(['uname', '-m'], out/'architecture.txt').stdout.decode().strip() == 'arm64'
        shutil.copy2(Path(__file__), out/'run-pair.py')
        shutil.copy2(args.locks, out/'run-locks.json')
        shutil.copy2(observer_source, out/'observer.swift')
        for side in ['A', 'B']:
            report['phase'] = 'verify-'+side; save()
            lock = locks[side]; app = Path(lock['app']).resolve(); cli = Path(lock['cli']).resolve()
            assert sha((app/'Contents/MacOS/Showcase').read_bytes()) == lock['gui_sha256']
            assert sha(cli.read_bytes()) == lock['cli_sha256']
            command(['codesign', '--verify', '--deep', '--strict', app], out/(side+'-original-signature.txt'))
            command(['codesign', '--verify', '--strict', cli], out/(side+'-original-cli-signature.txt'))
            original = dict(app_members=members(app), machos=app_machos(app), cli=macho(cli))
            originals[side] = original
            (out/(side+'-original-fingerprint.json')).write_text(json.dumps(original, indent=2)+'\n')
        for side in ['A', 'B']:
            assert deadline-time.monotonic() > 135, 'Insufficient remaining time for a complete 120s observer'
            report['phase'] = 'prepare-'+side; save()
            lock = locks[side]; directory = out/side; directory.mkdir()
            app = scratch/side/'Showcase.app'; app.parent.mkdir()
            command(['ditto', lock['app'], app], directory/'copy.log')
            copied = members(app); assert copied == originals[side]['app_members']
            identifier = 'dev.bern.toolbar13.'+side.lower()+'.'+uuid.uuid4().hex
            identities.append(identifier)
            state = Path.home()/'Library/Saved Application State'/(identifier+'.savedState')
            prefs = Path.home()/'Library/Preferences'/(identifier+'.plist')
            assert not any(p.exists() or p.is_symlink() for p in [prefs, state])
            assert command(['defaults', 'read', identifier], directory/'prelaunch-defaults.txt', check=False).returncode != 0
            info = app/'Contents/Info.plist'; raw = info.read_bytes(); plist = plistlib.loads(raw)
            original_id = plist['CFBundleIdentifier']; plist['CFBundleIdentifier'] = identifier
            info.write_bytes(plistlib.dumps(plist, fmt=plistlib.FMT_BINARY if raw.startswith(b'bplist') else plistlib.FMT_XML, sort_keys=False))
            command(['codesign', '--force', '--deep', '--sign', '-', '--identifier', identifier, app], directory/'resign.log')
            command(['codesign', '--verify', '--deep', '--strict', app], directory/'signature.txt')
            signed, after = members(app), app_machos(app)
            assert copied.keys() == signed.keys() and originals[side]['machos'].keys() == after.keys()
            changed = [k for k in copied if copied[k] != signed[k]]; assert set(changed) <= ALLOWED
            assert plistlib.loads(info.read_bytes()) == plist
            for name, before in originals[side]['machos'].items():
                assert before['sections'] == after[name]['sections']
                assert before['signature_storage_sizes_normalized_sha256'] == after[name]['signature_storage_sizes_normalized_sha256']
            cli = app.parent/'showcase'; shutil.copy2(lock['cli'], cli)
            assert sha(cli.read_bytes()) == lock['cli_sha256']
            command(['codesign', '--verify', '--strict', cli], directory/'copied-cli-signature.txt')
            owned.update([str(app/'Contents/MacOS/Showcase'), str(cli)])
            assert not processes()
            (directory/'isolation.json').write_text(json.dumps(dict(identifier=identifier, original_identifier=original_id,
                copied_members=copied, signed_members=signed, changed_members=changed, original_machos=originals[side]['machos'],
                signed_machos=after, cli_sha256=lock['cli_sha256']), indent=2)+'\n')
            group = dict(variant=side, source_sha=lock['source_sha'], bundle_id=identifier, start_epoch=time.time())
            report['groups'].append(group); report['phase'] = 'observe-'+side; save()
            env = os.environ.copy()
            for key in ['BERN_SCROLL_TRACE_DIR', 'BERN_SNAPSHOT_DIR', 'BERN_IPC_DIR']: env.pop(key, None)
            env.update(BERN_SOURCE_SHA=lock['source_sha'], BERN_TOOLBAR_VARIANT=side)
            with (directory/'observer.log').open('wb') as log:
                p = subprocess.Popen([str(observer), str(app), str(cli), str(directory/'runtime')],
                    stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
                try: group['exit_status'] = p.wait(timeout=120)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL); p.wait(timeout=5); group['timeout'] = True
                    raise RuntimeError('Observer exceeded external 120s cap; no retry')
            group['end_epoch'] = time.time()
            data = read_collector(group, directory); save()
            assert group['exit_status'] == 0 and data and data['success'] is True
            assert data['source_sha'] == lock['source_sha'] and data['variant'] == side
            assert data['expected_os_major'] == 13 and data['accessibility_trusted'] is True and data['screen_recording_preflight'] is True
            assert [s['option'] for s in data['stages']] == ['Buttons', 'Text', 'Controls', 'Buttons']
            assert all(v is False for v in data['normal_profile_start'].values())
            assert all(v is False for v in data['normal_profile_end'].values())
            for stage in data['stages']:
                assert stage['ax']['tree_complete'] is True and stage['capture']['equal_comparisons'] >= 4
                assert (directory/'runtime'/stage['capture']['png']).is_file()
            until = time.monotonic()+2
            while processes() and time.monotonic() < until: time.sleep(0.03)
            assert not processes(), 'Own process remains; do not start second group'
            group['complete'] = True; save()
        report['success'] = True
    except BaseException as error:
        report['failure'] = type(error).__name__+': '+str(error)
        (out/'failure-traceback.txt').write_text(traceback.format_exc())
    finally:
        receipt = dict(errors=[], removed=[], original_member_rechecks={}, processes_before=[])
        for side, original in originals.items():
            try:
                same = members(Path(locks[side]['app'])) == original['app_members'] and sha(Path(locks[side]['cli']).read_bytes()) == locks[side]['cli_sha256']
                receipt['original_member_rechecks'][side] = same
                if not same: receipt['errors'].append('Original app/CLI changed: '+side)
            except BaseException as error: receipt['errors'].append(str(error))
        try:
            receipt['processes_before'] = processes()
            for pid, path in receipt['processes_before']:
                if (pid, path) in processes():
                    try: os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError: pass
            until = time.monotonic()+2
            while processes() and time.monotonic() < until: time.sleep(0.03)
            receipt['processes_after'] = processes()
            if receipt['processes_after']: receipt['errors'].append('Own process remains after cleanup')
        except BaseException as error: receipt['errors'].append(str(error))
        for identifier in identities:
            prefs = Path.home()/'Library/Preferences'/(identifier+'.plist')
            state = Path.home()/'Library/Saved Application State'/(identifier+'.savedState')
            try:
                if prefs.is_file() and not prefs.is_symlink():
                    saved = out/(identifier+'.plist'); shutil.copy2(prefs, saved)
                    assert sha(saved.read_bytes()) == sha(prefs.read_bytes())
                if prefs.is_file() or prefs.is_symlink(): prefs.unlink()
                receipt.setdefault('own_preferences_disk_checks', []).append(dict(identifier=identifier,
                    absent_at_check=not prefs.exists() and not prefs.is_symlink(),
                    scope='Own new UUID disk file only; cfprefsd memory domain and later re-creation not asserted.'))
            except BaseException as error: receipt['errors'].append('Own preferences file cleanup: '+str(error))
            try:
                if state.is_symlink(): state.unlink()
                elif state.exists(): shutil.rmtree(state)
            except BaseException as error: receipt['errors'].append('Own savedState cleanup: '+str(error))
        for path in [scratch, observer_work]:
            try:
                size = sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
                shutil.rmtree(path); receipt['removed'].append(dict(path=str(path), logical_bytes=size))
            except BaseException as error: receipt['errors'].append('Own scratch cleanup: '+str(error))
        for group in report['groups']:
            try: read_collector(group, out/group['variant'])
            except BaseException as error: receipt['errors'].append('Collector metadata read: '+str(error))
        if receipt['errors']: report['success'] = False
        report['cleanup'] = receipt; report['ended_epoch'] = time.time(); save()
        (out/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.relative_to(out)}\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
