# Picture source-export：独立证据复核

结论：CI40136458675的这批文本通过有限源码生成证据门槛；未发现blocking问题。不是binary/UI等效或Picture布局修复验收。本审查未再编译、运行UI、dispatch或下载。

- 原raw确为8文件；原SHA256SUMS的7条成员逐一验过，无额外成员。完整源95129B，SHA `1d1da3167d9437b2305df1a39099f01f693b1b674f13cd2e4d88bffec2c52083`，与after及成员清单一致，未改源或复制大包。
- before记录的55个selected inputs逐一与Git9dd原blob比对bytes/SHA，全通过；source tree对象一致。覆盖实际generator/mac模板/Showcase输入及资源、Cargo/CLI，不扩大成每一编译器/环境输入均已枚举。
- 独立应用原unifiedpatch单hunk并核上下文，重构CLI SHA `5a05a83bf51900641e88f0502d6acd39e6446c62427324a4542af55d23ff8233`；它精确等于唯一target.plan前加canonical6行hook。原CLI SHA `63af68fa…d0fa64`，全部generated write在hook之前；tracked diff只有CLI。
- 原source为9dd，实际harness为213b515；从该harness的Git对象审helper/workflow，未用当前HEAD替代。helper SHA `e4f7bc61dce0241c53858d8c0f28250f13fa6bcac3c4c13759985ebb3b80df2e`。
- 缓存before虽已有相同源SHA，helper在prepare记录后以realpath守卫清掉目标生成目录，Rustcache保留；joblog确认restore→prepare→flaggedcargo→collect顺序。原generate.log完整2720B，记录20files/20changed、11components/2windows、exit0、marker恰1次，支持本轮重新生成。
- helper在复制源前断言产品GUI executable和bin/showcase均不存在；成功collect说明门槛通过。远程文件系统未单独留清单，本审查未独立运行find或重建产品。joblog和原generate.log均无产品build plan执行证据。
- 环境为macOS15.7.9、arm64、Xcode26.3、SDK26.2、Swift6.2.4、Rust1.99；generated build metadata为swiftui-modern/min13/release/arm64。它说明生成设置，不是新Mach-O minOS证明。

真实源结构可直接定位：layout_page1268–1409包含grouped Form、BernFormRows、首行四个literal VStack（3×120×90与64宽标志）、HDR2×192×108。没有重建isolated替代Scene。main_window在840起，NavigationSplitView850、case.layout883–884；main root1765起为BernWindowRoot→BernSearchPaletteHost→AppView_main_window，注入原session；@main1848起使用SwiftUI.Window(main)与Settings、共享engine、920×640默认size和contentMinSize。导出的文件没有独立BernApp.swift；应用入口就在此源内。

job120998905656完整log已绑定harness/source checkout、cache/prepare/generate/collect/upload，上传8文件，artifact12576963498；详细原路径、行号和哈希见review.json。上传log的ZIPdigest是远程记录，本审查未再下载或本地重算ZIP。

建议root在归档实际证据后删除旧 `work/picture-source-export-preparation` 的5个小草稿文本；正式repo/helper、raw和本review应保留。本审查没有删除。
