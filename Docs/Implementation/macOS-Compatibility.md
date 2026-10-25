# macOS 分阶段兼容计划

当前分支：`macos13-swiftui-baseline`。原始上游基线固定为 `ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee`。

上一轮 `e5d1e7e` 的共享 Objective-C 运行时保留为实验候选。它证明了两个入口使用同一套实现，不能证明与真正的上游 SwiftUI 等效。新的移植顺序以 **swiftui-modern → macOS 13 真 SwiftUI → macOS 11 / Swift 5.3 → Objective-C** 为准；iOS 暂停。

2026-10-25 用户澄清适用于后续所有阶段：Bern 应生成符合目标平台逻辑的 UI，不要求像素级复现。优先使用系统 SwiftUI / AppKit / UIKit 控件，保持内容、语义布局、状态和交互正确；细微的系统配色、间距、控件描绘及动画轨迹差异允许保留，不为消除它们创建自定义控件。当前具体检查以[原生逻辑验收合同](macOS13-Native-Logic-Acceptance.md)为准。

## 顺序与通过条件

| 阶段 | 当前范围 | 进入下一阶段的条件 |
| --- | --- | --- |
| 1：macOS 14 → 13 | 审查真正的 `swiftui-modern`；优先使用新编译器、新 SDK 和旧 target。只替换确实需要 14 运行时的能力。每次只处理一个可验证切片。 | 锁定的原实现与迁移实现有可比较的运行证据；原生外观可读、布局可达，操作、状态及动画终态正确，处理实质缺陷。允许细微版本差异，不能只以编译通过判定等效。 |
| 2：13 → 11、Swift 5.3 | 以阶段 1 通过的 macOS 13 SwiftUI 为基线，分别收紧 API 与语言语法边界。 | 按本任务约定，以本机 macOS 13 的运行对照，加 macOS 11 API / Swift 5.3 源码边界验证作为验收，不额外要求 macOS 11 设备。不能只以 Swift 5 语言模式代替 5.3 语法审查。 |
| 3：SwiftUI → Objective-C | 以阶段 2 的真实 SwiftUI 实现为参照，逐个控件与交互移植。尽可能使用系统 AppKit 控件。 | 相同输入、状态、尺寸、语言和外观下，内容、语义布局与交互一致，符合目标系统惯例；允许细微原生描绘差异。必要自定义组件明确说明。旧实验实现须重新对照，不能自动视作通过。 |
| 4：iOS | 暂不实现、构建或下载运行时。 | 本机空间充足且存在可调用的 iOS 17 模拟器，再建立 SwiftUI 基准并开始对照。 |

阶段 1 当前状态：**按目标平台原生逻辑标准，已审查的兼容路径及Showcase/Gallery代表性流程验收通过。** 新SDK构建target13与本机13.7.8运行有原件；Gallery连续关闭详情/外观切换、实际媒体挂载/离页和Showcase真正聚焦的键盘输入/单次提交均已补足。通过范围与未扩大的能力限制以[原生逻辑验收合同](macOS13-Native-Logic-Acceptance.md)为准；[旧验收日志](macOS13-Acceptance.md)与下文保留历史审查、比较和采集路线，不再附加像素门槛。

当前仅推进 macOS 13。macOS 11 / Swift 5.3、Objective-C 与 iOS 不进入本轮。新增的复用视图只用于确实缺失的系统能力：变化观察、Inspector、滚动协调、按键协调，以及旧系统 PQ/HLG 图片的系统 MTKView EDR 呈现；普通控件和页面继续使用 SwiftUI。系统显示时钟使用 CoreVideo 垂直同步，不替换为固定计时器。

首轮已通过 5 项后端 Rust 单元检查、1 项现有 Canvas/叠层布局生成检查，以及公共兼容文件在本机 target 13 的类型检查。它们尚不能代替使用新 SDK 编译完整应用。13 的吸附目前在原生惯性结束后校正，轨迹与 14 原生吸附不同；Inspector、额外大控件、焦点环、滚动相位和 EDR 画面仍待实际对照。

