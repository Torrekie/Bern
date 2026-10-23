# modern SwiftUI：macOS 14 → 13 剩余 API 等同审计

审计源码：`outputs/Bern`，最终快照 `5226454`（原始上游 `ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee`）。只读检查了 modern SwiftUI 的所有共享 Swift 模板、Mac AppKit 模板及 Rust Swift 生成器；未以旧 Objective-C 原型作为基线。没有 Rust 构建、UI 运行、下载或远程操作。

后续进展：`f9e08b1` 已为生成器选中的普通图标 PopoverButton 复用系统 `NSButton`，保留手写 helper 默认行为及有样式/显式尺寸/toolbar 等排除条件；未修改通用圆形样式或 Menu。独立窗口的 native action 检查已通过，该版两整应用已构建并在13启动，Gallery Frame绑定打开/编辑已通过；14/13 Frame实图对照仍待验收。以下正文保留 `5226454` 审计时的发现；当前状态以[验收记录](macOS13-Acceptance.md)为准。

唯一获另行授权的产品修改是 `BernPinch`：14 恢复原 `MagnifyGesture`，13 使用 `MagnificationGesture`，倍率与提交公式不变；已由父任务提交。局部 Swift5.9.2/SDK14.2 target13 类型检查通过，夹具用 `@MainActor` 模拟产品构建的默认 MainActor 隔离；完整新源码 CI 仍是独立门槛。

下面的“差距”区分 **确定采用近似实现** 与 **实际交互尚未验收**。仅有不同 API 不直接等于已复现缺陷。源码行号均为当前快照。所有 `Style`/`Runtime`/`Media`/`AppKit`/`Compatibility` 缩写指 `crates/bern-backend-swiftui/templates/Bern*.swift`；生成器路径以 `crates/bern-backend-swiftui/src/swift/` 为根。

## 最值得先验证的遗漏：Frame 音量弹出按钮

Gallery 的真实原例 `examples/gallery/gallery-ui/src/lib.rs:397` 定义 `PopoverButton(id: volume, icon: speaker.wave.3.fill)`。`controls.rs:278–299` 给它 `.bernButtonLook(.icon)`，**没有经过**只包裹普通 `IconButton` 的 `BernCircularIconButton`。

调用链：`Style:875–879` → `bernCircleBorderShape`（5071）→ 13 的 `BernLegacyShapedButton`（5110）；13 给 label 水平 padding8、垂直6、最小32×32，填 regularMaterial、0.5pt stroke、pressed brightness 与 disabled opacity。14 使用系统 bordered + circle。它保留实际 SwiftUI Button 激活，但其几何/材质/按压画法确实是近似。普通默认 IconButton 的20pt验收不能覆盖此入口。

最小下一项无需新页面：原始 Gallery 进入 **Frame**，保持窗口有活动、在 idle 隐藏前比较 volume 关闭/打开、禁用与键盘焦点。记录真实窗口中按钮对齐框、绘制框、弹出层锚点及一次操作只打开一次。先取得14/13原例实图再选择原生 AppKit 小桥接；本轮没有修改此组件。

## 剩余影响与原例入口

