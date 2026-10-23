# macOS 13 现代 SwiftUI 移植验收

本阶段使用真正的 `swiftui-modern` / `macos_modern`，不以旧的共享 Objective-C 原型代替上游 SwiftUI。macOS 11、Swift 5.3、Objective-C 和 iOS 阶段仍暂停。当前整应用视觉证据覆盖Showcase和Gallery，不能扩充为全部控件变体与示例均已验收。

## 已有可复核结果

| 检查 | 结果 | 范围 |
|---|---|---|
| 新编译器、新 SDK、target 13.0 | Showcase / Gallery 均编译、链接、签名验证成功 | 最新 `f9e08b1`：Swift 6.2.4、SDK 26.2、Rust 1.99；此前参考构建为 Swift 6.3.3/SDK26.5；仍需要新工具链，并未移植至 Swift 5.3 |
| 同一 target 13 应用在本机 13.7.8 启动 | 两个真正的 SwiftUI 应用均启动、建立 UI 会话 | arm64；Info.plist 与 Mach-O 的最低版本均为 13.0 |
| 原上游 A 与迁移 B，同在 macOS 14.8.9 运行 | 21 张 PNG：17 张 RGB 像素完全相同；3 张分别只有 12/35/76 个像素相差 1 级 | 余下图片页首个 section 多 1 点，后续内容随之下移；尚未把原因归给任何观察机制 |
| 13 系统圆形图标按钮 | 实际应用中的 AX 对齐尺寸为 20×20 点，位置与 14 参考一致 | 使用系统 `NSButton.circular`，没有自画 bezel；实际 AXPress 一次只运行一次引擎命令 |
| 13 Query 错误占位页 | 实际截图的图标、标题、两行说明、按钮与 14 参考的边界差不超过 1 点 | 错误卡高约 226.5 点，14 为 227；重试按钮绘制边界相同 |
| 13 Film 明确 Last 落点 | 浅、深两种外观中，放大卡片四边相对14差值为 [0, -0.5, +1, +0.5] 点 | 原始2x截图，无图像缩放补偿；初始Film身份仍不同，见未通过项 |
| 13 默认侧栏与宽度恢复 | 真正整应用、干净独立 defaults 首开210；AX调为260后，页面重建和进程重启均保留260 | 仅为隔离改变bundle ID及临时签名，可执行文件字节与CI产物相同；没有清用户窗口历史 |
| 空白与媒体占位、语言切换 | 空白/错误媒体占位测量边界均在1pt内；Ready→Failed→Ready恢复后原始画面像素相同；中英文切换及取消关闭保留草稿 | 状态切换通过实际控件绑定，语言测试不冒称真实输入法或菜单点击 |
| 原生交互 | 通知 AXPress 改变会话草稿；音量 AXIncrement 从 50 到 60，只产生一次引擎提交；Command-Comma 打开原生 Settings scene | 这些不是鼠标拖动验证；CLI 状态与原生 AX 操作分别记录 |

