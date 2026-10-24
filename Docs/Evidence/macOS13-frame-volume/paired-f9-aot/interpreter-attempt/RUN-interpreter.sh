#!/bin/bash
# Root-owned single attempt. Preparing this file does not execute any UI.
set -euo pipefail
probe_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$probe_dir"
test "$(sw_vers -productVersion | cut -d. -f1)" = 13
test "$(uname -m)" = arm64
test ! -e "$probe_dir/run"
shasum -a 256 -c APP-SHA256SUMS
codesign --verify --deep --strict "$probe_dir/isolated/Gallery.app"
codesign --verify --strict "$probe_dir/isolated/bin/gallery"
mkdir "$probe_dir/run"
probe_cache="$probe_dir/runtime-module-cache"
test ! -e "$probe_cache"
mkdir "$probe_cache"
trap 'rm -rf -- "$probe_cache"' EXIT
# The observer saves immediate original-front PID, permissions, deadline and
# source identity before launching Gallery. Every activation request is logged.
# Existing authorization only; preflight failure never requests TCC changes.
env -u CI -u GITHUB_ACTIONS -u BERN_SNAPSHOT_DIR -u BERN_SCROLL_TRACE_DIR -u BERN_MOTION \
    BERN_FRAME_LOCAL_EVENTS=own-pid-active13 \
    /usr/bin/xcrun swift -swift-version 5 -module-cache-path "$probe_cache" \
    "$probe_dir/gallery-frame-reference.swift" \
    "$probe_dir/isolated/Gallery.app" "$probe_dir/isolated/bin/gallery" \
    "$probe_dir/run" 13 C13 f9e08b1d55bed4b9d880b19934abe48281057bb3 \
    2>&1 | tee "$probe_dir/run/observer.log"
