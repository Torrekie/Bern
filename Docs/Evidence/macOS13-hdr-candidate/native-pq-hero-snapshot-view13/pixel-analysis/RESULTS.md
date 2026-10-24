# Stock NSImageView of the actual original hero snapshot — negative candidate

The candidate shows a nonempty atlas in the prescribed named Flight ROI. Replacing this one display path produces only small differences and does not remove the main macOS13/14 color residual. It is not the earlier experiment displaying an original source CGImage: this candidate uses the actual ImageRenderer→NSImage snapshot object, while the named Flight's original draw is suppressed. No conclusion assigns the remaining difference or the small new deltas to rounding, backing storage or any other cause.

All12 raw and ICC-normalized control panes match the frozen static-overlay13 baseline exactly. Against that control, only the two named-flight phase panes change; the other10 panes remain exact. Candidate ROI is root(16,244,320,180)pt / screenshot(32,544,640,360)px, alpha255. Each RGB channel spans0…255; all10 patch interiors and gray ramp were measured. Several patches already share the same white result, so their equal means do not indicate an empty crop. Native scalar records retain the same stock NSImageView, snapshot NSImage and Flight identities across mount/two PNGs/final check, with cleanup success.

## Same-host change

Both phases have the same whole-pane difference:

- Raw profile-encoded RGB MAE **0.10356481481481482**, max1,64851/230400 pixels differ.
- Embedded-ICC→sRGB RGB MAE **0.08673032407407406**, max1,54999/230400 pixels differ.
- Normalized ten-patch mean absolute change0.08229739010988896, maximum channel-mean change0.13598901098901098.
- Gray interior632×80: raw/sRGB MAE0.0943301687763713,max1;13078/50560 pixels differ. Column-mean RGB MAE0.09433016877637153,max0.21250000000000568. Full per-column RGB values are retained in each analyzer's gzip JSON.

The0.086730324 figure describes normalized sRGB, not raw profile RGB. The unchanged original comparison tool only reported raw exactness, so these domains must not be conflated.

## Full ten-color residual against frozen14

The frozen14 PNGs were reanalyzed with byte-identical atlas coordinates/analyzer and the same Pillow12.3.0 / LittleCMS2.19. Every recomputed comparison, per-ROI measurement and ramp-data SHA matches its frozen analysis. Both native pixel sizes retain exact atlas-interior integer coordinates; there is no cross-host rescaling or pixel-equality assertion.

For every patch/channel, Dhost=mean(hero)−mean(body); the table is mean_RGB(|D13−D14|), in encoded sRGB codes(0…255), not nits or whole-image pixel MAE. Full signed RGB vectors and all body/hero/oracle means are in JSON.

| Patch |p0 control|p0 image-view|p1 control|p1 image-view|
|---|---:|---:|---:|---:|
| blue812 | 0.129635989 | 0.218091804 | 0.000400641 | 0.088856456 |
| cool812 | 37.540321658 | 37.647350046 | 37.753806090 | 37.718778617 |
| green812 | 0.120879121 | 0.120879121 | 0.000000000 | 0.000000000 |
| pastel812 | 0.496594551 | 0.603050595 | 0.461624313 | 0.494763049 |
| red812 | 5.677283654 | 5.652529762 | 5.635960394 | 5.611206502 |
| warm406 | 6.023695055 | 6.130151099 | 6.132554945 | 6.167582418 |
| warm812 | 1.963770604 | 1.995478480 | 2.004292582 | 1.964571886 |
| white203 | 0.005351419 | 0.110319368 | 0.106484661 | 0.003519918 |
| white812 | 0.042324863 | 0.068595467 | 0.148208562 | 0.043297848 |
| yellow812 | 0.108774038 | 0.178428342 | 0.000658196 | 0.068996108 |

Across all30 patch/channel values, p0 absolute-residual mean changes **5.2108630952380945→5.27248740842491** (4 become smaller,19 larger,7 unchanged). p1 changes **5.224399038461538→5.21615728021978** (13 smaller,10 larger,7 unchanged). The maxima become larger in both phases: **112.61632898351648→112.72433035714288** and **113.04833447802197→113.15633585164836**. Custom-source residuals remain unchanged. Small improvements in one aggregate/phase do not repair the major residual or establish overall equivalence. Named13 hero-vs-body full-pane normalized MAE changes18.420225694444444→18.437042824074073, with max165 in both.

## Gray ramp

The same-host whole-ramp hero−body mean RGB changes from [15.309493670886042,15.31408227848101,15.303837025316483] to [15.403797468354412,15.402768987341744,15.403837025316449]. Against14, its aggregate D13−D14 changes:

- p0: [0.0049050632911189496,0.0022943037974698655,0.0029667721519217594]→[0.09920886075948943,0.09098101265820446,0.10296677215188765].
- p1: [−0.08694620253163521,−0.08631329113921993,−0.09869462025312714]→[0.007357594936735268,0.00237341772151467,0.001305379746838753].

These are native-resolution whole-ramp averages, not paired cross-host columns:13 has632 columns,14 has316. Per-host min/max/mean and every native column are retained. No curve fitting, column registration, color adjustment or threshold selection is used.

## Evidence boundary

One offline orchestration ran three unchanged host-analyzer invocations (control13,candidate13,reference14), two unchanged cross-host residual comparisons, and same-host crop/stat checks. Original reports/PNGs/archives were not modified or copied; no derived images, native executable, compile, UI or CI operation was added. Input hash list, versions, commands, logs and scripts are preserved. Recorded native/cache/normal/foreground gates are not independent reruns of runtime objects. This static opaque/up/same-aspect/corner0 endpoint result does not cover real-flight lifecycle, general alpha/orientation, High, physical HDR or full-app equivalence.
