#!/bin/bash
set -euo pipefail
fixture_dir="$(cd "$(dirname "$0")" && pwd)"
python3 "$fixture_dir/compose.py"
xcrun swiftc -O -parse-as-library -swift-version 5 -j 2 \
  -target arm64-apple-macos13.0 -module-cache-path "$fixture_dir/modules" \
  "$fixture_dir/Dependencies.swift" "$fixture_dir/ProductImage.swift" \
  "$fixture_dir/ProductStyle.swift" "$fixture_dir/ProductHero.swift" \
  -framework AppKit -framework SwiftUI -framework MetalKit -framework CoreImage \
  -framework ColorSync -framework ImageIO -framework CryptoKit \
  -o "$fixture_dir/HeroBaselineProbe" > "$fixture_dir/build.log" 2>&1
