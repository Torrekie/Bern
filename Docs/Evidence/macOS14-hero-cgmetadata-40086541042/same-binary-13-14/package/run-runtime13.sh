#!/bin/bash
# Run the already packaged binary on13; never rebuild or change permissions/preferences.
set -euo pipefail
probe_dir="$(cd "$(dirname "$0")" && pwd)"
test "$#" = 1
test "$(sw_vers -productVersion | cut -d. -f1)" = 13
test "$(uname -m)" = arm64
test ! -e "$1"
mkdir -p "$1"
output="$(cd "$1" && pwd)"
{
  printf 'expected_os_major=13\n'
  sw_vers
  uname -m
  shasum -a 256 "$probe_dir/HeroSnapshotProbe"
} > "$output/environment.txt" 2>&1
(cd "$probe_dir" && shasum -a 256 -c SHA256SUMS) > "$output/package-verification.txt" 2>&1
codesign --verify --strict "$probe_dir/HeroSnapshotProbe" > "$output/signature-verification.txt" 2>&1
cp "$probe_dir/build/environment.txt" "$output/build-environment.txt"
cp "$probe_dir/build/binary.txt" "$output/build-binary.txt"
BERN_HERO_EXPECT_OS=13 "$probe_dir/HeroSnapshotProbe" \
  "$probe_dir/assets/source-named-pq.png" "$probe_dir/assets/source-ffb-icc.png" \
  "$output" > "$output/runtime.log" 2>&1
