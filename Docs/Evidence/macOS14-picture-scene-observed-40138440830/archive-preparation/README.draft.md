# 完整 Picture Scene：macOS 14 只读观察

CI40138440830 的 build/capture 均成功。以原产品 source `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0` 导出的完整生成树为基线，在真实 `layout_page` 追加21个透明 background modifiers 与独立 helper；harness 为 `c9867c223b2efaf53a82214edd352b988c2952c9`。本节只记录已取得的 macOS14 证据；macOS13 A/B 应在实际完成后另附，不提前填写结论。

观察版本的 **13张选定原始 PNG** 与未插桩 control40135147500 全部逐文件逐字相同；13是文件数量，运行系统是14.8.9。Layout 原图 SHA256 为 `dfe053e307e033d0a4e583a88d34a4b60f428318f63e1954a500f14bb2016780`。冻结的 ICC→sRGB、15固定ROI及27个x800分段结果与 control/旧B14 逐值一致，完整可见边缘支持首卡125pt、HDR卡147pt保持。扫描线不是通用卡片 bbox detector，也未取得公开 API 命名的 native-card frame。采集保持 normal/en/en_US、920×668外框、1×及原完整路由；Layout 仍只等待0.8秒，没有五帧稳定门槛。

Light PID1926/window28 的原始 packet 含 **49条事件、21个精确标签**，序号0–48；286,397B，低于512KiB/256条上限。其49个有效窗口观察均 visible/key/main，各标签 probe identity 保持；该 packet 不涵盖独立 dark 进程。十项外层测量环境一致，包括 defaultMinListRowHeight24、locale en、font `inherited nil`。这个 font 是测量分支继承值，不是 Text 实际 glyph font。

事件明确保留 `end_state=not_observed`。Images Grid 的 resolved 高度105→109，而最后一次同记录的 native probe 高度仍为105；HDR后期 SwiftUI global y 增4pt时，所记录 native probe 框未同步移动。最近 graphics ancestor 的125/147pt是实际祖先 bounds，六层链全部截断；初始 document0×0等早期状态被保留。由此不能把最后一条当作稳定布局，不能将 SwiftUI/AppKit/WindowServer 坐标视作同步，也不能据此指定差异根因。所选截图通过不等于观察器在全部时序/交互下无影响。

来源复核独立从原 Generated、真实diff和 committed helper 重构106,494B编译输入，SHA256 `f4cac6965e72f454c257a30420ca5966d2b9afc012d1e9e264c20ed947b706d2`；去除仅21个modifier后恢复原源码全部字节。55个受检输入与9dd Git blob一致，生成器CLI（`crates/bern-cli`）仅增加构建前hook，交付的`bin/showcase`保持原字节。实际tar的16个文件逐字等于解包文件；15个成员与原9dd交付相同，仅GUI改变。实际 App/CLI 严格签名通过，arm64/min13/SDK26.2；构建记录为Swift6.2.4。重构与CI记录不是可重复构建同一binary的证明。

外层 build ZIP 的 upload/runner expected/runner download digest 同为 `477a14c31b24c6ae7a639e9eae90e15ca2bed7d7cd6ed78a6914f4a2ced4fb22`；本机实算的内层tar为 `bea6ff27c3b4b085d8b7459307278537a30e76e7a59ee5a8136bcb7df147bf4e`。二者容器范围不同。证据ZIP上传digest、job IDs、逐文件来源和签名结果见三份独立review及其manifest；本复核未在本机重hash两份外层ZIP。

不作 macOS13/11、Swift5.3、Objective-C、iOS、实际输入、flight/动画、HDR亮度或EDR等效验收。后续13 A/B 若使用 private重签副本，应分别保留原 payload 身份与重签派生关系，不把不同签名后的GUI hash称为同一个原签名binary。

归档建议见 `inventory-suggestion.json`。保留原PNG、event packet、运行/构建/CI收据与三份review；源码优先引用精确Git及既有source-export归档，避免无意义重复。App/tar仍是后续13验证输入，本建议不授权或记录其删除。只有root确认13/14证据链完成后，才由root决定清理，并另写实际cleanup收据与最终归档manifest。
