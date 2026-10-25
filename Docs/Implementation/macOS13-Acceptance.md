# macOS 13 现代 SwiftUI 移植验收

> **当前验收口径（用户于2026-10-25明确调整）**：不要求像素级复现，以目标平台的原生 UI 逻辑、可读可达布局、交互/状态与动画终态正确为准。细微系统配色、间距、轨迹和落点差异不再单独阻断。执行与收束以[原生逻辑验收合同](macOS13-Native-Logic-Acceptance.md)为准。
>
> 以下是历史研究日志：旧 exact PNG/RGB/ICC/ROI/frame/14.5pt/observer 门槛已被新口径取代，原数据和 false 收据仍保留。尚缺的实际功能证据不会自动变成通过。未启用的观察器路线已停止并清理；goal 仍 active，后续平台阶段延期。


本阶段使用真正的 `swiftui-modern` / `macos_modern`，不以旧的共享 Objective-C 原型代替上游 SwiftUI。macOS 11、Swift 5.3、Objective-C 和 iOS 阶段仍暂停。当前整应用视觉证据覆盖Showcase和Gallery，不能扩充为全部控件变体与示例均已验收。

最新检查点（2026-10-25）：[精确e48 Film的14后续参考](../Evidence/macOS14-film-e48-endpoints-40165343690/README.md)已由既有工作流单次CI40165343690取得，不重编App。真实14.8.9、原e48/d44/CLI31a、active/light/normal三false，一个fresh direct进程后原Last/First/Last-again/wide/restore；六终态AX完整六图、全部36组坐标和7PNG/ICC经独立复核。首次Last Windowpane中心573，重复Last565、wide599、restore565，均保留，未选优或套旧f9数。它补足当前port14准确参考，不是未修改上游ffb、本机13、完整动画或物理手势验收。源码未直接证明13兼容bug，不修改anchor/默认/nearest；下一本机只fresh direct后的第一次Last，安全入口另行source-only准备，旧CI stop-before-restore不能在用户桌面原样运行。原defaults5s失败未放宽，一次只读缺失域查询0.652s正常且无文件，不等于删除已证明健康。637806B ZIP核验API digest后清除，本轮没有本机构建缓存/新增App运行，108件约1.12MB小证据单份归档。整阶段颜色/布局/交互/动画仍未通过、goal active；remote14可用，11/Swift5.3/ObjC/iOS继续延期。

