"""CI-only runtime ABBA wrapper. The pinned external observer is never edited."""
import json
import math
import os
import ctypes
from pathlib import Path, PurePosixPath
import plistlib
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import traceback
import uuid

# Reused unchanged from the verified clean-e48 work/macho.py helper.
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

OBSERVER = '6c4d5c93c9331ba4dd6427aa18799b6a1e720b6e2e006e036fb908ced4f9e635'
CLI = '31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5'
SOURCES = {
    'A': dict(source='f9e08b1d55bed4b9d880b19934abe48281057bb3', run=39991406873,
              build_harness='c1900f58bca6fd283bce2d4cf9769f1e6029ebb0',
              archive='18a69e1536065f6722413aaebf26830aee11fa280990e0f7aa8206cf7ce38934',
              gui='887173af876a3f802c68dfff7fef087f318cc6909a61ea4beff69dad536dfd7e'),
    'B': dict(source='e48fff46b3a92a28465ad74295bd273a9d69af7d', run=40070407306,
              build_harness='25e18cbc7cd760c1c399042f1d7364c3d755a9dc',
              archive='e7ee2c11f7795bf9391b275ec9f6be329feceebf890193ee53434ec0607c3067',
              gui='d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c'),
}
NAMES = {'Gingham', 'Tartan', 'Madras', 'Glen', 'Houndstooth', 'Windowpane'}


