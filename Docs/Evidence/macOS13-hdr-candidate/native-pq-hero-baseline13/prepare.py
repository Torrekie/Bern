#!/usr/bin/env python3
"""Extract actual HEAD image/hero sources; do not build or launch anything.

Generated files are immutable inputs: rerunning refuses to overwrite a file
that differs, including a ProductHero.swift to which a driver was appended.
"""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess


D = Path(__file__).resolve().parent
REPO = D.parents[1] / 'outputs' / 'Bern'
TEMPLATES = 'crates/bern-backend-swiftui/templates/'
BASE = REPO / 'Docs/Evidence/macOS13-hdr-candidate/native-pq-product-body13'
BASE_COMMIT = '9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)


def extract(full, start, end):
    assert full.count(start) == 1, start
    a = full.index(start)
    b = full.index(end, a)
    # Match the old ProductImage.exact.swift's terminal-newline convention.
    raw = full[a:b].rstrip() + '\n'
    return raw, {
        'start_marker': start,
        'end_marker_exclusive': end,
        'first_line': full[:a].count('\n') + 1,
        'last_boundary_line': full[:b].count('\n'),
        'terminal_newline_convention': 'rstrip()+one LF',
        'exact_slice_sha256': sha(raw.encode()),
    }


commit = git('rev-parse', 'HEAD').decode().strip()
full = {}
sources = {}
for filename in ('BernRuntime.swift', 'BernStyle.swift', 'BernAppKit.swift'):
    relative = TEMPLATES + filename
    raw = git('show', f'{commit}:{relative}')
    working = (REPO / relative).read_bytes()
    assert raw == working, f'Working source differs from locked HEAD: {relative}'
    old = git('show', f'{BASE_COMMIT}:{relative}')
    full[filename] = raw.decode('utf-8')
    sources[filename] = {
        'repository_source': relative,
        'git_blob': git('rev-parse', f'{commit}:{relative}').decode().strip(),
        'full_source_sha256': sha(raw),
        'working_source_matches_HEAD': True,
        'full_source_identical_to_9dd': raw == old,
        'full_source_9dd_sha256': sha(old),
        'slices': [],
    }

image, image_range = extract(full['BernRuntime.swift'], 'enum BernImageFit {', '// MARK: - Files')
motion, motion_range = extract(full['BernStyle.swift'], '// MARK: - Motion', '// MARK: - Colors')
modifier, modifier_range = extract(
    full['BernStyle.swift'],
    '/// Images travel above the native split-view columns on macOS.',
    '// MARK: - Drawing',
)
hero, hero_range = extract(
    full['BernAppKit.swift'], '// MARK: - Window-level image heroes', '// MARK: - Search field',
)
for filename, text, boundary in (
    ('BernRuntime.swift', image, image_range),
    ('BernStyle.swift', motion, motion_range),
    ('BernStyle.swift', modifier, modifier_range),
    ('BernAppKit.swift', hero, hero_range),
):
    old = git('show', f'{BASE_COMMIT}:{TEMPLATES}{filename}').decode('utf-8')
    old_slice, _ = extract(old, boundary['start_marker'], boundary['end_marker_exclusive'])
    boundary['identical_to_9dd_slice'] = text == old_slice
    assert boundary['identical_to_9dd_slice'], f'Unexpected changed product slice: {filename}'
    sources[filename]['slices'].append(boundary)

old_provenance = json.loads((BASE / 'source-provenance.json').read_text())
assert image.encode() == (BASE / 'ProductImage.exact.swift').read_bytes()
assert sha(image.encode()) == old_provenance['exact_slice_sha256']
assert sources['BernRuntime.swift']['full_source_sha256'] == old_provenance['full_runtime_sha256']

start = image.index('        var decoded: CGImage?\n')
end = image.index('        guard let image = decoded ??', start)
original = image[start:end]
adapted_image = image[:start] + '''        #if compiler(>=6.0)
''' + original + '''        #else
        // Diagnostic SDK14.2 build: the15+ branch above cannot run on13.
        let decoded: CGImage? = nil
        #endif
''' + image[end:]

