"""Prepare one private 9dd copy and compile its Guard. Never launches either."""
import sys
sys.dont_write_bytecode = True
import ast
import difflib
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import uuid
from common import APP, DELIVERY, GUARD, HERE, PREP, REPO, ROOT, RUN, command, original_hashes, sha, write

def main():
    assert not PREP.exists() and not APP.parent.exists() and not GUARD.parent.exists() and not RUN.exists()
    PREP.mkdir()
    APP.parent.mkdir()
    GUARD.parent.mkdir()
    cache = HERE / 'module-cache'
    success = False
    try:
        original_hashes()
        prior = REPO / 'Docs/Evidence/macOS13-native-input-9dd-20261025/isolation.json'
        old = json.loads(prior.read_text())
        assert old['source_sha'] == '9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0'
        helper = REPO / 'Docs/Evidence/macOS13-film-first-last-e48-20261025/preparation/driver/prepare-film13.py'
        assert sha(helper) == old['macho_helper_sha256']
        spec = importlib.util.spec_from_file_location('macho_only', helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = ROOT / 'outputs/macOS13/Showcase.app'
        cli = ROOT / 'outputs/macOS13/bin/showcase'
        build_path = ROOT / 'outputs/macOS13/showcase-build.json'
        build = json.loads(build_path.read_text())
        assert build['source_sha'] == old['source_sha'] and build['executable_sha256'] == DELIVERY['outputs/macOS13/Showcase.app/Contents/MacOS/Showcase']
        before = module.members(original)
        assert before == old['original_members']
        before_macho = module.macho(original / 'Contents/MacOS/Showcase')
        command(['/usr/bin/codesign', '--verify', '--deep', '--strict', original], PREP, 'original-signature')
        command(['/usr/bin/codesign', '--verify', '--strict', cli], PREP, 'cli-signature')
        command(['/usr/bin/ditto', original, APP], PREP, 'copy')
        assert module.members(APP) == before
        identifier = 'dev.bern.native13.inputfg.' + uuid.uuid4().hex
        info = APP / 'Contents/Info.plist'
        values = plistlib.loads(info.read_bytes())
        assert values['CFBundleExecutable'] == 'Showcase' and values['LSMinimumSystemVersion'] == '13.0'
        values['CFBundleIdentifier'] = identifier
        info.write_bytes(plistlib.dumps(values, sort_keys=False))
        command(['/usr/bin/codesign', '--force', '--deep', '--sign', '-', '--identifier', identifier, APP], PREP, 'private-sign')
        command(['/usr/bin/codesign', '--verify', '--deep', '--strict', APP], PREP, 'private-signature')
        command(['/usr/bin/codesign', '-d', '--verbose=4', APP], PREP, 'private-signature-details')
        after = module.members(APP)
        assert before.keys() == after.keys()
        changed = [p for p in before if before[p] != after[p]]
        assert set(changed) <= {'Contents/Info.plist', 'Contents/MacOS/Showcase', 'Contents/_CodeSignature/CodeResources'}
        after_macho = module.macho(APP / 'Contents/MacOS/Showcase')
        assert before_macho['sections'] == after_macho['sections']
        assert before_macho['signature_storage_sizes_normalized_sha256'] == after_macho['signature_storage_sizes_normalized_sha256']
        assert module.members(original) == before
        write(PREP / 'macho-equivalence.json', {'original': before_macho, 'private': after_macho,
              'sections_identical': True, 'signature_storage_sizes_normalized_bytes_identical': True})
        source = ROOT / 'work/native-logic-gallery13-tools/FocusGuard.swift'
        source_bytes = source.read_bytes()
        assert sha(source) == 'b87279696d54a514fc8e406acad75f5e649e853816504cfb7577fad5bcf297f7'
        guard_text = source_bytes.decode().replace('dev.bern.native13.gallery.', 'dev.bern.native13.inputfg.').replace('Gallery', 'Showcase').replace('dev.bern.gallery', 'dev.bern.showcase')
        inverse = guard_text.replace('dev.bern.native13.inputfg.', 'dev.bern.native13.gallery.').replace('Showcase', 'Gallery').replace('dev.bern.showcase', 'dev.bern.gallery')
        assert inverse.encode() == source_bytes
        GUARD.with_suffix('.swift').write_text(guard_text)
        (PREP / 'guard-adaptation.patch').write_text(''.join(difflib.unified_diff(source_bytes.decode().splitlines(True), guard_text.splitlines(True), fromfile='GalleryFocusGuard.swift', tofile='ShowcaseFocusGuard.swift')))
        developer = '/Applications/Xcode.app/Contents/Developer'
        sdk = developer + '/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk'
        compiler = developer + '/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc'
        assert os.path.isdir(sdk) and os.path.isfile(compiler)
        env = dict(os.environ, DEVELOPER_DIR=developer)
        command([compiler, '--version'], PREP, 'compiler-version', env=env, timeout=45)
        command([compiler, '-swift-version', '5', '-target', 'arm64-apple-macosx13.0', '-sdk', sdk,
                 '-module-cache-path', cache, GUARD.with_suffix('.swift'), '-o', GUARD], PREP, 'compile-guard', env=env, timeout=90)
        command(['/usr/bin/codesign', '--force', '--sign', '-', GUARD], PREP, 'sign-guard')
        command(['/usr/bin/codesign', '--verify', '--strict', GUARD], PREP, 'guard-signature')
        command(['/usr/bin/codesign', '-d', '--verbose=4', GUARD], PREP, 'guard-signature-details')
        command(['/usr/bin/xcrun', 'vtool', '-show-build', GUARD], PREP, 'guard-build-metadata', env=env)
        command(['/usr/bin/lipo', '-archs', GUARD], PREP, 'guard-architectures')
        guard_macho = module.macho(GUARD)
        write(PREP / 'guard-macho.json', guard_macho)
        for candidate in [Path.home() / 'Library/Preferences' / (identifier + '.plist'),
                          Path.home() / 'Library/Saved Application State' / (identifier + '.savedState'),
                          Path(tempfile.gettempdir()) / (identifier + '.savedState')]:
            assert not candidate.exists(), candidate
        for path in HERE.glob('*.py'):
            ast.parse(path.read_text(), filename=str(path))
        write(PREP / 'isolation.json', {'schema': 'bern_foreground_name13_preparation_v1',
            'source_sha': old['source_sha'], 'source_build': build, 'source_build_sha256': sha(build_path),
            'canonical_prior_receipt': str(prior), 'canonical_prior_receipt_sha256': sha(prior),
            'app': str(APP), 'original_app': str(original), 'cli': str(cli), 'identifier': identifier,
            'private_gui_sha256': sha(APP / 'Contents/MacOS/Showcase'), 'guard': str(GUARD),
            'guard_sha256': sha(GUARD), 'guard_source_sha256': sha(GUARD.with_suffix('.swift')),
            'guard_original_source': str(source), 'guard_original_source_sha256': sha(source),
            'guard_adaptation': 'Private prefix, exact Showcase executable basename and original-identity exclusion strings only; inverse replacement byte-equal to Gallery source. Cleanup ordering unchanged.',
            'macho_helper_source': str(helper), 'macho_helper_sha256': sha(helper),
            'original_members': before, 'private_members': after, 'changed_members': changed,
            'macho_sections_unchanged': True, 'normalized_non_signature_bytes_unchanged': True,
            'original_four_binaries': original_hashes(), 'requested_developer_dir': developer,
            'requested_sdk': sdk, 'requested_target': 'arm64-apple-macosx13.0', 'swift_language_mode': '5',
            'actual_guard_build_metadata': 'guard-build-metadata.stdout', 'ipc': str(RUN / 'ipc'),
            'deadline_seconds': 240, 'startup_seconds': 18, 'cli_timeout_seconds': 8,
            'watch_executed': False, 'gui_or_guard_executed': False,
            'purpose': 'Single future foreground Name click, Unicode typing and Return; no AXValue, Search focus, backend/privacy/config or product change.'})
        success = True
    finally:
        entries = [p for p in cache.rglob('*') if p.is_file()] if cache.exists() else []
        sizes = sum(p.stat().st_size for p in entries)
        if cache.exists():
            assert not cache.is_symlink() and not any(p.is_symlink() for p in cache.rglob('*'))
            shutil.rmtree(cache)
        write(PREP / 'module-cache-cleanup.json', {'files': len(entries), 'logical_bytes_removed': sizes,
              'cache_absent': not cache.exists(), 'apfs_physical_savings_not_asserted': True})
        write(PREP / 'final-original-hashes.json', original_hashes())
        if not success:
            if APP.exists(): shutil.rmtree(APP)
            if GUARD.exists(): GUARD.unlink()
        sources = {str(p.relative_to(HERE)): sha(p) for p in sorted(HERE.glob('*.py'))}
        if GUARD.with_suffix('.swift').exists(): sources['tools/FocusGuard.swift'] = sha(GUARD.with_suffix('.swift'))
        write(PREP / 'sources.json', {'sha256': sources, 'syntax_parsed': success, 'watch_not_executed': True})

if __name__ == '__main__':
    assert len(sys.argv) == 1, 'No arguments; this command only prepares'
    main()