## 本机实际工具与组合尝试

2026-10-23 的宿主为 arm64 macOS 13.7.8。仅检查了已存在的工具，没有下载、安装或切换全局开发环境。

| 来源 | 实际编译器 / SDK |
| --- | --- |
| `/Applications/Xcode.app` | Xcode 15.2、Swift 5.9.2、macOS 14.2 SDK |
| Command Line Tools | Swift 5.8.1；还存在独立的 macOS 15.5 SDK |
| Downloads 中的旧 Xcode | Xcode 13.4.1、Swift 5.6.1、macOS 12.3 SDK |

没有在常见 Xcode、Developer/Toolchains、swiftly 或 swiftenv 安装位置发现 Swift 6。独立 SDK 的存在不代表有配套的新 Swift/Clang。

使用现有的 `showcase_generates_swift_that_type_checks` 检查，生成的是真正的 `SwiftUiMacos` 输出，而非共享原生桥接。只构建了生成器的该项检查，没有链接完整 Rust 应用或调用 iOS 工具。

| 尝试 | 结果与含义 |
| --- | --- |
| 上游配置：Swift 6 语言模式、target 14 | 本机 Swift 5.9.2 报 `invalid value '6' in '-swift-version 6'`。这是编译器门槛，不是 target 门槛。 |
| Swift 5.9.2、独立 15.5 SDK、target 13.0 | 在头文件/PCH 处失败：`module '_stddef' requires feature 'found_incompatible_headers__check_search_paths'`。不能将较新 SDK 与旧编译器强行混配后，把结果误判为 macOS 13 不支持。 |
| Swift 5.9.2、自带 14.2 SDK、target 13.0；诊断性地采用支持的 Swift 5 语言模式 | 首个已暴露诊断是生成的 `BernEngine` 报 `'Observable()' is only available in macOS 14.0 or newer`。未修改原源码或抑制可用性检查；这个依赖确实需要低版本实现，后续诊断不能视作已解决。 |

Rust 仍保留上游 1.99 要求。本机仅为运行生成器检查使用已安装的 1.94.1 和 `--ignore-rust-version`；这不表示修改了项目的 Rust 支持要求。

后续优先复用 CI 的新工具链构建 target 13，再将小型应用产物拿到本机运行，避免提前处理 Swift 5.9 语法和旧 SDK 的声明缺失。Swift 5.3 语法约束仍留在第二阶段，不为此下载本机开发环境。

## 第一阶段的有限审查清单

| 部分 | 实际边界与处理方向 |
| --- | --- |
| 观察机制与环境 | `BernRuntime.swift`、`BernMedia.swift`、`BernStyle.swift`、`BernAppKit.swift` 和 `src/swift/values.rs` 的 `@Observable` / 类型式环境需要 14。13 路径可用 `ObservableObject`、`@Published` 及对象环境；必须保留状态所有权、焦点、视图身份和更新时序。 |
| `onChange` | 新零参数/双参数及 `initial:` 重载需要 14。旧重载与首次出现处理需保持 old/new、初始化和注销的语义，不能仅替换拼写。 |
| 滚动 | `scrollPosition`、吸附、`scrollTransition`、`contentMargins`、默认锚点需要 14。逐项补足定位、惯性、边距和效果；不能删除修饰器作为等效实现。 |
| 侧栏、键盘、放大手势 | Inspector、`onKeyPress`、`focusEffectDisabled`、`MagnifyGesture` 有 14 边界。保留 SwiftUI 页面，必要时局部桥接 AppKit 的 responder/滚动协调；不全局吞键或干扰输入法。 |
| 空白/错误状态、按钮形状 | `ContentUnavailableView` 和部分 ButtonBorderShape 需要 14。保持图标、文字、重试、可访问动作及按钮按压状态。 |
| Settings / 激活窗口 | `OpenSettingsAction`、新 `NSApplication.activate()` 需要 14；13 可继续保留 Settings scene，用已有 AppKit 路径打开和激活。 |
| HDR 图片 | `.allowedDynamicRange(.high)` 需要 14。不能将 SDR 降级直接声称为 HDR 等效；亮度范围作为独立能力处理，普通 UI 先使用固定 SDR 对照。 |
| 13 小版本 | popover 的 `presentationBackground` / `presentationCompactAdaptation` 需要 13.3；目标 13.0 时仍须处理。 |
| 只缺 SDK 声明的接口 | 当前使用的 `onGeometryChange` 单值 action 重载可回部署至 13，但本机 14.2 SDK 无声明。有配套新编译器/SDK时优先保留，不先重写。 |
| 更高 SDK 的分支 | glass、ToolbarSpacer、TextRenderer 等有运行时分支，但全量模板缺少编译期隔离，旧 SDK 仍需识别这些名字。必须与实际 14 运行依赖分开。 |

