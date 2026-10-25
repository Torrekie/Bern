# 精确 e48 Gallery Frame 生成源码

[CI40152701810](https://github.com/Torrekie/Bern/actions/runs/40152701810)单次运行成功。固定产品源码为`e48fff46b3a92a28465ad74295bd273a9d69af7d`，采集流程为`84f1f07b927cd4056a57d04d3c52dcdb4859f33a`；本次在macOS15.7.9/arm64、Xcode26.3、SDK26.2、Swift6.2.4、Rust1.99.0生成源码。没有构建Swift应用、运行Gallery窗口或新增macOS14截图。

完整实际[BernGenerated.swift](ci/BernGenerated.swift)为81110B，SHA256 `f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653`。[Frame.component.swift](ci/Frame.component.swift)保留原文件1248–1353行、字节区间[65675,74696)，9021B，SHA256 `9e67b6890dcacdc2f8f84d330c422206dd2c05e19d08c1e2265213e2166d4a67`。它是实际输出的原字节切片，未手写替代生成内容。

采集前后核对631项固定版本tracked输入（crates、Gallery及根Cargo文件）；只允许CLI在生成文件写入之后、`target.plan`之前加入环境变量控制的退出。原CLI为`63af68fa…03d0fa64`，插入后为`0510fef5…2ef3636`。Cargo构建生成器CLI并输出20个生成文件，退出0、停止标记恰好一次；未产生Gallery可执行目录、dSYM或bin。`build.json`声明真正`swiftui-modern-macos`、release、arm64、minimum_macos13.0。这里的631项不是整个外部依赖或工具链的导出。

下载artifact12583158065共80767B。下载器先计算实际ZIP SHA256 `8309227d935aa86b6b8781c09a478b872fa2a6d18149024f40c84d311d4dc565`并与API digest匹配，再校验路径并提取10个成员，最后删除ZIP；保留下载收据及原artifact内清单。完整生成日志只有2360B，原样保留，没有截断。本机未创建Rust/Swift构建缓存或应用副本。

实际Frame在`!bernWindow.idle`内使用原`BernRow(alignment: .center, spacing: 12.0)`。源码中的四项依次是Caption的`BernSplitButton(capsule:false)`、Size的系统`SwiftUI.Menu`、Volume和条件文字Group；源码项数不证明运行时Layout.Subviews代理数。Frame内容显式使用dark。Caption弹出层内的Size Slider与旁边Size Menu是不同控件。

本次补足此前缺失的精确e48生成路径，未修复Caption/Size宽度差，也不把历史f9的13/14截图改标为e48验收。[下一步](next-row-plan/README.md)只在这一真实Row内取得原始宽度查询、分配及实际推进的一项布局事实，避免新增测量调用或猜测native cell属性；先验证观察前后画面保持，再解释数值。该测量尚未实现或运行，没有新增自定义UI或产品补偿。

准备阶段的源码事实、候选、独立审查与静态校验位于`preparation/`；[下载收据](download.json)、[独立复核](result-review/README.md)及[清理与交付哈希核验](root-review/result-and-cleanup.json)随同保留。实际源码/审查仅移动到这一归档，旧work路径为相对别名，没有保留重复payload。整个macOS13阶段仍未验收，goal active；macOS11/Swift5.3、Objective-C与iOS阶段继续推迟。

原始Frame切片保留生成文件的末尾空行；全量Git空白检查只报告这一处`blank at EOF`，未改写原证据。其余文件及该切片的其它空白检查均通过，见[检查记录](root-review/staged-whitespace.json)。
