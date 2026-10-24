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
| [13图片布局SDK复核](../Evidence/macOS13-image-layout/sdk26/validation.json) | SDK26.2与既有SDK14.2在同一13宿主的9组配置/27位置中，1800个公开坐标框、45次卡片检测均一致，27张PNG哈希全部相同。[同binary14普通效果](../Evidence/macOS14-image-layout/validation.json)也已完成，首卡129点相同；该夹具仍未复现完整14应用的124/125点。 |
| [13背景路径隔离](../Evidence/macOS13-window-background/README.md) | 同一个inactive浅色窗口中，语义颜色直接绘制为236灰；透明NavigationSplitView detail为240/236/237，显式填充后恢复236灰。五组各两次稳定缓冲，窗口2.446秒、前台不变；这不是完整Gallery或14对照。 |
| [13 toolbarRole候选](../Evidence/macOS13-toolbar-role/README.md) | 同一Showcase式固定标题样例中，automatic、split上的editor和detail上的editor共9个原生框样本均不移位，标题仍存在；未扩充为Gallery或所有公开composition均已排除。 |

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
| Film 初始身份 | 第三轮整应用Last几何在1pt内，14初始Glen、13初始Madras。新14普通效果上游三场景均为Glen，wait/direct原始Film PNG相同，说明Inspector关闭过渡不是该身份的必要条件；immediate仍有约35pt落点差异，且启动窗口恢复/实际resize是混杂。当前f9移植应用在14三场景也均Glen。AX几何并非NSClipView bounds，内部target/nearest仍未观测，不能断言3写回成4。[事实、原始证据与下一最小trace](macOS13-Film-Initial-Position.md)；不硬改默认值。 |
| 吸附轨迹 | 13 暂在原生惯性结束后校正，14 在原生目标计算阶段吸附；落点与运动过程应分开验收。 |
| 未覆盖控件变体 | `f9e08b1`已让生成器选中的普通volume PopoverButton复用系统圆形NSButton，独立native action检查通过（单次触发、快捷键、disabled、外部打开和WindowServer alpha=0的关闭，与原Button配对一致）；整应用该版本构建、本机启动及Frame绑定打开/编辑均通过；14/13 Frame视觉仍待验收。icon风格Menu、显式尺寸等仍有独立路径，不能套用普通IconButton的20pt系统按钮验收。Planner的styled SidebarItem才进入自定义侧栏键盘分支；Showcase/Gallery截图没有覆盖它。 |
| 工具栏 chrome | 13 与 14 自动 sidebar toggle / 标题的位置不同。公开 NSToolbar 临时重排会被下一次 SwiftUI 更新覆盖，不能作为产品修复。需要验证源级 composition 或独立原生 chrome 所有权，不能持续争夺 delegate/items。 |
| 图片页首卡高度 | 完整应用A14/B14/C13首卡分别124/125/129pt，图片和caption边界接近，后续HDR卡均147pt。新增[同binary14普通效果探针](../Evidence/macOS14-image-layout/validation.json)九组合/27位置中，首卡与fixed109卡均129、HDR147，均与13同binary相同；其它公开坐标仍有最高2.5pt差异。进一步[静态四子节点隔离](../Evidence/macOS13-image-layout/static-children/validation.json)在13和14各1800个公开坐标框均与原ForEach夹具相同，首卡仍129，已排除该单独因素；13全部27 PNG字节相同，14为25/27，未宣称全像素相等。独立probe仍未复现完整应用14首卡124/125，完整Scene及其余简化包装待隔离，不能把probe匹配当整应用修复，也不以负padding抵消。 |
| PQ/HLG 色彩 | `e06e080`的严格cICP识别、系统SDR转换、无Metal备用与真实余量通知已随`5226454`及最新`f9e08b1`完整构建并启动。原产品High尚未等同；新增独立Annex5候选在已知中性PQ样本上，Hd1完整ramp对14 MAE0.104109/255，Hd2提交linear EDR为1/1.996094，真实通知观察到1→2→1→2。这是未接入产品的有限输入实验，彩色/metadata/HLG及同条件14High未通过。[原系统路径证据](../Evidence/macOS13-hdr/reference.json)、[候选证据与限制](../Evidence/macOS13-hdr-candidate/reference.json)。 |
| 真正鼠标拖动 | 独立系统NSSlider也未收到自动化drag的mouseDown，值仍50；同控件AXIncrement能产生一次action并变55，因而已在Bern外复现输入交付限制。尚未证明“拖动时只预览，松手仅提交一次”。AXIncrement 单次提交不替代它。 |
| 物理 HDR、输入法、完整动画时序 | 未验收。屏幕潜在EDR为2，实际值会随HDR surface启动从1升到约2；不能把启动前的1当作设备不支持HDR，也不能用SDR截图证明物理HDR亮度等效。 |
| 原生材质配色 | ICC归一后的活动窗口背景仍有差异。原比较中canvas只是空白点位昵称；Patterns/Film该处是透明detail，并未填surface.canvas。[同binary13/14五组实窗比较](../Evidence/macOS13-window-background/sdk26-content-stable/comparison.json)已完成：语义颜色实画、SwiftUI Color、canvas和显式填detail模式RGB均236灰；透明split却为13的240/236/237与14的234灰。两边内容尺寸均800×520，原生外框/sidebar/chrome不同。该inactive手建窗口不能替代完整Gallery活动窗口，也不能唯一归因材质或系统tint；不以固定RGB抵销。 |