`Layout`、Grid、NavigationStack / NavigationSplitView、ImageRenderer 已在 13 可用；Canvas、Material、AppKit 语义色、普通 spring 动画更早就存在。第一阶段保留这些实现，不因兼容任务重写它们。

建议首个行为验收切片是现有 `controls_page` 的 SwiftUI Form、通知开关、音量滑块和已提交音量页脚：检查拖动预览、结束时只提交一次、状态回写、语言切换及焦点。仅有 Hello/计数截图不足以验收观察机制迁移。

第一次修改可先保持 target 14，只迁移生成的 `BernEngine` / `MainDraft` 与对应环境注入，在同系统比较观察机制变化；通过后再迁移 target 13 无条件触达的窗口、Host、语言、搜索宿主和媒体启动链。草稿 setter 必须先通过 Rust 校验再发布，快照加载不能回写 setter，整体失效不能重建窗口或中断拖动。有限切片的通过不能扩大为整个 modern 后端已经支持 13。

生成器仍无条件编译整套模板。缩小测试页面不会自动隔离其余依赖；构建原实现的 SDK 还必须能识别 26 系 glass 等声明，仅有 15.5 SDK 仍不够。先分清模板编译边界与页面验收范围，再逐步迁移。

## macOS 14 参考证据

使用三组对照隔离迁移与系统差异：

1. A：锁定上游现代实现，用足够新的 SDK 构建 target 14，在真实 macOS 14 运行。
2. B：迁移后的同一 SwiftUI 切片，在 macOS 14 运行，先与 A 比较。
3. C：与 B 相同的迁移实现，在本机 macOS 13 运行，再比较系统差异。

新 SDK 的构建主机与 macOS 14 的运行主机分开。不能使用 `macos-latest` 的成功结果充当 macOS 14 运行证据；它当前指向较新系统。现存上游截图没有可靠的系统版本标记，且早于当前示例内容，只作为设计参考。

每组固定源码/资源/输入、内容区尺寸、语言、外观、强调色、窗口活动状态、显示缩放和减少动态效果设置。已有 `BERN_SNAPSHOT_DIR` 是视图缓存绘制，会遗漏部分实时材质，需要真实窗口截图补充。没有截图权限或没有图形会话应明确失败，不把缓存快照当成替代证据。

