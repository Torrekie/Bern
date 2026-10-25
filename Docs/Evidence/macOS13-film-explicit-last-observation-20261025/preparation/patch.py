#!/usr/bin/env python3
"""Exact e48 templates -> diagnostic unified diffs only. Never mutates input files."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

STYLE_SHA = '3912ecdbe102508771174df91f4d7baa153cca9925d89f6e68cdffc2e90cbd89'
RUNTIME_SHA = '255bacb40db71fa17a8bd9ecaefc1b72c187864295221727c28653a09839e16e'
CORE_SHA = 'b9a7c8d9a4060148f150c562e96297c10482181c96bf88477a6bfcf6cf5f5b06'

STYLE_EDITS = [
('''    fileprivate func legacyFrame(_ key: AnyHashable) -> CGRect? { frames[key] }
''','''    fileprivate func legacyFrame(_ key: AnyHashable) -> CGRect? { frames[key] }
    fileprivate func filmLastSnapshot(_ wanted: AnyHashable) -> [String: Any] {
        ["nearest": BernFilmLastObservation.key(nearest), "arrived": BernFilmLastObservation.key(arrived),
         "arrivals": arrivals, "stops": stops, "coming": BernFilmLastObservation.key(coming),
         "viewport": ["width": Double(viewport.width), "height": Double(viewport.height)],
         "anchor": ["x": Double(anchor.x), "y": Double(anchor.y)],
         "frame_wanted": BernFilmLastObservation.rect(frames[wanted]),
         "initial_waiting": legacyInitial.waiting, "initial_generation": legacyInitial.generation]
    }
'''),
('''                    snapGeneration: initialOwner.map { owner in { [weak owner] in owner?.generation ?? 0 } }))
''','''                    snapGeneration: initialOwner.map { owner in { [weak owner] in owner?.generation ?? 0 } },
                    observationOwner: BernFilmLastObservation.enabled ? positionItems.map { owner in { [weak owner] in owner as AnyObject? } } : nil))
'''),
('''            withAnimation(animation) { target = wanted }
''','''            withAnimation(animation) { target = wanted }
            #if os(macOS)
            if BernFilmLastObservation.enabled {
                BernFilmLastObservation.request(owner: items, wanted: AnyHashable(wanted),
                    position: AnyHashable(position.wrappedValue), target: target.map { AnyHashable($0) },
                    snapshot: items.filmLastSnapshot(AnyHashable(wanted)))
            }
            #endif
'''),
('''    var snapGeneration: (@MainActor () -> UInt64)? = nil
''','''    var snapGeneration: (@MainActor () -> UInt64)? = nil
    var observationOwner: (@MainActor () -> AnyObject?)? = nil
'''),
('''            let generation = configuration.snapGeneration?()
            let work = DispatchWorkItem''','''            let generation = configuration.snapGeneration?()
            if let owner = configuration.observationOwner?() {
                BernFilmLastObservation.schedule(owner: owner, scroll: scroll, generation: generation, live: live)
            }
            let work = DispatchWorkItem'''),
('''            let length = horizontal ? bounds.width : bounds.height
            guard let wanted = snap(start, length) else { return }
''','''            let length = horizontal ? bounds.width : bounds.height
            let observationToken: UInt64?
            if let owner = configuration.observationOwner?() {
                observationToken = BernFilmLastObservation.beginSettle(owner: owner, scroll: scroll, clip: clip,
                    document: document, generation: generation, start: start, length: length)
            } else { observationToken = nil }
            guard let wanted = snap(start, length) else { return }
'''),
('''            let maximum = max(minimum, (horizontal ? document.frame.width + insets.right : document.frame.height + insets.bottom) - length)
''','''            let observationDocumentFrame = document.frame
            let maximum = max(minimum, (horizontal ? observationDocumentFrame.width + insets.right : observationDocumentFrame.height + insets.bottom) - length)
'''),
('''            let clamped = max(minimum, min(maximum, wanted))
            guard abs(clamped - start) > 0.5 else { return }
''','''            let clamped = max(minimum, min(maximum, wanted))
            if observationToken != nil {
                BernFilmLastObservation.finishSettle(observationToken, values: ["wanted": Double(wanted),
                    "minimum": Double(minimum), "maximum": Double(maximum), "clamped": Double(clamped),
                    "document_length": Double(horizontal ? observationDocumentFrame.width : observationDocumentFrame.height),
                    "insets": ["left": Double(insets.left), "right": Double(insets.right), "top": Double(insets.top), "bottom": Double(insets.bottom)]])
            }
            guard abs(clamped - start) > 0.5 else { return }
'''),
('''            if configuration.reduce {
                clip.scroll(to: point)
                scroll.reflectScrolledClipView(clip)
''','''            if configuration.reduce {
                clip.scroll(to: point)
                scroll.reflectScrolledClipView(clip)
                if let owner = configuration.observationOwner?() {
                    BernFilmLastObservation.writer(owner: owner, token: observationToken, kind: "direct", values: [
                        "start": Double(start), "length": Double(length), "wanted": Double(wanted),
                        "minimum": Double(minimum), "maximum": Double(maximum), "clamped": Double(clamped),
                        "document_length": Double(horizontal ? observationDocumentFrame.width : observationDocumentFrame.height),
                        "insets": ["left": Double(insets.left), "right": Double(insets.right), "top": Double(insets.top), "bottom": Double(insets.bottom)]])
                }
'''),
('''                    clip.animator().setBoundsOrigin(point)
''','''                    clip.animator().setBoundsOrigin(point)
                    if let owner = configuration.observationOwner?() {
                        BernFilmLastObservation.writer(owner: owner, token: observationToken, kind: "animator_requested", values: [
                        "start": Double(start), "length": Double(length), "wanted": Double(wanted),
                        "minimum": Double(minimum), "maximum": Double(maximum), "clamped": Double(clamped),
                        "document_length": Double(horizontal ? observationDocumentFrame.width : observationDocumentFrame.height),
                        "insets": ["left": Double(insets.left), "right": Double(insets.right), "top": Double(insets.top), "bottom": Double(insets.bottom)]])
                    }
''')]
RUNTIME_EDITS = [('''        case 0:  // ui.inspect
            let entries = controls.all
''','''        case 0:  // ui.inspect
            #if os(macOS)
            BernFilmLastObservation.exportIfRequested()
            #endif
            let entries = controls.all
''')]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def transform(original, edits):
    candidate = original
    for before, after in edits:
        assert candidate.count(before) == 1, 'Missing/ambiguous exact edit'
        candidate = candidate.replace(before, after)
    inverse = candidate
    for before, after in reversed(edits):
        assert inverse.count(after) == 1, 'Missing/ambiguous inverse'
        inverse = inverse.replace(after, before)
    assert inverse == original
    return candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template_directory', type=Path)
    parser.add_argument('fresh_output_directory', type=Path)
    args = parser.parse_args()
    template = args.template_directory.resolve(strict=True)
    output = args.fresh_output_directory.resolve()
    core_path = Path(__file__).resolve().with_name('FilmLastObservation.swift.inc')
    core = core_path.read_bytes()
    assert sha(core) == CORE_SHA and len(core) <= 16384
    assert output.parent.is_dir() and not output.exists()
    assert output != template and output not in template.parents and template not in output.parents
    assert output != core_path.parent and output not in core_path.parent.parents and core_path.parent not in output.parents
    originals = {}
    for name, pin in [('BernStyle.swift', STYLE_SHA), ('BernRuntime.swift', RUNTIME_SHA)]:
        path = template / name
        assert path.is_file() and not path.is_symlink()
        originals[name] = path.read_bytes()
        assert sha(originals[name]) == pin, 'Template hash mismatch; generated Runtime is unsupported'
    style = transform(originals['BernStyle.swift'].decode(), STYLE_EDITS)
    runtime = transform(originals['BernRuntime.swift'].decode(), RUNTIME_EDITS) + '\n' + core.decode()
    assert runtime.endswith('\n' + core.decode())
    candidates = {'BernStyle.swift': style.encode(), 'BernRuntime.swift': runtime.encode()}
    output.mkdir()
    proof = {'schema': 'bern_film_observation_template_patch_v1', 'input_kind': 'exact_e48_templates_only_not_generated_Runtime',
             'source': 'e48fff46b3a92a28465ad74295bd273a9d69af7d', 'core_sha256': sha(core), 'files': {}}
    for name, candidate in candidates.items():
        delta = ''.join(difflib.unified_diff(originals[name].decode().splitlines(True), candidate.decode().splitlines(True), fromfile='a/' + name, tofile='b/' + name))
        assert delta
        (output / (name + '.patch')).write_text(delta)
        proof['files'][name] = {'original_sha256': sha(originals[name]), 'candidate_sha256': sha(candidate),
                               'candidate_bytes': len(candidate), 'patch_sha256': sha(delta.encode()), 'all_edits_inverse_to_original': True}
        assert (template / name).read_bytes() == originals[name]
    (output / 'patch-proof.json').write_text(json.dumps(proof, indent=2) + '\n')


if __name__ == '__main__':
    main()
