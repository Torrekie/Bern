#!/usr/bin/env python3
"""Compare per-host normalized patch-mean hero minus body residuals; no PNG fitting."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
PHASES = ("progress-0", "progress-1")
SOURCES = ("named", "custom")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def subtract(left, right):
    return [float(a) - float(b) for a, b in zip(left, right)]


def rgb(value):
    require(isinstance(value, list) and len(value) == 3 and
            all(isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) for n in value),
            "Invalid normalized patch RGB mean")
    return value


def load_host(analysis_path, report_override, expected_major):
    analysis_path = analysis_path.resolve()
    analysis = json.loads(analysis_path.read_text())
    report_path = (report_override or Path(analysis["input_report"])).resolve()
    require(digest(report_path) == analysis["input_report_sha256"], "Actual runtime report differs from its offline analysis input hash")
    runtime = json.loads(report_path.read_text())
    match = re.search(r"(\d+)\.", str(runtime.get("os", "")))
    require(match is not None and int(match.group(1)) == expected_major,
            f"Actual runtime OS string does not identify macOS{expected_major}")
    if "expected_os_major" in runtime:
        require(runtime["expected_os_major"] == expected_major, "Runtime expected OS differs from selected host")
    require(analysis.get("analysis_complete") is True and runtime.get("success") is True and
            runtime.get("completed_phases") == 2, "Host did not complete both endpoint captures and offline analysis")
    captures = {c["phase"]: c for c in analysis["captures"]}
    require(len(analysis["captures"]) == 2 and set(captures) == set(PHASES), "Need exactly one analysis capture per endpoint")
    original_captures = {c["phase"]: c for c in runtime["captures"]}
    for phase, capture in captures.items():
        require(capture["png_sha256"] == original_captures[phase]["png_sha256"], "Offline PNG fingerprint differs from original report")
    context = dict(analysis=str(analysis_path), analysis_sha256=digest(analysis_path),
                   runtime_report=str(report_path), runtime_report_sha256=digest(report_path),
                   actual_os=runtime["os"], expected_major=expected_major,
                   versions=analysis["versions"], analyzer_sha256=analysis["analyzer_sha256"],
                   atlas_spec_sha256=analysis["atlas_spec_sha256"], warnings=analysis.get("warnings", []),
                   roi_pixel_sizes={phase: {name: row["pixel_size"] for name, row in c["rois"].items()} for phase, c in captures.items()},
                   capture_context={phase: dict(embedded_icc_sha256=c["embedded_icc_sha256"],
                       runtime_capture=c.get("runtime_capture", {})) for phase, c in captures.items()},
                   recorded_binary_fields={k: runtime[k] for k in ("binary_sha256", "fixture_binary_sha256", "executable_sha256") if k in runtime})
    return captures, context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis13", type=Path)
    parser.add_argument("analysis14", type=Path)
    parser.add_argument("--report13", type=Path, help="Unchanged original report if the analysis recorded path has moved")
    parser.add_argument("--report14", type=Path, help="Unchanged original report if the analysis recorded path has moved")
    parser.add_argument("--output", type=Path, default=HERE / "crosshost-result")
    args = parser.parse_args()
    destination = args.output.resolve()
    require(HERE in destination.parents and not destination.exists(), "Output must be a fresh subdirectory of this crosshost workspace")
    hosts = {}
    for major in (13, 14):
        hosts[major] = load_host(getattr(args, f"analysis{major}"), getattr(args, f"report{major}"), major)
    a13, c13 = hosts[13]
    a14, c14 = hosts[14]
    require(c13["atlas_spec_sha256"] == c14["atlas_spec_sha256"], "Atlas coordinate specifications differ")
    require(c13["analyzer_sha256"] == c14["analyzer_sha256"], "Per-host analyzer versions differ")
    require(c13["versions"] == c14["versions"], "Pillow/LittleCMS versions differ; reanalyze both locally with one interpreter")
    rows = []
    for phase in PHASES:
        for source in SOURCES:
            patches = {}
            residual13, residual14, residual_difference = [], [], []
            means = {}
            for major, captures in ((13, a13), (14, a14)):
                means[major] = {name: captures[phase]["rois"][name]["means"]["icc_to_srgb"]
                                for name in (f"body-{source}", f"flight-{source}", "oracle-top", "oracle-bottom")}
            names = set(means[13][f"body-{source}"])
            require(len(names) == 10 and all(set(patch_means) == names for h in means.values() for patch_means in h.values()),
                    "Need the same ten named atlas patches in all panes and both hosts")
            for name in sorted(names):
                values = {}
                for major in (13, 14):
                    pane = {key: rgb(value[name]) for key, value in means[major].items()}
                    values[str(major)] = dict(
                        body_mean_rgb=pane[f"body-{source}"], hero_mean_rgb=pane[f"flight-{source}"],
                        oracle_top_mean_rgb=pane["oracle-top"], oracle_bottom_mean_rgb=pane["oracle-bottom"],
                        hero_minus_body=subtract(pane[f"flight-{source}"], pane[f"body-{source}"]),
                        body_minus_own_oracle_top=subtract(pane[f"body-{source}"], pane["oracle-top"]),
                        hero_minus_own_oracle_bottom=subtract(pane[f"flight-{source}"], pane["oracle-bottom"]))
                difference = subtract(values["13"]["hero_minus_body"], values["14"]["hero_minus_body"])
                residual13.append(values["13"]["hero_minus_body"])
                residual14.append(values["14"]["hero_minus_body"])
                residual_difference.append(difference)
                patches[name] = dict(hosts=values, residual_13_minus_14=difference)
            def summary(vectors):
                return dict(channel_mean_absolute_codes=[sum(abs(row[c]) for row in vectors) / len(vectors) for c in range(3)],
                            channel_max_absolute_codes=[max(abs(row[c]) for row in vectors) for c in range(3)],
                            mean_absolute_codes=sum(abs(v) for row in vectors for v in row) / (len(vectors) * 3),
                            max_absolute_codes=max(abs(v) for row in vectors for v in row))
            rows.append(dict(phase=phase, source=source, patches=patches,
                             host13_hero_minus_body_patch_mean_residual=summary(residual13),
                             host14_hero_minus_body_patch_mean_residual=summary(residual14),
                             residual_13_minus_14_patch_mean_difference=summary(residual_difference)))
    result = dict(analysis_complete=True, script_sha256=digest(Path(__file__)), hosts={"13": c13, "14": c14},
                  formula="Per patch/channel: Dhost = normalized_mean(hero) - normalized_mean(body); reported cross-host residual = D13 - D14.",
                  units="8-bit encoded sRGB code values /255. Summaries are absolute patch-mean residual statistics, not whole-image pixel MAE, physical light or nits.",
                  binary_provenance="Not independently verified by this script. Recorded hash fields are carried as context; caller must retain build/transfer/signature/section evidence for any same-binary claim.",
                  comparisons=rows,
                  limitations=["No cross-host raw PNG or full-RGB pixel equality is required or asserted. Native 1x/2x frames and sampling differ; no resizing, interpolation, alignment or gray-ramp column fitting is performed.",
                               "Same-host oracle residuals are controls, not proof that OS alone caused cross-host differences. Display profiles, headroom, environment and rasterization remain context.",
                               "Same-image fixed-size snapshot/draw endpoints do not validate coordinator lifecycle, enter/leave, geometry animation, hide/restore, retarget/reversal, High or a full application.",
                               "No equivalence threshold or expected outcome is imposed. Computed zero/nonzero differences do not by themselves establish visual acceptance or a unique cause."])
    destination.mkdir()
    (destination / "comparison.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(dict(analysis_complete=True, output=str(destination), summaries=[
        {k: v for k, v in row.items() if k != "patches"} for row in rows]), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        print(f"Cross-host offline analysis failed: {error}", file=sys.stderr)
        sys.exit(1)
