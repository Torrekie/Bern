# macOS 分阶段兼容计划

当前分支：`macos13-swiftui-baseline`。原始上游基线固定为 `ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee`。

上一轮 `e5d1e7e` 的共享 Objective-C 运行时保留为实验候选。它证明了两个入口使用同一套实现，不能证明与真正的上游 SwiftUI 等效。新的移植顺序以 **swiftui-modern → macOS 13 真 SwiftUI → macOS 11 / Swift 5.3 → Objective-C** 为准；iOS 暂停。

## 顺序与通过条件

| 阶段 | 当前范围 | 进入下一阶段的条件 |
| --- | --- | --- |
| 1：macOS 14 → 13 | 审查真正的 `swiftui-modern`；优先使用新编译器、新 SDK 和旧 target。只替换确实需要 14 运行时的能力。每次只处理一个可验证切片。 | 锁定的原实现与迁移实现有可比较的运行证据；配色、布局、操作、状态变化与动画差异逐项处理。不能只以编译通过判定等效。 |
| 2：13 → 11、Swift 5.3 | 以阶段 1 通过的 macOS 13 SwiftUI 为基线，分别收紧 API 与语言语法边界。 | 按本任务约定，以本机 macOS 13 的运行对照，加 macOS 11 API / Swift 5.3 源码边界验证作为验收，不额外要求 macOS 11 设备。不能只以 Swift 5 语言模式代替 5.3 语法审查。 |
| 3：SwiftUI → Objective-C | 以阶段 2 的真实 SwiftUI 实现为参照，逐个控件与交互移植。尽可能使用系统 AppKit 控件。 | 相同输入、状态、尺寸、语言和外观下的界面及交互一致；必要自定义组件明确说明。旧实验实现须重新对照，不能自动视作通过。 |
| 4：iOS | 暂不实现、构建或下载运行时。 | 本机空间充足且存在可调用的 iOS 17 模拟器，再建立 SwiftUI 基准并开始对照。 |

阶段 1 当前状态：**本表所列有限源码审查与本机编译尝试完成，等效移植尚未开始；macOS 14 运行基准待采集。**

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

生成器仍无条件编译整套模板。缩小测试页面不会自动隔离其余依赖；构建原实现的 SDK 还必须能识别 26 系 glass 等声明，仅有 15.5 SDK 仍不够。先分清模板编译边界与页面验收范围，再逐步迁移。

## macOS 14 参考证据

使用三组对照隔离迁移与系统差异：

1. A：锁定上游现代实现，用足够新的 SDK 构建 target 14，在真实 macOS 14 运行。
2. B：迁移后的同一 SwiftUI 切片，在 macOS 14 运行，先与 A 比较。
3. C：与 B 相同的迁移实现，在本机 macOS 13 运行，再比较系统差异。

新 SDK 的构建主机与 macOS 14 的运行主机分开。不能使用 `macos-latest` 的成功结果充当 macOS 14 运行证据；它当前指向较新系统。现存上游截图没有可靠的系统版本标记，且早于当前示例内容，只作为设计参考。

每组固定源码/资源/输入、内容区尺寸、语言、外观、强调色、窗口活动状态、显示缩放和减少动态效果设置。已有 `BERN_SNAPSHOT_DIR` 是视图缓存绘制，会遗漏部分实时材质，需要真实窗口截图补充。没有截图权限或没有图形会话应明确失败，不把缓存快照当成替代证据。

GitHub 官方现仍列出 arm64 `macos-14`，但将于 **2026-11-02** 退役；2026-10-23 北京时间 **22:00 至次日 08:00** 有故意失败时段。不能将这类失败归为 Bern 回归。依据：[镜像列表](https://github.com/actions/runner-images#available-images)、[退役公告](https://github.com/actions/runner-images/issues/13518)。

本地账号对上游只有读取权限，尚未发现可复用的 Bern fork。先准备可审查的手动 CI 工作流，发布到哪个用户仓库及是否创建 fork 另行明确；目前没有远程写入或触发任务。
