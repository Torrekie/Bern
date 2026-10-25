# Single native search chain, exact delivered 9dd

Use the fresh private copy of the complete 9dd Showcase, with root's existing
PID/kernel-start ownership, foreground restoration and bounded cleanup guards.
Do not run the complete v2 collector: its Controls/Buttons/Inputs actions are
not prerequisites. This preparation ran no App, UI, state-changing CLI or build.
Only the delivered CLI's `--help` was executed (exit 0).

CLI: `outputs/macOS13/bin/showcase`, SHA256
`963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170`.
The old work/exact CLI path has been archived and no longer exists.

## Smallest preparation for root

Launch the private executable as v2 does: a fresh private 0700 `BERN_IPC_DIR`,
`BERN_APPEARANCE=light`, no `BERN_SNAPSHOT_DIR`, arguments
`-AppleLanguages '(en)' -AppleLocale en_US`. Pass that same IPC environment to
every CLI command. Require normal's three accessibility flags false without
writing user settings. Retain original front process and exact own PID identity.

```sh
"$CLI" sessions
"$CLI" --session "$SID" window list
"$CLI" --session "$SID" ui set-language --language en
"$CLI" --session "$SID" window resize --window "$MAIN" --width 920 --height 668
"$CLI" --session "$SID" ui inspect
```

Startup: within the inherited 18 s cap, require exactly one private session
(`session_id`), one window with `kind == "main"` (`window` gives MAIN), and one
visible normal-level own-PID native window. Session registration alone is not
readiness; existing startup evidence has sessions with `windows: []` and a
temporarily empty window list. Preserve per-command 8 s bounds and .15 s startup
polling; no full-route sleep/prefix is required. Bring only that verified app
front before root's native click, using existing restoration/cleanup guards.

The real generated MainDraft defaults are **Text**, query `""`; Controls was
selected by the old collector, not the product default. Inspect must show one
enabled `main_window.pages` / role `sidebar` / value `Text`, and one enabled
`main_window.sidebar_search` / role `search` / value `""`, both for MAIN.
If the page is not Text, select only Text and verify its value before input:

```sh
"$CLI" --session "$SID" ui select --target main_window.pages --option Text
```

## One native input and observation

Root performs native click on the visible sidebar search and one Unicode `!`
event. Do not substitute `ui edit`, `ui focus`, `ui submit`, Enter, state writes
or the direct `search-library` query. Read `ui inspect` until the same search row
has value exactly `!` while page remains Text. Inherit .12 s polling / 8 s cap;
if it fails, retain the actual result and stop without a CLI correction.

This value is a generated-binding observation of MainDraft.query, not a direct
memory read: BernGenerated.swift:602–609 defines session0/field1, and :869 binds
the native search to its getter/setter. CLI `state` is documented engine state;
help exposes no separate generic MainDraft getter.

Only then mount Library once (root can click its native row, or use the existing
sidebar binding), without ever visiting it earlier:

```sh
"$CLI" --session "$SID" ui select --target main_window.pages --option Library
"$CLI" --session "$SID" ui inspect
```

Require `main_window.pages.value == "Library"`, search value `!`, and one enabled
`library_page.library_results` / role `query` for MAIN. It may first be
`loading v1`; wait within 8 s for `failed v1 invalid_search:` and no trailing
retained-row count `(N)`. Do not Retry, clear, or recover in this single chain.
The first Library mount uses query6 with MainDraft.query as its actual parameter
(:1424–1428). Existing native first-mount output is exactly:
`failed v1 invalid_search: search text cannot start with \`!\`; search operators are not supported`.

## Evidence and limits

Original generated source: 95129 B / `1d1da316…c52083`; MainDraft defaults :590,602;
real sidebar/detail shape :842–895. v2 Collector: `aa722884…1a60d8`, startup
:376–429, single query preparation :296–306. Existing capture-A stdout020 shows
Text/empty search, 035 shows Text/`!`, 038 loading v1 and 039 failed v1. Those
old writes used CLI and prove only command/field/schema, not native input.
Fresh private launch plus no earlier Library mount is essential: editing an
already-ready Query can retain prior rows. A successful Unicode chain still
does not establish all keyboard, IME, search or full-UI acceptance.
