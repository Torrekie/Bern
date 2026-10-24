#!/usr/bin/env python3
"""Append measurement modifiers to one SHA-locked generated component; never edit input."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re

SOURCE_SHA = "1d1da3167d9437b2305df1a39099f01f693b1b674f13cd2e4d88bffec2c52083"
BLOCK_SHA = "e1479772ed383a7e1bd3b4fbf4749146b5601806194c217c797b7cd072527e87"
MARKER = b"/// Generated from the `layout_page` component.\n"
NEXT = b"/// Generated from the `library_page` component.\n"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def patch(source, output):
    raw = source.read_bytes()
    need(sha(raw) == SOURCE_SHA, "full generated source SHA mismatch")
    need(b"\r" not in raw and b".bernPictureMeasure(" not in raw, "unexpected newline or existing hook")
    need(raw.count(MARKER) == 1 and raw.count(NEXT) == 1, "component markers must be unique")
    start = raw.index(MARKER)
    end = raw.index(NEXT, start)
    block = raw[start:end]
    need(block.endswith(b"\n\n") and sha(block[:-1]) == BLOCK_SHA, "whole component SHA mismatch")
    need(block.startswith(MARKER + b"@MainActor\nstruct AppView_layout_page: View {\n"), "component header mismatch")
    need(len(re.findall(br"(?m)^/// Generated from the `", block)) == 1, "nested component boundary")
    need(block.count(b"        .formStyle(.grouped)") == 1, "Form modifier must be unique")
    hooks = []

    def add(label, expression, indent):
        needle = expression.encode()
        need(block.count(needle) == 1, "expression must match once: " + label)
        offset = start + block.index(needle) + len(needle)
        need(raw[offset:offset + 1] == b"\n", "expression does not end at a line: " + label)
        insertion = ("\n" + " " * indent + '.bernPictureMeasure("' + label + '")').encode()
        hooks.append({"label": label, "original_byte_offset": offset,
                      "original_expression_start_line": raw[:offset - len(needle)].count(b"\n") + 1,
                      "original_expression_end_line": raw[:offset].count(b"\n") + 1,
                      "expression_sha256": sha(needle), "insertion": insertion.decode()})

    columns = []
    specs = [
        ("images-contain", "0.0.0.0", "images/landscape.jpg", "120.0", "90.0", "contain"),
        ("images-cover", "0.0.0.1", "images/landscape.jpg", "120.0", "90.0", "cover"),
        ("images-fill", "0.0.0.2", "images/landscape.jpg", "120.0", "90.0", "fill"),
        ("images-mark", "0.0.0.3", "images/bern.png", "64.0", "nil", "contain"),
        ("hdr-gainmap", "0.1.0.0", "images/hdr-gainmap.jpg", "192.0", "108.0", "contain"),
        ("hdr-pq", "0.1.0.1", "images/hdr-pq.png", "192.0", "108.0", "contain"),
    ]
    for label, path, asset, width, height, fit in specs:
        image = ('                        BernImage(name: "' + asset + '", label: BernText.string("layout_page.'
                 + path + '.0.label"), width: ' + width + ', height: ' + height + ', fit: .' + fit + ', aspect: nil)')
        caption = ('                        SwiftUI.Text(verbatim: BernText.string("layout_page.' + path + '.1.content"))\n'
                   '                        .font(.caption)\n'
                   '                        .foregroundStyle(.secondary)')
        column = ('                    SwiftUI.VStack(alignment: .center, spacing: 6.0) {\n'
                  + image + '\n' + caption + '\n                    }')
        add(label + "-image", image, 24)
        add(label + "-caption", caption, 24)
        add(label + "-column", column, 20)
        columns.append(column)
    for label, minimum, content in [("images-grid", "120.0", columns[:4]), ("hdr-grid", "192.0", columns[4:])]:
        grid = ('                BernAdaptiveGrid(minimum: ' + minimum + ', gap: 16.0, rowGap: 16.0, motion: nil) {\n'
                + '\n'.join(content) + '\n                }\n'
                '                .frame(maxWidth: .infinity, alignment: .leading)')
        add(label, grid, 16)
    add("form-root", "        .formStyle(.grouped)", 8)
    need(len(hooks) == 21 and len({h["label"] for h in hooks}) == 21, "hook label/count mismatch")
    need(len({h["original_byte_offset"] for h in hooks}) == 21, "overlapping insertions")
    candidate = raw
    for hook in sorted(hooks, key=lambda h: h["original_byte_offset"], reverse=True):
        offset = hook["original_byte_offset"]
        candidate = candidate[:offset] + hook["insertion"].encode() + candidate[offset:]
    restored = candidate
    for hook in hooks:
        insertion = hook["insertion"].encode()
        need(restored.count(insertion) == 1, "insertion recovery must be unique: " + hook["label"])
        restored = restored.replace(insertion, b"", 1)
    need(restored == raw, "removing only inserted modifiers must recover every original byte")
    need(candidate[:start] == raw[:start] and candidate.endswith(raw[end:]), "outside-component mutation")
    need(candidate.count(b".bernPictureMeasure(") == 21, "unexpected generated hook count")
    diff = "".join(difflib.unified_diff(raw.decode().splitlines(True), candidate.decode().splitlines(True),
                                    fromfile="a/BernGenerated.swift", tofile="b/BernGenerated.swift")).encode()
    report = {"source_sha256": sha(raw), "source_bytes": len(raw), "component_export_slice_sha256": sha(block[:-1]),
              "component_raw_sha256": sha(block), "component_first_line": raw[:start].count(b"\n") + 1,
              "component_last_line_inclusive": raw[:end].count(b"\n"), "candidate_sha256": sha(candidate),
              "candidate_bytes": len(candidate), "diff_sha256": sha(diff), "hook_count": len(hooks),
              "original_restored_exact": restored == raw, "outside_component_unchanged": True,
              "helper_included": False, "hooks": sorted(hooks, key=lambda h: h["original_byte_offset"])}
    need(not output.exists(), "fresh output directory required; refusing overwrite")
    output.mkdir(parents=True, exist_ok=False)
    files = {"BernGenerated.measured.swift": candidate, "observer.patch": diff,
             "patch-map.json": (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()}
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "SHA256SUMS").write_text("".join(sha(data) + "  " + name + "\n" for name, data in sorted(files.items())))
    print(json.dumps({"output": str(output), "hook_count": len(hooks), "candidate_sha256": sha(candidate),
                      "original_restored_exact": True}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    patch(args.source.resolve(), args.output.resolve())
