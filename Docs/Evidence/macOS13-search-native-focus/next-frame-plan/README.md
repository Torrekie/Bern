# Frame Caption/Size：下一源级边界

**现有证据还不足以选定一个有依据的产品属性补丁。** 不应由2/3pt直接推出padding、字号、imageScale或AppKit cell属性，也不能把Volume的圆形NSButton桥接扩大到Caption/Size。

版本边界：[真实13 Frame记录](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/Docs/Evidence/macOS13-frame-volume/paired-f9-aot/README.md:3)与[14配对](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/Docs/Evidence/macOS14-frame-volume/paired-40065164350/README.md:5)使用f9 Gallery，14另有原上游A。当前交付为[e48 Gallery](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/Docs/Evidence/macOS13-gallery-clean-delivery-e48/README.md:3)，Showcase仍9dd。f9→e48的Gallery UI、controls/menu/layout生成器整文件及SplitButton/BernRow相关块逐字相同，但这不是e48的新Frame运行证据；HEAD实验不能覆盖该区分。

原图与[既有分析](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/Docs/Evidence/macOS13-frame-volume/paired-f9-aot/README.md:22)表明：

| 可见bezel/ink，半开点坐标 | 13 f9 | 14 f9 |
| --- | --- | --- |
| Caption bezel | x251…356，宽105 | x251…358，宽107 |
| Size bezel | x368…608，宽240 | x370…608，宽238 |
| Size文字左缘 | x398 | x401 |

两控件合计横跨251…608且间隔均12pt；Caption少2pt正好伴随Size多2pt。**先按耦合布局差异看待，不能分别修两处宽度。** Size文字总左移3pt包含bezel左缘2pt变化，扣掉后其内部ink差约1pt；不是已证实的3pt文字inset错误。这些是1×/2×原像素边缘，不是native view/cell frame。两张完整原图已读，未重算阈值或调整图片。

源路径明确：[Caption](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/crates/bern-backend-swiftui/templates/BernStyle.swift:1125)是系统ControlGroup、Toggle(.button)、Label(.titleAndIcon)与fixedSize；不是capsule自绘分支。Size是[原生SwiftUI.Menu(.button)+bordered secondary](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/crates/bern-backend-swiftui/src/swift/toolbar.rs:330)。外层[BernRow](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/crates/bern-backend-swiftui/templates/BernStyle.swift:4447)读取least/ideal/most、分配剩余宽度，再按实际dimensions推进位置。该路径未发现一个13专用错误属性；显式controlSize(.regular)目前也没有“原来不是regular”的证据。

缺口限于这一行，不需要新控件矩阵：①实际e48 Gallery的Frame生成片段（现存导出只有Showcase，不能手写假定生成源）；②同一Frame条件下Caption与Size本身的native类/框、controlSize/字体/label-image布局，以及BernRow给二者的least/ideal/most/offered/actual width。旧report只保Clip/Volume/slider原生AX几何；Caption/Size条目是registry语义，无这些框或cell事实。只有AX hit框时要明确其边界，不能升级成intrinsic/native-cell证据。

下一最小动作应先补上述**同一真实Frame行的一个确定布局事实**，优先利用既有只读源码/采集入口；不先改font/label/width，也不再为边距排列size或style。若发现单一公开属性确有13/14差异，才围绕该属性提出一个源级候选；否则保留未解。当前没有证据支持指定NSPopUpButton.imageHugsTitle、label spacing或controlSize为修复，更没有理由自绘或补固定2pt。

本轮仅源码、原图和已有JSON审查；未UI、编译、CI、改产品或写新probe，未重启已停止的输入/toolbar/width试验。
