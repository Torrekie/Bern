# Current product Standard color check on macOS13

This isolated fixture loads the two retained source atlases through normal ImageIO decode, then uses the current product HDR helper unchanged with Standard intent. Its third pane is native macOS13 SwiftUI Image for the named-PQ source. The extracted helper, Picture declaration and CICP classifier are byte-for-byte source copies; `extraction.json` records their hashes and the full Runtime hash. The fixture supplies only the minimal Picture namespace and three-pane UI, as in the earlier `macOS13-hdr/typecheck-current.swift` fixture.

Both product Standard images are pixel-identical after ICC->sRGB conversion, including all ten patches and the gray ramp: normalizing this valid CICP9/16/0/1 source adds no color difference relative to the product's named-PQ path.

**Product Standard is not pixel-equivalent to native macOS13 namedPQ.** Ten patch RGB means have MAE1.086999 and max4.758585 code values/255. The632 interior gray-ramp column means have MAE0.241660 and max0.8125. The retained validation reports each patch separately. This check identifies a remaining color-pipeline difference; it does not assign its cause or modify the product.

The unique own window was nonkey/inactive and visible for0.847seconds, with four consecutive identical canonical WindowServer buffers. Both product views requested no EDR; actual current headroom1/potential2. No activation or global key was used. Foreground was QQ PID75891 before, during captures and after. Both Metal views were stopped, notifications removed and the own view tree detached before exit. Executable/module cache were removed after hashing.

The output PNG is unmodified. `analyze.py` converts its ICC to sRGB using Pillow/LittleCMS perceptual intent0, then measures fixed interiors112x104 and632 ramp columns over80 rows; no fitting/rescaling. RGB values are encoded screenshot code values, not physical light. `ramp-columns.npz` retains all measured column RGB arrays.

This is a local Swift5.9.2/SDK14.2 target13 fixture for the exact Runtime matching commit e06e080665a0c774843762ca132edf31bcb82d77. It is not a full Bern application, macOS14 result, High equivalence, software-fallback test, or arbitrary ICC/metadata/HLG/alpha/EXIF acceptance. Source atlases remain in sibling `color-probe13/`; no source image is rewritten.
