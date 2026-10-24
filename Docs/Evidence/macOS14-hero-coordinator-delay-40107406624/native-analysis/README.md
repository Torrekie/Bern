# Next-sample coordinator native review — CI40107406624

`analyze.py` ran once after root confirmed the inputs were ready. It extracts the final Python native gate from committed workflow `e3999727ec919508402ed1ecc40cc48dc7c7fc4f`, SHA256 `5f0d71da1a07504e0bee49e6a6b8c3a750b10b667d5f97b68b3ad7fa4700bb28`. Only four report-path/expected-OS/binary-path literals change; assertions remain intact. Exact changes and both gate hashes are in `summary.json`.

Both native gates passed. Original binary `fca470c9174bd11d9fc6220fa61643b7ad2338a2bb4bc34e560b3de3cb5c6e23`, tar, source/package hashes, two reports/receipts and six PNG hashes matched. Each process kept default motion, normal flags false, cache/front unchanged, own-window/PID/non-key/inactive/no-MTK, one actual flight identity/timer/movement, and native retirement/settling. Weak source deallocation is false and is not required. Before/settled retain five stable buffers and scene ROIs.

| Host | Armed→capture sample | Progress | Sample uptime gap |
| --- | --- | --- | --- |
| 13 | 9→10 | .278344256→.368317506 | 19.179375 ms |
| 14 | 7→8 | .609194287→.714572322 | 27.410500 ms |

Actual capture-call durations were4.139292/6.810167ms; window lifetimes1.434776/1.951298s and front PIDs9292/333 remained. Full armed/captured logical states and actual shot brackets are retained. `trigger_state/progress` refer to **armed**; use `capture_sample` for the later sample. Both actual capture progress values stayed below.8, so permission to capture beyond.8 was not exercised by these runs.

**Pixel acceptance was not performed.** Logical state, adjacent samples and capture-call bounds do not prove presentation synchrony, pixel position, color equality or an animation fix. No pixel algorithm, UI, compiler or CI was run here; no source/image/binary/archive was copied.

Reproduce offline from the workspace root into a fresh output directory:

```sh
python3 work/hero-coordinator-delay-native-analysis/analyze.py work/native-pq-hero-coordinator-delay-ci-40107406624 work/hero-coordinator-delay-native-replay
```

Requires the pinned local Git commit and existing YAML library. Existing summaries are never overwritten. The script reads current binary/tar inputs, so after root cleanup those historical artifacts cannot be freshly rehashed without restoration. `provenance.json` separates preparation, parent context and this actual execution; `SHA256SUMS` freezes small analysis outputs only.
