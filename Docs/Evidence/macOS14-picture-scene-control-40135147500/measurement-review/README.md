# Fixed-ROI control14 measurement

`measured.py` is75lines. Usage: `python3 -B measured.py ORIGINAL.png SCALE FRESH.json`. It requires a fresh output path in an existing parent, positive integer scale, exactly920×668 window points, PNG and embedded ICC. ROI table, ICC conversion expression, ROI loops and x800 scan loop are AST-identical to the old source; thresholds35/25, exact-color segmentation and >=1pt run filtering are unchanged. There is no resampling or rendering-intent override.

Single actual invocation: `python3 -B work/picture-scene-measurement-review/measured.py work/picture-scene-control14/raw/images-layout-light.png 1 work/picture-scene-measurement-review/control14-measurements.json`, exit0. Script SHA`05b74fd7cbeefdccdd953699e10c7c7e20570887f70a9959bd8411be1f76aae9`; output SHA`cfc592e8358995bd3957d10459ea01aaf35e5a7a219c8c5e175863b0829b3807`. No original legacy script/result was executed or overwritten.

The new full PNG is920×668 at1×; SHA`dfe053e307e033d0a4e583a88d34a4b60f428318f63e1954a500f14bb2016780` exactly matches the recorded old B14 whole PNG. ICC SHA`3d40c076ef474f107eb2c08fa5cebe2546e836500f4029ded5db7de763eb5f55`. All15 ROI results and every retained x800 segment equal old B14.

At x800, first-card border runs are98..<99 and222..<223; HDR border runs321..<322 and467..<468. The complete original PNG was viewed offline and both cards have visible unclipped sides/top/bottom. Together with identical whole-PNG bytes and the old complete-edge records `[161,98,900,223)` / `[161,321,900,468)`, this supports the selected control reproducing125pt/147pt. This is an explicit edge interpretation, not a bbox output from the script or a public native card frame. Fill plateaus99..<222 and322..<467 are not the outer card bounds.

Raw result identifies source9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0, harnessd72cb5f9bcec8a90fa394bca1060ed0f392ba8f3, normal profile/all3 effective flags false, Apple Virtual1×, own PID1853/window24 and920×668 points; English CLI language commands succeeded. Resource decoding is recorded by the old collector; this reviewer did not rehash the app bundle. Root binds the exact existing artifact/assets.

Layout was captured after the legacy0.8s pause with no five-buffer stability chain. This measurement makes no stronger temporal claim. No UI/CI/compilation occurred here. Control→observed geometry still requires the same source/asset/window/language/normal/scale/route bindings and unchanged measured edges; no observed run or observer-effect verdict exists yet.

Read-only input fingerprints:

- `work/images-layout-geometry/measure.py` SHA`a113c13160ab40d73756ffa3ff70ee889987d847ff5daac87cd90821dd98875c`
- `work/images-layout-geometry/measurements.json` SHA`54692eb515663ab13abeddebb253e0db8378c5f388cabf4660d3ac9e04b6786f`
- `work/images-layout-geometry/report.json` SHA`bf167861fa4257fc2299a4d764d45281fe331b5d695d681f7c3ea762310e58ea`
- `work/picture-scene-control14/raw/result.json` SHA`e8315fe48e613ce03dee339261e67b883b4b83e58ccc6eb31ddc5b4bc539aa0c`
- `work/picture-scene-control14/raw/environment.txt` SHA`c564399d81246462f40b042839c1351f75cbe67555b7295d60fa22f4a47f8a65`
