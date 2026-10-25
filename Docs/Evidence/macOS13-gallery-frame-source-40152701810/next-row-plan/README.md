# Frame Row：下一次只取得一个布局事实

**建议取得真实 Frame 行在一次置放调用中使用的完整“宽度账本”，暂不改产品属性。** 精确 e48 的真实生成源已补齐；现有证据仍不能指定 2pt 修复或把文字差直接归给字体/inset。

## 已确定的源码边界

本次 CI 40152701810 仅生成源码。完整文件 81,110B，SHA `f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653`；Frame 原字节切片 9,021B，原行 1248–1353，与完整文件对应区间逐字相同。当前真实 BernStyle 全文件 SHA `3912ecdbe102508771174df91f4d7baa153cca9925d89f6e68cdffc2e90cbd89`，与该 CI 的 e48 输入收据相同。

[真实 Frame 行](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/work/gallery-frame-source-ci-40152701810/BernGenerated.swift:1274)只在 `!bernWindow.idle` 时存在，源码 builder 顺序如下；**四个 builder 项不等于已测得四个 Layout.Subviews。** 条件 Group 实际提供多少代理，以及代理和控件的对应，尚需运行证据。

| 源项 | 已确定实现及影响边界 |
| --- | --- |
| Caption，行1275 | `BernSplitButton(capsule:false)`；[模板](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/crates/bern-backend-swiftui/templates/BernStyle.swift:1125)为系统 ControlGroup + Toggle(.button) + chevron Button，外层 `.fixedSize()`。传入的 `height:34` 不在该非 capsule 分支强制定高，不能拿它当实测框。 |
| Size，行1286–1304 | SwiftUI.Menu + Label(textformat.size)，menuStyle(.button) / secondary；13/14 在[系统样式分支](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/crates/bern-backend-swiftui/templates/BernStyle.swift:875)采用 bordered。没有生成固定宽度或文字偏移。 |
| Volume，行1305 | `BernPopoverButton(nativeCircular:true)`；[模板](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/crates/bern-backend-swiftui/templates/BernStyle.swift:3398)在14走 SwiftUI trigger，在13复用现有 BernCircularIconButton。因此它同样可能参与行宽分配，不能省略其响应。 |
| 条件 Group，行1317起 | caption=true 时含说明 Text/transition。它可能参与剩余宽度分配；源码本身不能给出运行时增长分类或实际宽度。 |

[BernRow](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/crates/bern-backend-swiftui/templates/BernStyle.swift:4447)原本就依次查询每个代理在 width=0/nil/infinity 下的响应，将 least/most 与 ideal 归一化，用 `most > ideal+0.5` 判 grows，分配 offered；[arrange](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/crates/bern-backend-swiftui/templates/BernStyle.swift:4508)再以原 offered 查询 dimensions，并按**实际 dimensions.width**推进 x。不能把 offered、dimensions extent、AX命中框、截图 bezel/ink 当成同一种宽度。

## 唯一下一观测

若 root 批准实现诊断，只给这个已存在的 Frame BernRow 加可选 `diagnosticID`（BernRow 默认 nil，精确生成调用点设置标识）；无需新增 LayoutValueKey、包装控件或替换布局。仅把原调用中已经取得的值收集为有界记录，不增添 `sizeThatFits` / dimensions / intrinsicSize / native-cell 查询，也不改变原查询、算法、赋值及 place 顺序。

一次有效记录需关联同一个 **placeSubviews→arrange→widths** 调用：实际 subview count / 全部 ordinal；原 row bounds、proposal（nil/infinity明确编码）、12pt gaps；各项原始 least/ideal/most、归一化值/grows/spacer、最终 offered、实际 dimensions width/height、最终局部放置点和 row size。只记录既有计算，不为探测强制重新布局；未完成的测量调用不能混入该置放记录。先按 ordinal 比较，未有源码与实际位置的一致依据前，不把 ordinal 自动命名为 Caption/Size。

上下文沿现有 Frame closed：920×668 外窗、英语、window Light 但 Frame 自身 dark、caption=true、Volume关闭、视频暂停在0，保持已验证的存活机制。旧 [collector](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/Docs/Evidence/macOS13-frame-volume/paired-f9-aot/gallery-frame-reference.swift:261)只采 Clip/Volume/弹层 slider 的 AX几何；其 [closed采集](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/Docs/Evidence/macOS13-frame-volume/paired-f9-aot/gallery-frame-reference.swift:385)可作流程依据，但不是 e48 新测量。需同时确认实际行仍 awake、条件值和版本；不切换 Caption、不打开弹层、不扩 style/尺寸矩阵。

**先过无观察器对照的原图 gate，再解释记录。** 新诊断必须由 root 先按既有14 gate证明未改变该窗口/控件原像素，再开展同源13比较；对照和观测的源码/二进制/collector身份必须可核。若没有同版本 e48 对照，不把旧f9图重新标作e48。记录只在对应稳定 closed capture 的完整调用中采用，不以第一条回调冒充最终状态。

## 读数之后的界限

这个单一事实可区分“行分到不同 offered / 分类”与“相同 offered 得到不同 extent”等观测；也能揭示 Volume/条件项是否改变整行账本。它不能单独证明系统控件内部 padding 或唯一根因。账本相同而图不同，则停止这一布局诊断，保留字体/原生绘制边界未解；不补固定2pt、不改 controlSize/font/RGB、不自绘。count/语义/上下文不清、日志截断或像素 gate 失败时，记录不用于产品修复推断，本轮不转入试验矩阵。

本目录仅源码与既有 JSON 分析；未写 probe/产品补丁，未 build、UI、CI 或 Git mutation。
