#!/bin/bash
set -euo pipefail
fixture_dir="$(cd "$(dirname "$0")" && pwd)"
test ! -e "$fixture_dir/HeroColorModeProbe"
python3 -B "$fixture_dir/verify_sources.py"
{
  sw_vers
  uname -m
  xcode-select -p
  xcrun --sdk macosx --show-sdk-version
  xcrun swiftc -version
} > "$fixture_dir/build-environment.txt" 2>&1
xcrun swiftc -O -parse-as-library -swift-version 5 -j 2 \
  -target arm64-apple-macos13.0 -module-cache-path "$fixture_dir/modules" \
  "$fixture_dir/Dependencies.swift" "$fixture_dir/ProductImage.swift" \
  "$fixture_dir/ProductStyle.swift" "$fixture_dir/ProductHero.swift" \
  -framework AppKit -framework SwiftUI -framework MetalKit -framework CoreImage \
  -framework ColorSync -framework ImageIO -framework CryptoKit \
  -o "$fixture_dir/HeroColorModeProbe" > "$fixture_dir/build.log" 2>&1
python3 -B "$fixture_dir/fingerprint.py"
