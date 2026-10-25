#!/usr/bin/env python3
"""Disposable exact-e48 observer build preparation/collection. No App execution."""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

SOURCE = 'e48fff46b3a92a28465ad74295bd273a9d69af7d'
PACKAGE = Path(__file__).resolve().parent
GUARD_SHA = '5b4a254565f437f819a308f8cf3c5b1990b937f76b9918ff5b935e91e1a2b017'
SOURCE_MANIFEST = 'f939a41d78a5d78cbcdc51d2341952c200aa5187bb6befa2331521eb03565741'
GALLERY_GENERATED = 'f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653'
DERIVED_ORIGINAL_RUNTIME = '626c4b7785cf46f9e6d86389d5c64b8221d5f5ead8f7518a67e407b38883ba95'
DERIVED_PATCHED_RUNTIME = 'e38647f3b918e4d0c4c503eb8876889578a35b57efdb8feeaadafaac5a51f663'
STYLE = 'crates/bern-backend-swiftui/templates/BernStyle.swift'
RUNTIME = 'crates/bern-backend-swiftui/templates/BernRuntime.swift'
PINS = {STYLE: 'fb2adb075d7abcb70bc1b1b7d434d7686195e5d91a1d18f8156fce285fcb771c',
        RUNTIME: '1da1f603ef7397fcfb8ef2a454343e79257596805697175e7948c30f4e8a2b77'}
GENERATOR = 'crates/bern-backend-swiftui/src/lib.rs'
IR = 'crates/bern-ir/src/spec.rs'
SVG = 'crates/bern-target-api/src/svg.rs'
MAX_TEXT = 1024 * 1024
MAX_LOG = 128 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def regular(path, cap=None):
    require(path.is_file() and not path.is_symlink(), 'regular file required: ' + str(path))
    require(cap is None or path.stat().st_size <= cap, 'file over cap: ' + str(path))
    return path.read_bytes()


def meta(path):
    raw = regular(path)
    return {'bytes': len(raw), 'sha256': sha(raw)}