| 优先级 / 性质 | 源码位置；13 实际行为 | 原始例入口 / 最小验证 | 尚未等同的精确范围 |
|---|---|---|---|
| 高：确定近似的圆形/圆角形状族 | Style5071–5130；controls77–86、220；toolbar327。非桥接入口继续自绘上述32pt圆形；prominent IconButton 用自绘 rounded rectangle（radius12） | 首先 Gallery Frame `volume`（397）。`Menu(style: icon)`、显式 width IconButton、prominent IconButton 在现有原始例中未找到对应实例，需以后最小 API 样本 | 普通 IconButton20pt不代表 PopoverButton/Menu/显式宽度/prominent 的几何、材质、焦点、按压均通过。显式 height 圆形走 BernCircleControl，13/14本已共用该路径，另行区分 |
| 中：确定近似的 extra_large | Style5187–5195；controls239–249。13用 large +17pt font +横6/纵4 padding；14用系统 extraLarge | 当前原始例没有 `size: extra_large`；最小独立 style! Button { size: extra_large }，与 regular/large 并排，记录自然尺寸、baseline与hit target | 字体+padding不证明系统extraLarge的自然尺寸、内缩、bezel与focus等同；Planner的 Button.hero 仅 large，不能覆盖 |
| 中：按键与焦点处理不同，实际效果待测 | Style1275–1292、5134–5162。13 List.focusable/focused +局部 NSEvent monitor；没有14的 focusEffectDisabled。13拒绝任何 Cmd/Ctrl/Option/Shift，仅在 marked text 时排除 NSTextView | **Planner** `planner-ui/src/lib.rs:25` 的 SidebarItem style 和87起 main_window。Showcase/Gallery未定义SidebarItem样式，因 navigation.rs30–63 的条件不会进入此分支 | 焦点环是否露出、修饰箭头的选择行为、普通文本编辑不被抢键、跨窗口/移除后不吞键。不能把本地monitor view自身 focusRingType=.none 当成已抑制 List 焦点环 |
| 中：媒体键盘处理不同，实际效果待测 | AppKit1279–1287、1294–1342。13 monitor只收无修饰方向键，并拒绝所有 NSTextView；14 onKeyPress没有相同显式过滤 | Showcase Media，`showcase-ui/src/media.rs:27/56` 的可播放 Video，Media907/943 的进度与音量 scrubber。Gallery Frame controls:none 不覆盖 | 普通箭头、长按repeat、各修饰箭头、disabled、焦点切到文本框/另一窗口。源码只证明过滤谓词不同，不能未经运行断言14如何分派修饰键 |
| 中：Inspector 容器近似 | Style5083–5104；toolbar56–94。13 HSplitView、面板按binding条件插入，宽默认300或给定width，min=.8×/max=1.5×；14 native inspector | Gallery `gallery-ui/src/lib.rs:217` width280。已有打开/关闭静态样本；新增只需真实拖分隔线、窄窗口、隐藏再显示及状态保留 | 拖拽轨迹、宽度保留、窄宽下内容挤压、focus/辅助功能列语义尚不能从原生HSplitView的存在推得等同；没有擅加关闭栏 |
| 中：nudge 完成与中断时序待测 | Style2545–2641。14 withAnimation completion；13真实 AnimatableModifier 观察scale1.06和每次progress终值，再异步返弹；带request/mount guard及注销清理 | Gallery Film `lib.rs:284` arrival:nudge；Frame381 nudge:dragging。单击Last/First可达前者；后者需要真实拖入/移出文件 | 不是计时器假完成，但短促0.08s峰值、重复触发、中途离页、减弱动态效果仍无足够采样的时序对照；已有约0.14s间隔GIF不能证明峰值 |
| 中：Pinch 真实输入待测（14路径已修复） | Style2644–2695。14原MagnifyGesture，13MagnificationGesture；都start×倍率/clamp、结束commit | Gallery Patterns/Favorites `wall`，`lib.rs:264` pinch_cards | 原生触控板事件与ScrollView同时手势、缩放两方向/clamp、结束只commit一次、被取消时状态。局部类型检查只证明availability，不证明手势等同 |
| 较低：open_at 仅初次布局实现 | Style5183–5185、4889–4904；layout574–594。13在首次尺寸有效时直接设置clip origin，最多8次20ms重试，之后initiallyPositioned阻止再次定位 | 原始例没有 `open_at:`。以后最小 ScrollView(open_at:1) 分别用普通和lazy内容、初始空后异步变长、resize | 当前源码没有持续的anchor布局策略；是否与14 defaultScrollAnchor在上述情况下相同需对照。不能拿已通过Film position/snap样本替代此API |
| 较低：13.0–13.2 popover外观分支未跑 | Style5167–5180。13.3+用presentationBackground；更早只给content添加regularMaterial背景和scheme | Gallery Frame `caption` SplitButton389 / `volume`397，原始popover内容可复用 | 本机13.7.8根本不进入更早分支；content背景不能由源码证明等同系统popover整个chrome/透明区。无额外旧系统安装/设备要求 |
| 较低：显示时钟语义待测 | AppKit742–944。14 CADisplayLink；13 CVDisplayLink真vblank，向调用者runloop派发，支持隐藏/屏幕更新及停止清理 | 默认 AVFoundation 视频不一定运行此路径（Media140–154、679–691）；现有原始例未找到自定义media kernel消费者 | 13 timestamp由target减nominal period；遮挡通知存在但refresh不直接检查occlusionState。当前无证据表明实际缺陷，也不能凭普通Video播放认定该时钟已等同 |

## 完整分支覆盖核对（不重新认领已有验收）

