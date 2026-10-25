# Build-only CI workflow source

Single workflow_dispatch/build job; exact e48 checkout and github.sha harness. Reuses successful macos15/Xcode26.3/SDK26.2/Swift6/Rust1.99/arm64-min13 recipe, Cargo jobs2/incremental0. No cache restore/save, UI/helper/capture, old artifact download or CLI hook.

API agreed with build.py author: prepare SOURCE EVIDENCE, normal original cargo build, always collect SOURCE EVIDENCE after successful prepare. Only environment.txt/harness-inputs.sha256 precede prepare. Root publishes f939 packet as four original texts plus source-SHA256SUMS, build.py/README.build.md and sourceguard5b4a. Tar gallery-film-last-observer.tar.gz contains new Gallery.app+observer-build.json; fresh CLI is checked, not packaged or labelled original. Artifact retention3d; full log excluded.

Only YAML/bash-n and isolated regex/printf checks ran locally. No CI/Git/compiler/artifact execution or real build result. Driver/package integration and independent review remain root's gate before one dispatch.