GitHub 的 macos-14 在 2026-10-23 14:00 UTC 至次日00:00 UTC 进入公告的故意失败时段，并计划11月2日退役：[官方公告](https://github.com/actions/runner-images/issues/13518)。已取得的普通外观参考继续可用；该时段的 runner 失败不能归为源码失败。

## HDR独立候选的新增证据

[候选归档](../Evidence/macOS13-hdr-candidate/README.md)将数值推导与本机窗口实验分开保留。CPU原型在640×360上按原始PQ编码解码nit，以公开Annex5候选输出linear BT2020的`Lout/203`；current1与2的提交像素单位由GPU读回验证，Standard切换前后原始图像RGBA完全一致。1000仅是受这张14中性ramp支持的候选预设，203是ISO默认内容白，不是ICC lumi100。

13公开`CIImageOption.toneMapHDRtoSDR`仅有Bool，没有目标headroom；`CIExposureAdjust`只做线性曝光乘法。即使在已知Annex5标量函数下，Hd2的前后曝光也不等于直接目标映射，详见[接口边界与数学反例](../Evidence/macOS13-hdr-candidate/README.md)。没有将这类组合当作已完成的High替代，也没有追加系统CI组合实验。

原型只占前台约0.369秒后恢复即时前台，后续均采自有inactive窗口。CPU动态转换median18.64ms/max88.08ms，不能原样放在主线程产品化；进程resident采样峰60.1MB不是GPU峰值。彩色应用空间、合法元数据缺省/优先级和14实际High适配仍需新probe；当前没有用图片SHA/中性条件作为产品功能白名单，也没有修改产品色调映射。

新增[当前产品Standard彩色对照](../Evidence/macOS13-hdr-candidate/standard-color-e06/validation.json)确认：cICP规范化后的自定义ICC与命名PQ在现有产品helper中输出一致；但对13原生SwiftUI，10色块的通道均值MAE约1.087/255、最大差约4.759/255，不能只凭灰阶认定色彩等同。[公开原生组件比较](../Evidence/macOS13-hdr-candidate/native-sdr-components13/validation.json)中，NSImageView在真实Hd1与13原生SwiftUI整图逐像素相同；CGContext 8位转换仍有约5级色块差。早期[动态余量检查](../Evidence/macOS13-hdr-candidate/native-sdr-headroom13/validation.json)只完成初始Hd1；本轮[缩小后的完整动态采样](../Evidence/macOS13-hdr-candidate/native-standard-dynamic13/validation.json)已实际完成current1→2→1，20次trajectory、27次GPU完成/读回、76次真实屏幕通知、6张截图。两原生图像的12个ROI均逐像素相同，并复现旧静态基线；窗口3.218秒、未激活、前台不变。这仅证明该PQ彩色atlas在此13环境的截图稳定，不扩充为HLG、EXIF、alpha或物理亮度。

[14普通效果彩色基线](../Evidence/macOS14-hdr-color-normal/validation.json)已取得：同一binary在14的custom ICC与named PQ均识别为BT.2100 PQ并逐像素相同；13需要严格cICP规范化。13原生named PQ对14的10色块MAE约1.294/255，最大约26.515；现产品Standard helper更远。两个宿主的显示器/ICC/缩放也不同，不能单因归为系统版本，原生候选尚未进入产品。

## 恢复后的14普通效果采集

远程macOS14已实际运行。普通效果[图片run40062046351](https://github.com/Torrekie/Bern/actions/runs/40062046351)和[HDR run40062048900](https://github.com/Torrekie/Bern/actions/runs/40062048900)均成功，复用此前已在13运行的exact binary，不重新构建应用。独立profile.json从NSWorkspace验证reduceMotion/reduceTransparency/increaseContrast均false；图片probe还独立重复记录这三项。第一轮图片40061735500沿用runner的reduced默认值，已分开归档，不能冒充normal；第一轮HDR40061839104缺少profile记录，普通效果重采后的像素与它相同，但仍保持不同证据身份。

新SDK26.2与旧SDK14.2在同一13图片夹具中的框、卡片检测和全部27张PNG一致，只排除这组13条件下本轮编译组合造成的差异；不能据此解释14/13图片首卡高度或其它未测布局。HDR新probe也不能自动覆盖metadata、HLG或实际Hd>1。

上游Film[run40062194628](https://github.com/Torrekie/Bern/actions/runs/40062194628)已成功，使用既有Gallery构建39959549054，每组新进程区分立即关闭、等待关闭、从未打开Inspector；[原始证据与分析](../Evidence/macOS14-film-timing/analysis.json)。首次采集40061845578在建立会话前失败，已根据上游100字节socket上限将测试临时路径缩短；该失败没有Film结果。当前f9应用在14的同场景run40062837456也成功，进一步确认身份差异属于13路径，尚未证明内部绑定变化。

Frame仍未采集通过。首跑40062043370视频已Ready→Paused0，但own-PID事件后控件消失；第二跑40062688905事件往返保留窗口编号、CLI仍有音量控件，但AXButton查找失败。完整AX诊断确认native标识被上游覆盖为main_window.find；同父组中的真实Clip/Volume控件存在。严格限定窗口/父组/label/role的选择器在[40064763940](../Evidence/macOS14-frame-volume/attempt-40064763940/README.md)通过3.2秒idle及native几何，随后首张PNG因采集器将NSNumber对象传给要求原始CGWindowID的数组接口而失败。已修正原始ID编码，并在每帧前回读核对窗口ID和所属PID；新paired run40065164350验收中。此前均未进入B，PNG=0，不算视觉或物理输入验收，媒体/idle/AXPress/稳定buffer门槛保持。

背景探针[14 run40063500033](https://github.com/Torrekie/Bern/actions/runs/40063500033)及同一SDK26.5二进制在本机13均完成五组运行，归档见[13](../Evidence/macOS13-window-background/sdk26-content-stable/README.md)和[14](../Evidence/macOS14-window-background/content-stable/README.md)。早期“外框全程不变”断言阻止后两组；诊断已确认原生NavigationSplitView自动加toolbar改变外框，内容尺寸保持。新合同实际通过内容800×520、各variant双buffer像素/几何稳定及不激活条件，并保留真实外框变化。透明detail的跨系统颜色差异已复现，其余四组模式RGB相同；不将手建窗口结果冒充整应用等效。

## 暂停检查点（2026-10-24，北京时间）

此前按用户要求暂停，08:05一次性检查已执行并删除。用户/系统于12:16恢复同一个goal，当前active；实际14运行已恢复，不再因brownout空等。已有实现和上述未通过项均保留，不标记完成。macOS11、Swift5.3、Objective-C和iOS仍暂停。

## 空间控制

只保留需要复核的源码、原始证据和当前候选应用。传输 ZIP、提取后的重复 tar、经哈希验证的重复参考已清理；小型编译试验的 module cache 在完成后删除。没有安装新 Xcode、Swift 工具链或 iOS 模拟器，也不清理用户的窗口历史、其它项目产物或系统缓存。
