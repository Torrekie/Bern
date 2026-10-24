"""Verify existing downloaded build and prepare an isolated signed copy; never execute it."""
import hashlib
import json
import plistlib
import shutil
import struct
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCE = '9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0'
RUN = 40066468884
IDENTIFIER = 'dev.bern.probe.showcase.standard9dd.r40066468884'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (BASE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run(args, log):
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    (BASE / log).write_text(result.stdout + result.stderr)
    assert result.returncode == 0, (args, result.returncode, result.stderr)
    return result.stdout


def version(encoded):
    return f'{encoded >> 16}.{(encoded >> 8) & 255}.{encoded & 255}'


def macho(path):
    data = path.read_bytes()
    magic, cpu, subtype, filetype, count, command_bytes, flags, reserved = struct.unpack_from('<IiiIIIII', data)
    assert magic == 0xfeedfacf and cpu == 0x100000c and filetype == 2
    offset = 32
    sections = []
    build = None
    for index in range(count):
        command, size = struct.unpack_from('<II', data, offset)
        assert size >= 8 and offset + size <= 32 + command_bytes <= len(data)
        if command == 0x32:
            platform, minimum, sdk, tools = struct.unpack_from('<IIII', data, offset + 8)
            build = {'platform': platform, 'minimum': version(minimum), 'sdk': version(sdk)}
        elif command == 0x19:
            segment = struct.unpack_from('<II16sQQQQiiII', data, offset)
            assert 72 + segment[-2] * 80 <= size
            for n in range(segment[-2]):
                section = struct.unpack_from('<16s16sQQIIIIIIII', data, offset + 72 + n * 80)
                name, segment_name, address, length, start, alignment, reloc, reloc_count, section_flags, r1, r2, r3 = section
                zero = (section_flags & 255) in (1, 12, 18)
                assert zero or start + length <= len(data)
                sections.append({'segment': segment_name.rstrip(b'\0').decode(),
                                 'section': name.rstrip(b'\0').decode(), 'offset': start,
                                 'size': length, 'flags': section_flags, 'zero_fill': zero,
                                 'sha256': None if zero else hashlib.sha256(data[start:start + length]).hexdigest()})
        offset += size
    assert offset == 32 + command_bytes
    assert build == {'platform': 1, 'minimum': '13.0.0', 'sdk': '26.2.0'}, build
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
            'architecture': 'arm64', 'build_version': build, 'sections': sections}


