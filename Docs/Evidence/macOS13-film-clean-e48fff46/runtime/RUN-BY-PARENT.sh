#!/bin/bash
# Prepared only. The parent owns the one authorized UI execution.
set -euo pipefail
run_root="$(cd "$(dirname "$0")" && pwd)"
build_root="$run_root/../build"
app_root="$run_root/isolated/Gallery.app"
cli="$build_root/exact/bin/gallery"
result_root="$run_root/all-inactive13"
scratch_root="$run_root/observer-work"
test ! -e "$result_root"
test ! -e "$scratch_root"
test "$(sw_vers -productVersion | cut -d. -f1)" = 13
test "$(uname -m)" = arm64
printf '%s  %s\n' d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c "$build_root/exact/Gallery.app/Contents/MacOS/Gallery" | shasum -a 256 -c -
printf '%s  %s\n' 6248546901e8f2f3341d30e9d07b0af867052155e3845a046575f72aa133db5d "$app_root/Contents/MacOS/Gallery" | shasum -a 256 -c -
printf '%s  %s\n' 31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5 "$cli" | shasum -a 256 -c -
printf '%s  %s\n' 79da4a84909a07a6d975cf7606a0cae6d4c22c1c1979a3fdbb0ce0e29aeb0755 "$run_root/gallery-film-probe.swift" | shasum -a 256 -c -
test "$(plutil -extract CFBundleIdentifier raw -o - "$app_root/Contents/Info.plist")" = dev.bern.gallery.filmclean.9697c3c5499d42df80b9bdfd0f43f986
codesign --verify --deep --strict "$build_root/exact/Gallery.app"
codesign --verify --deep --strict "$app_root"
codesign --verify --strict "$cli"
mkdir -p "$result_root" "$scratch_root"
trap 'status=$?; python3 "$run_root/cleanup-observer.py" "$scratch_root" "$result_root" "$status"; exit "$status"' EXIT
cp "$run_root/gallery-film-probe.swift" "$run_root/isolation-provenance.json" "$run_root/validation.json" "$run_root/startup-gate-validation.json" "$run_root/README.md" "$run_root/RUN-BY-PARENT.sh" "$run_root/cleanup-observer.py" "$build_root/provenance.json" "$build_root/ci-confirmation.json" "$build_root/artifact.json" "$build_root/build.json" "$build_root/gallery.tar.gz.sha256" "$result_root/"
cp "$build_root/environment.txt" "$result_root/build-environment.txt"
cp "$build_root/binary.txt" "$result_root/build-binary.txt"
{
    sw_vers
    uname -m
    xcrun swiftc -version
    xcrun --show-sdk-version
    shasum -a 256 "$app_root/Contents/MacOS/Gallery" "$cli" "$run_root/gallery-film-probe.swift"
} > "$result_root/runtime-environment.txt" 2>&1
xcrun swiftc -swift-version 5 -target arm64-apple-macos13.0 -module-cache-path "$scratch_root/modules" "$run_root/gallery-film-probe.swift" -o "$scratch_root/FilmProbe" > "$result_root/observer-build.log" 2>&1
export BERN_SOURCE_SHA=e48fff46b3a92a28465ad74295bd273a9d69af7d
export GITHUB_SHA=3f434cf0313d5657a136b1f98d0ac1293b60f169
export FILM_VARIANT=port
export FILM_BUILD_RUN=40070407306
export BERN_FILM_EXPECTED_OS=13
export BERN_FILM_OBSERVATION=inactive13
export BERN_FILM_SCENARIO=all
export BERN_FILM_FOLLOWUP=none
# Clean production code has no logger. Never wait for a diagnostic trace.
unset BERN_SCROLL_TRACE_DIR
"$scratch_root/FilmProbe" "$app_root" "$cli" "$result_root" > "$result_root/observer.log" 2>&1
