# macOS 13 现代 SwiftUI 移植验收

本阶段使用真正的 `swiftui-modern` / `macos_modern`，不以旧的共享 Objective-C 原型代替上游 SwiftUI。macOS 11、Swift 5.3、Objective-C 和 iOS 阶段仍暂停。

## 已有可复核结果

| 检查 | 结果 | 范围 |
|---|---|---|
| 新编译器、新 SDK、target 13.0 | Showcase / Gallery 均编译、链接、签名验证成功 | Swift 6.3.3、SDK 26.5、Rust 1.99；仍需要新工具链编译，并未移植至 Swift 5.3 |
| 同一 target 13 应用在本机 13.7.8 启动 | 两个真正的 SwiftUI 应用均启动、建立 UI 会话 | arm64；Info.plist 与 Mach-O 的最低版本均为 13.0 |
| 原上游 A 与迁移 B，同在 macOS 14.8.9 运行 | 21 张 PNG：17 张 RGB 像素完全相同；3 张分别只有 12/35/76 个像素相差 1 级 | 余下图片页首个 section 多 1 点，后续内容随之下移；尚未把原因归给任何观察机制 |
| 13 系统圆形图标按钮 | 实际应用中的 AX 对齐尺寸为 20×20 点，位置与 14 参考一致 | 使用系统 `NSButton.circular`，没有自画 bezel；实际 AXPress 一次只运行一次引擎命令 |
| 13 Query 错误占位页 | 实际截图的图标、标题、两行说明、按钮与 14 参考的边界差不超过 1 点 | 错误卡高约 226.5 点，14 为 227；重试按钮绘制边界相同 |
| 13 Film 明确 Last 落点 | 浅、深两种外观中，放大卡片四边相对14差值为 [0, -0.5, +1, +0.5] 点 | 原始2x截图，无图像缩放补偿；初始Film身份仍不同，见未通过项 |
| 13 默认侧栏与宽度恢复 | 真正整应用、干净独立 defaults 首开210；AX调为260后，页面重建和进程重启均保留260 | 仅为隔离改变bundle ID及临时签名，可执行文件字节与CI产物相同；没有清用户窗口历史 |
| 空白与媒体占位、语言切换 | 空白/错误媒体占位测量边界均在1pt内；Ready→Failed→Ready恢复后原始画面像素相同；中英文切换及取消关闭保留草稿 | 状态切换通过实际控件绑定，语言测试不冒称真实输入法或菜单点击 |
| 原生交互 | 通知 AXPress 改变会话草稿；音量 AXIncrement 从 50 到 60，只产生一次引擎提交；Command-Comma 打开原生 Settings scene | 这些不是鼠标拖动验证；CLI 状态与原生 AX 操作分别记录 |

第三轮完整应用已验证源码为 `46a286245c1e4c1380ea0e2285587cfe6225a3f8`：

