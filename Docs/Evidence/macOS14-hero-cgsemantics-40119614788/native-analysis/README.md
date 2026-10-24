# CGImage drawing-semantics native review — CI40119614788

All four original complete native/ICC/semantics gates passed independently:13off/on and14off/on. The reviewed workflow is SHA `8c5acfad83bf97255f10d73ba3dd2836350b53ecf0396dd65eec3e29923ccdcb`; source/harness identities are3c137f307576a44ffc58543def3cfec5b310c9d7 /9989b904fe3bd2018d53ce91eec08bc52573fcc6. The root-extracted gate is reused without assertion changes. Two logical literals adapt argv report path/mode/major and expected major; its saved file additionally has one terminal LF. That file-ending serialization difference is explicitly reconstructed to match adapted SHA66302614538dc90f40ff1f1cb5ccd91137c2489416d0f639461925d5e7c6ea00. The initial checker stopped at this extraction byte check before executing its gates; it was not a runtime failure. No report or guard was changed.

Actual original signed binary `68974a3fe0ae28c23ef47de9657fbc6d34287bb36f50d12d6ac69d52b3eee334`, tar2c1151e83775c0a214f3ff36e33f1160883175c8709a6a86456072c52053b014,29 package members,21 source entries and exact concatenated assembly were independently hashed before root deleted exe/tar. Saved arm64/min13/SDK26.2/strict-signature evidence passed inspection; this reviewer did not rerun signing or a native command. `package-verification.json` preserves those actual pre-cleanup hashes. Other report/raw/PNG inputs were hashed during the current offline pass;70 unique fingerprints carry a stage label in summary and are listed in INPUT-SHA256SUMS.

Both named/custom keys on both hosts report rendering_intent_raw0, is_mask=false, should_interpolate=true, RGB model1/components3 and decode_present=false/count0/values[]/bits[]/values_read0. These observed fields match cross-host per key. Successful16-field schema, original provider-start→observation→release timing bounds, two on records and no off records pass. Decode-present/signed-zero cases were not observed. Per-record observation durations were:

| Process | Key | Getter observation μs |
| --- | --- | --- |
| 13-on | named | 8.416711 |
| 13-on | custom | 7.624971 |
| 14-on | named | 43.333333 |
| 14-on | custom | 15.000000 |

Full observed/provider/release uptimes and derived gaps are retained. On provider-copy/retained-peak counts remain2, off0; fixture retained count after export0. These counters concern the original provider export, not a new provider capture here, and do not prove deallocation or general zero observer effect.

Four new raw exports independently match the old float cohort same-host/same-key SHA and length:13 named edc1c938…a6a2469/custom314b9001…d36e67c, each1,843,200B;14 both807393b1…0201962, each460,800B. Eight original PNG file hashes/IHDR dimensions, owner PID/window, fixed/nonkey/inactive geometry, five reported equal buffers, normal flags, equal cache ledger/front, no MTK and manager flight/timer0 checks pass. Front PIDs remain9292 on13 and316 on14. Pixel-control JSONs from root were only fingerprinted; their algorithms were not repeated.

PNG/raw files were read as bytes for hashes only. WindowServer raw-buffer five-equal hashes are checked for report consistency, without recapture or pixel decoding. No clamp, conversion, display analysis, provider API, UI/native/compiler/CI run, raw copy or product/source edit occurred. These observations do not establish rendered-context/storage equivalence, a visible residual's unique cause, general zero observer effect or UI/full-flight acceptance.

`check-package.py` requires the original binary/tar to reproduce the pre-cleanup stage. With its saved package verification and retained runtime/raw files, reproduce the current pass into a fresh output directory containing a copy of that small package-verification.json:

```sh
python3 work/hero-cgsemantics-native-analysis/analyze.py work/native-pq-hero-cgsemantics-ci-40119614788 NEW_OUTPUT_DIRECTORY
```

The script refuses an existing summary. No large input is copied into this review directory.
