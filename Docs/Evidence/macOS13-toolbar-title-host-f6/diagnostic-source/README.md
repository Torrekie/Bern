# navigationTitle host — diagnostic only

只准备诊断候选；未发布、未建 branch、未编译、未运行、未触发 CI，未更改 `outputs/Bern`。基线是已交付 Showcase 的精确来源 `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`。补丁仅触及 `crates/bern-backend-swiftui/src/swift/navigation.rs`；`navigation.rs` 是该文件的完整候选副本，patch 可应用到该基线。

## 选择和成本

| 方案 | 隔离变量/代价 | 本次处理 |
| --- | --- | --- |
| 全 macOS 标题宿主迁移 | 最小单文件 diff；不引入新的 SwiftUI availability 条件树。13、14及更新系统均改变标题宿主。 | **仅此诊断候选**；先13检查阴性/阳性。 |
| 生成运行期 `if #available(macOS 14, *)`，两臂各生成完整 split |14臂可保留原 modifier 顺序，13臂迁移；但复制整段生成内容，且外层增加条件类型/结构身份，是第二个 composition 变量。保留14臂内容不等于保持14运行效果。 | root 已要求停止；没有准备或保留此补丁。仅13诊断阳性后重新评估。 |

**本候选14+也会改宿主，未保持14，不能合入产品。** 最终13-only实现和14对照仍是独立门槛；不能把这份诊断通过当成产品完成。

## 精确改动

1. 同一个 `title` 仍由既有 `nav_label(selection, sidebar.children, "SidebarItem")` 产生；文本、语言、当前选中项与未匹配回退 `bernWindow.title` 均未改。
2. 只在生成平台为 Macos、且原规则未识别显式 `Detail(titled:false)` 时，把 `.navigationTitle(title)` 从 detail Group 移到完整 NavigationSplitView 闭合后、sidebar bernControl 之前。toolbar/search/Inspector/width/role/Scene/原生 items/delegate 不改。没有新增 SwiftUI `if`、Group、AnyView 或 availability wrapper。
3. 显式 `Detail(titled:false)` 仍走原 detail `.navigationTitle` + `.bernToolbarTitleHidden()` 路径，且不在外层添加 title。识别条件与原有隐藏判断相同：`self.expr(titled)` 恰好为字符串 `false`，不扩大为运行期表达式求值。
4. 基线 `BernStyle.swift:941–954` 的隐藏 helper 在13/14返回 self，15+才 `toolbar(removing: .title)`。这里保留的是**原始行为及源码顺序**；没有声称修复13/14已有的隐藏能力限制。非 macOS 平台原生成路径也保留；未执行生成器，不能冒充生成输出逐字比较已跑过。

## 类型和隔离边界

- 对普通带标题 macOS split，detail 移除 title modifier、outer split 增加同一 modifier，opaque SwiftUI body/detail 类型及偏好传播归属随之变化。这正是诊断变量；不是布局 no-op。
- 不改变页面 match 的源码 arm、选择值或 action，但新的宿主类型可能影响 SwiftUI 内部状态/偏好传播/挂载次序；实际行为未知。14和更新系统同样受此影响。
- 生成器新增的 Rust `if`/let-chain 只决定输出 `.navigationTitle` 的位置，不把新条件树写进生成 Swift。原有标题隐藏判断会多做一次纯文本表达式生成；没有新目标侧状态、定时器、几何查询或原生对象。
- 没有 SidebarItem 时 `title=None`，不会在任一宿主新增标题；此次诊断不扩大该行为。
- 先按上一层 README 的13 Showcase 几何/动态标题/侧栏/焦点门槛采集。13无改善就记阴性停止；阳性也需后续13-only方案与14真实对照。此文件不能直接覆盖正在交付或运行的 app。

## 已做的静态检查

只在自己的临时 GIT_INDEX_FILE 中从精确基线 read-tree，并以 `git apply --cached --check --whitespace=error-all` 验证 patch 可应用和空白有效；临时 index/lock 已删除。未写主仓库 index/working tree/branch；此检查不是 Rust/Swift 编译或目标运行验证。