- [Showcase 构建](https://github.com/Torrekie/Bern/actions/runs/39975026355)
- [Gallery 构建](https://github.com/Torrekie/Bern/actions/runs/39975025096)

Gallery 的第三轮本机证据为两种外观各新进程、活动窗口、连续 5 次相同 WindowServer 缓冲后的 8 张原始 2x PNG。Showcase 当前保留的占位页、按钮、媒体证据来自第二轮 `0f5226d`，其 [Showcase 构建](https://github.com/Torrekie/Bern/actions/runs/39969189803) 与 [Gallery 构建](https://github.com/Torrekie/Bern/actions/runs/39969189761) 均通过；它们不能冒充第三轮重拍。

macOS 14 上的 A/B 对照使用此前的 `fa820f706e5faf1bae8b8f07e23545842a1648b7`；此后的按钮、占位页和滚动相位校准均限制在 13 分支。不要把旧源码的对照扩充成新源码已经在 14 再验收。

## 参考与采集方式

原上游固定为 `ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee`。新 SDK 构建与旧系统运行分开，应用不在 14 运行机上重新编译。普通参考的减少动态效果、减少透明度和增强对比均关闭；没有修改本机这些设置。

| 证据 | 内容 |
|---|---|
| [Showcase 原始参考](../Evidence/macOS14-reference-normal/reference.json) | 13 张 WindowServer PNG，涵盖浅/深色控件、Text、Buttons、Inputs、Query 错误/空白/恢复、图片、Video 状态；[采集](https://github.com/Torrekie/Bern/actions/runs/39961818954) |
| [Gallery 原始参考](../Evidence/macOS14-gallery-normal/reference.json) | 8 张浅/深色 PNG，4 个 Inspector/滚动 GIF；[采集](https://github.com/Torrekie/Bern/actions/runs/39964126654) |
| [本机13候选证据](../Evidence/macOS13-candidate/reference.json) | 14张原始窗口PNG，分开注明0f/46源码版本；[Gallery量化](../Evidence/macOS13-candidate/gallery-comparison.json)、[侧栏宽度](../Evidence/macOS13-candidate/sidebar-width.json)、[语言/关闭](../Evidence/macOS13-candidate/language-close.json) |
| [同系统迁移比较](../Evidence/macOS14-port-comparison/comparison.json) | 每张图片的 RGB 比较、原始文件哈希、不同 PNG、图片页差异测量；相同图片复用 A 的原图，避免重复保存 |

Gallery 的外观由它自己的 Light/Dark 动作设置，不能只给进程环境变量，因为示例会显式恢复 System。最终静态 Gallery 参考在连续 5 次 WindowServer 缓冲相同后采集。早期误标深色的图片不作为深色依据。

GIF 实际采样间隔约 0.135–0.147 秒，第一帧间隔可能更长；GIF 的播放延迟不是采集帧率。它们只说明程序化状态变化，不能证明 60fps、触控板惯性或短促 nudge 的峰值。

本机显示器为 2 倍缩放，14 CI 为 1 倍。13 的原始 PNG 保留 2 倍像素；比较几何时换算为点，比较颜色时读取 ICC 并统一到 sRGB。不同屏幕、焦点和系统原生材质的差异不能用整数像素全图相等掩盖。

## 必要的局部复用组件

- `BernCompatibility.swift` 保留 ObservableObject 所有权、对象环境及旧 onChange 的当前闭包和 old/new 语义。
- 13 Inspector 复用 `HSplitView`，内容仍为原 SwiftUI；滚动仍为系统 SwiftUI ScrollView。居中边距使用真实SwiftUI内容padding，并按滚动视图作用域隔离，避免直接改变NSScrollView insets造成LazyHStack原生/绘制坐标分离。相位使用14实窗校准的有效viewport及easeInOut Bezier曲线。
- 缺失的按键监听只作用于当前窗口和焦点，不全局吞键；文本编辑与输入法仍需单独实测。
- 普通无显式尺寸的圆形 IconButton 复用 `NSButton`。toolbar、bar/group、显式宽高、plain/prominent、custom look、cancel 保留原路径；destructive、enabled、快捷键、AX ID 与最新 action 转接系统属性。
- PQ/HLG 使用系统 MTKView/CoreImage/EDR 图层，严格识别标准cICP编码后才补足旧系统的色空间识别；SDR转换由Core Image完成，无Metal时复用NSImageView。请求HDR看潜在余量，绘制看当前余量，并通过系统屏幕通知更新，避免以启动前的1永久关闭HDR。普通SDR仍用SwiftUI Image；gain-map能力分支保持原逻辑。
- 显示时钟在 13 使用 CoreVideo 垂直同步；14 保留原生显示链接，不以固定 Timer 代替。

## 尚不能通过的项目

当前不能宣称整个阶段已等效完成，也不能进入 macOS 11 或 Objective-C 阶段。

| 项目 | 当前证据与后续条件 |
|---|---|
| Film 初始身份 | 第三轮已经修复原生探针/SwiftUI绘制坐标分离，并通过9种居中/缩放/减少动态效果小样例；整应用Last几何在1pt内。但是同样Inspector关闭后首次进入Film，14参考为Glen，13为声明初始值3对应Madras。尚未确定14的初始布局/侧栏时序，不硬改为4。 |
| 吸附轨迹 | 13 暂在原生惯性结束后校正，14 在原生目标计算阶段吸附；落点与运动过程应分开验收。 |
| 工具栏 chrome | 13 与 14 自动 sidebar toggle / 标题的位置不同。公开 NSToolbar 临时重排会被下一次 SwiftUI 更新覆盖，不能作为产品修复。需要验证源级 composition 或独立原生 chrome 所有权，不能持续争夺 delegate/items。 |
| 图片页首卡高度 | A14/B14/C13首卡分别124/125/129pt。图片均在y108…198，caption墨迹只差0.5pt；后续HDR卡均147pt，仅继承首卡偏移。三个13图片包装结构的公开Column/Grid框均109pt，[13独立公开框探针](../Evidence/macOS13-image-layout/reference.json)的9组合/27截图确认固定109pt行卡也为129pt，最小行高24/0/150均未改变卡高。尚缺14同一公开框测量；不能归因字体或用负padding抵消。 |
| PQ/HLG 色彩 | `e06e080`补足严格cICP识别、系统SDR转换、无Metal备用及真实余量通知更新。独立真实窗口SDR约228.93/254.89，与14虚拟SDR参考接近；真实OS通知观察到1→2→1→2， paused Metal view会重绘。但High仍缺14引入的自适应全局tone mapper，current2截图两半255，尚不能通过。完整应用CI仍待；[原始证据与范围](../Evidence/macOS13-hdr/reference.json)。 |
| 真正鼠标拖动 | 独立系统NSSlider也未收到自动化drag的mouseDown，值仍50；同控件AXIncrement能产生一次action并变55，因而已在Bern外复现输入交付限制。尚未证明“拖动时只预览，松手仅提交一次”。AXIncrement 单次提交不替代它。 |
| 物理 HDR、输入法、完整动画时序 | 未验收。屏幕潜在EDR为2，实际值会随HDR surface启动从1升到约2；不能把启动前的1当作设备不支持HDR，也不能用SDR截图证明物理HDR亮度等效。 |
| 原生材质配色 | ICC归一后的活动窗口背景仍有差异，可能受桌面染色等本机原生材质条件与14虚拟屏幕条件影响，尚未隔离归因。raised panel可相同，但整窗口颜色尚不能宣称等效；不以固定RGB抵销未经隔离的环境差异。 |

GitHub 的 macos-14 在 2026-10-23 14:00 UTC 至次日00:00 UTC 进入公告的故意失败时段，并计划11月2日退役：[官方公告](https://github.com/actions/runner-images/issues/13518)。已取得的普通外观参考继续可用；该时段的 runner 失败不能归为源码失败。

## 空间控制

只保留需要复核的源码、原始证据和当前候选应用。传输 ZIP、提取后的重复 tar、经哈希验证的重复参考已清理；小型编译试验的 module cache 在完成后删除。没有安装新 Xcode、Swift 工具链或 iOS 模拟器，也不清理用户的窗口历史、其它项目产物或系统缓存。
