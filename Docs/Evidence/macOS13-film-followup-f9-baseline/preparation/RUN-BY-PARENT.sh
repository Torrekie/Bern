#!/bin/bash
# Prepared only. The parent owns the one authorized UI execution.
set -euo pipefail
run_root="$(cd "$(dirname "$0")" && pwd)"
app_root="$run_root/isolated/Gallery.app"
cli="$run_root/bin/gallery"
result_root="$run_root/direct-last-resize"
scratch_root="$run_root/observer-work"
test ! -e "$result_root"
test ! -e "$scratch_root"
test "$(sw_vers -productVersion | cut -d. -f1)" = 13
test "$(uname -m)" = arm64
printf '%s  %s\n' f8dacbfe1df00c68bad4465516c69b4c975f8ea1ace17cd0f047977e22409000 "$app_root/Contents/MacOS/Gallery" | shasum -a 256 -c -
printf '%s  %s\n' 31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5 "$cli" | shasum -a 256 -c -
printf '%s  %s\n' 79da4a84909a07a6d975cf7606a0cae6d4c22c1c1979a3fdbb0ce0e29aeb0755 "$run_root/gallery-film-probe.swift" | shasum -a 256 -c -
test "$(plutil -extract CFBundleIdentifier raw -o - "$app_root/Contents/Info.plist")" = dev.bern.gallery.filmbaseline.925b37e2b4f944a3bf7be7394e02942d
codesign --verify --deep --strict "$app_root"
codesign --verify --strict "$cli"
mkdir -p "$result_root" "$scratch_root"
trap 'status=$?; python3 "$run_root/cleanup-observer.py" "$scratch_root" "$result_root" "$status"; exit "$status"' EXIT
cp "$run_root/gallery-film-probe.swift" "$run_root/provenance.json" "$run_root/validation.json" "$run_root/startup-gate-validation.json" "$run_root/README.md" "$run_root/RUN-BY-PARENT.sh" "$run_root/cleanup-observer.py" "$result_root/"
{
    sw_vers
    uname -m
    xcrun swiftc -version
    xcrun --show-sdk-version
    shasum -a 256 "$app_root/Contents/MacOS/Gallery" "$cli" "$run_root/gallery-film-probe.swift"
} > "$result_root/runtime-environment.txt" 2>&1
xcrun swiftc -swift-version 5 -target arm64-apple-macos13.0 -module-cache-path "$scratch_root/modules" "$run_root/gallery-film-probe.swift" -o "$scratch_root/FilmProbe" > "$result_root/observer-build.log" 2>&1
export BERN_SOURCE_SHA=f9e08b1d55bed4b9d880b19934abe48281057bb3
export GITHUB_SHA=3f434cf0313d5657a136b1f98d0ac1293b60f169
export FILM_VARIANT=port
export FILM_BUILD_RUN=39991406873
export BERN_FILM_EXPECTED_OS=13
export BERN_FILM_OBSERVATION=inactive13
export BERN_FILM_SCENARIO=direct
export BERN_FILM_FOLLOWUP=last-resize
# The exact f9 build has no diagnostic logger. Do not request or synthesize a trace.
unset BERN_SCROLL_TRACE_DIR
"$scratch_root/FilmProbe" "$app_root" "$cli" "$result_root" > "$result_root/observer.log" 2>&1
