# App-loop coordinator native review — CI40110795231

`analyze.py` ran once after root confirmed both hosts and original package were ready. It extracts the complete native plus appended `execution_model` Python gate from harness `be6eb08a91e74d900cdaccc6d8730c81aefb96bc`, workflow SHA `875747591a581fde4b4381482961405ab990cb279a878929a5627adc3791c7af`. Only four literals adapt report path, report OS, receipt OS and binary path; every native/app-loop assertion remains intact. Exact substitutions and gate hashes are in `summary.json`.

Both native and execution-model gates passed. Actual binary `a98bd3d415e98fbd84daa3d9c4bdbe21f2d731b3858b82fa66b20b59255e8d0d` and tar `7a3f4cb660797e3307d22dc73bfed58718123f49bb4245ca7635878d64a6bed8` independently matched root's announced hashes and saved package receipt. The18-member package,10-input source map, two reports/receipts and six original PNG hashes matched;31 unique input files are fingerprinted. Saved strict-signature verification is attributed to root; signing was not rerun.

Each process kept default motion, effective normal flags false, cache/front unchanged, own-window/PID/nonkey/inactive/no-MTK, one actual flight identity, actual frame/progress movement and timer/view retirement. Before/settled retain five equal buffers and scene ROIs. Both weak source references were deallocated in these reports; the gate does not require that value to be true. Front PIDs stayed9292/314; window lifetimes were1.295496/1.617048seconds.

| Host | Armed→capture sample | Progress | Sample uptime gap | Callbacks |
| --- | --- | --- | --- | --- |
| 13 | 8→9 | .237940663→.362234254 | 15.422417ms | 57 |
| 14 | 7→8 | .646607109→.693877248 | 8.734208ms | 49 |

Actual capture-call durations were4.616208/18.100417ms. Both capture progress values remained below.8, so permission to capture beyond.8 was not exercised. Full armed/captured states, capture brackets and complete execution_model are retained. `trigger_state/progress` refer to armed; capture_sample records the next observer callback.

Launch, app-loop entry/actual return, terminal, stop and own-queue applicationDefined wake each occurred once. Both sampler records show `kCFRunLoopDefaultMode`,1/60 interval, depth1, zero reentrant callbacks and zero callbacks after terminal. App-loop durations were1.520211/1.816907seconds; preload47.364167/34.515875ms; terminal-to-return.300833/.217958ms. Callback totals include preload. The invalidated-before-stop Boolean is a source-path flag, not an independent Timer.isValid observation. The terminal wake is not physical input, an extra sample, animation flush or presentation fence.

**Pixel acceptance was not performed.** Adjacent observer callbacks under NSApplication.run and capture-call brackets do not establish presentation synchrony, pixel position, color equality, cause/fix, zero observer effect or full-flight parity. No pixel algorithm, native/UI/compiler/CI run, polling/download or large source/image/binary copy occurred in this analysis.

Reproduce offline from the workspace root into a fresh output directory:

```sh
python3 work/hero-coordinator-app-native-analysis/analyze.py work/native-pq-hero-coordinator-app-ci-40110795231 work/hero-coordinator-app-native-replay
```

The script refuses an existing summary and caps output at128KiB. It needs the pinned local Git commit, existing YAML library and retained original package inputs; later cleanup may require restoring historical binary/tar before rehashing. `provenance.json` separates static preparation from this actual one-time execution; `SHA256SUMS` freezes only small analysis outputs.