image_imports = '''// Exact product image/cache slice, with one documented diagnostic compiler condition.
import AppKit
import SwiftUI
import Combine
import MetalKit
import CoreImage
import ColorSync
import ImageIO

'''
image_file = image_imports + adapted_image
# The only SDK adaptation must reproduce the previously reviewed body fixture.
assert image_file.encode() == (BASE / 'ProductImage.swift').read_bytes()
assert sha(image_file.encode()) == old_provenance['diagnostic_file_sha256']
style_exact = motion + '\n' + modifier
style_file = 'import SwiftUI\n\n' + style_exact
hero_file = 'import AppKit\nimport SwiftUI\n\n' + hero
dependencies = '''// Diagnostic support only. Actual Motion and PictureHero are extracted separately.
import SwiftUI
import Combine

typealias BernObservableObject = Combine.ObservableObject
enum BernColor { case fixed(light: UInt32, dark: UInt32) }
'''
assert 'struct BernPictureHero:' in style_file
assert 'struct BernReducedMotion:' in style_file
assert 'func snapshot(in overlay:' in hero_file
assert 'private final class BernHeroFlightView:' in hero_file
assert 'override func draw(_ dirtyRect:' in hero_file
assert 'struct BernPictureHero' not in dependencies

outputs = {
    'ProductImage.exact.swift': image.encode(),
    'ProductImage.swift': image_file.encode(),
    'ProductStyle.exact.swift': style_exact.encode(),
    'ProductStyle.swift': style_file.encode(),
    'ProductHero.exact.swift': hero.encode(),
    'ProductHero.swift': hero_file.encode(),
    'Dependencies.swift': dependencies.encode(),
    'sdk14-unreachable-gainmap.patch': ''.join(difflib.unified_diff(
        image.splitlines(True), adapted_image.splitlines(True),
        fromfile='HEAD/ProductImage.exact.swift', tofile='diagnostic/ProductImage.swift',
    )).encode(),
}
provenance = {
    'commit': commit,
    'sources': sources,
    'prior_body_fixture': str(BASE.relative_to(REPO)),
    'prior_body_commit': BASE_COMMIT,
    'prior_image_exact_sha256': old_provenance['exact_slice_sha256'],
    'prior_adapted_image_sha256': old_provenance['diagnostic_file_sha256'],
    'image_exact_and_adapted_identical_to_prior_fixture': True,
    'only_product_source_adaptation': old_provenance['only_product_slice_change'],
    'diagnostic_support': ['Combine.ObservableObject alias', 'BernColor.fixed enum case'],
    'actual_hero_preserved': [
        'BernPictureHero / BernMotion / BernReducedMotion and environment',
        'BernPictureHeroProbe / BernPictureHeroAnchor snapshot and capture',
        'BernViewHero / BernHeroPicture / BernHeroOverlay / BernHeroFlightView',
        'Complete BernWindowImageHeroes manager, timer and lifecycle',
    ],
    'same_file_driver_rule': 'Append root driver to ProductHero.swift without altering original hero block or access control; no driver is supplied by prepare.py.',
    'scope': 'Source extraction only; no main/build scripts, compilation, UI or CI. Endpoint validation is not full-flight validation.',
    'generated_files': {name: {'sha256': sha(data), 'bytes': len(data)} for name, data in outputs.items()},
    'prepare_script_sha256': sha(Path(__file__).read_bytes()),
}
outputs['source-provenance.json'] = (json.dumps(provenance, indent=2, sort_keys=True) + '\n').encode()

for name, data in outputs.items():
    path = D / name
    if path.exists() and path.read_bytes() != data:
        raise SystemExit(f'Refusing to overwrite differing prepared file: {path}')
for name, data in outputs.items():
    (D / name).write_bytes(data)

print(json.dumps({
    'commit': commit,
    'prepared_files': list(outputs),
    'provenance_sha256': sha(outputs['source-provenance.json']),
    'image_matches_prior_fixture': True,
    'all_extracted_slices_identical_to_9dd': True,
    'compiled_or_executed_UI': False,
}, indent=2))
