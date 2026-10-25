# Volume：复用 f9 原生证据的源码证明

结论：按“符合目标平台逻辑，允许细微版本差异”的验收口径，现有 f9 原生 Volume 开闭、内容挂载/卸载和草稿同步证据可复用于当前 e48，无需重复运行弹出层。

比较的是固定 f9 `f9e08b1d55bed4b9d880b19934abe48281057bb3`、交付 e48 `e48fff46b3a92a28465ad74295bd273a9d69af7d` 与审查时当前提交 `b72cb5dee3cf73b376a5e3d28b6e97f777eaf3d8`。通过只读 `git show REVISION:PATH` 逐字比较，未归一化源码。`comparison.json` 保存全部区域边界、各提交行号/字节偏移、大小、SHA256、直接相等断言与整文件元数据。当前工作树的五个对应文件也逐字等于 b72；e48→b72 这五文件无差异。

Gallery 声明、控件生成器及整个 AppKit 模板三个提交完全相同。Style 的 bernPopover、BernPopoverButton、系统材质、按钮样式区域，以及 Runtime 的控件注册/卸载与相关控制命令分派区域也完全相同。f9→e48 的实际变化仅属于 Picture/PQ 与 legacy scroll；这些已变化的整体文件没有被误称为完全相同。

未改变的链路为：生成器启用 nativeCircular → macOS13 使用系统圆形 NSButton 的 target/action → 切换 presentation Binding → SwiftUI popover 跟随 Binding → 内容消失时删除其 BernControl 注册。关闭没有另写一套自定义 popup 实现。

复用的两份原件位于仓库内，未在本目录复制：

- `Docs/Evidence/macOS13-frame-volume/paired-f9-aot/run-aot/report.json`：177832B，SHA256 `79334d78d4a1f8cc2a36e31d91b107270de052d1dee9cb5f2d5276ab697e7398`。实际13.7.8的 AXPress 打开/关闭、popup 窗口出现/消失、Slider 挂载/卸载。
- `Docs/Evidence/macOS13-popover/full-app/gallery/report.json`：14879B，SHA256 `a5e77d3ff9dec6488e107066aae2042be94da1f0917f3800a8fde9dd42c245fc`。实际旧整 App 中通过 CLI 修改草稿0.7→0.55并回读。

这两份原件是两次互补运行，不应合并描述成一次执行。它们都来自固定 f9；原 GUI 为 `887173af876a3f802c68dfff7fef087f318cc6909a61ea4beff69dad536dfd7e`，Swift6.2.4/SDK26.2/arm64/min13。相关 provenance 原件的摘要也写入 JSON。

验收分类应写“已有原生 macOS13 实测＋相关源码未改变”，不能写成“当前 e48 新实测”。证据不证明物理鼠标、Slider 拖动、键盘/VoiceOver、暗色/窄窗全矩阵或实际播放进度。三个修订中 Volume Slider 都仅绑定 GalleryDraft.volume；Video 没有 volume 绑定，因此0.7→0.55只证明草稿同步，不证明声音改变。

本次仅只读审查 Git 源码与现有记录，写入本目录的小型 provenance；未运行 GUI、构建、网络、Git 修改、清理或新探针，未复制完整源码和已有原始报告。
