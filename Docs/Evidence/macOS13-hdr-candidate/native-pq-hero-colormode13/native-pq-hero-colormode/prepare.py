#!/usr/bin/env python3
"""Copy the archived successful fixture and add only diagnostic colorMode selection.

No product/archive edits, compiler invocation, UI, network or CI operation.
"""
from pathlib import Path
import difflib
import hashlib
import json

D = Path(__file__).resolve().parent
REPO = D.parents[1] / 'outputs/Bern'
BASE = REPO / 'Docs/Evidence/macOS13-hdr-candidate/native-pq-hero-baseline13'
sha = lambda data: hashlib.sha256(data).hexdigest()


def once(text, old, new):
    assert text.count(old) == 1, (old[:80], text.count(old))
    return text.replace(old, new, 1)


names = ['ProductImage.exact.swift', 'ProductImage.swift', 'ProductStyle.exact.swift',
         'ProductStyle.swift', 'ProductHero.exact.swift', 'ProductHero.base.swift',
         'Dependencies.swift', 'sdk14-unreachable-gainmap.patch', 'sdk14-unused-clock.patch']
outputs = {name: (BASE / name).read_bytes() for name in names}
base_hero = (BASE / 'ProductHero.swift').read_text()
base_driver = (BASE / 'Driver.swift.inc').read_text()
assert base_hero.endswith(base_driver)
clock_adapted = base_hero[:-len(base_driver)]
assert 'self?.tick()' in clock_adapted
assert 'Static endpoint fixture unexpectedly started its excluded timer' in clock_adapted
assert clock_adapted.count('renderer.scale = window?.backingScaleFactor ?? 2') == 1
assert 'BERN_HERO_COLOR_MODE' not in base_driver and 'renderer.colorMode =' not in clock_adapted

selection = '''// Diagnostic-only configuration: environment is read exactly once per process.
private enum FixtureHeroColorMode: String {
    case systemDefault = "default"
    case linear
    case extendedLinear
    case nonLinear

    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_COLOR_MODE"]
    static let selected = FixtureHeroColorMode(rawValue: requested ?? "default")

    var rendererMode: ColorRenderingMode? {
        switch self {
        case .systemDefault: return nil
        case .linear: return .linear
        case .extendedLinear: return .extendedLinear
        case .nonLinear: return .nonLinear
        }
    }
}

'''
driver = once(base_driver, 'private struct FixtureFailure: Error { let message: String }\n',
              selection + 'private struct FixtureFailure: Error { let message: String }\n')
driver = once(driver, '        defer {\n', '''        report["hero_color_mode_environment"] = FixtureHeroColorMode.requested ?? "(unset)"
        report["hero_color_mode_selected"] = FixtureHeroColorMode.selected?.rawValue ?? "invalid"
        report["hero_color_mode_assignment_requested"] = FixtureHeroColorMode.selected?.rendererMode != nil
        defer {
''')
driver = once(driver,
    '            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)\n',
    '''            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
            guard FixtureHeroColorMode.selected != nil else {
                throw FixtureFailure(message: "Unknown BERN_HERO_COLOR_MODE; expected default, linear, extendedLinear or nonLinear")
            }
''')
hero = once(clock_adapted,
    '        renderer.scale = window?.backingScaleFactor ?? 2\n        guard let pixels = renderer.cgImage else { return nil }\n',
    '''        renderer.scale = window?.backingScaleFactor ?? 2
        // Diagnostic only: default deliberately leaves the actual renderer unset.
        if let colorMode = FixtureHeroColorMode.selected?.rendererMode {
            renderer.colorMode = colorMode
        }
        guard let pixels = renderer.cgImage else { return nil }
''')

# All acquisition/geometry/fit/cache/draw/gate code is inherited byte for byte.
outputs['ProductHero.clock-adapted.swift'] = clock_adapted.encode()
outputs['Driver.base.swift.inc'] = base_driver.encode()
outputs['Driver.swift.inc'] = driver.encode()
outputs['ProductHero.swift'] = (hero + driver).encode()
outputs['source-provenance.baseline.json'] = (BASE / 'source-provenance.json').read_bytes()
outputs['color-mode-snapshot.patch'] = ''.join(difflib.unified_diff(
    clock_adapted.splitlines(True), hero.splitlines(True),
    fromfile='baseline/ProductHero.clock-adapted.swift', tofile='diagnostic/ProductHero.swift')).encode()
