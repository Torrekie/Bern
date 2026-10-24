# macOS 13 现代 SwiftUI 移植验收

本阶段使用真正的 `swiftui-modern` / `macos_modern`，不以旧的共享 Objective-C 原型代替上游 SwiftUI。macOS 11、Swift 5.3、Objective-C 和 iOS 阶段仍暂停。当前整应用视觉证据覆盖Showcase和Gallery，不能扩充为全部控件变体与示例均已验收。

## 已有可复核结果

| 检查 | 结果 | 范围 |
|---|---|---|
| 新编译器、新 SDK、target 13.0 | Showcase / Gallery 均编译、链接、签名验证成功 | 已交付Showcase `9dd99b7`、Gallery `e48fff46`：Swift 6.2.4、SDK 26.2、Rust 1.99；此前参考构建为 Swift 6.3.3/SDK26.5；仍需要新工具链，并未移植至 Swift 5.3 |
| 同一 target 13 应用在本机 13.7.8 启动 | 两个真正的 SwiftUI 应用均启动、建立 UI 会话 | arm64；Info.plist 与 Mach-O 的最低版本均为 13.0 |
| 原上游 A 与迁移 B，同在 macOS 14.8.9 运行 | 21 张 PNG：17 张 RGB 像素完全相同；3 张分别只有 12/35/76 个像素相差 1 级 | 余下图片页首个 section 多 1 点，后续内容随之下移；尚未把原因归给任何观察机制 |
| 13 系统圆形图标按钮 | 实际应用中的 AX 对齐尺寸为 20×20 点，位置与 14 参考一致 | 使用系统 `NSButton.circular`，没有自画 bezel；实际 AXPress 一次只运行一次引擎命令 |
| 13 Query 错误占位页 | 实际截图的图标、标题、两行说明、按钮与 14 参考的边界差不超过 1 点 | 错误卡高约 226.5 点，14 为 227；重试按钮绘制边界相同 |
| 13 Film 明确 Last 落点 | 浅、深两种外观中，放大卡片四边相对14差值为 [0, -0.5, +1, +0.5] 点 | 原始2x截图，无图像缩放补偿；旧46初始身份仍不同；本轮e48及后续操作序列见未通过项 |
| 13 默认侧栏与宽度恢复 | 真正整应用、干净独立 defaults 首开210；AX调为260后，页面重建和进程重启均保留260 | 仅为隔离改变bundle ID及临时签名，可执行文件字节与CI产物相同；没有清用户窗口历史 |
| 空白与媒体占位、语言切换 | 空白/错误媒体占位测量边界均在1pt内；Ready→Failed→Ready恢复后原始画面像素相同；中英文切换及取消关闭保留草稿 | 状态切换通过实际控件绑定，语言测试不冒称真实输入法或菜单点击 |
| 14 Frame 原生对照 | f9与固定上游在同一14机器中的视频区/按钮/弹出层/滑块几何一致，Frame detail像素一致，独立音量popup PNG文件相同 | 仅浅色；主窗侧栏选中行仍5284像素灰/蓝差异；13对应验收及物理输入不由此通过 |
| 13 Frame 原生运行 | f9通过Ready→Paused0、3.2秒保活、native AXPress开关、raw窗口ID回读与3张稳定原图；Clip/popup/slider点几何精确同14 | active浅色，前台1390→1390；Volume可见bezel差≤.5pt，仍有配色、Caption/Size宽度及文字位置差异，不是全视觉或物理输入通过 |
| 原生交互 | 通知 AXPress 改变会话草稿；音量 AXIncrement 从 50 到 60，只产生一次引擎提交；Command-Comma 打开原生 Settings scene | 这些不是鼠标拖动验证；CLI 状态与原生 AX 操作分别记录 |