def main():
    assert len(sys.argv) == 6, 'BUILD_A BUILD_B OBSERVER EVIDENCE SCRATCH'
    assert os.environ.get('GITHUB_ACTIONS') == 'true', 'Disposable GitHub runner only'
    workspace = Path(os.environ['GITHUB_WORKSPACE']).resolve()
    inputs = dict(zip('AB', [Path(p).resolve() for p in sys.argv[1:3]]))
    observer, evidence, scratch = [Path(p).resolve() for p in sys.argv[3:]]
    assert inputs == {'A': workspace/'build-a', 'B': workspace/'build-b'}
    assert evidence == workspace/'evidence' and not evidence.exists()
    assert scratch.parent == Path(os.environ['RUNNER_TEMP']).resolve()
    assert scratch.name == 'bern-film-abba-' + os.environ['GITHUB_RUN_ID'] + '-' + os.environ['GITHUB_RUN_ATTEMPT']
    assert not scratch.exists() and sha(observer.read_bytes()) == OBSERVER
    deadline = float(os.environ['ABBA_DEADLINE_EPOCH'])
    evidence.mkdir(); scratch.mkdir()
    report = dict(schema=1, success=False, order=['A1', 'B1', 'B2', 'A2'], legs=[],
                  source_locks=SOURCES, observer_sha256=OBSERVER,
                  collection_harness_sha=os.environ['GITHUB_SHA'],
                  deadline_epoch=deadline, job_timeout_seconds=480, observer_cap_seconds=120,
                  scope='Same VM; four unique bundle identities; each runs the unchanged all/active14 observer. No native logger. No automatic pixel-equivalence claim.')
    exacts, owned_executables, identities, original_members = {}, set(), [], {}
    libproc = ctypes.CDLL('/usr/lib/libproc.dylib')
    libproc.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    libproc.proc_pidpath.restype = ctypes.c_int

    def save():
        temp = evidence/'summary.json.tmp'
        temp.write_text(json.dumps(report, indent=2) + '\n'); temp.replace(evidence/'summary.json')

    def command(args, log, limit=30, check=True):
        left = deadline-time.time()-15  # Reserve cleanup time; upload retains another job-budget minute.
        assert left > 0, 'ABBA work deadline exhausted'
        try:
            p = subprocess.run([str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               timeout=min(limit, left))
        except subprocess.TimeoutExpired as error:
            log.write_bytes(error.stdout or b'')
            raise
        log.write_bytes(p.stdout)
        if check: assert p.returncode == 0, f'Command failed; see {log.relative_to(evidence)}'
        return p

    def processes():
        rows = subprocess.check_output(['ps', '-ww', '-axo', 'pid=,comm='], timeout=5).decode().splitlines()
        own = []
        for row in rows:
            parts = row.strip().split(None, 1)
            if len(parts) != 2: continue
            pid = int(parts[0]); buffer = ctypes.create_string_buffer(4096)
            length = libproc.proc_pidpath(pid, buffer, len(buffer))
            if length > 0:
                path = buffer.value.decode()
                if path in owned_executables: own.append((pid, path))
            elif parts[1] in owned_executables:
                try: os.kill(pid, 0)
                except ProcessLookupError: continue
                raise RuntimeError('Cannot verify still-live own executable path')
        return own  # Exact proc_pidpath, never a truncated ps/name match.

    def members(app):
        return {str(p.relative_to(app)): sha(p.read_bytes()) for p in sorted(app.rglob('*')) if p.is_file()}

    def machos(app):
        result = {}
        for p in sorted(app.rglob('*')):
            if p.is_file():
                with p.open('rb') as f: magic = f.read(4)
                if magic == b'\xcf\xfa\xed\xfe': result[str(p.relative_to(app))] = macho(p)
                else: assert magic not in [b'\xfe\xed\xfa\xcf', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca',
                                          b'\xca\xfe\xba\xbf', b'\xbf\xba\xfe\xca', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xce'], 'Unexpected Mach-O format'
        assert 'Contents/MacOS/Gallery' in result
        return result

    def extract(build, destination, lock):
        archive = build/'gallery.tar.gz'
        assert sha(archive.read_bytes()) == lock['archive']
        assert (build/'gallery.tar.gz.sha256').read_text().split() == [lock['archive'], 'gallery.tar.gz']
        env = dict(line.split('=', 1) for line in (build/'environment.txt').read_text().splitlines() if '=' in line)
        assert env['source_repository'] == 'Torrekie/Bern'
        assert env['source_sha'] == lock['source'] and env['harness_sha'] == lock['build_harness']
        metadata = json.loads((build/'build.json').read_text())
        assert all(metadata[k] == v for k, v in dict(app_bundle='Gallery.app', protocol='gallery',
            architecture='arm64', platform='macos', minimum_macos='13.0', ui='swiftui-modern').items())
        destination.mkdir()
        with tarfile.open(archive) as package:
            names, total = set(), 0
            for m in package.getmembers():
                name = PurePosixPath(m.name)
                assert not name.is_absolute() and '..' not in name.parts and '\\' not in m.name
                assert m.isdir() or m.isfile()  # Reject links, devices and other special members.
                assert name.parts and name.parts[0] in ('Gallery.app', 'bin')
                key = str(name)
                assert key not in names; names.add(key)
                total += m.size
                assert len(names) <= 10000 and total <= 512*1024*1024
            package.extractall(destination)
        assert (destination/'bin/gallery').is_file()

    def validate(data, root, lock):
        assert data['success'] is True and data['source_sha'] == lock['source']
        assert data['harness_sha'] == os.environ['GITHUB_SHA'] and data['variant'] == 'port'
        assert data['expected_os_major'] == 14 and data['requested_scenario'] == 'all'
        assert data['observation_mode'] == 'active' and data['followup_sequence'] == 'none'
        assert data['accessibility_trusted'] is True and data['screen_recording_preflight'] is True
        assert data['appearance_profile'] == 'normal' and all(v is False for v in data['system_preferences'].values())
        assert [c['scenario'] for c in data['cases']] == ['immediate', 'wait', 'direct']
        assert len({c['pid'] for c in data['cases']}) == len({c['session'] for c in data['cases']}) == 3
        result = {}
        for c in data['cases']:
            film = c['film']; bounds = film['bounds_points']
            assert film['equal_comparisons'] >= 4 and (root/film['png']).is_file()
            assert bounds['Width'] == 920 and bounds['Height'] == 668
            assert c['first_second_ax'] and not c['settled_ax']['truncated']
            images = [e for e in c['settled_ax']['elements'] if e['role'] == 'AXImage' and e['text'] in NAMES]
            assert len(images) == 6 and {e['text'] for e in images} == NAMES
            for e in images:
                assert all(math.isfinite(e['frame'][k]) for k in ['x', 'y', 'width', 'height'])
                assert e['frame']['width'] > 0 and e['frame']['height'] > 0
            startup = [s for s in data['startup_readiness'] if s['pid'] == c['pid']]
            assert len(startup) == 1 and startup[0]['samples']
            initial = startup[0]['samples'][-1]['own_native_window']['kCGWindowBounds']
            frames = {e['text']: dict(x=e['frame']['x']-bounds['X'], y=e['frame']['y']-bounds['Y'],
                       width=e['frame']['width'], height=e['frame']['height']) for e in images}
            result[c['scenario']] = dict(startup_ready_bounds=initial, frames_window_points=frames,
                startup_width_matches_expected=initial['Width'] == (900 if c['scenario'] == 'immediate' else 920))
        return result

    save()
    try:
        for name, args in [('os', ['sw_vers']), ('architecture', ['uname', '-m']),
                           ('xcode', ['xcodebuild', '-version']), ('swift', ['xcrun', 'swiftc', '-version']),
                           ('sdk', ['xcrun', '--show-sdk-version'])]:
            command(args, evidence/(name+'.txt'))
        assert subprocess.check_output(['sw_vers', '-productVersion']).decode().split('.')[0] == '14'
        assert subprocess.check_output(['uname', '-m']).decode().strip() == 'arm64'
        shutil.copy2(observer, evidence/'gallery-film-probe.swift')
        shutil.copy2(Path(__file__), evidence/'gallery-film-abba.py')
        for side, build in inputs.items():
            report['phase'] = 'verify-source-'+side; save()
            lock = SOURCES[side]; out = evidence/('source-'+side); out.mkdir()
            for name in ['environment.txt', 'build.json', 'binary.txt', 'gallery.tar.gz.sha256']:
                shutil.copy2(build/name, out/name)
            exact = scratch/('exact-'+side); extract(build, exact, lock)
            gui, cli = exact/'Gallery.app/Contents/MacOS/Gallery', exact/'bin/gallery'
            assert sha(gui.read_bytes()) == lock['gui'] and sha(cli.read_bytes()) == CLI
            assert plistlib.loads((exact/'Gallery.app/Contents/Info.plist').read_bytes())['LSMinimumSystemVersion'] == '13.0'
            for kind, binary in [('gui', gui), ('cli', cli)]:
                assert command(['lipo', '-archs', binary], out/(kind+'-arch.txt')).stdout.decode().strip() == 'arm64'
                text = command(['xcrun', 'vtool', '-show-build', binary], out/(kind+'-loadcommands.txt')).stdout.decode()
                assert 'minos 13.0' in text and 'sdk 26.2' in text
            command(['codesign', '--verify', '--deep', '--strict', exact/'Gallery.app'], out/'signature-gui.txt')
            command(['codesign', '--verify', '--strict', cli], out/'signature-cli.txt')
            original = machos(exact/'Gallery.app')
            original_members[side] = members(exact/'Gallery.app')
            (out/'original-regular-members.json').write_text(json.dumps(original_members[side], indent=2)+'\n')
            (out/'original-machos.json').write_text(json.dumps(original, indent=2)+'\n')
            exacts[side] = (exact, original)
            owned_executables.add(str(cli))
        executable = scratch/'FilmProbe'
        report['phase'] = 'compile-observer-once'; save()
        command(['xcrun', 'swiftc', '-swift-version', '5', '-target', 'arm64-apple-macos14.0',
                 '-module-cache-path', scratch/'modules', observer, '-o', executable], evidence/'observer-build.log', 60)
        owned_executables.add(str(executable))
        report['observer_binary_sha256'] = sha(executable.read_bytes()); save()
        for leg in report['order']:
            report['phase'] = 'prepare-'+leg; save()
            assert deadline-time.time() > 135, 'Insufficient remaining budget for another full 120s observer'
            side = leg[0]; lock = SOURCES[side]; exact, original = exacts[side]
            out = evidence/leg; out.mkdir()
            identity = 'dev.bern.film.abba.'+os.environ['GITHUB_RUN_ID']+'.'+leg.lower()+'.'+uuid.uuid4().hex
            identities.append(identity)
            app = scratch/leg/'Gallery.app'; app.parent.mkdir()
            command(['ditto', exact/'Gallery.app', app], out/'copy.log')
            copied_members = members(app)
            assert copied_members == original_members[side]
            assert sha((app/'Contents/MacOS/Gallery').read_bytes()) == lock['gui']
            info = app/'Contents/Info.plist'; raw = info.read_bytes(); plist = plistlib.loads(raw)
            old_identifier = plist['CFBundleIdentifier']; plist['CFBundleIdentifier'] = identity
            info.write_bytes(plistlib.dumps(plist, fmt=plistlib.FMT_BINARY if raw.startswith(b'bplist') else plistlib.FMT_XML, sort_keys=False))
            before = machos(app)
            command(['codesign', '--force', '--deep', '--sign', '-', '--identifier', identity, app], out/'resign.log')
            command(['codesign', '--verify', '--deep', '--strict', app], out/'signature.txt')
            after = machos(app)
            signed_members = members(app)
            assert signed_members.keys() == copied_members.keys()
            changed_members = [name for name in copied_members if copied_members[name] != signed_members[name]]
            assert set(changed_members) <= {'Contents/Info.plist', 'Contents/MacOS/Gallery', 'Contents/_CodeSignature/CodeResources'}
            signed_plist = plistlib.loads(info.read_bytes())
            assert signed_plist == plist and signed_plist['CFBundleIdentifier'] == identity
            assert before.keys() == after.keys() == original.keys()
            for key in original:
                assert before[key]['sha256'] == original[key]['sha256']
                assert before[key]['sections'] == after[key]['sections']
                assert before[key]['signature_storage_sizes_normalized_sha256'] == after[key]['signature_storage_sizes_normalized_sha256']
            history = [Path.home()/'Library/Preferences'/(identity+'.plist'),
                       Path.home()/'Library/Saved Application State'/(identity+'.savedState')]
            assert not any(p.exists() for p in history), 'New identity unexpectedly has existing history'
            absent = command(['defaults', 'read', identity], out/'prelaunch-defaults.txt', check=False)
            assert absent.returncode != 0, 'New identity has an existing effective preferences domain'
            (out/'isolation.json').write_text(json.dumps(dict(identifier=identity, original_identifier=old_identifier,
                original=original, before=before, after=after, section_records_equal=True,
                copied_regular_members=copied_members, signed_regular_members=signed_members,
                changed_regular_members=changed_members, normalized_signature_storage_payload_equal=True,
                original_gui_sha256=lock['gui'], cli_sha256=CLI), indent=2)+'\n')
            gui = app/'Contents/MacOS/Gallery'; owned_executables.add(str(gui))
            env = os.environ.copy()
            for key in ['BERN_SCROLL_TRACE_DIR', 'BERN_SNAPSHOT_DIR', 'BERN_IPC_DIR']:
                env.pop(key, None)
            env.update(BERN_SOURCE_SHA=lock['source'], FILM_VARIANT='port', BERN_FILM_EXPECTED_OS='14',
                       BERN_FILM_SCENARIO='all', BERN_FILM_OBSERVATION='active', BERN_FILM_FOLLOWUP='none')
            runtime = out/'runtime'; assert not runtime.exists()
            item = dict(leg=leg, source_slot=side, source_sha=lock['source'], build_run=lock['run'],
                        build_harness_sha=lock['build_harness'], bundle_id=identity, started_epoch=time.time())
            report['legs'].append(item); save()
            report['phase'] = 'observe-'+leg; save()
            with (out/'observer.log').open('wb') as log:
                p = subprocess.Popen([str(executable), str(app), str(exact/'bin/gallery'), str(runtime)],
                                     stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
                try: item['observer_exit'] = p.wait(timeout=120)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL); p.wait(timeout=5)
                    item['timeout'] = True; raise RuntimeError('Observer exceeded 120s; no retry')
            item['ended_epoch'] = time.time(); save()
            assert item['observer_exit'] == 0, 'Observer failed; preserve partial and stop ABBA'
            teardown = []
            until = min(deadline-15, time.time()+2)
            while processes() and time.time() < until:
                teardown.append(dict(epoch=time.time(), processes=processes())); time.sleep(0.03)
            item['teardown_samples'] = teardown
            assert not processes(), 'Own app did not exit before next leg'
            item['geometry'] = validate(json.loads((runtime/'result.json').read_text()), runtime, lock)
            assert sha((exact/'Gallery.app/Contents/MacOS/Gallery').read_bytes()) == lock['gui']
            assert sha((exact/'bin/gallery').read_bytes()) == CLI
            assert members(exact/'Gallery.app') == original_members[side]
            item['completed'] = True; save()
        report['startup_width_conditions_met'] = all(c['startup_width_matches_expected']
            for leg in report['legs'] for c in leg['geometry'].values())
        report['repeat_geometry_max_abs_delta_pt'] = {}
        for pair in [('A1', 'A2'), ('B1', 'B2')]:
            a, b = [next(x for x in report['legs'] if x['leg'] == name) for name in pair]
            report['repeat_geometry_max_abs_delta_pt']['-'.join(pair)] = {
                scenario: max(abs(a['geometry'][scenario]['frames_window_points'][name][axis]
                                  - b['geometry'][scenario]['frames_window_points'][name][axis])
                              for name in NAMES for axis in ['x', 'y', 'width', 'height'])
                for scenario in ['immediate', 'wait', 'direct']}
        report['success'] = report['startup_width_conditions_met']
        if not report['success']:
            report['failure'] = 'Observed startup widths do not reproduce 900/920/920; raw acquisition retained, comparison ineligible'
        # Success means the acquisition contract passed, not repeatability or pixel equivalence.
    except BaseException as error:
        report['failure'] = type(error).__name__+': '+str(error)
        (evidence/'failure-traceback.txt').write_text(traceback.format_exc())
    finally:
        receipt = dict(owned_processes_before_cleanup=[], removed=[], errors=[])
        try:
            receipt['original_full_member_rechecks'] = {}
            for side, (exact, _) in exacts.items():
                same = members(exact/'Gallery.app') == original_members[side]
                receipt['original_full_member_rechecks'][side] = same
                if not same: receipt['errors'].append('Original exact app members changed: '+side)
            receipt['owned_processes_before_cleanup'] = processes()
            for pid, path in receipt['owned_processes_before_cleanup']:
                if (pid, path) in processes():
                    try: os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError: pass
            until = min(deadline, time.time()+2)
            while processes() and time.time() < until: time.sleep(0.03)
            for identity in identities:
                for p in [Path.home()/'Library/Preferences'/(identity+'.plist'),
                          Path.home()/'Library/Saved Application State'/(identity+'.savedState')]:
                    if p.is_file() and not p.is_symlink(): shutil.copy2(p, evidence/(identity+'.plist'))
                # Only this job's new identities; never touch original app domains.
                try:
                    subprocess.run(['defaults', 'delete', identity], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                except subprocess.TimeoutExpired:
                    receipt['errors'].append('New-identity defaults cleanup timed out: '+identity)
                state = Path.home()/'Library/Saved Application State'/(identity+'.savedState')
                try:
                    if state.is_symlink(): state.unlink()
                    elif state.exists(): shutil.rmtree(state)
                except OSError as error:
                    receipt['errors'].append('New-identity savedState cleanup failed: '+str(error))
            for p in [scratch, *inputs.values()]:
                size = sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
                shutil.rmtree(p); receipt['removed'].append(dict(path=str(p), logical_bytes=size))
            receipt['owned_processes_after_cleanup'] = processes()
            assert not receipt['owned_processes_after_cleanup']
        except BaseException as error:
            receipt['errors'].append(str(error)); report['success'] = False
        if receipt['errors']: report['success'] = False
        report['cleanup'] = receipt; report['finished_epoch'] = time.time(); save()
        (evidence/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.relative_to(evidence)}\n'
            for p in sorted(evidence.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
