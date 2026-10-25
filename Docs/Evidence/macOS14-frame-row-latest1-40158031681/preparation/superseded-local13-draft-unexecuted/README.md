# Local13 Frame ledger — stopped draft

**Frozen pending draft; do not execute prepare-copies.py --prepare or run-local13.py --run.** Root reported CI40155522534 built successfully and macOS14 control succeeded, but observer ledger hit byte_limit:35 complete placements in172ms,63,828B retained; truncated data is invalid. The macOS14 gate prerequisite failed, so no local13 run is authorized by this draft. Root is revising the protocol to a single latest complete slot without raising the byte cap; that revision is not implemented here.

No compiler/tests, application copies/signing, helper/product processes, UI, CI or Git mutation were run by this preparation. All files are regular source/text. Prior collector-v2 and its aliased historical source were read only, never executed. No payload or cache cleanup is needed from this preparation.

Current files:

- FocusGuard.swift is the existing kernel-start guard with only Showcase→Gallery spelling, public dev.bern.gallery rejection and narrower dev.bern.frame13. private prefix. Its kernel identity/restore-before-stop lifecycle is unchanged.
- FrameClosed.swift is the local-only cleanup adapter of exact dcbd5405f31e0797937049feed74c4d54d7136da602636077085a856b2f2cd3d. Only the final run() defer changes; all collection/media/capture/ledger prefix and do-body bytes remain original. It consumes the external driver ownership.json, invokes the independent guard, and leaves a child alive on missing/mismatched handoff. adapter-proof.json records the byte boundary proof. This is a different helper source/binary from macOS14, while the two future local13 cohorts would share this one adapter binary.
- prepare-copies.py drafts exact control/observer private CFIDs with only Info.plist/signature changes. It copies the reviewed Mach-O section/normalized non-signature logic as source, adapting only the Gallery basename assertion. Control GUI d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c and CLI31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5 are fixed; observer hashes come from an actual supplied observer-build.json and its explicit expected SHA, never guessed.
- run-local13.py drafts one cohort using supplied compiled helper hashes and the real14 PixelGate plus bound a/b report hashes/GUI identities. It precreates OUTPUT/ledger for observer, supplies own-pid-active13 outside CI, and independently checks libproc parent/path/kernel start before writing ownership. It reuses the existing collector-only freeze / guard restore / exact child fallback ordering. It does not call helper binaries during preparation.

Pending before any execution:

1. Rebase the local cleanup-only adapter on the new frozen collector protocol, proving exact prefix/body preservation again; update the driver source lock accordingly. Compile receipts and actual binaries do not exist here.
2. Review and implement the already-identified fail-closed tightening: the final prefs/IPC cleanup must require successful exact-child cleanup, missing exact IPC receipt on timeout cannot count as verified IPC cleanup, and the collector's captured original-front identity must be correlated with the outer kernel receipt before adapter cleanup. These points were identified after the first readable draft and intentionally remain unmodified at root's stop instruction.
3. Tighten prepare output/input non-overlap in both directions, then repeat AST/source review; current code checks freshness and ancestor overlap only. No execution of this draft is a substitute for that review.
4. Supply a real passing14 gate, actual downloaded observer manifest and root-reviewed compiled adapter/guard. Current failed/truncated14 result cannot satisfy the gate. Shared product code is verified through all Mach-O sections and signature-storage-size-normalized bytes after private signing; whole GUI bytes are expected to differ.

Root owns the next protocol/review/cleanup decision. This frozen directory is neither a successful13 acquisition nor a claim of complete cleanup safety or visual acceptance.