目前交付的Showcase来自 `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`，[CI40066468884](https://github.com/Torrekie/Bern/actions/runs/40066468884)成功；Gallery现为 `e48fff46b3a92a28465ad74295bd273a9d69af7d`，[CI40070407306](https://github.com/Torrekie/Bern/actions/runs/40070407306)成功。两者使用Swift6.2.4、SDK26.2、Rust1.99。新版Showcase独立签名副本在本机13.7.8通过启动、唯一main窗口和control inspect，6.575秒结束，未激活、前台PID1390→1390；完整原件、section/签名比较、早期startup gate不足的partial以及原始轮询见[交付证据](../Evidence/macOS13-native-standard-full-app-9dd/README.md)。未经修改的CI原件已移动到交付目录，旧Showcase及重复副本已清理。 Gallery e48原件也已[核验并交付](../Evidence/macOS13-gallery-clean-delivery-e48/README.md)，旧f9 App与重复CLI已清理。其[精确版本三场景记录](../Evidence/macOS13-film-clean-e48fff46/README.md)覆盖immediate/wait/direct独立进程，三者均Glen601，wait/direct全6图的frame对14最大分量差约0.0000098pt；immediate仍差35/36pt，卡宽差约−1.265pt。合同为inactive13，不能扩充为全Film视觉通过。

f9包含HDR路由/系统SDR修复、14原生Pinch路径恢复和音量PopoverButton系统按钮复用。此前两份f9应用均已在本机启动、建立唯一会话并完成window/control inspect；实际Gallery通过原绑定进入Frame、打开音量弹出层并将草稿0.7改为0.55。原始记录见[Showcase历史记录](../Evidence/macOS13-popover/full-app/showcase/report.json)和[当前Gallery记录](../Evidence/macOS13-popover/full-app/gallery/report.json)。组件内native action与关闭对照见[独立组件记录](../Evidence/macOS13-popover/component/README.md)。整应用绑定操作不替代真实鼠标或14/13 Frame视觉对照。这轮没有重拍全部视觉/交互样本，不能把下述0f/46截图改标为f9或9dd。

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
- 13的PQ/HLG High及HLG Standard使用系统MTKView/CoreImage/EDR图层，无Metal时复用NSImageView。严格识别标准cICP编码后才补足旧系统的色空间识别；9dd只将explicit Standard/original/PQ改为复用现SwiftUI Image，并在decode缓存显示用CGImage色空间copy，原图/ICC保留。完整Showcase构建和实际BernImage分支切换均通过限定检查，见下文；High颜色不由此通过。请求HDR看潜在余量，绘制看当前余量，并通过系统屏幕通知更新，避免以启动前的1永久关闭HDR。普通SDR仍用SwiftUI Image；gain-map能力分支保持原逻辑。
- 显示时钟在 13 使用 CoreVideo 垂直同步；14 保留原生显示链接，不以固定 Timer 代替。

## 尚不能通过的项目

当前不能宣称整个阶段已等效完成，也不能进入 macOS 11 或 Objective-C 阶段。

| 项目 | 当前证据与后续条件 |
|---|---|
| Film 初始身份 | 第三轮整应用Last几何在1pt内，14初始Glen、13初始Madras。新14普通效果上游三场景均为Glen，wait/direct原始Film PNG相同，说明Inspector关闭过渡不是该身份的必要条件；immediate仍有约35pt落点差异，且启动窗口恢复/实际resize是混杂。当前f9移植应用在14三场景也均Glen。新增整应用trace已记录14的target始终3，nearest变4，quiet释放后由Bern follow明确写position3→4；13后台trace则nearest保持3。14原生只读快照确认clip709、insets左右234.5、document1638；13使用真实padding。d146诊断候选已使direct初始Glen完整frame对14差小于0.00001pt，默认3及nearest保留。与旧f9同collector对照确认wide约16.5pt偏差旧13已有，First/Last-again/restore候选相对旧13约+0.186pt；首Last仍差且时序/前台条件不同。去插桩的clean修复已提交e48fff46，精确整应用CI40070407306及13三场景运行合同已成功，wait/direct几何吻合，immediate仍差35/36pt且启动恢复/resize历史未分离；不把诊断构建通过套给clean应用，也不改默认值。[事实、原始证据与下一最小trace](macOS13-Film-Initial-Position.md)；不硬改默认值。 |
| 吸附轨迹 | 13 暂在原生惯性结束后校正，14 在原生目标计算阶段吸附；落点与运动过程应分开验收。 |
| 未覆盖控件变体 | `f9e08b1`已让生成器选中的普通volume PopoverButton复用系统圆形NSButton，独立native action检查通过（单次触发、快捷键、disabled、外部打开和WindowServer alpha=0的关闭，与原Button配对一致）；整应用该版本构建、本机启动及Frame绑定打开/编辑均通过；14浅色Frame detail与原生popup已完成f9/上游配对：内容像素与几何一致，主窗侧栏仍有选中配色差异；新增13 active Frame已通过媒体/idle/AX与主要几何，仍有popup/视频色差、Caption/Size宽度约2pt及Size文字约3pt差异。icon风格Menu、显式尺寸等仍有独立路径，不能套用普通IconButton的20pt系统按钮验收。Planner的styled SidebarItem才进入自定义侧栏键盘分支；Showcase/Gallery截图没有覆盖它。 |
| 工具栏 chrome | 13 与 14 自动 sidebar toggle / 标题的位置不同。公开 NSToolbar 临时重排会被下一次 SwiftUI 更新覆盖，不能作为产品修复。新增[完整Showcase标题宿主候选](../Evidence/macOS13-toolbar-title-host-f6/RESULTS.md)仅迁移navigationTitle，四阶段A/B原PNG逐字相同、选定几何最大差0；已停止，不合产品，不追加14CI。仍需其它源级composition或独立原生chrome所有权证据，不能持续争夺delegate/items。 |
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

[严格PQ派生显示验证](../Evidence/macOS13-hdr-candidate/native-pq-canonical-copy13/README.md)现已完成：原file/ICC/provider/布局保留；派生custom和native named源的raw布局/字节相同。bare SwiftUI双列在actual1→2→1的12个ROI、与旧native13基线均逐像素相同。基于此，产品[9dd99b7](https://github.com/Torrekie/Bern/commit/9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0)只替换mac13 explicit Standard/original/PQ路径，复用已有standardImage的方向/fit/clip链；High/HLG/14/template、原缓存/平均色不改。独立只读审查及[完整Showcase CI40066468884](https://github.com/Torrekie/Bern/actions/runs/40066468884)通过，原件已交付。

新增[actual BernImage body验证](../Evidence/macOS13-hdr-candidate/native-pq-product-body13/README.md)使用提取的完整实际图片分支，仅为SDK14.2编译跳过mac15+且13不可达的gain-map decoder。Standard→High→Standard三阶段MTKView为0→2→0；保留观察的两个High视图在fixture cleanup前均已离窗、暂停且关闭EDR，不声称已dealloc。两源图片/缓存的identity/provider/ICC/file/布局/方向/平均色保持；4张Standard图的12个ROI原RGB和ICC归一后均逐像素等于原生oracle及旧native13基线。3.118秒、activation0、前台1390→1390；实际headroom从1升至1.470819后回到1，High捕获时为1.251183，不能称High已达到2或颜色通过。构建保留一个既有switch警告；此夹具不替代完整Showcase视觉。hero快照仍使用原图，尚未纳入本次显示修复。

## 恢复后的14普通效果采集

远程macOS14已实际运行。普通效果[图片run40062046351](https://github.com/Torrekie/Bern/actions/runs/40062046351)和[HDR run40062048900](https://github.com/Torrekie/Bern/actions/runs/40062048900)均成功，复用此前已在13运行的exact binary，不重新构建应用。独立profile.json从NSWorkspace验证reduceMotion/reduceTransparency/increaseContrast均false；图片probe还独立重复记录这三项。第一轮图片40061735500沿用runner的reduced默认值，已分开归档，不能冒充normal；第一轮HDR40061839104缺少profile记录，普通效果重采后的像素与它相同，但仍保持不同证据身份。

新SDK26.2与旧SDK14.2在同一13图片夹具中的框、卡片检测和全部27张PNG一致，只排除这组13条件下本轮编译组合造成的差异；不能据此解释14/13图片首卡高度或其它未测布局。HDR新probe也不能自动覆盖metadata、HLG或实际Hd>1。

上游Film[run40062194628](https://github.com/Torrekie/Bern/actions/runs/40062194628)已成功，使用既有Gallery构建39959549054，每组新进程区分立即关闭、等待关闭、从未打开Inspector；[原始证据与分析](../Evidence/macOS14-film-timing/analysis.json)。首次采集40061845578在建立会话前失败，已根据上游100字节socket上限将测试临时路径缩短；该失败没有Film结果。当前f9应用在14的同场景run40062837456也成功，进一步确认身份差异属于13路径，尚未证明内部绑定变化。

[Frame paired run40065164350](https://github.com/Torrekie/Bern/actions/runs/40065164350)现已成功，[原始A/B与离线复算](../Evidence/macOS14-frame-volume/paired-40065164350/README.md)保留六张原图。两边均通过真实Ready→Paused0、3.2秒idle、native AXPress开关、独立popup窗口、原始ID/ownPID回读及连续四次相同buffer。Frame detail/视频区逐像素相同，Clip/Volume/slider/popup几何完全一致；266×106的独立popup连PNG文件字节也一致。两张主窗均仅侧栏Frame选中行有5284像素灰/蓝差异，捕获时firstResponder未收集，不猜其原因。该结果只覆盖f9/原上游在14的浅色路径，不是13、深色或物理输入验收。

新增[13 active Frame原始对照](../Evidence/macOS13-frame-volume/paired-f9-aot/README.md)使用原件f9的独立签名副本。首次解释器在top-level之前因CryptoKit符号加载失败，原log保留；改用同源AOT后单次运行12.210秒成功，已有AX/Screen/PostEvent权限均true，没有请求系统权限。21次仅投本PID的mouseMoved保活不等于物理输入；真实媒体Ready→Paused0、>3.2秒mounted门槛、native AXPress及15次raw窗口ID/owner回读均通过。三张PNG各有4次相同buffer，前台1390→1390。

13/14的Clip、popup、slider点几何精确相同；可见Volume bezel均20×20且仅差.5pt，speaker ink四边≤1pt。Caption与Size bezel宽度各差2pt，Size文本约左移3pt；Rest及popup文字边界≤.5pt。保留原2x/1x图与ICC后，归一sRGB的closed detail MAE2.76324/255，popup全图4.23794/255（共同完全opaque区5.94792），平面panel明确偏暖且视频也有色值差，不能猜定系统材质、桌面tint或显示器是唯一原因。popup alpha bbox相同，alpha MAE约.00910；不能以这些几何通过宣称颜色完全一致。全部169项证据hash核验，临时app/CLI/AOT程序已清理。

早期Frame40062043370/40062688905/40063364941分别暴露事件窗口身份和AX标识覆盖等采集限制；[40064763940](../Evidence/macOS14-frame-volume/attempt-40064763940/README.md)已通过idle/native几何，首PNG则因NSNumber对象代替原始CGWindowID而失败。这些失败均未进入B、PNG=0。修正仅在外部采集器中，完整成功采集保留原媒体、idle、AXPress及稳定buffer门槛。

背景探针[14 run40063500033](https://github.com/Torrekie/Bern/actions/runs/40063500033)及同一SDK26.5二进制在本机13均完成五组运行，归档见[13](../Evidence/macOS13-window-background/sdk26-content-stable/README.md)和[14](../Evidence/macOS14-window-background/content-stable/README.md)。早期“外框全程不变”断言阻止后两组；诊断已确认原生NavigationSplitView自动加toolbar改变外框，内容尺寸保持。新合同实际通过内容800×520、各variant双buffer像素/几何稳定及不激活条件，并保留真实外框变化。透明detail的跨系统颜色差异已复现，其余四组模式RGB相同；不将手建窗口结果冒充整应用等效。

## 暂停检查点（2026-10-24，北京时间）

此前按用户要求暂停，08:05一次性检查已执行并删除。用户/系统于12:16恢复同一个goal，当前active；实际14运行已恢复，不再因brownout空等。已有实现和上述未通过项均保留，不标记完成。macOS11、Swift5.3、Objective-C和iOS仍暂停。

## 空间控制

只保留需要复核的源码、原始证据和当前候选应用。传输 ZIP、提取后的重复 tar、经哈希验证的重复参考已清理；小型编译试验的 module cache 在完成后删除。没有安装新 Xcode、Swift 工具链或 iOS 模拟器，也不清理用户的窗口历史、其它项目产物或系统缓存。

## e48原件在14的补充状态

[新14复核40071892408](../Evidence/macOS14-film-clean-e48fff46-40071892408/README.md)成功且wait/direct全部几何保持；immediate却为Glen677，而旧参考为565/566、13clean为601。为控制新增startup gate，补做[旧f9同collector40072273422](../Evidence/macOS14-film-f9-current-harness-40072273422/README.md)，其immediate仍565，全部frames与旧f9参考一致。当前不能宣称e48的14三路径均保持，也不据单次跨job观测锁定具体源代码原因。即刻关闭路径、firstLast与resize仍未通过，下一门槛为同VM配对与恢复历史控制；goal继续active，后续11/ObjC/iOS阶段保持暂停。

## 同机 Film ABBA 补充验收

[完整run40074197486](../Evidence/macOS14-film-abba-40074197486/README.md)现已完成f9→e48→e48→f9四组、12个fresh进程、72个完整末态图片frame；normal/active/稳定buffer/独立身份/签名与清理门槛均通过。wait/direct八场景的全部六图几何逐值相同。immediate的Glen中心依次为677、565、677、662，两个源码各自重复也变化，未形成固定源码分组；因此此前跨job565/677差异不能指定为e48的固定源码效应，也不为该未重复关联增加中间构建。这不证明源码绝无影响，更不将13的immediate601标记为等效。

ready宽度900/920/920满足，但高度/恢复时序不同；所有末态捕获才统一920×668。首次Last、resize、首次恢复过程及物理手势仍未验收，跨组像素/ICC本轮未测。详见[Film事实与边界](macOS13-Film-Initial-Position.md)。[源码审查](../Evidence/macOS14-film-source-delta-f9-e48/README.md)确认新增属性/共享闭包会改变14结构，不能只凭runtime guard宣称14结构无差异；本轮未指定根因。

[首次ABBA失败记录](../Evidence/macOS14-film-abba-attempt-40073935416/README.md)完整保留：A1稳定截图后末态AX120ms截断，B1/B2/A2未开始。随后仅把该唯一末态walk改为既有followup的2秒预算，完整六图门槛不变，得到本轮完整结果；两轮不拼接。父任务独立核验失败raw166项、成功raw495项及各自离线总清单。远端已清除自有scratch/download/cache，本机work路径改为唯一归档的符号链接，没有重复保留应用。

## 工具栏标题宿主的完整应用阴性结果

[诊断source f6 / CI40075331576](../Evidence/macOS13-toolbar-title-host-f6/RESULTS.md)基于已交付9dd，只将动态navigationTitle从detail移到整个NavigationSplitView；显式隐藏标题仍走原路径。这是all-macOS诊断候选，不宣称14保持，未合入产品。与9dd工具链、CLI/资源相同，仅GUI不同。本机active13的Buttons→Text→Controls→Buttons四阶段中，A/B原PNG文件与全部RGBA逐字相同，标题header、两层Toggle、sidebar/detail几何最大差0。因此停止此变量，不为阴性结果再运行14CI。

首轮因可选AX属性错误而中止于A首页，B未启动；原68项证据保留。修订采集器区分严格Role/Children树完整性与可选属性错误，2秒AX预算和动作/PNG顺序不动；v2完整134项原始hash通过父任务及离线复核。tree_complete=true仍伴随complete=false，不能说所有AX属性完整。八张稳定原图、normal首尾false、前台恢复、原件全成员复验与清理均有记录；effective Light未断言，仅是同机A/B几何比较。

自有应用副本、两轮observer/cache、诊断exact、传输包均清理，原交付9dd/e48精确GUI及严格签名保持。历史静态清单中有意移除的17个artifact成员由收据列出，当前现存证据另有最终清单。goal继续active，Film即刻关闭/首次Last/resize、chrome、图片布局、HDR/hero等未通过项继续保留；不进入11/Objective-C/iOS。

## Standard PQ hero 的真实静态端点

[本机13旧链证据](../Evidence/macOS13-hdr-candidate/native-pq-hero-baseline13/README.md)现已测得真实BernImage非空hero key→实际Probe/Anchor→原snapshot→原FlightView.draw，不再使用identity hero。两源body与同排原生oracle-top在raw和ICC→sRGB均逐像素相同；hero对同排oracle-bottom在固定progress0/1的sRGB fullRGB MAE却为named18.377760、custom18.385720/255，最大差164/255，各159539/230400像素不同，两phase结果相同。上下oracle自身仍有normalized MAE0.294106/max5的小差异；此前扩写为上下两排都exact的文字已纠正，数值报告未改。所有图均保留原WindowServer PNG/ICC，每phase五次连续相同raw buffer；1.970秒、前台不变、normal三项false、Metal0、原缓存/ICC/provider/identity保持。

该AppKit hero完整区块与锁定上游逐字相同，因此这是13宿主中hero与body不同的证据，尚不能归为移植回归或认定其应改成body颜色。named也失败，不能假定只传cached-derived图已足够修复；已备的optional-display候选尚未应用产品。下一门槛为新SDK编译同一源码、同一个binary在14普通效果与13运行，再比较两宿主的body/hero差值。新增手动[采集工作流](../../.github/workflows/macos14-hero-probe.yml)只构建一次，14不重编。

本轮仅静态端点，manager flight_count0/timer不存在，不声称完整flight、hide/restore、插值、retarget、High/HLG/alpha/EXIF等通过。本机SDK14.2 fixture另有已明示的gain-map编译条件及未使用时钟分支失败保护，原源码和首次失败日志均保留；远程新SDK包移除这两项适配。自有可执行文件及module cache约57.4MB逻辑文件已清理，36项归档hash和父任务独立像素复算通过。goal继续active，后续11/Objective-C/iOS仍暂缓。

新增[同一binary的13/14 hero基线](../Evidence/macOS14-hero-snapshot-40080838898/README.md)已完成：build40080291082成功，首14 job仅因optional原始defaults键缺失而在应用启动前退出、PNG0；只修改该日志读取为nonfatal后，保留实际NSWorkspace normal首尾门槛，runtime-only40080838898复用原已签名binary成功，没有重编。新SDK26.2/Swift6.2.4的13两phase×六ROI在raw/normalized均逐像素等于旧SDK13；原先SDK14 fixture编译适配不再参与这份同binary证据。

14自身hero也不等于body，因此不能把13hero强制等于live body当作已证实14目标。两宿主的`D=hero−body`十色块均值残差之差，MAE5.210863–5.236956、最大113.048334/255，最差cool812的R；父任务独立重算一致。14 hero跨phase还有max1/2的小差异，13各ROI跨phase不变，显示ICC/倍率/潜在余量不同，未指定唯一原因。13/14窗口分别1.612/2.499秒，normal首尾false、前台不变、Metal0、flight0/timer无、缓存不变均通过。optional-display候选未误合产品，公开ImageRenderer colorMode的限定诊断随后已完成，见下节；未拟合颜色或改上游14行为。新包/传输tar939623逻辑字节已清理，原始失败和成功证据分开保留；hero与整阶段继续未通过。


## Hero 色彩格式与系统转换的限定排查（2026-10-24）

[公开colorMode实验](../Evidence/macOS13-hdr-candidate/native-pq-hero-colormode13/RESULTS.md)已完成default→extendedLinear两个独立进程，没有额外模式矩阵。default两phase×六ROI的原始RGB与ICC→sRGB均精确复现原13；extendedLinear保持body/oracle与几何不变，仅hero的normalized fullRGB MAE改变named0.004439、custom0.007953/255，max3/255。跨宿主十色块`(hero−body)13−(hero−body)14`的最大差仍为113.048334/255，主要cool812.R未改善。它是阴性诊断，未合入产品。

[元数据采集40086541042](https://github.com/Torrekie/Bern/actions/runs/40086541042)成功构建并运行14，同一原签名二进制`e4b389d9…7be14`已在13运行。[原始证据和分析](../Evidence/macOS14-hero-cgmetadata-40086541042/RESULTS.md)保留实际`renderer.cgImage`之后的一处观察点：绘制期间只记录格式标量和CGColorSpace引用，全部ICC导出/分类在截图及原窗口teardown之后执行，不读新像素或保留CGImage/NSImage。13、14均为16bpc浮点、64bpp、extendedSRGB，完整ICC均3144字节且SHA256为`2b3aa1645779a9e634744faf9b01e9102b0c9b88fd6deced7934df86b949af7e`；尺寸640×360与320×180跟随实际2×/1×尺度。元数据相同不等于像素、动态范围或显示环境相同，不能把色差归为标签不同。

新13对原13、新14对历史14，各自两phase×六ROI在raw和normalized均精确相同；十色块/灰阶ramp也无差，因此这次观察未改变所测区域。仍不据单次结果宣称普遍零观察效应。最初eager观察版本仅p0有max3/255差、p1精确复现；原图保留，原因未知，不认定ICC查询已被证明是原因。当前deferred版本首尾normal均false、前台不变、无flight/timer/MTKView、原缓存不变；13/14窗口分别2.413/2.476秒。两边截图ICC、倍率及potential headroom仍不同。

[系统Core Image转换实验](../Evidence/macOS13-hdr-candidate/native-pq-hero-native-ci13/RESULTS.md)随后使用SHA锁定的不透明、up、fill640×360→320×180pt@2×输入，仅在实际snapshot边界改用已有cached canonicalPQ→显式源色空间CIImage→RGBAh/extendedSRGB CGImage，保持同一NSImage包装与Flight.draw。默认control仍12ROI全部精确、未创建CIContext；selected分支只改变hero：normalized fullRGB MAE为named0.010739、custom0.018699/255、max3/255，body/oracle全部不变。最大跨宿主残差仍113.048334/255，未解决主色差，未合产品；无自拟tone curve或色块补偿。selected窗口6.791秒，默认1.623秒，均通过既有7.9秒window界限；MTKView=0不意味着CIContext内部没有使用GPU。

以上均只覆盖实际snapshot和固定progress0/1的同图端点，不覆盖完整flight、High/HLG、透明图、其它方向/fit、物理HDR或整应用等效。下一步先审查真实NSImage.draw边界在13可用的公开行为与14变化，只有形成可验证的单一假设才增加运行实验。当前goal继续active，后续macOS11/Swift5.3/Objective-C/iOS阶段仍暂缓；本轮自有缓存与重复构建物的清理见[收据](../Evidence/macOS13-hdr-candidate/hero-color-experiments-cleanup-20261024.json)。
