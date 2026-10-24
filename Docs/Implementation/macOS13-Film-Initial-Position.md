# Film 初始卡片：已知事实与最小区分采样

本项尚未等同。固定上游 A14 与此前移植 B14 的首次 Film 都显示 Glen；本机 C13 显示 Madras。Rust 声明的 `GalleryDraft.centered` 初始值为3。旧外部采集只证明可见身份；本轮整应用诊断现已记录14的nearest变4、释放target后follow把position3写为4，仍未证明原生Binding setter直接写4或首次原生定位的根因。

## 已排除与尚未排除

- A14、B14 的 Patterns、Inspector、Film、Last 最终外框均为920×668点，window version保持4；C13同样920×668点。最终外框差异不能解释卡片身份。
- A14/C13 detail 都从x211起。Inspector稳定显示时，分隔线约x695，右侧实际约224点加分隔线；关闭后detail约709点。不能把实现中的默认300或理想280直接当作实际宽度。
- 初始放大卡本身的四边差值与Last一样在约1点内，且Last双方均为Windowpane。身份差异与最终卡片大小应分开判断。
- A14/B14首次Film的深色PNG相同，浅色仅少数像素相差1级；身份差异不是Combine移植独有。
- 原采集在`show_details=false`后紧接着选择Film，仅在Film出现后等待静态缓冲。C13对应两条命令间隔约0.068–0.303秒，也没有等关闭稳定。
- Inspector修饰器位于Detail的page match外，可与新Film的首次挂载同时经历退出布局。现有GIF只记录Inspector打开和Film→Last，没有关闭→首次Film，最终静态截图不能排除首次布局时序。

以上来自[A14原始记录](../Evidence/macOS14-gallery-normal/reference.json)、[C13比较](../Evidence/macOS13-candidate/gallery-comparison.json)及`navigation.rs`的Inspector生成位置；它们不足以归因某个原生动画或contentMargins算法。

## 本轮三场景实测

