# SHA-locked Picture Scene modifier patch

`patch.py` (115 lines) accepts only the exported exact 9dd generated source (95,129 bytes, SHA-256 `1d1da3167d9437b2305df1a39099f01f693b1b674f13cd2e4d88bffec2c52083`). It also checks the complete unique `layout_page` component slice against exporter SHA-256 `e1479772ed383a7e1bd3b4fbf4749146b5601806194c217c797b7cd072527e87` and each complete expression needle exactly once. No source inference or general Swift parser is used.

Usage from the workspace root (the output directory must not exist):

```sh
python3 work/picture-scene-observer-patch/patch.py \
  work/picture-source-export-run/raw/BernGenerated.swift \
  work/picture-scene-observer-patch/candidate
```

The prepared `candidate/` contains an independent generated file, exact unified diff, original byte offsets/expression hashes/insertion strings in `patch-map.json`, and hashes. There are 21 additions: Form after its grouped style, two complete Grids after their original frames, and six complete Columns plus their six Images and six fully styled captions. Labels match the root's specified protocol. Other Sections, FormRows, children, Scene, font, frame and padding expressions remain byte-identical. Removing only the recorded unique insertion strings recovers the complete original source exactly; the input SHA was rechecked unchanged after generation. The helper implementation is intentionally absent and supplied independently.

The candidate SHA-256 is `f152c30b1ed4e3107c7198db2652c536ea0f5cddf81a046ecc9b0fed0ea47c10`; the diff SHA-256 is `4adc088242aa5dfbdefe1c71b275ad5f5310b509810803643c38faa7db18bd23`. Python syntax parsing and the source-only patch application passed. No Swift compilation, UI or CI ran. These source checks do not prove a zero layout/observer effect; an observed card-height change must stop runtime interpretation as specified in the frozen plan.
