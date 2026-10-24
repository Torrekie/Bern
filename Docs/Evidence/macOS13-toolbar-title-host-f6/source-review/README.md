# macOS13 toolbar composition 只读审查

本记录只追踪当前真正 `swiftui-modern` 的 Scene、标题和 toolbar 责任边界；没有产品补丁、编译、运行、GUI 操作或 CI。来源文件的 HEAD、路径和 SHA256 见 `provenance.json`。现有截图/原生框测量均来自较早记录，本次没有重采，也不声明修复。

## 实际生成链与所有权

- `examples/showcase/Bern.toml:78–81` 与 `examples/gallery/Bern.toml:41–44` 的 `macos_modern` 显式选择 `swiftui-modern`；对应 `crates/bern-backend-swiftui/src/lib.rs:157–158,205–223` 的 `SwiftUiMacos`，不是较早引入的 AppKit/共享原生入口。
- `src/swift/app.rs:218–260` 对普通窗口生成 `SwiftUI.Window(Text(verbatim: 本地化 Window.title), id:)`，不是 WindowGroup，也不自行 new NSWindow。主窗口再包 dialogs、engine environment、defaultSize/min-size。此处没有 windowToolbarStyle 或显式 NSToolbar。
- `src/swift/windows.rs:69–113` 为每个窗口保留 StateObject context，并生成 `BernWindowRoot { BernSearchPaletteHost { 实际组件 } }`。随后才按窗口声明挂 `BernWindowBehavior`、theme、session/environment。`BernRuntime.swift:2123–2212` 的 root 管启动错误、modal/hero、alert、平台挂接、尺寸与环境；不直接设置 NSWindow.title 或 toolbar.items。
- `src/swift/navigation.rs:29–99,127–168` 生成 NavigationSplitView → Sidebar List / detail Group。detail 的 `.navigationTitle(selectedSidebarLabel)` 在 `.toolbar` 和 `.bernInspector` 之前；整个 split 上还有 sidebar 控件注册和 fallback。`nav_label` 在 `:352–366` 逐项匹配当前选中值，未匹配才回退 `bernWindow.title`；后者是 `BernRuntime.swift:640–643` 中 Window 声明的本地化标题。Scene 的 Gallery/Bern Showcase 与 detail 的 Patterns/Buttons 等是两个明确的标题输入，不能用固定标题替掉动态选中标题。
- **自动 sidebar toggle 没有 Bern 显式 ToolbarItem**；它由 NavigationSplitView/SwiftUI 供应。`src/swift/toolbar.rs:8–50` 只提取源 Toolbar 内容：普通 Search 被分离为 searchable；其余生成系统 ToolbarItem/ToolbarItemGroup。`:130–211` 中 Spacer 前为 `.navigation`，剩余在 macOS 为 `.automatic`，Picker 独占 `.principal`。macOS26 spacer/背景分支在13/14不执行。Showcase page 子组件上的 Toolbar 由 `src/swift/layout.rs:111–114` 等内容容器挂载，所以不能假定只检查 split_view 自身 detail.children 就覆盖全部 toolbar 来源。
- `BernAppKit.swift:45–89,499–521,624–668` 只读回 Scene 创建的 window，注册系统窗口事实和 openWindow/openSettings。close guard 在需要时代理 NSWindowDelegate；这与 NSToolbarDelegate 不同。当前模板没有安装 NSToolbar、重排 items 或直接写 window.title 的产品代码。

## Showcase 与 Gallery 并不共享同一个最简组合

Showcase (`examples/showcase/showcase-ui/src/lib.rs:106–129,143–176`) 是标准 chrome 主窗口，sidebar 含 Search，按页切换独立组件；Buttons 页有 automatic Button toolbar，Controls 页有 principal segmented Picker（`pages.rs:76–78,115–117`）。split sidebar 在有 search 时直接用原始 ranged width。Gallery (`gallery-ui/src/lib.rs:82–85,138–244`) 无 sidebar search，有 footer，detail 是持久 toolbar + toolbar Search + 可变页面 + Inspector。无 sidebar search 的 macOS 分支改用 `bernSidebarColumnWidth`，其13首次 ideal 预热和恢复选择见 `BernAppKit.swift:671–740`。

Gallery `idle_after:3` 使 windows.rs 挂 BernWindowBehavior（Showcase 不挂）。Gallery 未声明 unified/immersive，默认 Standard 来自 `bern-ir/src/lib.rs:487–496` / `bern-compiler/src/lib.rs:630–632`。`BernAppKit.swift:1530–1548` 因而将 fullSizeContentView 清除、titlebarAppearsTransparent=false、titleVisibility=visible、toolbar.isVisible=true；这条路径也在14执行。它不拥有 toolbar 的 item 顺序，但不能从 Gallery 的 composition 隔离里删掉。

Gallery inspector 在14是系统 `.inspector`，13是包裹原 detail 的 HSplitView（`BernStyle.swift:5221–5248`），标题/toolbar modifier 位于这层 wrapper 的内部。因而 title 偏好传播和挂载形状存在需要实测的层级边界；源码不足以判定这就是几何差异根因。

## 已有负例的边界