[40062194628](https://github.com/Torrekie/Bern/actions/runs/40062194628)运行同一锁定上游build39959549054，harness为2aa4e63，macOS14.8.9、light、普通动态效果。三项辅助功能标志均false，AX及屏幕录制已有权限。三个独立PID/session、最终外框均920×668点，原始PNG与公开AX记录见[本轮证据](../Evidence/macOS14-film-timing/README.md)。

| 组别 | 最终放大卡 | Glen中心x / 宽度（窗口内点） | 首次取得完整AXImage集合 |
|---|---|---|---|
| immediate：关闭后立即进入 | Glen | 566.0 / 268.79975 | 选择命令后0.566秒 |
| wait：关闭且缓冲稳定后进入 | Glen | 601.0 / 267.53479 | 0.225秒 |
| direct：从未打开Inspector | Glen | 601.0 / 267.53479 | 0.704秒 |

wait/direct的Film PNG逐字节相同。Inspector关闭过渡不是出现Glen身份的必要条件。immediate与其余组最终落点仍相差35点；但首组启动为900×652再实际调整到920×668，后两组启动已恢复920×668、resize没有改变尺寸，且每种序列只采了一次。因此不能将这35点单独归因为关闭动画，启动布局历史/顺序也未分离。

取得的Detail AXSplitGroup宽709点，Film AXScrollArea宽240点；后者是可访问性区域，不能当作已测到NSClipView.bounds。早期遍历有截断，Inspector AX快照也未完整到达其内容区，所以没有实际记录484→709的过渡。wait/direct的Madras中心331点比Detail中心565.5点小234.5点，恰与(709−240)/2居中边距相符；这是几何相关性，尚不能确定内部定位/边距更新顺序。

此前40061845578没有任何Film测量：observer把IPC放在长CI输出路径，59字节前缀加42字节socket后缀为101，超过上游100字节限制。路径拒绝由精确源码和路径长度推导，应用日志没有直接打印bind错误。失败原始诊断与完整下载文件清单保留在[failed-ipc-capture](../Evidence/macOS14-film-timing/failed-ipc-capture/README.md)；短/tmp路径修正只改采集器。

## 整应用 direct 对照与已实现的内部 trace

本轮使用真实整应用，而非独立样例。诊断分支[e4c01e4](https://github.com/Torrekie/Bern/commit/e4c01e4df31e7e9a5380285cb4fe8fd01a90b985)基于原 f9，只对 `BernStyle.swift` 追加132行/替换7行诊断；[build40064305202](https://github.com/Torrekie/Bern/actions/runs/40064305202)采用SDK26.2/Swift6.2.4，真实SwiftUI，ARM64/min13。原始绑定、150毫秒静止判断、target赋值顺序和已有View modifier均未更换。仅在 `BERN_SCROLL_TRACE_DIR` 启用时，MainActor最多缓存4096事件，首个expect后约2秒一次写JSON。记录既有回调与显式写入，**没有拦截每次原生Binding setter**；native snap behavior可能离开主线程，其回调也未插入日志。

[未插桩 f9 direct40064744315](https://github.com/Torrekie/Bern/actions/runs/40064744315)与[诊断 direct40064766856](https://github.com/Torrekie/Bern/actions/runs/40064766856)均为macOS14.8.9，light、normal三项false，分别用新进程直接从Patterns进入Film。两者最终六张AXImage的完整frame逐值相同：Glen中心601.0、宽267.53479，Madras中心331.0；外框920×668、Detail宽709。两者Patterns PNG逐字节相同；Film PNG不同，不声称整图逐字节一致。诊断自己的首次Film与trace写出后Film PNG逐字节一致，均经过4次相同原始buffer比较。因此诊断已复现相同身份和已测几何，但不能宣称所有调度没有观察效应。

诊断文件为 `scroll-1579.json`（SHA256 `80fe7a3166efe9d8a4f6feae0ccc1e46c8010a082f70412232fb1ad6c011070b`），102个事件、drop0、一个position实例，以及分别标记的snap/largest实例。相对首次expect的时间如下；同批geometry先后由真实时间戳记录，不从源码声明顺序推断。

| 时间 | 已记录事实 |
|---|---|
| expect前约0.3毫秒 | position viewport变为709×207；id3 frame x564/width240，snap viewport709、largest240×159 |
| 0毫秒 | onAppear以position3执行expect(nudge:false)，明确target nil→3、placed=true |
| 0.65毫秒 | snap body计算margin234.5=(709−240)/2 |
| 9.68毫秒 | id3 report x798.5；目标观察回调为nil→3 |
| 46.97毫秒 | id3 report x234；约145毫秒settle算nearest3 |
| 147.76毫秒 | id3 report x0、id4 x270；viewport仍709，随后settle算nearest4 |
| 300.05毫秒 | 原150毫秒quiet任务有效唤醒，coming清空、stops变1 |
| 301.02–301.47毫秒 | 原回调释放target3→nil；follow随后明确把position3写为4 |

这次已实际观测到框架的nearest/follow写回3→4；此前的“内部轨迹未观测”仅适用于旧外部采集。目标观察回调只出现nil→3→nil，未记录target4；不能据此断言原生setter的每次瞬间写入均已覆盖，也不能改称“系统把target写成4”。在最终report坐标中，id3覆盖x0…240，而nearest仍以完整709的中心354.5计算，故id4中心390更近。这解释了本次框架为什么选择4，**尚未解释为何原生定位最终产生该坐标**。234.5的边距相关性仍不等于确定因果；该e4采集本身没有真实NSClipView/document/contentInsets快照，也未记录原生snap retarget；后续744快照已补静态原生布局，见下。

## 13与14的明确源码边界及下一步

两支都使用同一 `tracked`：geometry更新anchor/viewport后settle；onAppear执行expect→target=position→placed=true；在最后目标geometry后150毫秒释放target；只有target为nil时follow才写position。不能仅凭这些声明推定SwiftUI实际回调先后。

14由原生 `.scrollPosition(id:$target,anchor:)` 消费目标，native `contentMargins` 负责边距；snap在item尚为0时也按当时viewport计算margin。13由 `ScrollViewReader` 的target回调执行 `proxy.scrollTo`，首次不动画；目标仍非nil时，margin preference变动会再次 `scrollTo`。13在largest尚0时将legacyMargin设0，测量完成后改真实SwiftUI内容padding，命名snap坐标含padding，并在每个ScrollView边界消费/reset margin preference。它们不是同一定位机制，13不能在没有证据时硬模拟14的偏移或把默认改成4。

### 同构建13后台诊断

[本轮完整归档](../Evidence/macOS13-film-scroll-trace/README.md)保留两次active采集未交付的partial及一次成功的显式 `inactive13` 诊断。第一次在Patterns之前失焦，没有记录activation返回；第二次唯一activation请求返回false，约2.05秒的38个样本均保持Messages PID437。两次都未选择Film、没有PNG或scroll trace，不是产品Film回归结论。

成功后台诊断使用同一e4构建的代码，observer为a332bd4，唯一bundleID与ad-hoc签名隔离本机历史。原exact bundle和CLI不变；本地GUI签名使完整exe hash改变，所有section hash相同、只归一签名存储字段后的payload相同，详见归档的isolation provenance。这与14原bundle环境不同，不能简写为完整二进制逐字节相同。

后台模式不请求activate/恢复前台；27次截图前记录均为Simulator PID35793、ownGallery PID64326、ownCGWindow9675、alpha1。窗口/alpha/原始buffer经过4次相等比较，Film与trace写出后PNG相同。采样点之外没有原子性的持续失活保证。13为本机2x后台，14为runner1x前台，**不构成同条件active视觉验收**。

13最大卡仍Madras：AX中心565.5、宽268.8，Detail宽709，和旧13卡片身份/中心/宽度相符，不能据此宣布颜色/材质与所有布局等同。其AX遍历有截断，未观测项目不补造。内部trace94events/drop0、一个position实例：

| 13相对expect时间 | 事实 |
|---|---|
| 0 / 0.70毫秒 | target设3；margin计算234.5，viewport709×207 |
| 12.33 / 13.43毫秒 | margin回调持target3并调用Reader重定位；首次target回调以原center scrollTo3 |
| 27.97毫秒 | id3 report到x234.5，随后保持 |
| 72.75毫秒 | settle计算nearest3 |
| 225.18–228.35毫秒 | quiet完成、target释放nil；follow因nearest与position同为3而不写4 |

因此已记录的分歧在quiet/follow之前：两边一度都报id3约x234，14随后变0，而13保持234.5。不能通过更改nearest或默认值来掩盖首次定位差异。

### 后续14原生快照与候选边界

Root的[原始原生快照与源码](../Evidence/macOS14-film-timing/native-snapshot-40066003179/README.md)来自独立诊断[744e316/build40065764593、run40066003179](https://github.com/Torrekie/Bern/actions/runs/40066003179)仅在原2秒flush追加公开AppKit只读快照，不改变之前回调。active14、111个view无截断：真实HostingScrollView/clip为709×207，clip.bounds.x=564；document宽1638，contentInsets左右234.5、autoAdjust=false。document宽正好等于6×240+5×30+2×24，没有13的额外469点SwiftUI padding。故AXScrollArea240不是clip宽。

这支持一个**仅首次安装阶段、尚待候选验证**的坐标假设：若14按有效内容长度 `Ve=V−2m` 应用目标anchor，而13Reader按完整 `V` 定位，目标长度为 `L`、轴向anchor为 `a`，非clamp时两边目标origin相同要求 `a′=a(V−2m−L)/(V−L)`。本样本a=.5且L=Ve，结果为0；它不能等同于无条件改leading。另一种“固定减leading margin”的式子 `a′=a−m/(V−L)` 在a=.5也相同，现有数据不能区分其它anchor的语义。当前生成器只有snap:center配.center，非center为leading/top且margin0；helper任意anchor不应扩大为已证范围。

margin0应保持原anchor；一致的largest≥L条件下，L≥V会推出margin0，避免0/0。未知/nonfinite/尚未证明L≤Ve的短暂测量不应夹负anchor或写AppKit偏移。resize及目标长度变化可能需要新计算，但targetnil或用户接管后不得重新夺回。**旧13的Last已在1点内匹配14**，首次快照没有证明后续animated target或snap retarget遵循同一公式，因此不得全局套到全部programmatic scrollTo。

下一小步只准备独立work候选：限13首次still-owned target阶段，采用实际axis/viewport/margin/目标frame，在已存在回调中有界重定位；保留默认3、nearest、150毫秒quiet、release/follow、后续Last与用户接管路径。先审确切diff和重定位触发门槛，再由单次direct+Last+resize验证；当前没有产品修复或视觉等同通过声明。
