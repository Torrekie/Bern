# e48 Gallery source-export preflight facts

固定commit `e48fff46b3a92a28465ad74295bd273a9d69af7d`，tree
`9b028204744063ae5c23a336a4eb32dbb41b6d86`。只读Git对象，无生成、编译、UI、CI或Git写入。

`examples/gallery/Bern.toml`实际声明macos_modern为macos / swiftui-modern / ipc；
ui.sources=`gallery-ui/src/lib.rs`、root=`app`。协议来源gallery-protocol/src/lib.rs，
engine包gallery-core。实际Gallery输入仅9文件：Bern.toml、三个crate各Cargo.toml/src/lib.rs，
media/poster.jpg及media/tides.mp4。audit.json包含全部路径、字节数与SHA256，无资源复制。

真实DSL：`examples/gallery/gallery-ui/src/lib.rs`，22898 B，SHA256
`9840fcaa199b643842f490e89b071ba7b1c9af76e8857354cc4240100f525f07`。

- `app` :80，WindowSet primary main :82；main Window :83，900×600、initial open、idle_after3；
  main_window调用 :84，另有about dialog :86。
- main_window :132；sidebar pages :139，Frame选项 :142；Page::Frame→`frame(app: app)` :191。
- Frame组件真实名为`frame` :378，session为GalleryDraft；外层Drop :380，Stack强制dark :381。
- Caption SplitButton(id caption) :389；内部“Caption text” :390、Size Slider(id caption_size) :391，
  draft.caption_size初始13 :60，范围11–20；相邻Size Menu(id caption_sizes) :393，Small12/Large18。
- 整个控件Row受`if !window.idle` :387约束；padding/Video corner也随idle变化 :385–386。
  不从窗口light推Frame内容light，不把idle隐藏误判为生成缺失。

CLI `crates/bern-cli/src/main.rs`原45322 B / SHA256
`63af68fa7f763b118ca34ed432b0f1b9fdfa2b3190582ebde747135303d0fa64`。
原needle `        let plan = match target.plan(&app, &context) {`只出现一次，:917；
target.generate :876，文件写入 :901–911、Generated日志 :913–916均在其前。
旧精确6行BERN_DIAGNOSTIC_GENERATE_ONLY hook可复用，插入后预期SHA仍为
`5a05a83bf51900641e88f0502d6acd39e6446c62427324a4542af55d23ff8233`。

旧picture INPUT_PATHS仅将examples/showcase换为examples/gallery，e48实际为**38**项
（公共29+Gallery9），不能保留55硬断言。这覆盖直接SwiftUI emitter/src/swift、names、glue、
resources/style、mac模板与Gallery声明资源，不能称完整generator依赖闭包。
例如SwiftUI glue.rs直接委托bern_target_api::glue；compiler/IR/syntax/protocol、target-api
icon/svg/style、theme及其它CLI/SwiftUI编译模块不在38项中。audit.json列出Cargo依赖证据。
保持固定HEAD/tree、起始全tracked clean、结尾全repo仅CLI有tracked diff，就能对其余tracked
源保留更广边界；不必复制整仓，但不要把selected38的逐文件清单写成“全部生成输入”。

供root审查新候选的具体断言：

1. SOURCE_SHA=e48；manifest精确Gallery路径、target macos_modern、release；input集合38且逐项
   bytes==该Git对象；全tracked clean，CLI原SHA/needle唯一，无已有hook。
2. hook只在全部生成文件写入后、target.plan之前env gated early return；只有CLI tracked mutation。
   先记录cache，再只清repo/target/bern/macos_modern，保留Rust cache；旧生成源不得充作新结果。
3. 原backend src/lib.rs :272–283明确输出`Sources/BernGenerated.swift`（实际文件名），另有
   BernCompatibility/Runtime/Media/Style/AppKit、bern.h、glue与build.json；没有独立BernApp.swift。
4. 导出实际新BernGenerated.swift，记录非空、字节数/SHA、实际build.json、日志rc0和marker1，
   min13/profile release/ui swiftui-modern；拒绝产品GUI/CLI executable残留。
5. 生成源中的真实frame/主Scene段落要在实际输出后定位、记录行号和slice哈希；不能把Showcase
   layout_page、95129 B/SHA或20文件数当Gallery预期，不能预造AppView_frame或生成源码。

这只是导出前源事实审查，没有实际Gallery生成结果、二进制或原生布局结论。