1. `Docs/Evidence/macOS13-toolbar-role`：automatic / split-editor / detail-editor 共9次隐藏、非 key 样本，toggle hosting x153.5/w39.5、graphics center173.25、Buttons title field x199，均不动。只是固定标题 Showcase 式 Scene，不覆盖 Gallery/动态标题传播。
2. `work/toolbar-scene-fixture`：8种 detail/outer **toolbar**、automatic/unified、Button/Picker 组合共24样本仍相同。关键是 `ToolbarProbe.swift:53–54` 在 outer 两支都把 **navigationTitle 留在 detail**；没有测下述单变量。
3. `work/navigation-view-toolbar-fixture`：NavigationView 自动方式失去 toggle；显式 navigation toggle 又回到13位置。已有动态标题和程序调用 collapse/reopen 结果，无需重复该迁移。
4. `work/native-toolbar-owner-fixture`：Scene window + NSViewControllerRepresentable 拥有原生 split/toolbar 已证明所有权能稳定。Showcase visible ink 几何接近14；Gallery toggle 仍偏17.25pt，且原搜索 suggestions/query/focus 未等效。不是可以直接采用的产品修复。已有 tracking separator、isNavigational、compact/small/no-space 比较，不再排列这些候选。

这些记录中 native view frame、glyph canvas、可见 ink 是不同量；例如旧 fixture title field x199 不能直接减去参考可见文字 x154，得出所谓45pt同类框差。旧 native-owner captures 为 inactive/dark，参考为 active/light，只能保留其限定的几何结论。

## 下一最小隔离：只迁移 navigationTitle 的宿主

候选尚未写代码。对一个精确来源的现代生成输入复制件做 A/B：A 保持当前 detail Group 上的 `.navigationTitle(同一动态表达式)`；B 只将该 modifier 移到完整 NavigationSplitView 上，紧跟 `navigation.rs:156` 的 split 闭合之后、sidebar bernControl 之前。不要同时移动 toolbar/search/inspector、改变 Scene/title 文本/role/style、替换容器、强制栏宽、增加偏移/固定 RGB，或接管 delegate/items。`Detail(titled:false)` 不属于当前两个 app；若将来扩大范围，需单独处理其隐藏标题语义，不能凭该 A/B 宣称已支持。

此变量检查 **标题偏好归属的 composition 是否改变系统对自动 toggle/title 的放置**，不预言会有效。与先前“把 toolbar 挪到外层”不是重复。最低成本先按实际 Showcase 生成层级（包含 BernWindowRoot/SearchPaletteHost/context/动态页 toolbar）隔离，保留 SwiftUI.Window；若本机13完全无几何变化，记录阴性并停止，不为了这一候选新增14 CI。若确有改善，再以相同输入在14配对，再扩大到含原有 Inspector wrapper 的 Gallery。不得先把固定标题极简探针当作整应用通过。

### 采集与门槛

- 必须是独立新身份、未写入历史的自有实例；A/B 同一原始构建来源、observer、语言/appearance、像素倍率归一化方法及启动/resize顺序。记录真实创建/ready window.frame、contentRect/contentLayoutRect、safe-area、sidebar实际宽度和每次时间戳，不能只对后期920×668断言通过。初始栏宽/内容尺寸应与对应未修改基线一致，不用强制 setPosition 掩盖变化。
- 先观察 Showcase Buttons→Text→Controls→Buttons；确认每次 NSWindow.title、可见 title NSTextField 和 sidebar 控件 label 都更新为正确本地化选中名；页 toolbar 项存在且只一份，Button action/Picker state 仍对应原 registry，title 不消失或重复。Gallery 有效后再 Patterns→Favorites→Frame→Patterns，Inspector真实开关，不替换成无 panel detail。
- 对每个稳定阶段分别记录 sidebar toggle 的 toolbar item/view frame、可见 glyph canvas、title field frame、可见 ink、系统窗口按钮 frame、toolbarStyle/items身份、sidebar与detail frame。每阶段至少3个相等原生几何样本和稳定自有 CGWindowID buffers；native geometry 与同条件14对照以≤0.5pt作为提升门槛，可见 ink 以≤1pt（注明1×/2×栅格误差）衡量。任何仍有明显间距/标题排列差异都只能记部分改善。不能把AX hit框当可见边界。
- sidebar collapse/reopen 要记录控制状态和展开宽度返回；同次页面选择/搜索/Inspector变更后再采一轮，确保无需手动重排或异步争夺所有权。若开始出现改善，才追加一次窄/宽窗口检查，必须保留真实 resize 顺序与 content尺寸，避免初始history混淆。
- 仅内存绑定/程序 action 不能算焦点交互通过。保留原 search 的编辑、提交、建议、取消；记录真实 firstResponder/field-editor 与 focused 状态，快捷键/AX action 后对应正确自有窗口。13/14 的 `BernSearchable`（`BernStyle.swift:1020–1054`）只有15+将 FocusState接入 searchFocused；更早分支设置 focused 的实际效果在此源审查中未知，须以各自原始基线实测，不顺带宣称本候选修复。若未做物理键鼠/IME，应明确仍未通过。
- 活跃/非活跃窗口分别保留，只有相同 activeState/appearance/ICC 下才做颜色或像素等效判断。隐藏 fixture 不能替代用户可见的 active full-app验收。若运行时拿不到这些条件，只报告几何，不升级结论。

本候选只复用现有 SwiftUI/AppKit 系统元素，不需要新绘制的 UIView/UIControl/NSView 控件。它没有经过编译或运行；当前 chrome 等效仍未验收。
