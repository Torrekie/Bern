# Scene showsTitle：只读排除审查

**现有留存记录没有实际测试 Scene 层的 `UnifiedCompactWindowToolbarStyle(showsTitle: false)`，该开关尚不能算已排除。** 本结论限于当前源码、Git现有全部refs及本任务保留的toolbar证据；不推断它能移动sidebar toggle，也不把API存在当编译或运行通过。

已测变量彼此不同：

| 留存记录 | 实际变量 | 不能外推的部分 |
| --- | --- | --- |
| [Scene fixture源码](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/work/toolbar-scene-fixture/ToolbarProbe.swift:170)及其README | automatic vs `.unified(showsTitle: true)`，detail/outer toolbar与Button/Picker | 没有compact，也没有showsTitle=false |
| [editor-role源码](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/Docs/Evidence/macOS13-toolbar-role/ToolbarProbe.swift:32) | automatic/split-editor/detail-editor；9个隐藏非key框样本阴性 | toolbarRole是View角色，不是Scene标题开关 |
| [f6完整应用结果](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/Docs/Evidence/macOS13-toolbar-title-host-f6/RESULTS.md:3) | navigationTitle由detail移到完整split；四阶段A/B原PNG逐字同 | 没有改Scene style或showsTitle；此变量已停止 |
| [native-owner源码](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/work/native-toolbar-owner-fixture/NativeToolbarProbe.swift:103) | 自建整套NSToolbar后写NSWindow.toolbarStyle.unifiedCompact，并保持titleVisibility.visible | 不等同SwiftUI管理的toolbar或Scene showsTitle；其compact曾出现38pt顶部高度 |
| [先前只读window方案](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/work/toolbar-next-public-window-plan/README.md:11) | 已明确Scene compact路径未测；仅提出原SwiftUI toolbar的一次性NSWindow setter | 方案不是运行证据，也不能代替Scene modifier |

[当前Scene生成器](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/crates/bern-backend-swiftui/src/swift/app.rs:234)只生成Window、defaultSize、windowResizability；没有windowToolbarStyle。针对compact/showsTitle=false的源码与Git历史搜索没有找到该Scene候选的实现或采集记录。搜索命令与输入hash保存在audit.json。

本机SDK14.2确有该公开接口，实际路径是`Versions/A/Modules/SwiftUI.swiftmodule/arm64e-apple-macos.swiftinterface`：

- [Scene.windowToolbarStyle:20920](/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk/System/Library/Frameworks/SwiftUI.framework/Versions/A/Modules/SwiftUI.swiftmodule/arm64e-apple-macos.swiftinterface:20920)：macOS11.0起可用。
- [unifiedCompact(showsTitle:):27154](/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk/System/Library/Frameworks/SwiftUI.framework/Versions/A/Modules/SwiftUI.swiftmodule/arm64e-apple-macos.swiftinterface:27154)：macOS11.0起可用。
- [UnifiedCompactWindowToolbarStyle及init:27169](/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk/System/Library/Frameworks/SwiftUI.framework/Versions/A/Modules/SwiftUI.swiftmodule/arm64e-apple-macos.swiftinterface:27169)：同样macOS11.0；显式`init(showsTitle:)`存在。

因此目前Swift5.9/SDK14.2/target13具备声明层面的使用条件；本次没有编译。也不由此宣称整个现代App已经支持macOS11/Swift5.3。

若继续，最多先做**一个本机native13 Boolean pair**：复用既有Showcase式真实App/Window Scene与Buttons页，同一源码/二进制只以不可变输入选择`UnifiedCompactWindowToolbarStyle(showsTitle: true)`或`false`，其它标题、toolbar宿主、role、sidebar/search和布局不变。两个新身份实例即可，不开样式/页面矩阵。A/B都用compact，才能只归因showsTitle；把automatic直接换成compact(false)会同时改变style与标题参数。该小pair只测试原生Scene机制，不能替代完整Bern应用验收。

保留原始窗口/内容框、toolbar高度/style、NSWindow.title字符串与**实际可见标题**、toggle item/图形框、sidebar/detail边界和原图。不要用额外resize或content高度补偿掩盖style变化；getter仍有标题字符串不代表标题可见。

停止条件：任一侧出现已知52→38pt高度差、标题消失/重复、控件丢失/裁切，或Boolean pair没有保留标题与几何的改善，就记录边界后停止此候选；不补自定义标题、不抢delegate/items、不加偏移/重复setter，也不为阴性再开14CI。若只得到隐藏非key几何，则保留该scope，不升级为颜色或用户交互等效。只有小pair保住结构并出现可核改善，才值得另行处理实际完整App范围；本审查不预告成功或要求新增矩阵。

本次只读源码、接口与历史证据，只写此小审查目录；没有UI、编译、CI、cache或产品修改，也没有重启已停止的width诊断。