outputs['color-mode-driver.patch'] = ''.join(difflib.unified_diff(
    base_driver.splitlines(True), driver.splitlines(True),
    fromfile='baseline/Driver.swift.inc', tofile='diagnostic/Driver.swift.inc')).encode()

baseline_fingerprint = json.loads((BASE / 'build-fingerprint.json').read_text())
assert sha(base_hero.encode()) == baseline_fingerprint['hashes']['ProductHero.swift']
assert sha(base_driver.encode()) == baseline_fingerprint['hashes']['Driver.swift.inc']
for name in names:
    assert sha(outputs[name]) == baseline_fingerprint['hashes'][name], name

interface = Path('/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk/System/Library/Frameworks/SwiftUI.framework/Versions/A/Modules/SwiftUI.swiftmodule/arm64e-apple-macos.swiftinterface')
interface_text = interface.read_text()
assert 'public enum ColorRenderingMode : Swift.Sendable {' in interface_text
assert '  case nonLinear\n  case linear\n  case extendedLinear\n' in interface_text
assert '@_Concurrency.MainActor final public var colorMode: SwiftUI.ColorRenderingMode {' in interface_text
provenance = dict(
    scope='Prepared only. No compile/typecheck, UI, CI or product/archive modification. Single-mode process, not a matrix.',
    baseline_archive=str(BASE.relative_to(REPO)),
    baseline_product_commit='b08db54e01ac2ec54fb84e6f2a70041f1f4c3604',
    baseline_compiled_source_sha256=sha(base_hero.encode()),
    baseline_driver_sha256=sha(base_driver.encode()),
    baseline_build_fingerprint_sha256=sha((BASE / 'build-fingerprint.json').read_bytes()),
    baseline_source_provenance_sha256=sha((BASE / 'source-provenance.json').read_bytes()),
    input_sources_verified_against_successful_baseline_fingerprint=True,
    diagnostic_changes=['One optional public colorMode assignment after actual renderer creation/scale and before cgImage read.',
                        'One process-cached BERN_HERO_COLOR_MODE enum plus report fields and invalid-mode prewindow failure.'],
    default_policy='No colorMode setter when env is absent/default. No assumption that explicit nonLinear equals an unset property.',
    inherited_adaptations=['Exact archived compiler condition around SDK14-unavailable gain-map decode.',
                          'Exact archived compiler/availability failguard on unused coordinator clock. Timer must remain absent.'],
    unchanged=['Actual ProductImage body/decode/cache', 'Actual ProductStyle/hero modifier', 'Actual NSImage.draw/FlightView',
               'All window geometry/normal/frontmost/nonkey/noMetal/noTimer/capture/stable-buffer/deadline gates'],
    public_api=dict(interface_path=str(interface), interface_sha256=sha(interface.read_bytes()),
                    ImageRenderer_available_macos='13.0', property='public MainActor ImageRenderer.colorMode',
                    public_enum_cases=['nonLinear', 'linear', 'extendedLinear']),
    generated_files={name: dict(bytes=len(data), sha256=sha(data)) for name, data in outputs.items()},
    prepare_script_sha256=sha(Path(__file__).read_bytes()))
outputs['source-provenance.json'] = (json.dumps(provenance, indent=2, sort_keys=True) + '\n').encode()
for name, data in outputs.items():
    path = D / name
    if path.exists() and path.read_bytes() != data:
        raise SystemExit(f'Refusing to overwrite differing prepared file: {path}')
for name, data in outputs.items():
    (D / name).write_bytes(data)
print(json.dumps(dict(prepared_files=len(outputs), baseline_source_verified=True,
    source_provenance_sha256=sha(outputs['source-provenance.json']), compiled_or_run=False), indent=2))
