#!/usr/bin/env python3
"""Prepare a separate native-CI diagnostic; never build/run or edit prior fixtures."""
from pathlib import Path
import hashlib,json,difflib

D=Path(__file__).resolve().parent
R=D.parents[1]/'outputs/Bern'
B=R/'Docs/Evidence/macOS13-hdr-candidate/native-pq-hero-baseline13'
sha=lambda b:hashlib.sha256(b).hexdigest()
def once(text,old,new):
    assert text.count(old)==1,(old[:80],text.count(old))
    return text.replace(old,new,1)

fp=json.loads((B/'build-fingerprint.json').read_text())
names=['Dependencies.swift','ProductImage.exact.swift','ProductImage.swift','ProductStyle.exact.swift',
       'ProductStyle.swift','ProductHero.exact.swift','ProductHero.base.swift',
       'sdk14-unreachable-gainmap.patch','sdk14-unused-clock.patch']
out={n:(B/n).read_bytes() for n in names}
for n,data in out.items(): assert sha(data)==fp['hashes'][n],n
driver=(B/'Driver.swift.inc').read_text(); combined=(B/'ProductHero.swift').read_text()
assert sha(driver.encode())==fp['hashes']['Driver.swift.inc']
assert sha(combined.encode())==fp['hashes']['ProductHero.swift'] and combined.endswith(driver)
hero=combined[:-len(driver)]
out['Driver.base.swift.inc']=driver.encode()
out['ProductHero.clock-adapted.swift']=hero.encode()
helper=(D/'NativeCI.swift.inc').read_text()
assert helper.count('CIContext()')==1 and helper.count('ProcessInfo.processInfo.environment[')==1
driver_new=once(driver,'private struct FixtureFailure: Error { let message: String }\n',
                helper+'\nprivate struct FixtureFailure: Error { let message: String }\n')
driver_new=once(driver_new,'        defer {\n','''        report["hero_snapshot_backend_environment"] = FixtureHeroSnapshotBackend.requested ?? "(unset)"
        report["hero_snapshot_backend_selected"] = FixtureHeroSnapshotBackend.selected?.rawValue ?? "invalid"
        defer {
''')
driver_new=once(driver_new,'            report["os"] = ProcessInfo.processInfo.operatingSystemVersionString\n',
'''            report["os"] = ProcessInfo.processInfo.operatingSystemVersionString
            report["native_ci_diagnostic"] = FixtureNativeCI.report
''')
driver_new=once(driver_new,'            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)\n',
'''            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
            guard FixtureHeroSnapshotBackend.selected != nil else {
                throw FixtureFailure(message: "Unknown BERN_HERO_SNAPSHOT_BACKEND; expected default or nativeCI")
            }
''')
driver_new=once(driver_new,'            let before = try fixtureLedger(urls); report["cache_before"] = before\n',
'''            if FixtureHeroSnapshotBackend.selected == .nativeCI {
                try FixtureNativeCI.prepareInputs(urls)
            }
            let before = try fixtureLedger(urls); report["cache_before"] = before
''')
hero_new=once(hero,'    fileprivate func snapshot(in overlay: NSView) -> BernHeroPicture? {\n',
'''    fileprivate func snapshot(in overlay: NSView) -> BernHeroPicture? {
        guard let backend = FixtureHeroSnapshotBackend.selected else {
            FixtureNativeCI.fail("Unknown snapshot backend; no fallback"); return nil
        }
        if backend == .nativeCI && capturesView {
            FixtureNativeCI.fail("nativeCI does not support non-image capture"); return nil
        }
''')
hero_new=once(hero_new,'        guard rect.width > 0, rect.height > 0 else { return nil }\n        let image = SwiftUI.Image(decorative: picture.image, scale: 1, orientation: picture.orientation).resizable()\n',
'''        guard rect.width > 0, rect.height > 0 else { return nil }
        if backend == .nativeCI {
            guard let pixels = FixtureNativeCI.pixels(picture, fit: fit, bounds: bounds, rect: rect,
                scale: window?.backingScaleFactor ?? 0, corner: corner) else { return nil }
            return BernHeroPicture(rect: rect, image: NSImage(cgImage: pixels, size: bounds.size),
                corner: corner * rect.width / bounds.width)
        }
        let image = SwiftUI.Image(decorative: picture.image, scale: 1, orientation: picture.orientation).resizable()
''')
out['Driver.swift.inc']=driver_new.encode()
out['ProductHero.swift']=(hero_new+driver_new).encode()
out['source-provenance.baseline.json']=(B/'source-provenance.json').read_bytes()
for label,old,new in [('snapshot',hero,hero_new),('driver',driver,driver_new)]:
    out['native-ci-'+label+'.patch']=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
        fromfile='baseline/'+label+'.swift',tofile='diagnostic/'+label+'.swift')).encode()
provenance={'scope':'Work-only uncompiled/unrun fixed-input public native-CI conversion diagnostic; no product/other fixture/archive modification.',
 'baseline_archive':str(B.relative_to(R)),'baseline_product_commit':'b08db54e01ac2ec54fb84e6f2a70041f1f4c3604',
 'baseline_successful_combined_sha256':sha(combined.encode()),'baseline_driver_sha256':sha(driver.encode()),
 'baseline_build_fingerprint_sha256':sha((B/'build-fingerprint.json').read_bytes()),
 'native_ci_helper_sha256':sha(helper.encode()),
 'default_path':'Original archived ImageRenderer block byte-preserved after a backend guard/early-branch; does not create CIContext or inspect selected-CI inputs.',
 'selected_path':'Actual cached canonicalPQ CGImage or exact SHA-locked known namedPQ original, explicit input colorSpace, CIContext.createCGImage RGBAh/extendedSRGB; same original NSImage wrapper arguments and Flight.draw.',
 'metadata_policy':'Only CGImage scalar fields; no new CopyICCData/color flags/name traversal. Helper registry stores only identity/label, not CGImage/NSImage. Report assembled after original window teardown; original driver ledger/NSImageRep observations unchanged.',
 'lock':'Known opaque/up SHA-locked640x360 inputs; fill320x180pt, backingScale2, no transform/corner. Unsupported/unknown fail; no renderer fallback.',
 'limits':['Not a general fit/orientation/alpha/HLG/gainmap/product solution','No assumption about14 CGImage metadata/cause; compare measured14 baseline','No filter/exposure/tone curve/custom mapper; system conversion behavior remains to be measured'],
 'preserved':['Actual Image/body/cache/Style','Same root driver frames/actions/stability/normal/front/cache/noMetal/noTimer/deadlines','Archived SDK14 gainmap guard and unused clock failguard'],
 'generated_files':{n:{'bytes':len(data),'sha256':sha(data)} for n,data in out.items()},
 'prepare_script_sha256':sha(Path(__file__).read_bytes())}
out['source-provenance.json']=(json.dumps(provenance,indent=2,sort_keys=True)+'\n').encode()
for n,data in out.items():
 p=D/n
 if p.exists() and p.read_bytes()!=data: raise SystemExit('Refuse differing output: '+str(p))
for n,data in out.items(): (D/n).write_bytes(data)
print(json.dumps({'prepared_files':len(out),'source_provenance_sha256':sha(out['source-provenance.json']),'compiled_or_run':False},indent=2))
