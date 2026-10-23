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
| 原生交互 | 通知 AXPress 改变会话草稿；音量 AXIncrement 从 50 到 60，只产生一次引擎提交；Command-Comma 打开原生 Settings scene | 这些不是鼠标拖动验证；CLI 状态与原生 AX 操作分别记录 |

第二轮已验证源码为 `0f5226d0dcdf2c7cbd50db3e1745d58d5d1a6532`：

- [Showcase 构建](https://github.com/Torrekie/Bern/actions/runs/39969189803)
- [Gallery 构建](https://github.com/Torrekie/Bern/actions/runs/39969189761)

macOS 14 上的 A/B 对照使用此前的 `fa820f706e5faf1bae8b8f07e23545842a1648b7`；此后的按钮、占位页和滚动相位校准均限制在 13 分支。不要把旧源码的对照扩充成新源码已经在 14 再验收。

## 参考与采集方式

原上游固定为 `ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee`。新 SDK 构建与旧系统运行分开，应用不在 14 运行机上重新编译。普通参考的减少动态效果、减少透明度和增强对比均关闭；没有修改本机这些设置。

| 证据 | 内容 |
|---|---|
| [Showcase 原始参考](../Evidence/macOS14-reference-normal/reference.json) | 13 张 WindowServer PNG，涵盖浅/深色控件、Text、Buttons、Inputs、Query 错误/空白/恢复、图片、Video 状态；[采集](https://github.com/Torrekie/Bern/actions/runs/39961818954) |
| [Gallery 原始参考](../Evidence/macOS14-gallery-normal/reference.json) | 8 张浅/深色 PNG，4 个 Inspector/滚动 GIF；[采集](https://github.com/Torrekie/Bern/actions/runs/39964126654) |
| [同系统迁移比较](../Evidence/macOS14-port-comparison/comparison.json) | 每张图片的 RGB 比较、原始文件哈希、不同 PNG、图片页差异测量；相同图片复用 A 的原图，避免重复保存 |

Gallery 的外观由它自己的 Light/Dark 动作设置，不能只给进程环境变量，因为示例会显式恢复 System。最终静态 Gallery 参考在连续 5 次 WindowServer 缓冲相同后采集。早期误标深色的图片不作为深色依据。

GIF 实际采样间隔约 0.135–0.147 秒，第一帧间隔可能更长；GIF 的播放延迟不是采集帧率。它们只说明程序化状态变化，不能证明 60fps、触控板惯性或短促 nudge 的峰值。

本机显示器为 2 倍缩放，14 CI 为 1 倍。13 的原始 PNG 保留 2 倍像素；比较几何时换算为点，比较颜色时读取 ICC 并统一到 sRGB。不同屏幕、焦点和系统原生材质的差异不能用整数像素全图相等掩盖。

## 必要的局部复用组件

- `BernCompatibility.swift` 保留 ObservableObject 所有权、对象环境及旧 onChange 的当前闭包和 old/new 语义。
- 13 Inspector 复用 `HSplitView`，内容仍为原 SwiftUI；滚动仍为系统 SwiftUI ScrollView。
- 缺失的按键监听只作用于当前窗口和焦点，不全局吞键；文本编辑与输入法仍需单独实测。
- 普通无显式尺寸的圆形 IconButton 复用 `NSButton`。toolbar、bar/group、显式宽高、plain/prominent、custom look、cancel 保留原路径；destructive、enabled、快捷键、AX ID 与最新 action 转接系统属性。
- PQ/HLG 使用系统 MTKView/CoreImage/EDR 图层；普通 SDR 仍使用 SwiftUI Image。gain-map 的系统能力分支保持原逻辑。
- 显示时钟在 13 使用 CoreVideo 垂直同步；14 保留原生显示链接，不以固定 Timer 代替。

## 尚不能通过的项目

当前不能宣称整个阶段已等效完成，也不能进入 macOS 11 或 Objective-C 阶段。

| 项目 | 当前证据与后续条件 |
|---|---|
| Film 滚动相位 | 14 的独立真实窗口校准已确认有效 viewport、居中阈值与 easeInOut 曲线。13 整应用发现 NSView 探针坐标与 SwiftUI 实际绘制相差内容边距，导致相邻卡片被放大；必须修复并重拍，不能减去一个固定 item 当成修复。 |
| 吸附轨迹 | 13 暂在原生惯性结束后校正，14 在原生目标计算阶段吸附；落点与运动过程应分开验收。 |
| 工具栏 chrome | 13 与 14 自动 sidebar toggle / 标题的位置不同。公开 NSToolbar 临时重排会被下一次 SwiftUI 更新覆盖，不能作为产品修复。需要验证源级 composition 或独立原生 chrome 所有权，不能持续争夺 delegate/items。 |
| 默认侧栏宽度 | 同一范围偏好 min180/ideal210/max320，在 13 新窗口选择180，而14为210；额外 frame 无效。单参数210会锁死调整范围，已排除。比较内容时可记录并通过原生 AX 把实际宽度设为210，但这不算默认行为已修复。 |
| 图片页 1 点差 | 14 A/B 对齐后 footer、Layers、gain-map 完全相同；PQ 残差最大2级。下一步连拍并记录首个 section 高度，区分稳定测高与时序，不能用负 padding 抵销。 |
| 真正鼠标拖动 | 当前自动化鼠标没有把拖动送达；尚未证明“拖动时只预览，松手仅提交一次”。AXIncrement 单次提交不替代它。 |
| 物理 HDR、输入法、完整动画时序 | 未验收。当前屏幕可用 EDR 为1，潜在为2；SDR 截图不能证明 HDR 亮度等效。 |

GitHub 的 macos-14 在 2026-10-23 14:00 UTC 至次日00:00 UTC 进入公告的故意失败时段，并计划11月2日退役：[官方公告](https://github.com/actions/runner-images/issues/13518)。已取得的普通外观参考继续可用；该时段的 runner 失败不能归为源码失败。

## 空间控制

只保留需要复核的源码、原始证据和当前候选应用。传输 ZIP、提取后的重复 tar、经哈希验证的重复参考已清理；小型编译试验的 module cache 在完成后删除。没有安装新 Xcode、Swift 工具链或 iOS 模拟器，也不清理用户的窗口历史、其它项目产物或系统缓存。