GitHub 官方现仍列出 arm64 `macos-14`，但将于 **2026-11-02** 退役；2026-10-23 北京时间 **22:00 至次日 08:00** 有故意失败时段。不能将这类失败归为 Bern 回归。依据：[镜像列表](https://github.com/actions/runner-images#available-images)、[退役公告](https://github.com/actions/runner-images/issues/13518)。

手动工作流见 [macos14-reference.yml](../../.github/workflows/macos14-reference.yml)，采集脚本见 [macos14-reference.swift](../../.github/scripts/macos14-reference.swift)。它分离上游源码与采集脚本，用新 SDK 构建 target 14，然后把同一个产物送到 macOS 14；不在旧运行主机重新构建。采集固定外框的 light/dark 控件页及 CLI 状态变化，记录显示缩放、色彩空间、强调色与辅助功能偏好。CLI 未暴露内容区精确尺寸；鼠标、键盘与动画仍须后续实际验证。

本机已通过工作流 YAML、内嵌 shell 语法和采集脚本的 Swift 类型检查。已创建公开 [Torrekie/Bern](https://github.com/Torrekie/Bern) fork 并发布两个 CI 文件；远程默认分支仅比创建时的上游增加这两个采集文件，未发布本地旧实验后端。

首次采集：[39943744831](https://github.com/Torrekie/Bern/actions/runs/39943744831)，采集脚本提交 `69af5582318d33c734b84ba5d13c538efd05ea53`。应用源码仍为固定的 `ffbdbdf`。

构建 job 已通过：arm64 macOS 26.6.2 / Xcode 26.6 / SDK 26.5 / Swift 6.3.3 / Rust 1.99.0；生成应用的 Info.plist 与 Mach-O 均为最低 macOS 14.0，签名验证通过。这确认了新 SDK 配旧 target 的构建路线，但不证明 13 可运行。

采集主机确为 arm64 macOS 14.8.9 / Xcode 15.4 / Swift 5.10。第一轮在采集脚本的窗口筛选链式表达式处发生 Swift 类型检查超时；未启动应用，不能归为上游运行失败。已拆为显式循环并通过本机类型检查；工作流支持复用已有构建产物、只补跑采集。

补跑采集：[39946674436](https://github.com/Torrekie/Bern/actions/runs/39946674436)，脚本提交 `377b488810db926a2486ef2a75c58ca0dc628a2f`，复用第一轮的同一应用归档，构建 job 跳过。采集通过：真实窗口为 920×668 点/像素、1 倍缩放；浅色初始音量 50，CLI 提交后为 73、通知关闭；重新启动后的深色初始值仍为 50。三张原始 PNG 已逐张检查，未编辑或缩放。屏幕录制权限预检通过。

**该 runner 开启了减少动态效果和减少透明度。** 因此本次只建立这些设置下的颜色/布局与 CLI 状态参考，不能作为普通透明材质或动画的完整证据；也未验证真实鼠标拖动、键盘、输入法或手势。第一阶段仍未等效完成。

保留的证据约 260 KB：

- [浅色初始窗口](../Evidence/macOS14-reference/controls-light.png)
- [浅色提交后窗口](../Evidence/macOS14-reference/controls-light-after-commit.png)
- [深色初始窗口](../Evidence/macOS14-reference/controls-dark.png)
- [源码、环境、截图校验与完整 CLI 结果](../Evidence/macOS14-reference/reference.json)

构建应用未下载到本机；本机仅保存上述原始参考图和合并后的文本记录，已清理传输归档、重复证据副本与完成的编译缓存。

### 普通外观参考

[39956399796](https://github.com/Torrekie/Bern/actions/runs/39956399796) 复用同一上游构建，已在可丢弃的 CI 主机上关闭减少动态效果和减少透明度，并由 `NSWorkspace` 检查生效。三张真实窗口采集通过：

- [浅色](../Evidence/macOS14-reference-normal/controls-light.png)
- [浅色提交后](../Evidence/macOS14-reference-normal/controls-light-after-commit.png)
- [深色](../Evidence/macOS14-reference-normal/controls-dark.png)
- [环境、校验与命令记录](../Evidence/macOS14-reference-normal/reference.json)

它补足普通设置下的静态材质/颜色参考；单张截图仍不能证明动画时序或真实鼠标拖动行为。没有修改本机的辅助功能偏好。