此前检查点（2026-10-25）：[通用SplitButton选中标签系统语义色候选](../Evidence/macOS13-split-label-color-40163364000/README.md)已停止，未合入产品或替换交付。独立候选ce462仅对13非capsule、selected+enabled+key+dark的既有Toggle/Label使用selectedControlTextColor，不加控件/固定RGB/字体或布局补偿。单次[CI40163364000](https://github.com/Torrekie/Bern/actions/runs/40163364000)新SDK26.2/min13完整构建成功（631固定输入仅Style改变）；真实14.8.9新color gate通过：固定Frame ROI原像素/ICC完全相同，整窗仍有5284侧栏像素差异。随后单次真实13.7.8采集程序0/8.766747s、stable4/5samples，原PNG与未插桩原13全文件逐字相同（ece61b2d…），预先冻结957像素/全部RGB指标无严格改善。不能据此猜定分支环境或原生style根因；按预定停止，不试第二色/强制白/条件或门槛矩阵、不重采。外层wrapper原失败保留：exact私有域defaults删除超原5s，App/IPC已清；另有独立root收据在强内核身份absence/noopen后仅删除279B残余私有偏好，不补写PASS、不宣称daemoncache已flush。原前台1390恢复、App15319stop0、lease释放/鼠标距离0/config不变/最终overlayfalse均经独立有限复核。约111.1MB逻辑自有无用App/helpers/tar/模块缓存已在读完/无open后退休，423件小证据归档，四原交付exe和产品Style保持。整阶段颜色/布局/交互/动画仍未通过，goal active；实际14可用，未触发数小时不可用暂停条件；11/Swift5.3、ObjC、iOS继续延期。

此前检查点（2026-10-25）：[未插桩原e48的本机13 Frame基线](../Evidence/macOS13-frame-control-e48-20261025/README.md)已单次成功，并经独立运行结果和离线复核。复用原SDK26.2/min13交付，仅私有CFID/签名改变，完整10成员来源及Mach-O各section/归一非签名字节核验；无产品重编或新CI。真实13.7.8完成8.712s原Ready→Paused0/awake/closed路径，normal三false、captiontrue、ledgerfalse，1840×1336/2x原PNG及ICC保留、stable4/5samples；App8075stop0、同一原ChatGPT1390内核身份在stop前恢复，IPC/私有偏好清理通过、lease释放、鼠标距离0，空overlay经仅clear复原。与同e48成功14 control相比，clip相对外窗(251,167,629,354)pt exact；Volume AX边界13(620.5,533,20,20)对14(619,536,22,15)，不是相同bezel或Layout宽度证明。ICC/尺度不同，预声明完整Frame ROI经各自ICC→sRGB及仅13整数2×2 BOX后仍有外观差异；不是跨OSrawexact/PixelGate或全UI等效。Root原图目检Caption选中标签灰/白及chrome/material差别；下一仅准备原生Label的系统selectedControlTextColor候选，先审可复用边界，不在generic后端硬编码Gallery目标，也不改布局/字体/新控件/固定RGB。原因仍未知，14实际无影响与13其它行为仍须验收。两旧Row observer失败保持，禁止重开记录路线。约49.7MB逻辑模块缓存、3,876,101B私有App及436,112B helpers在结束/无open/独立读完后清理，四原交付exe不变；localhelper实际embeddedSDK13.0与requestedheaders14.2差异及一次错误SDK检查均保留。整阶段颜色/布局/交互/动画仍未通过，goal active；11/Swift5.3、ObjC、iOS继续延期。

此前检查点（2026-10-25）：[latest1真实采集与失败复核](../Evidence/macOS14-frame-row-latest1-40158031681/README.md)已归档。latest1 完整置放槽在 `2c199894` 实现并经独立源码/打包审查，精确Row+helper及collector的SDK14.2/min13局部typecheck均0。单次[CI40158031681](https://github.com/Torrekie/Bern/actions/runs/40158031681)（harness `c28f678f`）新SDK完整产品/helper构建成功，真实14.8.9原e48 control成功、observer失败：记录容量问题已消失，但图像后仍有置放，cleanup后最终SHA与已绑定快照不同，原严格门槛正确拒绝。绑定摘要为122次/seq121，最终文件2287B/140次/seq139，比实际稳定采样晚0.802764s；绑定时完整记录已被替换，最终记录也不能用于解释截图，不能拿其宽度归因或补偿。PixelGate未运行。两原PNG各自与旧401555完全逐字相同，仅保留离线固定Frame ROI/ICC相同这一有限事实，整窗侧栏差异仍在。两App均停止/termination0且前台343恢复。本轮停止Row记录诊断路线，不再改采样、放宽cap/时序/最终SHA或重跑CI；本机13 observer禁跑、原guard草稿未编译。下一仅审查未插桩原e48的独立13基线方案，不把本失败变成PASS。局部缓存49,799,262逻辑字节及149517B经API digest校验的ZIP已清，未下载不必要构建包，四个交付可执行文件保持。真实14仍可用，goal active，完整颜色/布局/交互/动画尚未验收；11/Swift5.3、ObjC、iOS继续延期。

此前检查点（2026-10-25）：[真实e48 Frame行的14采集](../Evidence/macOS14-frame-row-ledger-40155522534/README.md)已由CI40155522534执行：新SDK26.2/min13产品及两helper构建成功，原e48 control与观测版在真实14.8.9均取得稳定关闭状态原图并停止归零。但观测组记录在172ms内35条/63828B后达到64KiB上限，原packet明确truncated，整体失败，PixelGate未运行；不解释有限前缀的宽度值。离线与独立原RGBA/ICC复算仅证明本失败cohort固定Frame detail原像素相同，整窗仍5284像素侧栏选中差异，不冒充全窗或13/14等效。下一唯一修正为新schema的latest1完整置放槽与显式总数/替换数，仍64KiB，不升cap或放宽时间/像素门槛，尚未实现。本机13禁跑；仅cleanup的Gallery guard适配草稿未验收。已清本机约49.8MB逻辑模块缓存及校验后的下载ZIP，交付App保持。此次真实14可用，goal active；整阶段未通过，后续11/Swift5.3、ObjC、iOS继续推迟。

此前检查点（2026-10-25）：[精确e48 Gallery Frame生成源码](../Evidence/macOS13-gallery-frame-source-40152701810/README.md)已由单次CI40152701810取得并独立复核：631项固定输入保持，只有CLI在生成后、target.plan之前加入退出；实际完整Swift81110B、Frame原片段9021B/1248–1353行保留，rc0/标记1。此次只在macOS15生成源码，没有编译Swift产品或新增13/14窗口证据。真实Frame行的源码包含Caption、Size、Volume和条件Group，源码项数不证明运行时Layout.Subviews数；下一步只读取这一行原有查询得到的宽度分配与实际推进，先验证观察不改变画面，再解释数值，不据历史f9的2pt差加入补偿。下载ZIP在实算并匹配API digest后清理，本机没有新增构建缓存或App副本，四个原交付可执行文件hash保持。整阶段仍未通过、goal active，后续11/Swift5.3、ObjC、iOS继续推迟。

此前检查点（2026-10-25）：[原生搜索焦点门槛](../Evidence/macOS13-search-native-focus/README.md)未通过：长IPC启动失败保留；短IPC实例坐标点击后AX仍outline，独立一次Shift-Tab后未取得search焦点，因此均未投递`!`、未进入Library或验收Query。坐标组还保留root超180s后的缺finish/迟到截图错误，不把App退出0当采集通过。来源/签名与清理已独立核验，约62.4MB自有产物/cache退休，原交付保持。停止输入试验，不指定Bern根因；下一项先补精确e48 Gallery Frame源片段，历史f9 Caption/Size耦合2pt变化不足以支持padding/字体补偿。整阶段仍未通过、goal active，后续11/Swift5.3、ObjC、iOS继续推迟。

此前检查点（2026-10-25）：[Scene compact showsTitle原生对照](../Evidence/macOS13-toolbar-scene-shows-title/README.md)已完成冻结源修链后的true/false pair：同一次Swift5.9.2/SDK14.2/min13编译，实际三样本/AX/原PNG及身份清理均独立核验。两侧顶部均38pt，false隐藏可见Buttons标题并把plus左移691pt，不满足现有52pt/可见标题目标，停止候选、不合产品、不追加14CI。首轮编译输入未锁定，保留为source-unbound，未回填验收。已退休本轮约51.6MB逻辑产物/cache并合并两张重复PNG，原交付GUI/CLI与签名保持。整阶段仍未通过、goal active，11/Swift5.3、ObjC与iOS继续推迟。

此前检查点（2026-10-25）：[原Grid宽度action的同binary13/14记录](../Evidence/macOS14-picture-grid-width-40144017622/README.md)已完成CI40144017622和本机B4：14原13PNG全部保持125/147，13原9PNG逐字等A2且仍129/147；21点Generated106494B逐字保持，Style只追加原action捕获/defer日志。两系统各3条width记录去掉uptime后逐字段相同（配置140→192→120、+0→719、body-captured columns1、main/guardtrue）；geometry的49/21条均保持既有边界，环境仅scale不同，caption分数尺寸完整保留。匹配的有限prefix未解释4pt，按计划停止width诊断，不追加探针/CI或据此调padding。新outer ZIP在删除前实算并匹配API digest，内tar、55源/两patch、native签名与min13SDK26.2均独立核验；B4先恢复原前台再停止自有进程，桌面最终released。本轮清除约61.9MB自有产物/cache并合并22张重复PNG，原交付App/CLI保留。整阶段尚未通过、goal active；下一步回其它未通过项的源级最小候选，不扩展本width实验。

此前检查点（2026-10-25）：[完整Scene只读观察的14构建/运行](../Evidence/macOS14-picture-scene-observed-40138440830/README.md)已通过CI40138440830：21背景探针保留原Scene，13张原PNG逐字等于无插桩control，首卡125/HDR147不变；实际49事件覆盖21标签。[同一SDK26.2/min13产物的本机A2/B3对照](../Evidence/macOS13-picture-scene-observed-9dd/README.md)完成：9张原PNG逐字相同，源/签名section/normal开始结束/原页面顺序/自动前台恢复与进程清理均独立核验。13取得21事件/21标签，Images Grid为109、最近原生graphics祖先129，HDR127/147；14早期Grid105、后期resolved109而native仍105、祖先125。两边十个公开环境字段仅scale2/1不同，图片90高/caption13高等保留；两边侧栏均140–141pt，排除本轮宽度上下文不一致。首卡129对125及后续4pt下移仍未修，不能把异步末条坐标当同步/settled或根因。原v1清理失败和首次B漏建输出目录导致日志关闭均保留原状态，真实日志以B3为准。本轮退休约75.4MB自有副本/tar/helper/cache，重复原PNG只核哈希后以相对别名合并；原交付App/CLI保留。下一最小候选仅记录原Grid宽度action旧值/测量值/捕获列数与时序，尚未运行，不加padding/固定高度或RGB补偿；整阶段未通过、goal active。

此前检查点（2026-10-25）：[完整 Picture Scene 的未插桩14 control](../Evidence/macOS14-picture-scene-control-40135147500/README.md)已重现：CI40135147500复用原9dd完整应用，不重编/重签，首卡125pt、HDR147pt；13张选定原PNG全部逐字等于历史B14对应文件。source9dd、normal三项false、英文、920×668及原页面/动作顺序均绑定；原Layout只等0.8秒，不宣称五帧稳定。独立ROI/边缘与元数据/13张哈希复核通过，startup两次sessions/status3均在各进程ready前，之后78条命令均0。这补足了真实Scene插桩的前置门槛；[精确9dd生成源](../Evidence/macOS14-picture-source-40136458675/README.md)已由CI40136458675导出并独立核验：95129B、55输入不变、原Scene完整；未编译Swift产品。21点纯追加补丁可逐字恢复原源，187行公开观察helper已用本机现有Swift5.9.2/SDK14.2/target13通过独立typecheck，临时cache已清。下一步在完整Swift6产品运行中只读记录Form/首Grid row/HDR row，先通过control→observed卡高125/147保持再解释环境；静态准备不当作观察无影响或13差异通过。未增加布局补偿，13差异与整阶段仍未通过，goal active。13个逐字重复PNG改为指向既有原件的相对别名，自有work目录移入单一归档；未下载产品App/tar或本机构建缓存。

此前检查点（2026-10-25）：[真实coordinator的bounded timing](../Evidence/macOS14-hero-timing-40132685948/README.md)已完成：SDK26.2/min13同binary在13/14各一次default，原native/execution/SDR及新增strict timing均通过，6原PNG、四个对应端点raw/ICC exact。14注册后checkpoint距started0.435ms、首callback前缀0.666ms、first tick159.427ms；其中scalars结束→tick140.835ms尚未区分尾部/自动draw/分派，不是根因或等效响应性声明。上一[14缺样失败](../Evidence/macOS14-hero-coordinator-sdr-40129608288/README.md)保留；本次有效参考不因未归因间隔停用，也不据此改产品clock或盲CI。此前[静态SDR候选](../Evidence/macOS13-hdr-candidate/native-pq-hero-snapshot-sdr13/README.md)混合色差及产品intent链仍未解决，候选未采用。下一步回实际Picture Scene首卡布局等未通过项。下列整应用交付版本及其它未通过项保留，goal active。

## 已有可复核结果

| 检查 | 结果 | 范围 |
|---|---|---|
| 新编译器、新 SDK、target 13.0 | Showcase / Gallery 均编译、链接、签名验证成功 | 已交付Showcase `9dd99b7`、Gallery `e48fff46`：Swift 6.2.4、SDK 26.2、Rust 1.99；此前参考构建为 Swift 6.3.3/SDK26.5；仍需要新工具链，并未移植至 Swift 5.3 |
| 同一 target 13 应用在本机 13.7.8 启动 | 两个真正的 SwiftUI 应用均启动、建立 UI 会话 | arm64；Info.plist 与 Mach-O 的最低版本均为 13.0 |
| 原上游 A 与迁移 B，同在 macOS 14.8.9 运行 | 21 张 PNG：17 张 RGB 像素完全相同；3 张分别只有 12/35/76 个像素相差 1 级 | 余下图片页首个 section 多 1 点，后续内容随之下移；尚未把原因归给任何观察机制 |
| 13 系统圆形图标按钮 | 实际应用中的 AX 对齐尺寸为 20×20 点，位置与 14 参考一致 | 使用系统 `NSButton.circular`，没有自画 bezel；实际 AXPress 一次只运行一次引擎命令 |
| 13 Query 错误占位页 | 实际截图的图标、标题、两行说明、按钮与 14 参考的边界差不超过 1 点 | 错误卡高约 226.5 点，14 为 227；重试按钮绘制边界相同 |
| 13 Film 明确 Last 落点 | 浅、深两种外观中，放大卡片四边相对14差值为 [0, -0.5, +1, +0.5] 点 | 原始2x截图，无图像缩放补偿；旧46初始身份仍不同；本轮e48及后续操作序列见未通过项 |
| 13 默认侧栏与宽度恢复 | 真正整应用、干净独立 defaults 首开210；AX调为260后，页面重建和进程重启均保留260 | 仅为隔离改变bundle ID及临时签名，对应可执行代码的Mach-O sections与CI产物一致；没有清用户窗口历史 |
| 空白与媒体占位、语言切换 | 空白/错误媒体占位测量边界均在1pt内；Ready→Failed→Ready恢复后原始画面像素相同；中英文切换及取消关闭保留草稿 | 状态切换通过实际控件绑定，语言测试不冒称真实输入法或菜单点击 |
| 14 Frame 原生对照 | f9与固定上游在同一14机器中的视频区/按钮/弹出层/滑块几何一致，Frame detail像素一致，独立音量popup PNG文件相同 | 仅浅色；主窗侧栏选中行仍5284像素灰/蓝差异；13对应验收及物理输入不由此通过 |
| 13 Frame 原生运行 | f9通过Ready→Paused0、3.2秒保活、native AXPress开关、raw窗口ID回读与3张稳定原图；Clip/popup/slider点几何精确同14 | active浅色，前台1390→1390；Volume可见bezel差≤.5pt，仍有配色、Caption/Size宽度及文字位置差异，不是全视觉或物理输入通过 |
| 原生交互 | 通知 AXPress 改变会话草稿；音量 AXIncrement 从 50 到 60，只产生一次引擎提交；Command-Comma 打开原生 Settings scene | 这些不是鼠标拖动验证；CLI 状态与原生 AX 操作分别记录 |

目前交付的Showcase来自 `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`，[CI40066468884](https://github.com/Torrekie/Bern/actions/runs/40066468884)成功；Gallery现为 `e48fff46b3a92a28465ad74295bd273a9d69af7d`，[CI40070407306](https://github.com/Torrekie/Bern/actions/runs/40070407306)成功。两者使用Swift6.2.4、SDK26.2、Rust1.99。新版Showcase独立签名副本在本机13.7.8通过启动、唯一main窗口和control inspect，6.575秒结束，未激活、前台PID1390→1390；完整原件、section/签名比较、早期startup gate不足的partial以及原始轮询见[交付证据](../Evidence/macOS13-native-standard-full-app-9dd/README.md)。未经修改的CI原件已移动到交付目录，旧Showcase及重复副本已清理。 Gallery e48原件也已[核验并交付](../Evidence/macOS13-gallery-clean-delivery-e48/README.md)，旧f9 App与重复CLI已清理。其[精确版本三场景记录](../Evidence/macOS13-film-clean-e48fff46/README.md)覆盖immediate/wait/direct独立进程，三者均Glen601，wait/direct全6图的frame对14最大分量差约0.0000098pt；immediate仍差35/36pt，卡宽差约−1.265pt。合同为inactive13，不能扩充为全Film视觉通过。

f9包含HDR路由/系统SDR修复、14原生Pinch路径恢复和音量PopoverButton系统按钮复用。此前两份f9应用均已在本机启动、建立唯一会话并完成window/control inspect；实际Gallery通过原绑定进入Frame、打开音量弹出层并将草稿0.7改为0.55。原始记录见[Showcase历史记录](../Evidence/macOS13-popover/full-app/showcase/report.json)和[当前Gallery记录](../Evidence/macOS13-popover/full-app/gallery/report.json)。组件内native action与关闭对照见[独立组件记录](../Evidence/macOS13-popover/component/README.md)。整应用绑定操作不替代真实鼠标或14/13 Frame视觉对照。这轮没有重拍全部视觉/交互样本，不能把下述0f/46截图改标为f9或9dd。

此前`5226454`两CI及启动检查仍保留为独立历史证据：[Showcase](../Evidence/macOS13-latest-build/showcase/report.json)、[Gallery](../Evidence/macOS13-latest-build/gallery/report.json)。

第三轮整页视觉证据源码为 `46a286245c1e4c1380ea0e2285587cfe6225a3f8`：

- [Showcase 构建](https://github.com/Torrekie/Bern/actions/runs/39975026355)
- [Gallery 构建](https://github.com/Torrekie/Bern/actions/runs/39975025096)

Gallery 的第三轮本机证据为两种外观各新进程、活动窗口、连续 5 次相同 WindowServer 缓冲后的 8 张原始 2x PNG。Showcase 当前保留的占位页、按钮、媒体证据来自第二轮 `0f5226d`，其 [Showcase 构建](https://github.com/Torrekie/Bern/actions/runs/39969189803) 与 [Gallery 构建](https://github.com/Torrekie/Bern/actions/runs/39969189761) 均通过；它们不能冒充第三轮重拍。

macOS 14 上的 A/B 对照使用此前的 `fa820f706e5faf1bae8b8f07e23545842a1648b7`；此后的按钮、占位页和滚动相位校准均限制在 13 分支。不要把旧源码的对照扩充成新源码已经在 14 再验收。

## 参考与采集方式

原上游固定为 `ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee`。新 SDK 构建与旧系统运行分开，应用不在 14 运行机上重新编译。普通参考的减少动态效果、减少透明度和增强对比均关闭；没有修改本机这些设置。

| 证据 | 内容 |
|---|---|
| [Showcase 原始参考](../Evidence/macOS14-reference-normal/reference.json) | 13 张 WindowServer PNG，涵盖浅/深色控件、Text、Buttons、Inputs、Query 错误/空白/恢复、图片、Video 状态；[采集](https://github.com/Torrekie/Bern/actions/runs/39961818954) |
| [Gallery 原始参考](../Evidence/macOS14-gallery-normal/reference.json) | 8 张浅/深色 PNG，4 个 Inspector/滚动 GIF；[采集](https://github.com/Torrekie/Bern/actions/runs/39964126654) |
| [本机13候选证据](../Evidence/macOS13-candidate/reference.json) | 14张原始窗口PNG，分开注明0f/46源码版本；[Gallery量化](../Evidence/macOS13-candidate/gallery-comparison.json)、[侧栏宽度](../Evidence/macOS13-candidate/sidebar-width.json)、[语言/关闭](../Evidence/macOS13-candidate/language-close.json) |
| [同系统迁移比较](../Evidence/macOS14-port-comparison/comparison.json) | 每张图片的 RGB 比较、原始文件哈希、不同 PNG、图片页差异测量；相同图片复用 A 的原图，避免重复保存 |
| [13图片布局SDK复核](../Evidence/macOS13-image-layout/sdk26/validation.json) | SDK26.2与既有SDK14.2在同一13宿主的9组配置/27位置中，1800个公开坐标框、45次卡片检测均一致，27张PNG哈希全部相同。[同binary14普通效果](../Evidence/macOS14-image-layout/validation.json)也已完成，首卡129点相同；该夹具仍未复现完整14应用的124/125点。 |
| [13背景路径隔离](../Evidence/macOS13-window-background/README.md) | 同一个inactive浅色窗口中，语义颜色直接绘制为236灰；透明NavigationSplitView detail为240/236/237，显式填充后恢复236灰。五组各两次稳定缓冲，窗口2.446秒、前台不变；这不是完整Gallery或14对照。 |
| [13 toolbarRole候选](../Evidence/macOS13-toolbar-role/README.md) | 同一Showcase式固定标题样例中，automatic、split上的editor和detail上的editor共9个原生框样本均不移位，标题仍存在；未扩充为Gallery或所有公开composition均已排除。 |

Gallery 的外观由它自己的 Light/Dark 动作设置，不能只给进程环境变量，因为示例会显式恢复 System。最终静态 Gallery 参考在连续 5 次 WindowServer 缓冲相同后采集。早期误标深色的图片不作为深色依据。

GIF 实际采样间隔约 0.135–0.147 秒，第一帧间隔可能更长；GIF 的播放延迟不是采集帧率。它们只说明程序化状态变化，不能证明 60fps、触控板惯性或短促 nudge 的峰值。

本机显示器为 2 倍缩放，14 CI 为 1 倍。13 的原始 PNG 保留 2 倍像素；比较几何时换算为点，比较颜色时读取 ICC 并统一到 sRGB。不同屏幕、焦点和系统原生材质的差异不能用整数像素全图相等掩盖。

## 必要的局部复用组件

- `BernCompatibility.swift` 保留 ObservableObject 所有权、对象环境及旧 onChange 的当前闭包和 old/new 语义。
- 13 Inspector 复用 `HSplitView`，内容仍为原 SwiftUI；滚动仍为系统 SwiftUI ScrollView。居中边距使用真实SwiftUI内容padding，并按滚动视图作用域隔离，避免直接改变NSScrollView insets造成LazyHStack原生/绘制坐标分离。相位使用14实窗校准的有效viewport及easeInOut Bezier曲线。
- 缺失的按键监听只作用于当前窗口和焦点，不全局吞键；文本编辑与输入法仍需单独实测。
- 普通无显式尺寸的圆形 IconButton 复用 `NSButton`。本轮生成器为普通图标PopoverButton选择同一桥接，并显式转发快捷键；手写helper默认、显式宽高、绘制外观和toolbar不请求此桥接，bar/group由原有组件保留原路径。toolbar、bar/group、显式宽高、plain/prominent、custom look、cancel 保留原路径；destructive、enabled、快捷键、AX ID 与最新 action 转接系统属性。
- 13的PQ/HLG High及HLG Standard使用系统MTKView/CoreImage/EDR图层，无Metal时复用NSImageView。严格识别标准cICP编码后才补足旧系统的色空间识别；9dd只将explicit Standard/original/PQ改为复用现SwiftUI Image，并在decode缓存显示用CGImage色空间copy，原图/ICC保留。完整Showcase构建和实际BernImage分支切换均通过限定检查，见下文；High颜色不由此通过。请求HDR看潜在余量，绘制看当前余量，并通过系统屏幕通知更新，避免以启动前的1永久关闭HDR。普通SDR仍用SwiftUI Image；gain-map能力分支保持原逻辑。
- 显示时钟在 13 使用 CoreVideo 垂直同步；14 保留原生显示链接，不以固定 Timer 代替。

## 尚不能通过的项目

当前不能宣称整个阶段已等效完成，也不能进入 macOS 11 或 Objective-C 阶段。

| 项目 | 当前证据与后续条件 |
|---|---|
| Film 初始身份 | 第三轮整应用Last几何在1pt内，14初始Glen、13初始Madras。新14普通效果上游三场景均为Glen，wait/direct原始Film PNG相同，说明Inspector关闭过渡不是该身份的必要条件；immediate仍有约35pt落点差异，且启动窗口恢复/实际resize是混杂。当前f9移植应用在14三场景也均Glen。新增整应用trace已记录14的target始终3，nearest变4，quiet释放后由Bern follow明确写position3→4；13后台trace则nearest保持3。14原生只读快照确认clip709、insets左右234.5、document1638；13使用真实padding。d146诊断候选已使direct初始Glen完整frame对14差小于0.00001pt，默认3及nearest保留。与旧f9同collector对照确认wide约16.5pt偏差旧13已有，First/Last-again/restore候选相对旧13约+0.186pt；首Last仍差且时序/前台条件不同。去插桩的clean修复已提交e48fff46，精确整应用CI40070407306及13三场景运行合同已成功，wait/direct几何吻合，immediate仍差35/36pt且启动恢复/resize历史未分离；不把诊断构建通过套给clean应用，也不改默认值。[事实、原始证据与下一最小trace](macOS13-Film-Initial-Position.md)；不硬改默认值。 |
| 吸附轨迹 | 13 暂在原生惯性结束后校正，14 在原生目标计算阶段吸附；落点与运动过程应分开验收。 |
| 未覆盖控件变体 | `f9e08b1`已让生成器选中的普通volume PopoverButton复用系统圆形NSButton，独立native action检查通过（单次触发、快捷键、disabled、外部打开和WindowServer alpha=0的关闭，与原Button配对一致）；整应用该版本构建、本机启动及Frame绑定打开/编辑均通过；14浅色Frame detail与原生popup已完成f9/上游配对：内容像素与几何一致，主窗侧栏仍有选中配色差异；新增13 active Frame已通过媒体/idle/AX与主要几何，仍有popup/视频色差、Caption/Size宽度约2pt及Size文字约3pt差异。icon风格Menu、显式尺寸等仍有独立路径，不能套用普通IconButton的20pt系统按钮验收。Planner的styled SidebarItem才进入自定义侧栏键盘分支；Showcase/Gallery截图没有覆盖它。 |
| 工具栏 chrome | 13 与 14 自动 sidebar toggle / 标题的位置不同。公开 NSToolbar 临时重排会被下一次 SwiftUI 更新覆盖，不能作为产品修复。新增[完整Showcase标题宿主候选](../Evidence/macOS13-toolbar-title-host-f6/RESULTS.md)仅迁移navigationTitle，四阶段A/B原PNG逐字相同、选定几何最大差0；已停止，不合产品，不追加14CI。新增[Scene compact Boolean pair](../Evidence/macOS13-toolbar-scene-shows-title/README.md)两侧均38pt，false还隐藏实际标题并将plus左移691pt，已停止；这是独立Scene机制，未合完整产品。仍需其它源级composition或独立原生chrome所有权证据，不能持续争夺delegate/items。 |
| 图片页首卡高度 | 完整应用A14/B14/C13首卡分别124/125/129pt，图片和caption边界接近，后续HDR卡均147pt。 最新[width同binary13/14](../Evidence/macOS14-picture-grid-width-40144017622/README.md)的三个回调除时间外完全相同，13/14首卡仍129/125，已停止该诊断；它没有解释原因，也不足以支持4pt补偿。 最新[完整9dd Scene A2/B3](../Evidence/macOS13-picture-scene-observed-9dd/README.md)已在13复现129/147并通过9PNG原版/观察版逐字一致；14同观察版13PNG保持125/147。13 Grid/native为109/109、祖先129，14记录105→109/native仍105、祖先125；环境仅scale不同，未确认原因，也未以最后callback当稳定终态。新增[同binary14普通效果探针](../Evidence/macOS14-image-layout/validation.json)九组合/27位置中，首卡与fixed109卡均129、HDR147，均与13同binary相同；其它公开坐标仍有最高2.5pt差异。进一步[静态四子节点隔离](../Evidence/macOS13-image-layout/static-children/validation.json)在13和14各1800个公开坐标框均与原ForEach夹具相同，首卡仍129，已排除该单独因素；13全部27 PNG字节相同，14为25/27，未宣称全像素相等。独立probe仍未复现完整应用14首卡124/125，完整Scene及其余简化包装待隔离，不能把probe匹配当整应用修复，也不以负padding抵消。 |
| PQ/HLG 色彩 | `e06e080`的严格cICP识别、系统SDR转换、无Metal备用与真实余量通知已随`5226454`及最新`f9e08b1`完整构建并启动。原产品High尚未等同；新增独立Annex5候选在已知中性PQ样本上，Hd1完整ramp对14 MAE0.104109/255，Hd2提交linear EDR为1/1.996094，真实通知观察到1→2→1→2。这是未接入产品的有限输入实验，彩色/metadata/HLG及同条件14High未通过。[原系统路径证据](../Evidence/macOS13-hdr/reference.json)、[候选证据与限制](../Evidence/macOS13-hdr-candidate/reference.json)。 |
| 真正鼠标拖动 | 独立系统NSSlider也未收到自动化drag的mouseDown，值仍50；同控件AXIncrement能产生一次action并变55，因而已在Bern外复现输入交付限制。尚未证明“拖动时只预览，松手仅提交一次”。AXIncrement 单次提交不替代它。 |
| 物理 HDR、输入法、完整动画时序 | 未验收。屏幕潜在EDR为2，实际值会随HDR surface启动从1升到约2；不能把启动前的1当作设备不支持HDR，也不能用SDR截图证明物理HDR亮度等效。 |
| 原生材质配色 | ICC归一后的活动窗口背景仍有差异。原比较中canvas只是空白点位昵称；Patterns/Film该处是透明detail，并未填surface.canvas。[同binary13/14五组实窗比较](../Evidence/macOS13-window-background/sdk26-content-stable/comparison.json)已完成：语义颜色实画、SwiftUI Color、canvas和显式填detail模式RGB均236灰；透明split却为13的240/236/237与14的234灰。两边内容尺寸均800×520，原生外框/sidebar/chrome不同。该inactive手建窗口不能替代完整Gallery活动窗口，也不能唯一归因材质或系统tint；不以固定RGB抵销。 |

GitHub 的 macos-14 在 2026-10-23 14:00 UTC 至次日00:00 UTC 进入公告的故意失败时段，并计划11月2日退役：[官方公告](https://github.com/actions/runner-images/issues/13518)。已取得的普通外观参考继续可用；该时段的 runner 失败不能归为源码失败。

## HDR独立候选的新增证据

[候选归档](../Evidence/macOS13-hdr-candidate/README.md)将数值推导与本机窗口实验分开保留。CPU原型在640×360上按原始PQ编码解码nit，以公开Annex5候选输出linear BT2020的`Lout/203`；current1与2的提交像素单位由GPU读回验证，Standard切换前后原始图像RGBA完全一致。1000仅是受这张14中性ramp支持的候选预设，203是ISO默认内容白，不是ICC lumi100。

13公开`CIImageOption.toneMapHDRtoSDR`仅有Bool，没有目标headroom；`CIExposureAdjust`只做线性曝光乘法。即使在已知Annex5标量函数下，Hd2的前后曝光也不等于直接目标映射，详见[接口边界与数学反例](../Evidence/macOS13-hdr-candidate/README.md)。没有将这类组合当作已完成的High替代，也没有追加系统CI组合实验。

原型只占前台约0.369秒后恢复即时前台，后续均采自有inactive窗口。CPU动态转换median18.64ms/max88.08ms，不能原样放在主线程产品化；进程resident采样峰60.1MB不是GPU峰值。彩色应用空间、合法元数据缺省/优先级和14实际High适配仍需新probe；当前没有用图片SHA/中性条件作为产品功能白名单，也没有修改产品色调映射。

新增[当前产品Standard彩色对照](../Evidence/macOS13-hdr-candidate/standard-color-e06/validation.json)确认：cICP规范化后的自定义ICC与命名PQ在现有产品helper中输出一致；但对13原生SwiftUI，10色块的通道均值MAE约1.087/255、最大差约4.759/255，不能只凭灰阶认定色彩等同。[公开原生组件比较](../Evidence/macOS13-hdr-candidate/native-sdr-components13/validation.json)中，NSImageView在真实Hd1与13原生SwiftUI整图逐像素相同；CGContext 8位转换仍有约5级色块差。早期[动态余量检查](../Evidence/macOS13-hdr-candidate/native-sdr-headroom13/validation.json)只完成初始Hd1；本轮[缩小后的完整动态采样](../Evidence/macOS13-hdr-candidate/native-standard-dynamic13/validation.json)已实际完成current1→2→1，20次trajectory、27次GPU完成/读回、76次真实屏幕通知、6张截图。两原生图像的12个ROI均逐像素相同，并复现旧静态基线；窗口3.218秒、未激活、前台不变。这仅证明该PQ彩色atlas在此13环境的截图稳定，不扩充为HLG、EXIF、alpha或物理亮度。

[14普通效果彩色基线](../Evidence/macOS14-hdr-color-normal/validation.json)已取得：同一binary在14的custom ICC与named PQ均识别为BT.2100 PQ并逐像素相同；13需要严格cICP规范化。13原生named PQ对14的10色块MAE约1.294/255，最大约26.515；现产品Standard helper更远。两个宿主的显示器/ICC/缩放也不同，不能单因归为系统版本，原生候选尚未进入产品。

[严格PQ派生显示验证](../Evidence/macOS13-hdr-candidate/native-pq-canonical-copy13/README.md)现已完成：原file/ICC/provider/布局保留；派生custom和native named源的raw布局/字节相同。bare SwiftUI双列在actual1→2→1的12个ROI、与旧native13基线均逐像素相同。基于此，产品[9dd99b7](https://github.com/Torrekie/Bern/commit/9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0)只替换mac13 explicit Standard/original/PQ路径，复用已有standardImage的方向/fit/clip链；High/HLG/14/template、原缓存/平均色不改。独立只读审查及[完整Showcase CI40066468884](https://github.com/Torrekie/Bern/actions/runs/40066468884)通过，原件已交付。

新增[actual BernImage body验证](../Evidence/macOS13-hdr-candidate/native-pq-product-body13/README.md)使用提取的完整实际图片分支，仅为SDK14.2编译跳过mac15+且13不可达的gain-map decoder。Standard→High→Standard三阶段MTKView为0→2→0；保留观察的两个High视图在fixture cleanup前均已离窗、暂停且关闭EDR，不声称已dealloc。两源图片/缓存的identity/provider/ICC/file/布局/方向/平均色保持；4张Standard图的12个ROI原RGB和ICC归一后均逐像素等于原生oracle及旧native13基线。3.118秒、activation0、前台1390→1390；实际headroom从1升至1.470819后回到1，High捕获时为1.251183，不能称High已达到2或颜色通过。构建保留一个既有switch警告；此夹具不替代完整Showcase视觉。hero快照仍使用原图，尚未纳入本次显示修复。

## 恢复后的14普通效果采集

远程macOS14已实际运行。普通效果[图片run40062046351](https://github.com/Torrekie/Bern/actions/runs/40062046351)和[HDR run40062048900](https://github.com/Torrekie/Bern/actions/runs/40062048900)均成功，复用此前已在13运行的exact binary，不重新构建应用。独立profile.json从NSWorkspace验证reduceMotion/reduceTransparency/increaseContrast均false；图片probe还独立重复记录这三项。第一轮图片40061735500沿用runner的reduced默认值，已分开归档，不能冒充normal；第一轮HDR40061839104缺少profile记录，普通效果重采后的像素与它相同，但仍保持不同证据身份。

新SDK26.2与旧SDK14.2在同一13图片夹具中的框、卡片检测和全部27张PNG一致，只排除这组13条件下本轮编译组合造成的差异；不能据此解释14/13图片首卡高度或其它未测布局。HDR新probe也不能自动覆盖metadata、HLG或实际Hd>1。

上游Film[run40062194628](https://github.com/Torrekie/Bern/actions/runs/40062194628)已成功，使用既有Gallery构建39959549054，每组新进程区分立即关闭、等待关闭、从未打开Inspector；[原始证据与分析](../Evidence/macOS14-film-timing/analysis.json)。首次采集40061845578在建立会话前失败，已根据上游100字节socket上限将测试临时路径缩短；该失败没有Film结果。当前f9应用在14的同场景run40062837456也成功，进一步确认身份差异属于13路径，尚未证明内部绑定变化。

[Frame paired run40065164350](https://github.com/Torrekie/Bern/actions/runs/40065164350)现已成功，[原始A/B与离线复算](../Evidence/macOS14-frame-volume/paired-40065164350/README.md)保留六张原图。两边均通过真实Ready→Paused0、3.2秒idle、native AXPress开关、独立popup窗口、原始ID/ownPID回读及连续四次相同buffer。Frame detail/视频区逐像素相同，Clip/Volume/slider/popup几何完全一致；266×106的独立popup连PNG文件字节也一致。两张主窗均仅侧栏Frame选中行有5284像素灰/蓝差异，捕获时firstResponder未收集，不猜其原因。该结果只覆盖f9/原上游在14的浅色路径，不是13、深色或物理输入验收。

新增[13 active Frame原始对照](../Evidence/macOS13-frame-volume/paired-f9-aot/README.md)使用原件f9的独立签名副本。首次解释器在top-level之前因CryptoKit符号加载失败，原log保留；改用同源AOT后单次运行12.210秒成功，已有AX/Screen/PostEvent权限均true，没有请求系统权限。21次仅投本PID的mouseMoved保活不等于物理输入；真实媒体Ready→Paused0、>3.2秒mounted门槛、native AXPress及15次raw窗口ID/owner回读均通过。三张PNG各有4次相同buffer，前台1390→1390。

13/14的Clip、popup、slider点几何精确相同；可见Volume bezel均20×20且仅差.5pt，speaker ink四边≤1pt。Caption与Size bezel宽度各差2pt，Size文本约左移3pt；Rest及popup文字边界≤.5pt。保留原2x/1x图与ICC后，归一sRGB的closed detail MAE2.76324/255，popup全图4.23794/255（共同完全opaque区5.94792），平面panel明确偏暖且视频也有色值差，不能猜定系统材质、桌面tint或显示器是唯一原因。popup alpha bbox相同，alpha MAE约.00910；不能以这些几何通过宣称颜色完全一致。全部169项证据hash核验，临时app/CLI/AOT程序已清理。

早期Frame40062043370/40062688905/40063364941分别暴露事件窗口身份和AX标识覆盖等采集限制；[40064763940](../Evidence/macOS14-frame-volume/attempt-40064763940/README.md)已通过idle/native几何，首PNG则因NSNumber对象代替原始CGWindowID而失败。这些失败均未进入B、PNG=0。修正仅在外部采集器中，完整成功采集保留原媒体、idle、AXPress及稳定buffer门槛。

背景探针[14 run40063500033](https://github.com/Torrekie/Bern/actions/runs/40063500033)及同一SDK26.5二进制在本机13均完成五组运行，归档见[13](../Evidence/macOS13-window-background/sdk26-content-stable/README.md)和[14](../Evidence/macOS14-window-background/content-stable/README.md)。早期“外框全程不变”断言阻止后两组；诊断已确认原生NavigationSplitView自动加toolbar改变外框，内容尺寸保持。新合同实际通过内容800×520、各variant双buffer像素/几何稳定及不激活条件，并保留真实外框变化。透明detail的跨系统颜色差异已复现，其余四组模式RGB相同；不将手建窗口结果冒充整应用等效。

## 暂停检查点（2026-10-24，北京时间）

此前按用户要求暂停，08:05一次性检查已执行并删除。用户/系统于12:16恢复同一个goal，当前active；实际14运行已恢复，不再因brownout空等。已有实现和上述未通过项均保留，不标记完成。macOS11、Swift5.3、Objective-C和iOS仍暂停。

## 空间控制

只保留需要复核的源码、原始证据和当前候选应用。传输 ZIP、提取后的重复 tar、经哈希验证的重复参考已清理；小型编译试验的 module cache 在完成后删除。没有安装新 Xcode、Swift 工具链或 iOS 模拟器，也不清理用户的窗口历史、其它项目产物或系统缓存。

## e48原件在14的补充状态

[新14复核40071892408](../Evidence/macOS14-film-clean-e48fff46-40071892408/README.md)成功且wait/direct全部几何保持；immediate却为Glen677，而旧参考为565/566、13clean为601。为控制新增startup gate，补做[旧f9同collector40072273422](../Evidence/macOS14-film-f9-current-harness-40072273422/README.md)，其immediate仍565，全部frames与旧f9参考一致。当前不能宣称e48的14三路径均保持，也不据单次跨job观测锁定具体源代码原因。即刻关闭路径、firstLast与resize仍未通过，下一门槛为同VM配对与恢复历史控制；goal继续active，后续11/ObjC/iOS阶段保持暂停。

## 同机 Film ABBA 补充验收

[完整run40074197486](../Evidence/macOS14-film-abba-40074197486/README.md)现已完成f9→e48→e48→f9四组、12个fresh进程、72个完整末态图片frame；normal/active/稳定buffer/独立身份/签名与清理门槛均通过。wait/direct八场景的全部六图几何逐值相同。immediate的Glen中心依次为677、565、677、662，两个源码各自重复也变化，未形成固定源码分组；因此此前跨job565/677差异不能指定为e48的固定源码效应，也不为该未重复关联增加中间构建。这不证明源码绝无影响，更不将13的immediate601标记为等效。

ready宽度900/920/920满足，但高度/恢复时序不同；所有末态捕获才统一920×668。首次Last、resize、首次恢复过程及物理手势仍未验收，跨组像素/ICC本轮未测。详见[Film事实与边界](macOS13-Film-Initial-Position.md)。[源码审查](../Evidence/macOS14-film-source-delta-f9-e48/README.md)确认新增属性/共享闭包会改变14结构，不能只凭runtime guard宣称14结构无差异；本轮未指定根因。

[首次ABBA失败记录](../Evidence/macOS14-film-abba-attempt-40073935416/README.md)完整保留：A1稳定截图后末态AX120ms截断，B1/B2/A2未开始。随后仅把该唯一末态walk改为既有followup的2秒预算，完整六图门槛不变，得到本轮完整结果；两轮不拼接。父任务独立核验失败raw166项、成功raw495项及各自离线总清单。远端已清除自有scratch/download/cache，本机work路径改为唯一归档的符号链接，没有重复保留应用。

## 工具栏标题宿主的完整应用阴性结果

[诊断source f6 / CI40075331576](../Evidence/macOS13-toolbar-title-host-f6/RESULTS.md)基于已交付9dd，只将动态navigationTitle从detail移到整个NavigationSplitView；显式隐藏标题仍走原路径。这是all-macOS诊断候选，不宣称14保持，未合入产品。与9dd工具链、CLI/资源相同，仅GUI不同。本机active13的Buttons→Text→Controls→Buttons四阶段中，A/B原PNG文件与全部RGBA逐字相同，标题header、两层Toggle、sidebar/detail几何最大差0。因此停止此变量，不为阴性结果再运行14CI。

首轮因可选AX属性错误而中止于A首页，B未启动；原68项证据保留。修订采集器区分严格Role/Children树完整性与可选属性错误，2秒AX预算和动作/PNG顺序不动；v2完整134项原始hash通过父任务及离线复核。tree_complete=true仍伴随complete=false，不能说所有AX属性完整。八张稳定原图、normal首尾false、前台恢复、原件全成员复验与清理均有记录；effective Light未断言，仅是同机A/B几何比较。

自有应用副本、两轮observer/cache、诊断exact、传输包均清理，原交付9dd/e48精确GUI及严格签名保持。历史静态清单中有意移除的17个artifact成员由收据列出，当前现存证据另有最终清单。goal继续active，Film即刻关闭/首次Last/resize、chrome、图片布局、HDR/hero等未通过项继续保留；不进入11/Objective-C/iOS。

## Standard PQ hero 的真实静态端点

[本机13旧链证据](../Evidence/macOS13-hdr-candidate/native-pq-hero-baseline13/README.md)现已测得真实BernImage非空hero key→实际Probe/Anchor→原snapshot→原FlightView.draw，不再使用identity hero。两源body与同排原生oracle-top在raw和ICC→sRGB均逐像素相同；hero对同排oracle-bottom在固定progress0/1的sRGB fullRGB MAE却为named18.377760、custom18.385720/255，最大差164/255，各159539/230400像素不同，两phase结果相同。上下oracle自身仍有normalized MAE0.294106/max5的小差异；此前扩写为上下两排都exact的文字已纠正，数值报告未改。所有图均保留原WindowServer PNG/ICC，每phase五次连续相同raw buffer；1.970秒、前台不变、normal三项false、Metal0、原缓存/ICC/provider/identity保持。

该AppKit hero完整区块与锁定上游逐字相同，因此这是13宿主中hero与body不同的证据，尚不能归为移植回归或认定其应改成body颜色。named也失败，不能假定只传cached-derived图已足够修复；已备的optional-display候选尚未应用产品。下一门槛为新SDK编译同一源码、同一个binary在14普通效果与13运行，再比较两宿主的body/hero差值。新增手动[采集工作流](../../.github/workflows/macos14-hero-probe.yml)只构建一次，14不重编。

本轮仅静态端点，manager flight_count0/timer不存在，不声称完整flight、hide/restore、插值、retarget、High/HLG/alpha/EXIF等通过。本机SDK14.2 fixture另有已明示的gain-map编译条件及未使用时钟分支失败保护，原源码和首次失败日志均保留；远程新SDK包移除这两项适配。自有可执行文件及module cache约57.4MB逻辑文件已清理，36项归档hash和父任务独立像素复算通过。goal继续active，后续11/Objective-C/iOS仍暂缓。

新增[同一binary的13/14 hero基线](../Evidence/macOS14-hero-snapshot-40080838898/README.md)已完成：build40080291082成功，首14 job仅因optional原始defaults键缺失而在应用启动前退出、PNG0；只修改该日志读取为nonfatal后，保留实际NSWorkspace normal首尾门槛，runtime-only40080838898复用原已签名binary成功，没有重编。新SDK26.2/Swift6.2.4的13两phase×六ROI在raw/normalized均逐像素等于旧SDK13；原先SDK14 fixture编译适配不再参与这份同binary证据。

14自身hero也不等于body，因此不能把13hero强制等于live body当作已证实14目标。两宿主的`D=hero−body`十色块均值残差之差，MAE5.210863–5.236956、最大113.048334/255，最差cool812的R；父任务独立重算一致。14 hero跨phase还有max1/2的小差异，13各ROI跨phase不变，显示ICC/倍率/潜在余量不同，未指定唯一原因。13/14窗口分别1.612/2.499秒，normal首尾false、前台不变、Metal0、flight0/timer无、缓存不变均通过。optional-display候选未误合产品，公开ImageRenderer colorMode的限定诊断随后已完成，见下节；未拟合颜色或改上游14行为。新包/传输tar939623逻辑字节已清理，原始失败和成功证据分开保留；hero与整阶段继续未通过。


## Hero 色彩格式与系统转换的限定排查（2026-10-24）

[公开colorMode实验](../Evidence/macOS13-hdr-candidate/native-pq-hero-colormode13/RESULTS.md)已完成default→extendedLinear两个独立进程，没有额外模式矩阵。default两phase×六ROI的原始RGB与ICC→sRGB均精确复现原13；extendedLinear保持body/oracle与几何不变，仅hero的normalized fullRGB MAE改变named0.004439、custom0.007953/255，max3/255。跨宿主十色块`(hero−body)13−(hero−body)14`的最大差仍为113.048334/255，主要cool812.R未改善。它是阴性诊断，未合入产品。

[元数据采集40086541042](https://github.com/Torrekie/Bern/actions/runs/40086541042)成功构建并运行14，同一原签名二进制`e4b389d9…7be14`已在13运行。[原始证据和分析](../Evidence/macOS14-hero-cgmetadata-40086541042/RESULTS.md)保留实际`renderer.cgImage`之后的一处观察点：绘制期间只记录格式标量和CGColorSpace引用，全部ICC导出/分类在截图及原窗口teardown之后执行，不读新像素或保留CGImage/NSImage。13、14均为16bpc浮点、64bpp、extendedSRGB，完整ICC均3144字节且SHA256为`2b3aa1645779a9e634744faf9b01e9102b0c9b88fd6deced7934df86b949af7e`；尺寸640×360与320×180跟随实际2×/1×尺度。元数据相同不等于像素、动态范围或显示环境相同，不能把色差归为标签不同。

新13对原13、新14对历史14，各自两phase×六ROI在raw和normalized均精确相同；十色块/灰阶ramp也无差，因此这次观察未改变所测区域。仍不据单次结果宣称普遍零观察效应。最初eager观察版本仅p0有max3/255差、p1精确复现；原图保留，原因未知，不认定ICC查询已被证明是原因。当前deferred版本首尾normal均false、前台不变、无flight/timer/MTKView、原缓存不变；13/14窗口分别2.413/2.476秒。两边截图ICC、倍率及potential headroom仍不同。

[系统Core Image转换实验](../Evidence/macOS13-hdr-candidate/native-pq-hero-native-ci13/RESULTS.md)随后使用SHA锁定的不透明、up、fill640×360→320×180pt@2×输入，仅在实际snapshot边界改用已有cached canonicalPQ→显式源色空间CIImage→RGBAh/extendedSRGB CGImage，保持同一NSImage包装与Flight.draw。默认control仍12ROI全部精确、未创建CIContext；selected分支只改变hero：normalized fullRGB MAE为named0.010739、custom0.018699/255、max3/255，body/oracle全部不变。最大跨宿主残差仍113.048334/255，未解决主色差，未合产品；无自拟tone curve或色块补偿。selected窗口6.791秒，默认1.623秒，均通过既有7.9秒window界限；MTKView=0不意味着CIContext内部没有使用GPU。

以上均只覆盖实际snapshot和固定progress0/1的同图端点，不覆盖完整flight、High/HLG、透明图、其它方向/fit、物理HDR或整应用等效。后续采用了[读取原snapshot浮点样本的单一边界诊断](macOS13-Hero-Snapshot-Boundary.md)：先验证新增retain/readback的off/on控制，再比较对应平坦内区的原始half-float；不通过NSImage再缓存或重新渲染取图。该诊断现已执行，结果见下节；现有聚合数据仍不能定位可见主差的来源。当前goal继续active，后续macOS11/Swift5.3/Objective-C/iOS阶段仍暂缓；本轮清除自有缓存/构建/下载59,748,632字节和已逐字归档的work重复副本15,658,753字节，合计约75.4MB逻辑文件；不把它当成APFS实际回收或磁盘总可用量变化。清理见[收据](../Evidence/macOS13-hdr-candidate/hero-color-experiments-cleanup-20261024.json)。


## 原始半精度快照与真实容器边界（2026-10-24）

[本机off/on证据](../Evidence/macOS13-hdr-candidate/native-pq-hero-float13/RESULTS.md)先通过既有v2→关闭读取、关闭→开启两组12ROI raw/ICC归一精确复现，再发布[手动CI40091326190](https://github.com/Torrekie/Bern/actions/runs/40091326190)。远程新SDK26.2/min13仅构建一次，原签名binary`38d0bf9b…647a517`在14与13各运行off/on；[同binary完整证据](../Evidence/macOS14-hero-float-40091326190/RESULTS.md)保留四进程、八原PNG、四原raw及全部控制。14既有v2→新off、14off→on、新13v2→off、13off→on四组各12ROI精确相同；不把CI success或单次控制扩大为零观察效应保证。

on只强留原renderer返回的两个CGImage，PNG与原teardown之后各读一次原provider，layout/长度失败即停；没有重画、再取图、色彩转换、relabel或NSImage再缓存。raw严格为RGBA16Little/16float、64bpp、rowbytes×height：13合计3,686,400B，14为921,600B，均在4MiB额度内。导出后fixture保留数0；cleanup只计数不留图。新SDK13 off/on窗口1.609/1.564秒，14为2.201/1.852秒，首尾normal三项false、前台分别9292/322保持、cache/noMTK/noFlight/noTimer/五stable均通过。13与14导出本身约.010/.004秒，属于window teardown后的时间，另有15秒外层进程界限。

13的两份raw逐字复现旧SDK13；14 named/custom两份raw则彼此逐字相同。四图snapshot ICC仍完全相同；全部分量finite、alpha全1，RGB均有负值及>1值。未选择行方向、未重采样或按颜色对齐。只看未定方向的全buffer分布，14−13 named各RGB均值约+.000159264（原half样本数值，非sRGB8位码/nit），>1计数在13比4×14各多120；这种分布差别已在snapshot存储边界出现，但仍含1×/2×采样与环境混杂，不能指定具体色块、唯一系统原因或可见主差来源。

source审查还确认：当前固定端点夹具将真实FlightView挂在FixtureRoot，真实coordinator则挂在window父视图中的BernHeroOverlay。两者的实际图层/祖先状态尚未记录，因而不能把夹具主色差直接称作完整应用flight的同一缺陷。下一步[先只读记录两条容器链与现有layer hint](macOS13-Hero-Backing-Observation.md)，不先设定RGBA8根因或强制新layer。现有产品未加入浮点导出或未证实的色彩修复；goal继续active，整阶段与后续11/Swift5.3/Objective-C/iOS门槛保持。


本轮raw证据归档后，已删除自有probe/cache/传输包/临时组装草稿58,261,039B及逐字核验的work重复副本15,427,392B，合计约73.7MB逻辑文件，见[清理收据](../Evidence/macOS13-hdr-candidate/hero-float-experiments-cleanup-20261024.json)。原始raw/PNG、源码和数值报告保留；现存证据有独立最终清单。此数字不代表APFS回收量或磁盘总可用量变化。


## 已有backing与真实overlay静态路由（2026-10-24）

[backing采集40095339192](../Evidence/macOS14-hero-backing-40095339192/README.md)已完成：SDK26.2/min13只构建一次，原签名binary`86130e8e…b9b9d3f`在13/14各运行off/on。两边旧float-off→新backing-off及off→on共四组各12ROI原始RGB/ICC归一全部exact；首尾normal false、缓存/前台保持、noMTK/noFlight/noTimer/五stable与原窗口界限均通过。新增观察只发生在全部PNG和原最终检查之后、原teardown之前，不读contents/presentation/provider或设置layer。观察后看到两flight/root在13报告`AutomaticAppKit`，在14报告`RGBA8`；两边已存在的真实overlay及NSThemeFrame均`RGBA8`，wantsLayer都false但layer存在。不能从这些getter值推断实际storage、前PNG持久状态、唯一系统原因或真实动画通过。

随后完成[本机13静态route控制](../Evidence/macOS13-hdr-candidate/native-pq-hero-static-route13/README.md)：只把相同实际Flight挂到已存在的manager overlay，通过公开convert保持原屏幕ROI，mount/采样/postPNG直接检查retained两flight及其子树。默认root复现backing-off，overlay复现root，各12ROI raw/normalized exact；root y244→overlay y272→root y244，误差0pt。窗口1.681/1.614秒、前台1390保持、normal/cache/noMTK/flight0/timernil/五stable通过。该parent切换没有改善本机主色差；14的对应route和真实coordinated flight仍需验证。产品没有加入格式setter、层创建或未证实颜色修复。

下一检查点：复用已冻结`native-pq-hero-static-route13`源码差分，准备单一root/overlay手动14采集（新SDK一次构建、同原签名binary运行13），先通过默认路径和route控制，再决定是否对已有layer测试单一格式请求。实际enter/leave/计时退出/隐藏恢复仍是独立门槛，不以静态同图端点代替。其它Film/chrome/图片布局/Frame/交互/动画与HDR未通过项保持；goal继续active，不进入11/Swift5.3/Objective-C/iOS。

本轮归档后清理自有binary/tar/module cache58,872,876B及逐字核验的work副本9,955,282B，合计约68.8MB逻辑文件，见[清理收据](../Evidence/macOS13-hdr-candidate/hero-backing-route-cleanup-20261024.json)。保留源码/原PNG/ICC/元数据/控制与最终现存清单，不将此数字称为APFS实际回收或磁盘总可用量变化。


## 真实overlay的双宿主控制与早期格式请求停止（2026-10-24）

[CI40097558084与同binary13/14记录](../Evidence/macOS14-hero-route-40097558084/README.md)已完成：新SDK26.2/min13一次构建，原签名binary`cb4bd5d0…022f8d1`分别跑root/overlay。四组旧→root、root→overlay控制各12ROI raw/ICC归一exact；坐标往返0pt，normal/cache/前台/原窗口界限、noMTK/managerFlight0/timernil/五stable均通过。独立route源码目录保留原float/backing工作流功能；只改变两个manual静态flight的parent，未改变产品draw/renderer或加入新层。13窗口1.853/1.818秒、14为2.167/1.929秒。两系统均有prepareOverlay unknown-subview日志，不能当13独有原因。容器切换没有改善既有主差，也未验收真实coordinator。

随后[本机RGBA8限定候选](../Evidence/macOS13-hdr-candidate/native-pq-hero-existing-rgba8-13/README.md)的control复现新SDK13 overlay12ROI。request在第一flight mount后/下一原display前的existing layer getter返回nil，0.209秒exit1、setter0、PNG0；因此仅该早期前提不成立，不是RGBA8视觉阴性，更不是完整cache/final guards通过。未等待重试、开启wantsLayer或强制绘制，产品未合此候选。

下一检查点转为[一次真实coordinator条件替换](../Evidence/macOS14-hero-route-40097558084/next-coordinator-plan/README.md)及[至多三PNG的补充](../Evidence/macOS14-hero-route-40097558084/next-coordinator-plan/Supplement.md)：真实BernImage同非空key、source/destination不同.id/位置，用正常SwiftUI dismantle/update触发，不手调enter/leave/flight/tick/visibility；只读实际maps/timer/frame/progress，须见运动、自动finish归零/timer停止/overlay临时view移除、目的图可见。before/settled各5stable，中途首次.2<p<.8取一张原窗口并记录capture前后状态，需目检实际绘制，不能用不同步13/14逐像素相等代替动画验收。仅新SDK原Hero exact+imports同binary13/14，不带旧SDK fatal clock guard或旧float双key/双snapshot合同；单次失败保留证据，不隐式重试。此方案尚未实现或运行。

其它Film/chrome/图片布局/Frame/交互/HDR和动画未通过项继续保留，完整macOS13阶段未验收，goal active；不进入11/Swift5.3/Objective-C/iOS。本轮清理自有binary/tar/cache 58,335,236B与逐字核验的work副本5,392,458B（约63.7MB逻辑文件），见[收据](../Evidence/macOS13-hdr-candidate/hero-route-format-cleanup-20261024.json)；不当作APFS实际回收或磁盘净变化。


## 一次真实hero协调的原生结果与采样边界（2026-10-24）

上节未执行方案现已由[CI40103369574及同binary13/14运行](../Evidence/macOS14-hero-coordinator-40103369574/README.md)落实。新SDK26.2/min13原签名binary`5739a040…82ecea36`使用完整原Hero计时回调，单个同key的BernImage在不同.id/位置间由一次真实SwiftUI条件替换驱动；无manual Flight、手调enter/leave/tick/finish或visibility/frame/progress。两端均观察到同一真实flight及live timer/位移，最终flight/timer/overlay临时view归零，source离开原层级但weak未dealloc。normal/cache/noMTK/前台/原窗口界限、before/settled五stable通过；13/14窗口1.547/2.044秒。CI成功仅为原生采集门槛通过。

原始起点/终点均可见，完全opaque同宿主ROI经ICC归一sRGB后13 MAE0.294106/255、max5，14 MAE0.271169、max2，均非exact。原中图13已有位移、14仍在source；固定几何inset内非白内容bounds分别root[80.5,66,400.5,246]与[16,24,336,204]，而逻辑trigger为p.287/root(112.5062,87.1886)与p.692/(248.5375,176.2567)。native前后bracket不等于画面同步，不据此唯一归因系统、RunLoop或渲染阶段；中间帧、颜色和完整动画仍未验收。

下一检查点只调整[采样时机](../Evidence/macOS14-hero-coordinator-40103369574/next-sampling-plan/README.md)：首次.2<p<.8仅arm，恰下一原自然RunLoop/sample后拍一次mid，保留分开的index/state/uptime；失去同一live flight则incomplete、不寻第二次band或强制flush/进度。尚未实现/运行，它不承诺同步修复。产品没有合入颜色/layer请求；Film/chrome/Picture/Frame/交互/HDR和完整动画未通过项保持，goal active，11/Swift5.3/Objective-C/iOS仍推迟。

本批原binary/tar和已用完module cache清理57,691,387B；逐字核验后的work重复副本另行清理，见[收据](../Evidence/macOS14-hero-coordinator-40103369574/cleanup.json)。保留六张原PNG/ICC、报告、源码与最终现存清单；数字为逻辑文件量，不代表APFS实际回收或磁盘净变化。


## 下一原样本采集的实测对照（2026-10-24）

上节采样方案已由[CI40107406624及同binary13/14](../Evidence/macOS14-hero-coordinator-delay-40107406624/README.md)落实。新SDK26.2/min13原签名binary`fca470c9…cb5c6e23`只改变observer，首次band仅arm，下一次原outer-loop的RunLoop.run/sample才采唯一mid，不重试或修改clock/draw/progress/visibility。两边schema与原生门槛通过：13 index9→10、p.278344→.368318、间隔19.179ms；14 index7→8、p.609194→.714572、间隔27.411ms。窗口1.435/1.951秒、normal/cache/front/noMTK及真实结束清理保持，weak source仍未dealloc。本机未编译、重签或生成模块缓存。

四项same-host旧→新before/source、settled/destination ROI的原RGB和ICC intent0归一sRGB均exact，端点内容保持。新before→settled仍非exact：13 sRGB MAE0.294106/max5，14为0.271169/max2。root原mid目检和固定12pt opaque inset非白内容bounds显示13已有位移[109.5,85,429.5,265]，14仍source[16,24,336,204]；capture逻辑原点却为(139.7547,105.0299)/(256.0963,181.2059)，CG前后native bracket未变。bounds不作精确flight配准；新的trigger字段是arm别名，不能误当capture状态。额外一次原循环仍未建立presentation同步，不通过中间帧/颜色/动画，也不唯一归因系统或手动泵。

下一检查点为[正常NSApplication.run生命周期](../Evidence/macOS14-hero-coordinator-delay-40107406624/next-app-loop-plan/README.md)的单一observer执行模型对照，尚未实现/运行：原采样body以MainActor timer调度，保留原产品/clock/scene/key/action/arm/截图与门槛，terminal后stop→run返回→正常defer。此入口更接近实际应用，但不是同步fence或已知修复。原7.2s入口deadline及hard watchdog minimal-report限制明确保留；不叠加等待、flush/layout/display或进度控制。本批原binary/tar和逐字校验work副本已清理，见[收据](../Evidence/macOS14-hero-coordinator-delay-40107406624/cleanup.json)。其它未通过项与goal active保持，不进入11/Swift5.3/Objective-C/iOS。


## 正常AppKit循环中的可见过渡（2026-10-25）

上节执行模型已由[CI40110795231及同binary13/14](../Evidence/macOS14-hero-coordinator-app-40110795231/README.md)实跑。新SDK26.2/min13原签名binary`a98bd3d4…255e8d0d`保留完整原Hero与capture/save helpers，用唯一NSApplication.run、delegate async preload和default-mode selector sampler代替手动泵；launch/entry/实际return/terminal/stop/terminal-only own wake各1，depth1/reentry0/terminal后callback0。两边native/execution门槛、normal/cache/front/noMTK、singleFlight运动及真实结束归零通过，窗口1.295/1.617秒。本例weak source均为nil，未当通用内存验收。本机未编译、重签或生成模块缓存。

root原mid目检两边都有位移，14本次已离开source；固定12pt opaque inset非白内容bounds为13 [96,76.5,416,256.5]、14 [233,166,554,347]，不是精确flight配准。arm→capture为13 index8→9/p.237941→.362234，14 index7→8/p.646607→.693877；保留分开的状态/时间和CG bracket，不要求它们等于画面，也不归因内部提交步骤。四项同host旧delay→新app端点ROI原RGB/ICC归一均exact；新before→settled仍为13 sRGB MAE.294106/max5、14 .271169/max2，均非exact。本例已有可见中间运动证据，颜色、完整轨迹/时序和其他输入/中断仍未验收。

下一步只补[同一actual snapshot NSImage的原生显示对照](../Evidence/macOS14-hero-coordinator-app-40110795231/next-native-view-plan/README.md)，尚未实现/运行：保留默认Flight控制，比较NSImageView，而不换原图或绕过ImageRenderer。旧NSImageView/body exact不是同输入，14 Hero也不等于body，不能直接以body为目标或合入产品。候选先复现13默认静态控制，再对完整色块/灰阶报告改善与恶化；不加层setter、RGB补偿、图像白名单或自创tonemap，不为此未知再触发14CI。本轮binary/tar和逐字归档work重复副本已清理，见[收据](../Evidence/macOS14-hero-coordinator-app-40110795231/cleanup.json)。其余未通过项和完整阶段门槛保持，goal active，11/Swift5.3/Objective-C/iOS仍延期。

## 同一snapshot的系统显示组件对照（2026-10-25）

上节[同snapshot NSImageView限定诊断](../Evidence/macOS13-hdr-candidate/native-pq-hero-snapshot-view13/README.md)已在本机13实际完成。SDK14.2/Swift5.9.2、语言模式5、arm64/min13、O/j2构建成功，原ad-hoc严格签名binary`514079a0…8679f1b`依次运行control/image-view；继承静态fixture已有的gain-map/unused-clock编译适配，不冒充真实coordinator或完整应用构建。只把named Flight原同一snapshot NSImage交给stock NSImageView，跳过该父view原draw；custom、body/oracle、actual overlay、几何和原采样循环均保留。未换原图、再次缓存/渲染、加入layer setter或产品代码。

control先精确复现冻结13-overlay的全部12ROI原RGB/ICC归一，才运行candidate。独立native核验构建/同binary/21输入组装、normal/cache/前台9292保持、五stable/noMTK/managerFlight0/timernil、route回转0pt均通过，窗口1.787775/1.607795秒。candidate四阶段保持同child/flight/image、320×180、stock配置与原parent/window；orderOut后child.image=nil并detach，仅证明child/helper清理。原普通catch/try?report写和hardwatchdog绕defer的边界保留，由fresh-output wrapper和实际完整输出分别核验，不声称所有失败均保存完整report。

root已目检两张原p0，candidate named内容实际可见。control→candidate只两phase的flight-named变化：raw fullRGB MAE0.103565/255、max1，ICC intent0→sRGB MAE0.086730/255、max1；其余10ROI原RGB/归一均exact，嵌入ICC相同。完整十色块和灰阶、固定14参考重算保留：`|D13−D14|`的30通道平均p0为5.210863→5.272487，p1为5.224399→5.216157；p0有4通道改善/19恶化/7不变，p1为13/10/7。最大残差两phase都变大（112.616329→112.724330、113.048334→113.156336）。不能只挑平均或一块颜色宣称改进，也不把max1变化指定为取整根因；该显示组件替换未解决主色差，停止这一限定方向，未合入产品、不追加14 CI或真实flight。

下一检查点转回已经保留的actual snapshot float样本：只读确定能否建立13/14平坦内区的行/通道语义，再比较边界两侧；尚无新离线语义分析或修复。保留同snapshot原PNG/ICC、源码、日志、独立审查和数值结果；自有binary及module cache57,493,320B已清理，work重复副本另以逐字归档收据记录，不当作APFS实际回收。四项原交付binary hash及两app严格签名保持。颜色、完整动画及其余Film/chrome/Picture/Frame/交互/HDR门槛未通过，goal active，不进入11/Swift5.3/Objective-C/iOS。

## Named平坦快照内区的原bits相同（2026-10-25）

上节[离线语义分析](../Evidence/macOS14-hero-float-semantics-20261025/README.md)已完成：Apple公开SDK直接确定RGBA16F LE lane，预先固定十flat/三band/五x-bin的完整tuple结构，四份原raw均唯一top-down。独立Fraction/struct复核两个方向的全部结构细项和原hash；不是按PQ预期数值、RGB大小关系或13/14更接近来选方向。source PNG无损active SHA与旧验证一致，raw/PNG只引用旧cohort，未新构建/UI/CI。

独立review冻结并绑定后才运行原analyzer known-direction，另一struct<4H/<4e reader确认40flat整区恒定、alpha1、20patch/80delta以及4whole/44region统计。named十patch RGBA原half bits13/14全部相同，包括主差涉及的cool812；custom仅white812/red812/green812/blue812/pastel812不同，RGB最大原数值差0.001953125、30项绝对差平均0.000244140625。保留负值/>1/finite/NaN/Inf；无ICC/transfer/clamp/unpremultiply/nits换算。13/14每flat11648/2912原pixels，只比较对应恒定值，不resize或配对ramp列。

这排除了named十对应平坦内区的原数值差作为其主显示差解释，仍不能宣称整个CGImage或最终显示相同。下一[单一检查点](../Evidence/macOS14-hero-float-semantics-20261025/next-display-plan/README.md)先补deferred renderingIntent/isMask/shouldInterpolate/decode，尚未实施；不提前把未读对象语义或NSImage/context/显示余量指定为根因，也不把directCG当已知修复。

首轮source filter0限制在读snapshot raw前停止，第二轮在pretty JSON体积guard处未写结果；原失败均保留。成功版本只补标准PNG过滤器并压缩JSON空白，原几何判据/128KiB上限不变。没有新binary/cache，九个work重复树673116B逐字核验归档后清理，不当作磁盘净回收。完整macOS13颜色/布局/交互/动画及其它未通过项保持，goal active，不进入11/Swift5.3/Objective-C/iOS。

## 原 CGImage 的四项绘制属性相同（2026-10-25）

上节 deferred getter 已由[CI40119614788及同binary13/14](../Evidence/macOS14-hero-cgsemantics-40119614788/README.md)落实。新SDK26.2/Swift6.2.4只构建一次，原签名arm64/min13 binary `68974a3f…b3eee334`在两host各运行off/on；29包成员/21源码输入/拼接/严格签名执行前核验通过，本机未重编或重签。实际原PNG、teardown及raw导出后，才对同一renderer-return对象各读取renderingIntent/isMask/shouldInterpolate/decode一次；RGB3 guard复用原descriptor，不增加image.colorSpace读取。原产品/Driver/finish保持，optional backing observer明确off。

两key跨host均为intent0、非mask、允许插值、decode=nil；16字段schema与provider-start→observation→release时序、普通partial失败传播均核验。nil只记录空值，不合成默认decode；非nil六项/±0/nonfinite分支只有源码审查，未运行。四份完整native gate通过，13窗口1.657092/1.612711秒、14为2.352033/1.916948秒，normal/cache/前台/noMTK/五报告buffer保持。manual static flight0/timernil只覆盖同图p0/p1，不冒充真实coordinator或完整动画；export后helper引用0不证明全部对象释放。

四组旧float→新off及off→on控制各12图像ROI原RGB/ICC intent0归一sRGB均exact，同host嵌入ICC保持。四份新raw分别与旧同host/key长度及SHA逐字相同，因此先前独立语义结果仍适用。它们排除了本例四项已读显式属性不同的解释，没有解决主色差、证明全部CGImage/目标context相同或指定唯一根因。本轮仅补观察，无产品修复合入。

下一[单一检查点](../Evidence/macOS14-hero-cgsemantics-40119614788/next-direct-plan/README.md)已冻结但未实施：本机13对相同原snapshot/retention做默认NSImage.draw与scoped CG direct配对，先复现default和完整方向/extent门槛，再完整比较D13−D14，不能把body颜色当目标。没有新增widget/cache/layer/曲线组合或额外14CI。原binary/tar844797B及逐字归档work重复8742890B已清理，归档内部22同字文件硬链接去重名义2765989B；均非APFS实际回收或磁盘净变化。完整颜色、动画和其它未通过项保持，goal active，11/Swift5.3/Objective-C/iOS继续延期。

## 同一原 CGImage 直接绘制未改变结果（2026-10-25）

上节[本机13 default/direct 对照](../Evidence/macOS13-hdr-candidate/native-pq-hero-cg-direct13/README.md)已完成。SDK14.2/Swift5.9.2、语言模式5、O/j2、arm64/min13首次构建成功，原linker ad-hoc严格签名binary `be263dfb…09d8fd0`运行两模式。继承不可达gain-map/静态unused-clock编译条件；不是新的跨host同binary或真实coordinator构建。两mode共用原held与释放范围，只增加weak NSImage绑定和同步CGImage借用；default仍是原两行NSImage.draw，direct仅named在当前context中保存/恢复状态、一次局部y反转，以normal/sourceOver和原alpha顺序画同一CGImage两次。custom保持，缺绑定不回退成功，原float freeze/export/finish/release逐字不变。

完整原gate与附加gate均通过，窗口1.717993/1.657393秒、前台9292保持，normal/cache/五报告buffer/noMTK/managerFlight0/timernil保持。default先复现旧on全部12ROI原RGB/归一sRGB；direct随后全部12ROI也exact，四raw直接bytes比较同旧同key。root逐p0/p1原PNG目检方向、非空及完整可见extent通过，但white/background同色处不证明每像素覆盖，未跑tuple或真实flight。独立native首次错误预期exe已删的复核方法另有addendum更正：exe保留时，两模式原字节validator及完整base均独立退出0，无UI重采。

完整十patch/ramp算法在绑定几何门槛后单次执行；保留14参考重算的全部68comparisons/16primary/ROI/ramp SHA与冻结结果一致。named/custom每phase30通道的改善0/恶化0/不变30，全部signed变化与ramp aggregate变化均0；named的mean absolute(D13−D14)仍p0 5.210863095/p1 5.224399038，最大112.616328984/113.048334478。该适配变量未改善主差，停止此路线、不合产品，不唯一归因NSImage/context/系统或显示环境。

下一[唯一固定原生SDR表示候选](../Evidence/macOS13-hdr-candidate/native-pq-hero-cg-direct13/next-sdr-plan/README.md)尚未实施：actual snapshot经CoreImage→RGBA8/sRGB，再用原NSImage双draw，区别于旧cached-PQ→RGBAh；不假定toneMap Bool对extendedSRGB已生效，不重标记/拟合。exe及module cache57500008B和逐字work重复13585553B已清理，内部16同字别名硬链接去重名义5716684B，均非APFS实际回收。颜色、完整动画与其它未通过项保持，goal active，后续11/Swift5.3/Objective-C/iOS阶段继续延期。

## 实际快照输出 SDR 的混合结果（2026-10-25）

上节[本机系统SDR recipe](../Evidence/macOS13-hdr-candidate/native-pq-hero-snapshot-sdr13/README.md)已执行。同一SDK14.2/Swift5.9.2、arm64/min13原linker ad-hoc binary `e555781e…365d15dc`先default再baked-named。FloatCapture与原双NSImage.draw逐字保持，只在实际renderer返回对象之后为named一次创建CIImage(true、原空间)→单context→精确extent RGBA8/sRGB/deferred:false派生显示；custom/default不转换。实际toneMap执行仍unknown，不能把Bool请求或8位输出当因果证明。

两完整native/additive gate均通过；default旧on12ROI raw/sRGB exact，candidate仅named两phase变化，其它10ROI exact，四原raw同旧同key直接bytes相同。窗口1.729275/1.868617秒、前台9292保持、normal/cache/五报告buffer/noMTK/静态flight0/timernil保持。一次转换0.258979292秒、17条phase同一derived/display身份；helper和原float引用按各自范围清空，不声称全部对象dealloc。两原PNG方向/非空/完整可见extent目检通过，但white/background及无逐像素覆盖限制保留；candidate两phase PNG本身逐字相同。

单次完整算法与五子命令均0，保留14参考的68comparisons/16primary/所有ROI/ramp SHA严格重算一致。named mean absolute(D13−D14) p0 5.210863095→1.525197459、p1 5.224399038→1.567882898；最大112.616328984→25.754035027、113.048334478→26.186040522。但p0改善5/恶化7，p1改善3/恶化9；最大新增恶化为green812 R约2.43544码值，全部120通道和16恶化项保留。named ramp p0三通道略改善/p1略恶化，custom全不变；不是单调改善，不据均值采用或改阈值验收。

下一[真实Standard named transition门槛](../Evidence/macOS13-hdr-candidate/native-pq-hero-snapshot-sdr13/next-flight-plan/README.md)尚未实施：新SDK/min13保留实际timer和正常AppKit loop，同key的source/destination必须两次独立snapshot/派生，记录触发→snapshot→Flight.started延迟。静态259ms不证明真实进入动画成本；生产dynamicRange尚未传至Hero链，private Standard不能冒充产品正确门控。本轮无产品改动或新远程CI，exe/cache57485328B及work重复13677124B清理，内部13同字别名硬链接去重名义5077367B，均非APFS实际回收。完整UI/颜色/动画及其它门槛未通过，goal active，后续平台阶段继续延期。

## 原始 Film 首次 Last 的本机对照（2026-10-25）

[唯一原生采集与复核](../Evidence/macOS13-film-first-last-e48-20261025/README.md)已完成，保留原e48 Gallery/CLI，没有产品改动或新CI。13.7.8/arm64正常三false、Light/active，先Patterns setup，再Film initial和一次Last。collector0/8.599078s、wrapper0/10.444415s；两终态AX各六图完整，原buffer四次连续相等。新外部helper使用Swift5.9.2/14.2头文件/target13，但实际内嵌SDK13.0，区别于交付App的SDK26.2/min13。

离线方案在读本机数据前冻结，独立复算两状态的12图原screen/窗口origin-relative xywh与逐字段差。对固定14参考40165343690的首次Last，前五图relative x均为−14.5pt；Windowpane为−14.504430837515656pt，y/width/height的小非零差原样保留。initial四个未放大图的relative xywh精确相同，其余两图保留原浮点差。没有把14的repeat Last混作参考，没有按阈值归零、拟合补偿或新增位置成功判定。13的2×/ICC4032B与14的1×/ICC3300B均原样记录，本轮没有像素比较/归一化；AX在PNG之后，端点不代替完整动画，14参考仍是当前port e48而非未修改上游。

本次强kernel清理完整通过：先恢复原1390/kernel1792598787.261710，再停止自有25080/kernel1792908958.713508，termination0、postown=null；exact-child/IPC/private prefs/state均通过，defaults delete0且原5秒上限不变。旧cohort清理false不改写。独占桌面已释放、cursor位移0、配置不变，空overlay clear-only后的false与原visible状态都保留。自有helper/privateApp及编译cache合计53,933,813B逻辑文件已核hash/lsof后退役，原四个交付exe不变；不把此数字当APFS回收量。

本轮属于采集与证据推进，位置一致性仍未通过；尚不能由单次差异归因或改默认3/nearest/anchor/间距。下一先审查显式Last程序化滚动与现有几何证据，缺口明确后再决定最小观察；不重开已停止的Row/颜色/搜索/Scene路线。完整13颜色/布局/交互/动画门槛及后续macOS11/Swift5.3、Objective-C、iOS阶段保持未通过/延期，goal active。

## 显式 Last 的证据边界与观察准备（2026-10-25）

[源码与有界观察包](../Evidence/macOS13-film-explicit-last-observation-20261025/README.md)已独立复核。13兼容snap允许响应非live的bounds变化，包括程序化滚动可能产生的通知；initial owner首次退役后generation不再递增，后续显式Last不因此使这波工作失效。实际执行、哪个writer介入、native坐标及−14.5pt原因仍无运行证据，未改滚动条件或补偿。

现有AX的“完整/未截断”只指筛选后的walk；持久化flat行没有原生父子树、数值AXValue或NSClipView/document offset，AXScrollArea矩形不能当viewport。Last成功响应证明注册闭包被调用并返回，generated setter却可能静默拒绝，故不能当Rust draft/私有target/原生到达的直接读回；这不表示本次确有拒绝。

已实现仅显式启用的macOS13诊断源码：五固定槽及有界计数、weak身份、首post-request inspect才序列化导出，记录请求、首eligible snap/首writer owninputs及postcapture native scalar，不增加View/Task/timer/滚动操作。原条件、算式、动画与150/160/180ms不变；有限观测仍有开销，不能先宣称无影响。真实standalone core typecheck0、两完整patch模板parse0（Swift5.9.2/请求SDK14.2/target13）及实际fuzz0补丁应用通过；不等于完整SwiftUI类型检查、Swift6产品构建或运行。template-only patcher故意拒绝generated Runtime。

本轮无产品源码/行为改动、无新native或CI；临时cache与重复源码49,916,983B逻辑文件已核hash/lsof清除，原四个交付exe和两个模板保持。下一先完成新SDK/Swift6/target13 observer构建与实际generated来源，再核观察影响/适用14参考及独立强kernel入口，才可运行。诊断失败不得改写原采集/清理真假；完整13验收及后续平台阶段仍未通过，goal active。


## 完整 Swift6 观察版首次构建失败（2026-10-25）

[CI40175193229的原始失败与审查](../Evidence/macOS13-film-last-observer-build-40175193229/README.md)已保留：新SDK26.2/Swift6.2.4/arm64/target13执行原CLI完整构建计划，在`BernSnap.body`的SIL生成阶段出现signal6与ErrorExpr编译器崩溃。cargo1、collector false、无App tar/运行结果。生成Runtime132272/e386、Generated81110/f72及Style214581/fb2符合预期源码身份，但不能据此称产品编译或后续signature/inverse gates通过。完整17,182B日志未截断，API ZIP摘要校验后已删除下载ZIP。

独立源码审查把最小候选限定为将新增可选弱owner闭包移出ViewBuilder，以显式MainActor方法和闭包类型表达相同enabled/nil/weak身份语义；原snapAllowed/snapGeneration、计算及150/160/180ms保持。旧两条Sendable warning在原版已存在，不能当本次根因。该表达式候选仍需完整Swift6重建，不称已修复或观察无影响。

本机只执行真实prepare校验，未调用编译器或生成模块缓存。首轮临时源码/harness副本42,550,185B逻辑文件在独立读完、核hash和lsof为空后清除；证据单处归档，历史work别名只读。原交付产品及模板保持，完整13视觉验收和后续平台阶段仍未通过，goal active。


## 完整 Swift6 观察版构建通过（2026-10-25）

[修正后CI40176620054与实物复核](../Evidence/macOS13-film-last-observer-build-40176620054/README.md)已通过原CLI完整生成/构建计划：Swift6.2.4、SDK26.2、arm64/target13，cargo0、collector0与额外二进制校验通过。仅把新增可选弱owner表达式移入显式MainActor helper；原snap条件、计算、动画/延时、coreb9及Runtime字节不变。它确认该写法能构建，不唯一解释旧编译器崩溃；首轮失败false及原日志保持。

实际生成Runtime132272/e386、Generated81110/f72与Style214863/179b绑定固定源码，成功collector验证Runtime扩展表/noSVG及逆向恢复626c。App实际3770800B/e2fb，root与独立审查仅内存读取tar：10成员hash、包内外JSON、arm64/MH_EXECUTE/min13.0/SDK26.2一致。严格签名由CI执行通过，本机未重验签名、抽出App、重签或启动UI；新build的CLI未交付或冒称原31a。

两轮prepare临时源码/harness共85,104,782B逻辑文件已清除，成功App tar1,729,195B在双方读完及lsof为空后退役；下载ZIP验证API摘要后删除。保留小源码/收据与远端3日artifact，用前须重查可用性；这些数字不当作APFS回收量。四个原交付exe及两个产品模板的hash保持不变。

本节仅完成编译与来源门槛，没有native13/14、观察JSON或观察影响验收；−14.5pt差异及完整UI等效仍未解决。下一先做与新App/原CLI身份绑定的fresh强kernel入口与固定PNG→AX→inspect顺序，再验证观察对端点的影响，才可用诊断解释路径。完整goal active，macOS11/Swift5.3、Objective-C及iOS继续延期。
