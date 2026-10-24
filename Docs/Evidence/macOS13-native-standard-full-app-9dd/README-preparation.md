# Exact 9dd Showcase build prepared for root-owned smoke

Source `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`, successful build run40066468884; artifact12549219297 `macos13-showcase`. The run's head SHA is the separate harness commit, not the source commit. `build/environment.txt` records the exact requested source, and `run-api.json`/`artifacts-api.json` preserve the retrieved GitHub records.

The transfer archive was SHA256-verified (`fb5fd66e8247d1adada07411cb8368de716cc8e251f6ecf70968678b3d74662b`), then safely extracted to `exact/`: only 25 unique relative regular-file/directory members, no links or special members, 5,113,490 regular-file bytes. `archive-verification.json` retains all16 extracted file hashes. The verified transfer tar was then removed; its supplied checksum and all build metadata remain.

`exact/` is unchanged from the archive. `app/Showcase.app` is a separate temporary copy, with only its CFBundleIdentifier changed to `dev.bern.probe.showcase.standard9dd.r40066468884` and a local ad-hoc signature regenerated. No original entitlements were present. The only changed copy files are Info.plist, the embedded GUI signature, and CodeResources. The CLI copy is byte-identical to the original. Both original and copied GUI/CLI pass strict codesign verification. All40 GUI and14 CLI Mach-O section descriptors and file-backed section SHA256 values match before/after signing; zerofill sections are identified explicitly rather than hashed as file data. `binary-verification.json` records every section and full binary hash.

Both executables are thin arm64 with LC_BUILD_VERSION macOS/min13.0.0/sdk26.2.0. The build manifest specifies `swiftui-modern-macos`, release/in-process/native colors and min13.0; bundle Info.plist also specifies min13.0.

Root can pass `execution-plan.json` to the existing `work/check-latest-apps.py`. At preparation time `work/focus-helper` did not exist; this precondition is explicitly recorded in `preparation.json`. No helper was created or executed. No GUI or CLI executable, smoke script, activation, preference/domain/history change, or UI operation occurred in this preparation. Root owns any later execution and acceptance.

Original GUI SHA256 `cc267abcafeec30112c2796b3c0ea7699a6836a0f09a1caa73f66ea48bfa1c1b`; signed temporary GUI `c7f9b6d2f4acbd254a16038d367f0a333b1e85da371a3fcb1d024cfbbaaa06f4`; original/copied CLI `963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170`.