最新完整应用源码为 `f9e08b1d55bed4b9d880b19934abe48281057bb3`，已包含HDR路由/系统SDR修复、14原生Pinch路径恢复和本轮音量PopoverButton系统按钮复用。两项CI均通过：[Showcase](https://github.com/Torrekie/Bern/actions/runs/39991409277)、[Gallery](https://github.com/Torrekie/Bern/actions/runs/39991406873)，环境为Swift6.2.4、SDK26.2、Rust1.99。两份产物均已在本机13.7.8启动、建立唯一会话并完成window/control inspect；实际Gallery通过原绑定进入Frame、打开音量弹出层并将草稿0.7改为0.55。随后停止自有进程，检查前后的前台应用一致。原始记录见[Showcase](../Evidence/macOS13-popover/full-app/showcase/report.json)和[Gallery](../Evidence/macOS13-popover/full-app/gallery/report.json)。组件内native action与关闭对照见[独立组件记录](../Evidence/macOS13-popover/component/README.md)。整应用绑定操作不替代真实鼠标或14/13 Frame视觉对照。这轮没有重拍全部视觉/交互样本，不能把下述0f/46截图改标为f9。

此前`5226454`两CI及启动检查仍保留为独立历史证据：[Showcase](../Evidence/macOS13-latest-build/showcase/report.json)、[Gallery](../Evidence/macOS13-latest-build/gallery/report.json)。

第三轮整页视觉证据源码为 `46a286245c1e4c1380ea0e2285587cfe6225a3f8`：

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
| [13图片布局SDK复核](../Evidence/macOS13-image-layout/sdk26/validation.json) | SDK26.2与既有SDK14.2在同一13宿主的9组配置/27位置中，1800个公开坐标框、45次卡片检测均一致，27张PNG哈希全部相同。此结论仅限该夹具条件；14同项测量仍待完成。 |

Gallery 的外观由它自己的 Light/Dark 动作设置，不能只给进程环境变量，因为示例会显式恢复 System。最终静态 Gallery 参考在连续 5 次 WindowServer 缓冲相同后采集。早期误标深色的图片不作为深色依据。

GIF 实际采样间隔约 0.135–0.147 秒，第一帧间隔可能更长；GIF 的播放延迟不是采集帧率。它们只说明程序化状态变化，不能证明 60fps、触控板惯性或短促 nudge 的峰值。

本机显示器为 2 倍缩放，14 CI 为 1 倍。13 的原始 PNG 保留 2 倍像素；比较几何时换算为点，比较颜色时读取 ICC 并统一到 sRGB。不同屏幕、焦点和系统原生材质的差异不能用整数像素全图相等掩盖。

## 必要的局部复用组件

- `BernCompatibility.swift` 保留 ObservableObject 所有权、对象环境及旧 onChange 的当前闭包和 old/new 语义。
- 13 Inspector 复用 `HSplitView`，内容仍为原 SwiftUI；滚动仍为系统 SwiftUI ScrollView。居中边距使用真实SwiftUI内容padding，并按滚动视图作用域隔离，避免直接改变NSScrollView insets造成LazyHStack原生/绘制坐标分离。相位使用14实窗校准的有效viewport及easeInOut Bezier曲线。
- 缺失的按键监听只作用于当前窗口和焦点，不全局吞键；文本编辑与输入法仍需单独实测。
- 普通无显式尺寸的圆形 IconButton 复用 `NSButton`。本轮生成器为普通图标PopoverButton选择同一桥接，并显式转发快捷键；手写helper默认、显式宽高、绘制外观和toolbar不请求此桥接，bar/group由原有组件保留原路径。toolbar、bar/group、显式宽高、plain/prominent、custom look、cancel 保留原路径；destructive、enabled、快捷键、AX ID 与最新 action 转接系统属性。
- PQ/HLG 使用系统 MTKView/CoreImage/EDR 图层，严格识别标准cICP编码后才补足旧系统的色空间识别；SDR转换由Core Image完成，无Metal时复用NSImageView。请求HDR看潜在余量，绘制看当前余量，并通过系统屏幕通知更新，避免以启动前的1永久关闭HDR。普通SDR仍用SwiftUI Image；gain-map能力分支保持原逻辑。
- 显示时钟在 13 使用 CoreVideo 垂直同步；14 保留原生显示链接，不以固定 Timer 代替。

## 尚不能通过的项目

当前不能宣称整个阶段已等效完成，也不能进入 macOS 11 或 Objective-C 阶段。

| 项目 | 当前证据与后续条件 |
|---|---|
| Film 初始身份 | 第三轮已经修复原生探针/SwiftUI绘制坐标分离，并通过9种居中/缩放/减少动态效果小样例；整应用Last几何在1pt内。但是同样Inspector关闭后首次进入Film，14参考为Glen，13为声明初始值3对应Madras。尚未确定14的初始布局/侧栏时序，不硬改为4。 |
| 吸附轨迹 | 13 暂在原生惯性结束后校正，14 在原生目标计算阶段吸附；落点与运动过程应分开验收。 |
| 未覆盖控件变体 | `f9e08b1`已让生成器选中的普通volume PopoverButton复用系统圆形NSButton，独立native action检查通过（单次触发、快捷键、disabled、外部打开和WindowServer alpha=0的关闭，与原Button配对一致）；整应用该版本构建、本机启动及Frame绑定打开/编辑均通过；14/13 Frame视觉仍待验收。icon风格Menu、显式尺寸等仍有独立路径，不能套用普通IconButton的20pt系统按钮验收。Planner的styled SidebarItem才进入自定义侧栏键盘分支；Showcase/Gallery截图没有覆盖它。 |
| 工具栏 chrome | 13 与 14 自动 sidebar toggle / 标题的位置不同。公开 NSToolbar 临时重排会被下一次 SwiftUI 更新覆盖，不能作为产品修复。需要验证源级 composition 或独立原生 chrome 所有权，不能持续争夺 delegate/items。 |
| 图片页首卡高度 | A14/B14/C13首卡分别124/125/129pt。图片均在y108…198，caption墨迹只差0.5pt；后续HDR卡均147pt，仅继承首卡偏移。三个13图片包装结构的公开Column/Grid框均109pt，[13独立公开框探针](../Evidence/macOS13-image-layout/reference.json)的9组合/27截图确认固定109pt行卡也为129pt，最小行高24/0/150均未改变卡高。尚缺14同一公开框测量；不能归因字体或用负padding抵消。 |
| PQ/HLG 色彩 | `e06e080`的严格cICP识别、系统SDR转换、无Metal备用与真实余量通知已随`5226454`及最新`f9e08b1`完整构建并启动。原产品High尚未等同；新增独立Annex5候选在已知中性PQ样本上，Hd1完整ramp对14 MAE0.104109/255，Hd2提交linear EDR为1/1.996094，真实通知观察到1→2→1→2。这是未接入产品的有限输入实验，彩色/metadata/HLG及同条件14High未通过。[原系统路径证据](../Evidence/macOS13-hdr/reference.json)、[候选证据与限制](../Evidence/macOS13-hdr-candidate/reference.json)。 |
| 真正鼠标拖动 | 独立系统NSSlider也未收到自动化drag的mouseDown，值仍50；同控件AXIncrement能产生一次action并变55，因而已在Bern外复现输入交付限制。尚未证明“拖动时只预览，松手仅提交一次”。AXIncrement 单次提交不替代它。 |
| 物理 HDR、输入法、完整动画时序 | 未验收。屏幕潜在EDR为2，实际值会随HDR surface启动从1升到约2；不能把启动前的1当作设备不支持HDR，也不能用SDR截图证明物理HDR亮度等效。 |
| 原生材质配色 | ICC归一后的活动窗口背景仍有差异，可能受桌面染色等本机原生材质条件与14虚拟屏幕条件影响，尚未隔离归因。raised panel可相同，但整窗口颜色尚不能宣称等效；不以固定RGB抵销未经隔离的环境差异。 |

GitHub 的 macos-14 在 2026-10-23 14:00 UTC 至次日00:00 UTC 进入公告的故意失败时段，并计划11月2日退役：[官方公告](https://github.com/actions/runner-images/issues/13518)。已取得的普通外观参考继续可用；该时段的 runner 失败不能归为源码失败。

## HDR独立候选的新增证据

[候选归档](../Evidence/macOS13-hdr-candidate/README.md)将数值推导与本机窗口实验分开保留。CPU原型在640×360上按原始PQ编码解码nit，以公开Annex5候选输出linear BT2020的`Lout/203`；current1与2的提交像素单位由GPU读回验证，Standard切换前后原始图像RGBA完全一致。1000仅是受这张14中性ramp支持的候选预设，203是ISO默认内容白，不是ICC lumi100。

13公开`CIImageOption.toneMapHDRtoSDR`仅有Bool，没有目标headroom；`CIExposureAdjust`只做线性曝光乘法。即使在已知Annex5标量函数下，Hd2的前后曝光也不等于直接目标映射，详见[接口边界与数学反例](../Evidence/macOS13-hdr-candidate/README.md)。没有将这类组合当作已完成的High替代，也没有追加系统CI组合实验。

原型只占前台约0.369秒后恢复即时前台，后续均采自有inactive窗口。CPU动态转换median18.64ms/max88.08ms，不能原样放在主线程产品化；进程resident采样峰60.1MB不是GPU峰值。彩色应用空间、合法元数据缺省/优先级和14实际High适配仍需新probe；当前没有用图片SHA/中性条件作为产品功能白名单，也没有修改产品色调映射。

新增[当前产品Standard彩色对照](../Evidence/macOS13-hdr-candidate/standard-color-e06/validation.json)确认：cICP规范化后的自定义ICC与命名PQ在现有产品helper中输出一致；但对13原生SwiftUI，10色块的通道均值MAE约1.087/255、最大差约4.759/255，不能只凭灰阶认定色彩等同。[公开原生组件比较](../Evidence/macOS13-hdr-candidate/native-sdr-components13/validation.json)中，NSImageView在真实Hd1与13原生SwiftUI整图逐像素相同；CGContext 8位转换仍有约5级色块差。[动态余量检查](../Evidence/macOS13-hdr-candidate/native-sdr-headroom13/validation.json)在7.5秒采集上限内只完成初始Hd1，不能推断其它余量条件恒定。此原生候选尚未进入产品，14彩色基线仍待。

## 下一次14运行采集

已发布[轻量runtime probe工作流](https://github.com/Torrekie/Bern/actions/workflows/macos14-probe-runtime.yml)，仅下载运行现有exact artifact，不重新构建。截至本次记录尚未dispatch14。计划在brownout结束的北京时间2026-10-24 08:00后，图片公开框测量使用`probe=image, build_run=39986052533`（[已构建输入](https://github.com/Torrekie/Bern/actions/runs/39986052533)）；HDR中性/彩色探针使用`probe=hdr, build_run=39987622874`（[已构建输入](https://github.com/Torrekie/Bern/actions/runs/39987622874)）。这些是待执行输入，不是14通过结果。

新SDK26.2与旧SDK14.2在同一13图片夹具中的框、卡片检测和全部27张PNG一致，只排除这组13条件下本轮编译组合造成的差异；不能据此解释14/13图片首卡高度或其它未测布局。HDR新probe也不能自动覆盖metadata、HLG或实际Hd>1。

## 空间控制

只保留需要复核的源码、原始证据和当前候选应用。传输 ZIP、提取后的重复 tar、经哈希验证的重复参考已清理；小型编译试验的 module cache 在完成后删除。没有安装新 Xcode、Swift 工具链或 iOS 模拟器，也不清理用户的窗口历史、其它项目产物或系统缓存。
