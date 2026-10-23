# Native macOS13 public SDR components

This independent follow-up to `standard-color-e06/` tests two public components without product changes. One named-PQ CGImage is normally decoded by ImageIO, copied to the named BT.2100 PQ color space with byte-identical provider data, then shown through NSImageView, an8bit sRGB CGContext->SwiftUI Image, and direct native SwiftUI Image.

At current headroom1/potential2, **NSImageView equals direct SwiftUI in every640x360 image RGB pixel**, both in the original screenshot profile and after ICC->sRGB conversion. All ten patch means and632 gray-ramp column means have zero difference. CGContext8bit sRGB differs: patch MAE0.917777/max5.059409 codes/255; ramp MAE0.257338/max0.75. The retained report, validation, one raw screenshot and full column arrays preserve the comparison.

NSImage's logical size is320x180points on this2x display. The actual NSImageView native frame/bounds/image size are asserted320x180; all three images are displayed at640x360 physical pixels. An earlier fixture attempt used640x360 logical points and clipped the NSImageView; its invalid NSImageView comparisons were rejected and remain only in work/rejected-intrinsic-size. They are not this evidence.

The unique own window was nonkey/inactive for0.791seconds, four consecutive canonical WindowServer buffers were exact, and no activation/global key occurred. Foreground QQ PID75891 stayed unchanged. The native view's image was released and own view tree detached before exit. Executable and newly created module cache were removed after hashing.

The screenshot is original. Analysis uses its ICC profile with Pillow/LittleCMS perceptual intent0, no resizing/fitting,112x104 patch interiors and632 gray-ramp columns over80rows. All values are encoded screenshot RGB, not physical light. Source atlases remain in sibling `color-probe13/`.

This is a public native candidate at13 Hd1, not product acceptance or macOS14 equivalence. It does not prove that NSImageView preserves Standard output when another view raises current headroom, nor High, arbitrary profiles, metadata rules, HLG, alpha or EXIF behavior. No mapper was inferred or implemented.
