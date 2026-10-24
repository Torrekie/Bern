# Clean e48 Gallery: prepared macOS 13 three-scenario check

Build 40070407306 completed successfully (parent-confirmed job 120802424623). App source is e48fff46b3a92a28465ad74295bd273a9d69af7d, distinct from build harness 25e18cbc7cd760c1c399042f1d7364c3d755a9dc and later documentation commits. The build used SDK 26.2, Swift 6.2.4, ARM64, min13 and real SwiftUI-modern. Source Style is 3912ecdb… and existing 9dd Runtime is 255bacb4…; diagnostic logger/nativeSnapshot code is absent.

Artifact 12550744117 was downloaded once. Its ZIP digest matched GitHub metadata; ZIP/TAR paths, member types, top-level names and package SHA were checked before extraction. Exact app and CLI remain in build/exact for later delivery. Only redundant ZIP/TAR compression layers were removed after recording their hashes. Existing outputs/macOS13 delivery was untouched.

The local run copy uses unique bundleID dev.bern.gallery.filmclean.9697c3c5499d42df80b9bdfd0f43f986 and a local ad-hoc signature. All Mach-O section records/hashes and normalized signature-storage payload match the exact executable. The full signed executable hash differs. This is the same built code with a different bundle/signature environment, not byte-identical signed apps.

The parent may execute RUN-BY-PARENT.sh once. It compiles the unchanged collector 3f434cf / SHA79da4a84… ahead of time, then runs inactive13, scenario=all, followup=none and trace explicitly unset. Three fresh processes exercise Inspector immediate-close→Film, wait-static-close→Film and direct-Film. It never activates/restores focus or changes preferences, history or TCC. Normal accessibility flags are checked without mutation. The startup gate has a 15-second overall deadline plus an 8-second per-CLI-call cap; it does not promise every cold call the full 15 seconds.

This preparation has not launched the app or CLI. CI success and offline signature/hash/architecture/minOS checks do not constitute actual runtime acceptance. Any future successful run must retain raw PNG/AX/CLI results and distinguish inactive13/2x from active14/1x references. Last/resize followups and physical gestures are outside this run.

On exit, only this observer executable/module cache is removed and a cleanup receipt is written. Exact artifact and isolated app remain until later ownership-scoped cleanup. A pre-existing output directory blocks re-execution, preserving partial evidence.
