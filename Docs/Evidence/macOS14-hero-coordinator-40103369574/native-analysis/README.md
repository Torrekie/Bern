# Private coordinator native-gate review — CI40103369574

Both existing reports passed the reviewed gate with only paths/expected OS changed. Receipts and the current binary match SHA256 `5739a0405bf78c04e71a46116c99fd48a7fa7b0b659bf8e97744ee3982ecea36`; archive, 18 package members and source-map hashes also matched. Signature status is the hashed root receipt, without another signing command.

Normal flags were false, cache unchanged, front restored (13:9292;14:309), and captures were own-window/PID, non-key/inactive and no-MTK. Each run had one real transition and one observed flight view identity, live timer/frame/progress changes, source no longer attached, and final flight/timer/temporary-view counts zero. Weak source deallocation remained false on both hosts and was not required. There were37/20 live samples on13/14. Before/settled had five stable buffers and declared scene ROIs; all six PNG file hashes matched. Window lifetimes were1.546953/2.044402 seconds.

| Host | Mid trigger progress | Recorded logical flight rect in root (x,y) |
| --- | --- | --- |
| 13 | 0.2872209362 | 112.506235,87.188606 |
| 14 | 0.6920757961 | 248.537468,176.256675 |

Trigger and screenshot-bracket scalar states both recorded a live flight/timer in these runs. Exact original states, capture-call monotonic bounds and live-trace endpoints remain in `summary.json`. These timestamps are not presentation timestamps and do not establish pixel/state synchrony.

**Native pass is not pixel pass.** Root reported the14 mid image near the source despite its logical frame and13 movement behind its logical progress. This analysis did not inspect/measure those pixels or infer a rendering-lag cause. Before/settled visibility and crosshost color equality remain unaccepted here; `pixel_acceptance` stays not performed. No full UI/visual/color/lifecycle parity is claimed.

Only small JSON/README/hash outputs were created. No original input, repository, UI, compiler or CI was changed/executed, no agents were spawned, and no source/PNG/archive/binary was copied. Exact input paths/hashes are recorded for archival.