def write_json(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    require(len(raw) <= 512 * 1024, 'JSON over cap')
    path.write_bytes(raw)


def module(path, expected, name):
    require(sha(regular(path, MAX_TEXT)) == expected, 'tool hash mismatch: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)  # main guards remain false; no generate-only prepare/collect called.
    return result


def tools():
    guard_path = PACKAGE.parent / 'frame-source-export.py'
    guard = module(guard_path, GUARD_SHA, 'film_sourceguard')
    manifest = regular(PACKAGE / 'source-SHA256SUMS', 4096)
    require(sha(manifest) == SOURCE_MANIFEST, 'frozen observer manifest differs')
    files = {}
    for line in manifest.decode().splitlines():
        h, name = line.split('  ', 1)
        require(Path(name).name == name and name not in files, 'unsafe/duplicate source member')
        raw = regular(PACKAGE / name, MAX_TEXT)
        require(sha(raw) == h, 'frozen observer source changed: ' + name)
        files[name] = {'bytes': len(raw), 'sha256': h}
    require(set(files) == {'FilmLastObservation.swift.inc', 'patch.py', 'source-proof.json', 'README.md'}, 'source set differs')
    patch = module(PACKAGE / 'patch.py', files['patch.py']['sha256'], 'film_template_patch')
    return guard, patch, files


def runtime_source(template, spec):
    # Exact fixed-table grammar only; no general Rust evaluator.
    marker = b'/*bern:file-extensions*/'
    require(template.count(marker) == 1, 'runtime extension marker must occur once')
    match = re.search(r'pub const FILE_KIND_EXTENSIONS:.*?= &(\[.*?\n\]);', spec.decode(), re.S)
    require(match is not None, 'fixed file-extension table missing')
    literal = match.group(1)
    require(re.fullmatch(r'[\s\[\](),&"a-z0-9]+', literal) is not None, 'unsupported extension table grammar')
    rows = ast.literal_eval(literal.replace('&', ''))
    require([r[0] for r in rows] == ['video', 'audio', 'picture'] and [len(r[1]) for r in rows] == [19, 13, 12], 'unexpected fixed extension table')
    table = ', '.join('"' + key + '": [' + ', '.join('"' + ext + '"' for ext in extensions) + ']'
                      for key, extensions in rows).encode()
    require(len(table) == 352, 'fixed table byte count differs')
    return template.replace(marker, table)


def check_svg_scope(repo):
    manifest = regular(repo / 'examples/gallery/Bern.toml', MAX_TEXT).decode()
    ui = regular(repo / 'examples/gallery/gallery-ui/src/lib.rs', MAX_TEXT)
    require('sources = ["gallery-ui/src/lib.rs"]' in manifest, 'unsupported Gallery UI source graph')
    require(re.search(rb'\bSvg\s*\(', ui) is None, 'Gallery Svg input is unsupported by this bounded driver')
    # All three sources below are already checked byte-exact against fixed e48 by sourceguard.
    generator = regular(repo / GENERATOR, MAX_TEXT)
    require(b'let mut source = runtime_source(source);' in generator and
            b'if bern_target_api::svg::used(app)' in generator, 'runtime expansion/conditional SVG path differs')
    require(b'e.kind == "Svg"' in regular(repo / SVG, MAX_TEXT), 'SVG admission source differs')


def source_state(repo, before, guard):
    guard.require_head(repo)
    require(guard.git(repo, 'diff', 'HEAD', '--name-only').decode().splitlines() == sorted(PINS), 'only two template tracked changes allowed')
    require(guard.git(repo, 'diff', '--cached', '--name-only').strip() == b'', 'index change refused')
    require(guard.input_names(repo) == [r['path'] for r in before['inputs']], 'fixed631 input names changed')
    for row in before['inputs']:
        current = meta(repo / row['path'])
        expected = before['templates'][row['path']] if row['path'] in PINS else row
        require(current['bytes'] == expected['bytes'] and current['sha256'] == expected['sha256'], 'tracked input changed: ' + row['path'])
    require(meta(repo / guard.CLI)['sha256'] == guard.CLI_ORIGINAL_SHA256, 'original CLI changed')


def prepare(repo, out):
    guard, patch, files = tools()
    require(not out.exists() or out.is_dir() and not out.is_symlink(), 'evidence directory invalid')
    out.mkdir(parents=True, exist_ok=True)
    require({p.name for p in out.iterdir()} <= {'environment.txt', 'harness-inputs.sha256'}, 'fresh evidence required')
    for p in out.iterdir():
        regular(p, MAX_LOG)
    guard.require_head(repo)
    require(not guard.git(repo, 'status', '--porcelain', '--untracked-files=no').strip(), 'clean tracked checkout required')
    rows = guard.original_input_rows(repo)
    require(len(rows) == 631, 'fixed631 inputs required')
    check_svg_scope(repo)
    require('BERN_DIAGNOSTIC_GENERATE_ONLY' not in os.environ, 'generate-only environment forbidden')
    require(sha(regular(repo / guard.CLI)) == guard.CLI_ORIGINAL_SHA256, 'original CLI pin differs')
    target = repo / 'target/bern/macos_modern'
    require((repo / 'target').resolve() == repo / 'target' and target.resolve() == target and not target.is_symlink(), 'target reset path unsafe')
    before = {'source_sha': SOURCE, 'source_tree': guard.git(repo, 'rev-parse', 'HEAD^{tree}').decode().strip(),
              'inputs': rows, 'input_count': 631, 'sourceguard_sha256': GUARD_SHA,
              'source_manifest_sha256': SOURCE_MANIFEST, 'package_sources': files,
              'driver': meta(Path(__file__).resolve()),
              'cached_generated_before_reset': {n: guard.file_meta(target / n) for n in
                  ['Sources/BernRuntime.swift', 'Sources/BernStyle.swift', 'Sources/BernGenerated.swift', 'Gallery.app/Contents/MacOS/Gallery']},
              'reset_scope': 'Only target/bern/macos_modern; Rust caches retained. CLI/generator unchanged.'}
    write_json(out / 'before.json', before)
    if target.exists():
        require(target.is_dir(), 'target output is not a directory')
        shutil.rmtree(target)
    result = subprocess.run([sys.executable, str(PACKAGE / 'patch.py'), str(repo / Path(STYLE).parent), str(out / 'patches')], capture_output=True)
    (out / 'patcher.log').write_bytes(result.stdout + result.stderr)
    require(result.returncode == 0, 'frozen template patcher failed')
    proof = json.loads(regular(out / 'patches/patch-proof.json', MAX_TEXT))
    deltas = [out / ('patches/' + Path(n).name + '.patch') for n in sorted(PINS)]
    command = ['git', '-C', str(repo), 'apply', '--directory=' + str(Path(STYLE).parent)]
    subprocess.check_call(command + ['--check', *map(str, deltas)])
    subprocess.check_call(command + list(map(str, deltas)))
    before['templates'] = {}
    for name, pin in PINS.items():
        actual = meta(repo / name)
        require(actual['sha256'] == pin == proof['files'][Path(name).name]['candidate_sha256'], 'patched template mismatch')
        before['templates'][name] = actual
    before['patch_proof_sha256'] = sha(regular(out / 'patches/patch-proof.json'))
    write_json(out / 'before.json', before)
    source_state(repo, before, guard)


def command(out, name, argv):
    result = subprocess.run(argv, capture_output=True, timeout=60)
    data = result.stdout + result.stderr
    require(len(data) <= MAX_LOG, 'metadata command log over cap')
    (out / (name + '.txt')).write_bytes(data)
    require(result.returncode == 0, 'metadata command failed: ' + name)
    return data.decode()


def bounded_log(out):
    p = out / 'build.full.log'
    require(p.is_file() and not p.is_symlink(), 'missing build.full.log')
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            h.update(chunk)
    size = p.stat().st_size
    with p.open('rb') as stream:
        if size <= MAX_LOG:
            kept = stream.read()
        else:
            omission = b'\n[bounded build log: middle omitted]\n'
            half = (MAX_LOG - len(omission)) // 2
            kept = stream.read(half) + omission
            stream.seek(-(MAX_LOG - len(kept)), 2)
            kept += stream.read()
    (out / 'build.log').write_bytes(kept)
    return {'full_bytes': size, 'full_sha256': h.hexdigest(), 'retained_bytes': len(kept), 'truncated': size > MAX_LOG}


def collect(repo, out):
    require(not (out / 'observer-build.json').exists(), 'fresh collect required')
    result = {'schema': 'bern_film_last_observer_build_v1', 'source_sha': SOURCE, 'success': False,
              'scope': 'Build-only diagnostic observer App. No native execution or pixel/diagnostic acceptance.',
              'run_id': os.environ.get('GITHUB_RUN_ID'), 'harness_sha': os.environ.get('GITHUB_SHA')}
    archive = out / 'gallery-film-last-observer.tar.gz'
    partial = out / (archive.name + '.partial')
    archive_sha = out / (archive.name + '.sha256')
    own_archive_started = False
    try:
        result['log'] = bounded_log(out)
        result['cargo_exit_code'] = int(regular(out / 'build.exit-code.txt', 32).decode().strip())
        base = repo / 'target/bern/macos_modern'
        require(base.resolve() == base and base.is_dir(), 'generated output path unsafe')
        generated = {}
        for name in ['BernRuntime.swift', 'BernStyle.swift', 'BernGenerated.swift']:
            path = base / 'Sources' / name
            if path.is_file():
                raw = regular(path, MAX_TEXT)
                generated[name] = {'bytes': len(raw), 'sha256': sha(raw)}
                if name in ['BernRuntime.swift', 'BernGenerated.swift']:
                    (out / (name.removesuffix('.swift') + '.generated.swift')).write_bytes(raw)
        result['generated_actual'] = generated
        if (base / 'build.json').is_file():
            (out / 'product-build.json').write_bytes(regular(base / 'build.json', MAX_TEXT))
        guard, patch, files = tools()
        before = json.loads(regular(out / 'before.json', 256 * 1024))
        require(before['source_sha'] == SOURCE and before['driver'] == meta(Path(__file__).resolve()) and before['package_sources'] == files, 'preparation provenance differs')
        source_state(repo, before, guard)
        require(guard.git(repo, 'rev-parse', 'HEAD^{tree}').decode().strip() == before['source_tree'], 'source tree changed')
        require(result['cargo_exit_code'] == 0, 'original normal cargo build failed')
        require(generated.get('BernGenerated.swift') == {'bytes': 81110, 'sha256': GALLERY_GENERATED}, 'actual Gallery generated application differs from frozen actual e48 export')
        check_svg_scope(repo)
        original_runtime = guard.git(repo, 'show', SOURCE + ':' + RUNTIME)
        original_style = guard.git(repo, 'show', SOURCE + ':' + STYLE)
        spec = regular(repo / IR, MAX_TEXT)
        expected_runtime = runtime_source(regular(repo / RUNTIME), spec)
        original_generated_runtime = runtime_source(original_runtime, spec)
        require(sha(expected_runtime) == DERIVED_PATCHED_RUNTIME and sha(original_generated_runtime) == DERIVED_ORIGINAL_RUNTIME, 'independent fixed-table derivation differs')
        actual_runtime = regular(base / 'Sources/BernRuntime.swift', MAX_TEXT)
        require(actual_runtime == expected_runtime, 'actual generated Runtime differs from patched template plus fixed extensions; SVG/other append unsupported')
        core = regular(PACKAGE / 'FilmLastObservation.swift.inc', 16384)
        require(actual_runtime.endswith(b'\n' + core), 'actual generated Runtime core suffix differs')
        inverse = actual_runtime[:-len(core)-1].decode()
        for old, new in reversed(patch.RUNTIME_EDITS):
            require(inverse.count(new) == 1, 'generated Runtime inspect inverse ambiguous')
            inverse = inverse.replace(new, old, 1)
        require(inverse.encode() == original_generated_runtime, 'generated Runtime inverse does not restore derived original generation')
        actual_style = regular(base / 'Sources/BernStyle.swift', MAX_TEXT)
        require(actual_style == regular(repo / STYLE) and sha(actual_style) == PINS[STYLE], 'generated Style differs')
        inverse_style = actual_style.decode()
        for old, new in reversed(patch.STYLE_EDITS):
            require(inverse_style.count(new) == 1, 'Style inverse ambiguous')
            inverse_style = inverse_style.replace(new, old, 1)
        require(inverse_style.encode() == original_style, 'Style inverse differs from fixed e48')
        result['runtime_binding'] = {'actual_matches_derived_patched_bytes': True, 'no_svg': True,
            'derived_original': {'bytes': len(original_generated_runtime), 'sha256': sha(original_generated_runtime)},
            'derived_patched': {'bytes': len(expected_runtime), 'sha256': sha(expected_runtime)},
            'core_and_inspect_hook_inverse_to_derived_original': True, 'historical_generated_runtime_sha_assumed': False}
        build = json.loads(regular(base / 'build.json', MAX_TEXT))
        require(build['target'] == 'swiftui-modern-macos' and build['ui'] == 'swiftui-modern' and build['minimum_macos'] == '13.0' and build['architecture'] == 'arm64' and build['profile'] == 'release' and build['app_bundle'] == 'Gallery.app', 'wrong product plan')
        require(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'arm64 macOS build host required')
        swift = command(out, 'swift-version', ['xcrun', 'swiftc', '--version'])
        sdk = command(out, 'selected-sdk', ['xcrun', '--show-sdk-version']).strip()
        rust = command(out, 'rust-version', ['rustc', '+1.99.0', '--version'])
        require(re.search(r'Apple Swift version 6\.', swift) is not None and sdk == '26.2' and rust.startswith('rustc 1.99.0 '), 'unexpected compiler/SDK')
        app = base / 'Gallery.app';exe = app / 'Contents/MacOS/Gallery'
        actual_metadata = command(out, 'app-build-metadata', ['xcrun', 'vtool', '-show-build', str(exe)])
        require(re.findall(r'^\s*minos\s+(\S+)', actual_metadata, re.M) == ['13.0'], 'actual App minimum OS differs')
        embedded_sdk = re.findall(r'^\s*sdk\s+(\S+)', actual_metadata, re.M)
        require(embedded_sdk == ['26.2'], 'actual App SDK differs from26.2')
        require(command(out, 'app-architecture', ['lipo', '-archs', str(exe)]).strip() == 'arm64', 'actual App architecture differs')
        command(out, 'app-strict-signature', ['codesign', '--verify', '--deep', '--strict', str(app)])
        info = plistlib.loads(regular(app / 'Contents/Info.plist', MAX_TEXT))
        require(info['CFBundleExecutable'] == 'Gallery' and info['CFBundleIdentifier'] == 'dev.bern.gallery' and info['LSMinimumSystemVersion'] == '13.0', 'actual App Info differs')
        members = {}
        for path in sorted(app.rglob('*')):
            require(not path.is_symlink(), 'App symlink unsupported')
            if path.is_file():
                members[str(path.relative_to(app))] = meta(path)
        result.update({'success': True, 'sourceguard_sha256': GUARD_SHA, 'source_manifest_sha256': SOURCE_MANIFEST,
                       'driver': before['driver'], 'before_sha256': sha(regular(out / 'before.json')),
                       'templates': before['templates'], 'tracked_changes': sorted(PINS), 'other_fixed_inputs_unchanged': 629,
                       'original_cli_source_sha256': guard.CLI_ORIGINAL_SHA256, 'normal_cli_not_hooked': True,
                       'build': build, 'gui': meta(exe), 'app_members': members,
                       'toolchain': {'swift': swift.strip(), 'selected_sdk': sdk, 'actual_app_embedded_sdk': embedded_sdk[0], 'rust': rust.strip()},
                       'rebuilt_cli_shipped_or_claimed_original': False, 'native_execution_performed': False})
        write_json(out / 'observer-build.json', result)
        require(all(not p.exists() and not p.is_symlink() for p in [archive, partial, archive_sha]), 'fresh archive/checksum required')
        own_archive_started = True
        with tarfile.open(partial, 'w:gz') as tar:
            tar.add(app, arcname='Gallery.app')
            tar.add(out / 'observer-build.json', arcname='observer-build.json')
        archive_digest = sha(regular(partial))
        partial.replace(archive)
        archive_sha.write_text(archive_digest + '  ' + archive.name + '\n')
    except Exception as error:
        result['success'] = False
        result['error'] = type(error).__name__ + ': ' + str(error)
        if own_archive_started:
            # Only paths admitted fresh above belong to this packaging attempt.
            for p in [partial, archive, archive_sha]:
                if p.exists() and p.is_file() and not p.is_symlink():
                    p.unlink()
            result['failed_own_archive_removed'] = all(not p.exists() and not p.is_symlink() for p in [partial, archive, archive_sha])
        write_json(out / 'observer-build.json', result)
    return 0 if result['success'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'collect'])
    parser.add_argument('source', type=Path)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    repo = args.source.resolve(strict=True);out = args.evidence.resolve()
    require(all(out != p and out not in p.parents and p not in out.parents for p in [repo, PACKAGE]), 'source/package/evidence must not overlap')
    if args.mode == 'prepare':
        try:
            prepare(repo, out)
        except Exception as error:
            if out.is_dir() and not out.is_symlink():
                write_json(out / 'prepare-failure.json', {'success': False, 'error': type(error).__name__ + ': ' + str(error)})
            raise
    else:
        sys.exit(collect(repo, out))