| API / 位置 | 13替代与判定 |
|---|---|
| Combine环境/所有权；Compatibility7、28–33；Runtime/Style/Media各观察类；app/windows/values/mod/drawing生成器 | Mac统一ObservableObject/Published、EnvironmentObject/StateObject与显式presentation订阅；13和14执行同一路径。已有同系统A/B证据；本轮未发现新确定状态遗漏，不把源码审计扩成所有模块已运行 |
| onChange；Compatibility47–50、89–137 | State previous +稳定最新action box，old/new及initial有真实实现；没有自我返回。重入、重现、卸载等精确时序可另验收，但本轮无确定bug。实际入口含Runtime初始adaptive尺寸、navigation381动态可见目的地回退与语言/主题 |
| ContentUnavailableView；Runtime2023–2055、Media754–783 | 13固定字体/间距SwiftUI替代、动作保留。已有Query错误与媒体空白实图校准，不重复判为未实现。新长文本/窄宽换行仍未覆盖；入口Showcase Library查询（pages245–251）、Media损坏35/Preview56 |
| openSettings、activate；AppKit141–152、652–665 | 注册modifier在13直接content，但host有真实showSettingsWindow:/showPreferencesWindow:替代；activate使用旧系统API。不能将单个self分支认作设置功能丢失。已有实际Settings证据 |
| default圆形IconButton；AppKit1348–1510、controls77–99 | 已复用系统NSButton并校准，不重复fixture；仅将此桥接明确排除的入口列在上表 |
| named coordinateSpace；Style2164–2171 | 13旧API同名空间替代；不是no-op |
| scrollTargetLayout；Style2174–2181 | 13直接self，但每item的bernSnapItem/bernScrollItem实际几何注册已接替targetlayout；不是功能被删除。snap空间和position空间有独立注册 |
| scrollTransition、snap、contentMargins；Style1950–2181、4816–5075 | 已校准相位/真实SwiftUI padding/作用域；本轮不重跑。仍保留已记录的惯性结束后160ms再校正、180ms动画轨迹差异，14原生在目标阶段选点 |
| scrollPosition；Style2389–2500 | 13ScrollViewReader实际定位、用户接管清target，已记录初始Film身份差异；此问题不因Last落点通过而关闭。本轮不重复fixture |
| allowedDynamicRange/HDR识别；Runtime2223–2648 | 13表面modifier的self由HDR原图路径上的MTKView/系统SDR转换接替；High未等同已在Docs独立列明。保持本轮SDR局部通过边界，不重跑HDR |
| 其它platform self | tvOS无pointer/popover/本机form差异等原有设计不属于Mac13兼容替代；UIKit模板不在本轮实现/运行范围 |

## 13和14本来就共同降级：不能误报为这次13回归

| 更高系统API / 位置 | 13和14实际共同执行 | 原始入口 |
|---|---|---|
| toolbar(removing:.title)，Style941–949 | 15前直接self，所以13/14都没有这个修饰器能力。现有13/14 toolbar chrome位置差异仍是独立真问题，不能靠这个no-op解释完毕 | Planner main Window(lib78)有immersive；titled:false生成路径存在但原例未找到使用。具体窗口差异已有Docs记录 |
| searchFocused，Style1016–1058 | 15前不把FocusState附到searchable；shortcut和外部focus只写未连接的state。是上游本有的低系统能力限制，13与14相同 | Showcase sidebar_search(lib145)；Gallery toolbar find(lib170,cmd+k)。Gallery此处是默认searchable，不是style:palette |
| TextRenderer，Style1807–1840 | 15前Text(mark:)是underline，不是胶囊逐行highlight | Planner overview lib131 mark:accent；不能用当前14基线期望15的capsule效果 |
| ImageIO gain map HDR decode，Runtime2555–2560 | 15前普通decode，13/14都未用DecodeToHDR新API | Showcase Images layout中gain-map JPEG；PQ识别和High问题另列 |
| mac26 glass/toolbarSpacer/sharedBackground，Style868/921/4034/4160、toolbar147/171/188 | 13/14共用bordered/material和旧ToolbarItem组合。26视觉不是本轮基线 | Showcase/Gallery常规button、toolbar、capsule等 |
| Media26系统slider（Media990）、AppKit27 icon-only tabs（AppKit347） | 13/14共用旧scrubber与带标题tab | Showcase Media；Gallery About tabs |
| Mac Form section gap/heading，Style4728–4743 | Mac本来只设置minRowHeight；iOS专用sectionSpacing/contentMargins没有移植回Mac，此点13/14相同 | 原始Form各页；当前图片首section高度差另有真实证据，不能归咎此处新no-op |

## 建议顺序和验收边界

1. **Gallery Frame volume闭/开**：最小现有例、直接覆盖仍在用的近似圆形组件；与已通过默认IconButton区分。先测再改，无需扩UI/API。
2. **Planner styled sidebar键盘/focus + Showcase媒体scrubber键盘**：两页静态截图无法覆盖，先测试普通/修饰箭头、文本焦点和跨窗口；不根据源码谓词提前断言最终系统分派。
3. **Nudge/Pinch真实短动画与输入**：保留实际状态/引擎提交次数证据；不要把程序化绑定或低帧率GIF标为触控板/鼠标验证。
4. extra_large、open_at、没有原例的圆形Menu/显式尺寸/角色组合，用小型原API样本补覆盖；不必为此重写整个API或扩大工具链矩阵。

High HDR、Film初始身份、吸附轨迹、toolbar chrome、图片首卡高度、环境材质配色等既有未通过项继续见 `Docs/Implementation/macOS13-Acceptance.md`。本报告没有将“可编译”或“源码有替代”升级为全UI等同通过。
