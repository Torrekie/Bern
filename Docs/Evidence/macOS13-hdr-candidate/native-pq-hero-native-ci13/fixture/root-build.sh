#!/bin/bash
set -euo pipefail
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
fixture_dir="$(cd "$(dirname "$0")" && pwd)"
module_cache="$fixture_dir/../native-pq-hero-colormode/modules"
test -d "$module_cache"
test ! -e "$fixture_dir/HeroNativeCIProbe"
python3 -B "$fixture_dir/verify_sources.py"
{
  sw_vers
  uname -m
  xcodebuild -version
  xcrun --sdk macosx --show-sdk-version
  xcrun swiftc -version
  printf 'module_cache=%s\n' "$module_cache"
} > "$fixture_dir/build-environment.txt" 2>&1
xcrun swiftc -O -parse-as-library -swift-version 5 -j 2 \
  -target arm64-apple-macos13.0 -module-cache-path "$module_cache" \
  "$fixture_dir/Dependencies.swift" "$fixture_dir/ProductImage.swift" \
  "$fixture_dir/ProductStyle.swift" "$fixture_dir/ProductHero.swift" \
  -framework AppKit -framework SwiftUI -framework MetalKit -framework CoreImage \
  -framework ColorSync -framework ImageIO -framework CryptoKit \
  -o "$fixture_dir/HeroNativeCIProbe" > "$fixture_dir/build.log" 2>&1
python3 -B "$fixture_dir/fingerprint.py"