def all_files(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


build = json.loads((BASE / 'build/build.json').read_text())
environment = (BASE / 'build/environment.txt').read_text()
assert f'source_sha={SOURCE}\n' in environment
assert build['architecture'] == 'arm64' and build['minimum_macos'] == '13.0'
assert build['ui'] == 'swiftui-modern' and build['target'] == 'swiftui-modern-macos'
exact = BASE / 'exact'
original_app = exact / 'Showcase.app'
original_gui = original_app / 'Contents/MacOS/Showcase'
original_cli = exact / 'bin/showcase'
archive = json.loads((BASE / 'archive-verification.json').read_text())
assert all_files(exact) == archive['members']
original = {'gui': macho(original_gui), 'cli': macho(original_cli)}
run(['/usr/bin/codesign', '--verify', '--deep', '--strict', '--verbose=2', str(original_app)], 'original-gui-signature-verify.log')
run(['/usr/bin/codesign', '--verify', '--strict', '--verbose=2', str(original_cli)], 'original-cli-signature-verify.log')
run(['/usr/bin/codesign', '-d', '--verbose=4', str(original_app)], 'original-gui-signature-details.log')
run(['/usr/bin/codesign', '-d', '--verbose=4', str(original_cli)], 'original-cli-signature-details.log')
entitlements = run(['/usr/bin/codesign', '-d', '--entitlements', '-', str(original_app)], 'original-gui-entitlements.log')
assert not entitlements.strip(), 'Unexpected original entitlements; preserve before signing'
info = plistlib.loads((original_app / 'Contents/Info.plist').read_bytes())
assert info['CFBundleIdentifier'] == 'dev.bern.showcase'
assert info['LSMinimumSystemVersion'] == '13.0'
app_dir = BASE / 'app'
assert not app_dir.exists(), 'Do not overwrite an existing test copy'
app_dir.mkdir()
shutil.copytree(original_app, app_dir / 'Showcase.app', copy_function=shutil.copy2)
shutil.copytree(exact / 'bin', app_dir / 'bin', copy_function=shutil.copy2)
copy_app = app_dir / 'Showcase.app'
copy_gui = copy_app / 'Contents/MacOS/Showcase'
copy_cli = app_dir / 'bin/showcase'
before = {'gui': macho(copy_gui), 'cli': macho(copy_cli)}
assert before == original
copy_info_path = copy_app / 'Contents/Info.plist'
copy_info = plistlib.loads(copy_info_path.read_bytes())
copy_info['CFBundleIdentifier'] = IDENTIFIER
copy_info_path.write_bytes(plistlib.dumps(copy_info, sort_keys=False))
run(['/usr/bin/codesign', '--force', '--sign', '-', '--identifier', IDENTIFIER,
     '--timestamp=none', str(copy_app)], 'copy-sign.log')
run(['/usr/bin/codesign', '--verify', '--deep', '--strict', '--verbose=2', str(copy_app)], 'copy-gui-signature-verify.log')
run(['/usr/bin/codesign', '--verify', '--strict', '--verbose=2', str(copy_cli)], 'copy-cli-signature-verify.log')
run(['/usr/bin/codesign', '-d', '--verbose=4', str(copy_app)], 'copy-gui-signature-details.log')
after = {'gui': macho(copy_gui), 'cli': macho(copy_cli)}
for role in original:
    assert before[role]['sections'] == after[role]['sections'], role
assert original['cli']['sha256'] == after['cli']['sha256']
assert all_files(exact) == archive['members'], 'Exact original was modified'
expected_changes = {'Showcase.app/Contents/Info.plist',
                    'Showcase.app/Contents/MacOS/Showcase',
                    'Showcase.app/Contents/_CodeSignature/CodeResources'}
copy_files = all_files(app_dir)
assert copy_files.keys() == archive['members'].keys()
changed = {p for p in copy_files if copy_files[p] != archive['members'][p]}
assert changed <= expected_changes, changed
run_meta = json.loads(run(['gh', 'api', f'repos/Torrekie/Bern/actions/runs/{RUN}'], 'run-api.json'))
assert run_meta['id'] == RUN and run_meta['conclusion'] == 'success'
artifacts = json.loads(run(['gh', 'api', f'repos/Torrekie/Bern/actions/runs/{RUN}/artifacts'], 'artifacts-api.json'))
artifact = [a for a in artifacts['artifacts'] if a['name'] == 'macos13-showcase']
assert len(artifact) == 1 and not artifact[0]['expired']
plan = [{'name': 'showcase', 'folder': BASE.name, 'run': RUN, 'source_sha': SOURCE}]
save('execution-plan.json', plan)
save('binary-verification.json', {'original': original, 'copy_before_sign': before,
                                 'copy_after_sign': after, 'all_sections_unchanged': True})
save('copy-files.json', copy_files)
save('preparation.json', {'scope': 'Artifact inspection/signing only; no app, CLI, focus helper or UI execution.',
                         'run': RUN, 'source_sha': SOURCE, 'harness_sha': run_meta['head_sha'],
                         'artifact': {k: artifact[0].get(k) for k in ('id', 'name', 'digest', 'size_in_bytes')},
                         'archive_sha256': archive['archive_sha256'],
                         'exact': str(exact), 'app': str(copy_app), 'cli': str(copy_cli),
                         'original_bundle_id': info['CFBundleIdentifier'], 'copy_bundle_id': IDENTIFIER,
                         'focus_helper': {'path': str(BASE.parent / 'focus-helper'),
                                          'exists': (BASE.parent / 'focus-helper').is_file(), 'executed': False},
                         'changed_copy_files': sorted(changed), 'all_sections_unchanged': True,
                         'exact_member_manifest_still_valid': True, 'strict_signatures_valid': True,
                         'build_manifest_sha256': sha(BASE / 'build/build.json'),
                         'environment_sha256': sha(BASE / 'build/environment.txt'),
                         'future_smoke_plan': str(BASE / 'execution-plan.json'), 'executed_app_or_cli': False})
print(json.dumps({'success': True, 'original_gui_sha256': original['gui']['sha256'],
                  'copy_gui_sha256': after['gui']['sha256'], 'cli_sha256': after['cli']['sha256'],
                  'section_count_gui': len(after['gui']['sections']),
                  'section_count_cli': len(after['cli']['sections']),
                  'plan': str(BASE / 'execution-plan.json')}))
