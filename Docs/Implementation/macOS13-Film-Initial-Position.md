# Film 初始卡片：测量、兼容修复与剩余边界

诊断候选已经复现 macOS 14 的初始 Glen 身份与卡片几何；它没有把 Rust 默认值 3 改成 4。父任务已将不含日志的最小 Style 语义补丁提交为 `e48fff46b3a92a28465ad74295bd273a9d69af7d`。**该 clean 源码已通过整应用 CI，仍待实际 macOS 13 验证**，不能套用诊断构建的通过记录。后续首次 Last 和加宽窗口仍有差异，完整 Film 等同尚未通过。

## 原始外部现象与已排除项

锁定上游 A14、此前移植的 f9/B14 首次进入 Film 都显示 Glen；旧 C13 显示 Madras。`GalleryDraft.centered` 初始值始终为 3。原始截图只证明可见身份，不能证明原生 Binding setter 曾直接写入 4。

- A14、B14 和 C13 的最终外框均为 920×668 点，detail 从窗口内 x211 起，宽 709 点。最终外框不能解释初始身份差异。
- Inspector 稳定显示时，分隔线约在 x695，右区实际约 224 点加分隔线。不能把声明的默认 300 或理想 280 当作实测宽度。
- Inspector 修饰器位于 detail 的 page match 之外，关闭与 Film 首次挂载可能重叠；旧 GIF 未记录关闭到首次 Film 的完整过程。
- 早期 Last 比较曾在约 1 点内吻合，但那不是本轮完整操作序列的普遍保证，见后面的首次 Last 对照。

原始输入见 [A14 记录](../Evidence/macOS14-gallery-normal/reference.json)与 [C13 比较](../Evidence/macOS13-candidate/gallery-comparison.json)。

## 三个 fresh-process 场景

[run 40062194628](https://github.com/Torrekie/Bern/actions/runs/40062194628) 使用同一上游 build 39959549054、harness `2aa4e63`，在 macOS 14.8.9 / light 下运行三个独立进程。三项辅助功能标志均为 false；最终外框均为 920×668 点。原始 PNG、AX 和命令记录保存在 [Film timing 证据](../Evidence/macOS14-film-timing/README.md)。

| 场景 | 最终放大卡 | Glen 中心 x / 宽度（窗口内点） | 首次完整 AXImage 集合 |
|---|---|---|---|
| immediate：关闭 Inspector 后立即进入 | Glen | 566.0 / 268.79975 | 选择命令后 0.566 秒 |
| wait：关闭且缓冲稳定后进入 | Glen | 601.0 / 267.53479 | 0.225 秒 |
| direct：从未打开 Inspector | Glen | 601.0 / 267.53479 | 0.704 秒 |

wait/direct 的 Film PNG 逐字节相同，因此 Inspector 退出过渡不是 Glen 身份的必要条件。immediate 的最终落点仍差 35 点；但首组从 900×652 调整到 920×668，后两组启动时已恢复到目标尺寸，且每种序列只运行一次。不能单独归因关闭动画。

早期 AXScrollArea 宽 240 点只是可访问性区域，不能当作 NSClipView 的真实宽度。早期遍历有截断，也没有取得 Inspector 退出期间完整的宽度时间序列。Madras 中心 331 相对 detail 中心 565.5 差 234.5 点，与 `(709−240)/2` 相关，但这个相关性本身不证明更新顺序。

此前 run 40061845578 没有 Film 测量：采集器的长 IPC 路径与 socket 后缀合计 101 字节，超过上游 100 字节限制。此判断来自路径与精确源码，不是应用日志直接打印的 bind 错误。失败原始诊断保存在 [failed-ipc-capture](../Evidence/macOS14-film-timing/failed-ipc-capture/README.md)；短 `/tmp` 路径修正只改变采集器。

## 整应用内部 trace：已观测到什么

[e4c01e4 诊断分支](https://github.com/Torrekie/Bern/commit/e4c01e4df31e7e9a5380285cb4fe8fd01a90b985)基于 f9，仅在 `BernStyle.swift` 的已有回调和显式写入处记录日志；[build 40064305202](https://github.com/Torrekie/Bern/actions/runs/40064305202) 使用 SDK 26.2 / Swift 6.2.4，ARM64 / min13，真实 SwiftUI。未增加 View modifier 或 Binding wrapper，未改变原 150 毫秒 quiet 判断及 target 赋值顺序。

只在 `BERN_SCROLL_TRACE_DIR` 存在时，MainActor 有界缓存最多 4096 个事件，首次 expect 后约 2 秒一次写入 JSON。**未拦截每次原生 Binding setter，也未记录可能离开主线程的 native snap 回调。**

未插桩 f9 的 [direct 40064744315](https://github.com/Torrekie/Bern/actions/runs/40064744315) 与 e4 的 [direct 40064766856](https://github.com/Torrekie/Bern/actions/runs/40064766856) 在 active macOS 14 上取得完全相同的六张 AXImage frame：Glen 中心 601、宽 267.53479，Madras 中心 331。Patterns PNG 相同，Film PNG 不同；不声称整图像素一致。诊断自身的首次 Film 与日志写出后 Film PNG 相同。

14 的 trace 有 102 个事件、drop 0、一个 position 实例；相对首次 expect 的主要时间如下：

| 时间 | 已记录事实 |
|---|---|
| expect 前约 0.3 毫秒 | viewport 为 709×207；id3 frame 为 x564 / width240 |
| 0 毫秒 | onAppear 以 position3 执行 expect，明确 target nil→3 |
| 0.65 毫秒 | snap 计算 margin234.5 |
| 9.68 毫秒 | id3 report 为 x798.5；目标观察回调 nil→3 |
| 46.97 毫秒 | id3 report 为 x234；随后 nearest 为 3 |
| 147.76 毫秒 | id3 report 为 x0、id4 为 x270；随后 nearest 为 4 |
| 300.05 毫秒 | quiet 有效唤醒，coming 清空，stops 增加 |
| 301.02–301.47 毫秒 | target3→nil；follow 明确把 position3 写为 4 |

因此已记录到的是框架的 nearest/follow 写回，不是“原生 setter 直接写 4”。当 id3 覆盖 x0…240 时，nearest 仍按完整 709 点视口中心 354.5 计算，id4 中心 390 更近。这解释这次 follow 的选择，但还不能独立解释首次原生定位为何到达该坐标。

### 同一 e4 构建的 macOS 13 后台诊断

[原始完整归档](../Evidence/macOS13-film-scroll-trace/README.md)包含两次 active 交付失败的 partial 与一次明确的 inactive13 诊断。两次失败都在选择 Film 之前；第二次唯一 activation 请求返回 false，样本始终为 Messages。没有 Film PNG 或 trace，不能作为产品 Film 回归结论。

成功后台诊断使用同一 e4 构建的代码、唯一 bundleID 和合法 ad-hoc 签名，隔离本机历史。完整 GUI hash 因签名改变；所有 section hash 及归一签名存储字段后的 payload 相同。原 exact bundle/CLI 未改。

该次 27 个截图前样本均为 Simulator 前台、Gallery 后台、own window alpha1。Film 与日志写出后 PNG 相同。13 为 2x 后台，14 为 1x 前台，不能作为同条件 active 颜色/材质验收。13 的放大卡仍为 Madras，中心 565.5、宽 268.8。94 个事件、drop0 显示：margin 与 target 回调在约 12–13 毫秒执行 Reader 定位；id3 在 27.97 毫秒到 x234.5 后保持；nearest 为 3；225–228 毫秒释放 target 后 follow 没有写 4。

两边的分歧发生在 quiet/follow 之前，不能更改 nearest 或默认值来掩盖。

## 真实原生快照与首次坐标修复范围

独立 [744 原生快照 / run 40066003179](../Evidence/macOS14-film-timing/native-snapshot-40066003179/README.md)只在原 2 秒 flush 时追加公开 AppKit 只读查询。active14 下，111 个 view 未截断：真实 HostingScrollView/clip 为 709×207，clip.bounds.x564；document 宽 1638，左右 contentInsets234.5，autoAdjust=false。1638 正好是 `6×240+5×30+2×24`，不含 13 真实 SwiftUI padding 增加的 469 点。

13 的 Reader 使用完整 viewport 定位；14 native contentMargins 与首次目标安装产生另一坐标。在**首次仍持有目标、center anchor、正 center-snap margin、真实长度有效**的已测域中，设 viewport 为 `V`、单侧 margin 为 `m`、目标长度为 `L`、有效长度 `Ve=V−2m`，Reader 轴向 anchor 候选为：

`a′ = 0.5 × (Ve−L) / (V−L)`

Film 恰好 `L=Ve=240`，因此算出 0；没有写死 leading、id4 或 234.5 像素。非 center、margin0、unknown/nonfinite、`L>Ve` 或退化尺寸保持原 anchor。其它任意 anchor 公式没有被本轮样本证明，也不应推作全局 programmatic-scroll 规则。

诊断候选 [d14655fb / build 40067955380](https://github.com/Torrekie/Bern/actions/runs/40067955380)只增加初次 ownership 与 generation：原有 geometry/nearest/margin 回调可按不含 origin 的几何签名有界重定位；quiet release、明确 Last/First、用户接管及 13 的 onDisappear 同步 retire。旧的 160 毫秒 snap work 捕获 generation，不能在 150 毫秒 release 后跨代复活。没有新 timer，不改 nearest、phase、默认 3 或 native14 路径。

同一保留 StateObject 再出现时按 once-only 处理；新 identity 才有新 owner。目标长度在其它观测值不变时单独变化的重试、同 identity 重现与未测方向仍是泛化边界。

## 新增三方对照：初始修复与后续差异分开

[active14 followup](../Evidence/macOS14-film-followup-40067683100/README.md)使用未插桩 f9，同一构建在固定顺序下执行 Last→First→Last again→加宽 1020→恢复 920。父任务随后单次运行了 d146 候选与[旧 f9 原件基线](../Evidence/macOS13-film-followup-f9-baseline/README.md)，两者使用相同 collector `3f434cf`、inactive13/direct/last-resize 与 startup readiness gate。

各阶段 AX 均完整、六张图片齐全，每张 PNG 均通过 4 次相同原始 buffer 比较；detail 宽度均为 709→809→709。下表为窗口内中心 x：

| 阶段 | 旧 f9 / 13 | 候选 d146 / 13 | f9 / 14 |
|---|---|---|---|
| 初始 | Madras 565.500 | Glen 601.000 | Glen 601.000 |
| Last | Windowpane 558.500 | Windowpane 565.686 | Windowpane 573.000 |
| First | Gingham 565.500 | Gingham 565.686 | Gingham 565.000 |
| Last again | Windowpane 565.500 | Windowpane 565.686 | Windowpane 565.000 |
| 加宽 1020 | Windowpane 615.500 | Windowpane 615.686 | Windowpane 599.000 |
| 恢复 920 | Windowpane 565.500 | Windowpane 565.686 | Windowpane 565.000 |

候选初始 Glen 与 14 的完整 frame 差值最多 0.0000062 点。First、Last again、恢复与加宽阶段，候选相对旧 13 仅差约 0.186 点；加宽约 16.5 点的主要差异在旧 13 已存在，不能归为此次初始修复新引入。

**首次 Last 不能宣称相同：**候选与旧 13 的中心差 7.186 点，且与 14 仍差 −7.314 点。两次 13 初始身份不同；候选还经过一次 2 秒 trace flush 和 after-trace 截图，旧 f9 明确 unset trace 环境且没有额外暂停。两次前台分别是 Simulator/Codex，14 是 active/1x。每条序列仅一次，不能给首次 Last 差异指定动画、AX 或其它原因，也不能以这些条件宣称整图颜色/材质等同。PNG 与逐 stage 数值均保留，未修 raw。

旧 f9 基线的 startup gate 是 15 秒总 deadline 加单次 CLI 8 秒上限，等待非空 CLI window 与 samePID onscreen alpha≥0.99 的 CGWindow；不能改称对每个 cold call 都完整容忍 15 秒。

## Clean 源码状态与下一门槛

父任务已将上述语义去除全部 logger/nativeSnapshot 后应用为 `e48fff46`，仅修改 Style（119 行增加、10 行删除）。Style SHA256 为 `3912ecdbe102508771174df91f4d7baa153cca9925d89f6e68cdffc2e90cbd89`。主 Runtime 保留现有 9dd/HDR 修复，未被 f9 诊断版本覆盖。

准备时 `git apply --check`、回调/150–160 毫秒 timer 计数合同及独立只读审查通过。随后 [Gallery CI 40070407306](https://github.com/Torrekie/Bern/actions/runs/40070407306)（source e48fff46，build harness 25e18cbc）完整构建成功（job 120802424623）。父任务的单次本机 session 67853 也已 exit 0；它实际运行这一 clean 构建，而非借用 d146 结果。


### 精确 clean 应用的三场景后台验证

[完整原始归档](../Evidence/macOS13-film-clean-e48fff46/README.md)保留 219 个本机 run 文件、102 个已有 f9/14 参考文件，以及 source/build、合法唯一 bundle 签名、section/hash 与未改的 collector 3f434cf。运行采用 inactive13 / all / followup=none / trace unset，三个 fresh process，无 activation，normal 三项 false。Film 的 AX 每组都完整且有六张图片，PNG 各通过四次相同原始 buffer 比较。

| 场景 | clean 13 Glen 中心 / 宽度 | 上游 14 Glen 中心 / 宽度 | f9/14 Glen 中心 / 宽度 |
|---|---|---|---|
| immediate | 601.000 / 267.534781 | 566.000 / 268.799753 | 565.000 / 268.799753 |
| wait | 601.000 / 267.534781 | 601.000 / 267.534787 | 601.000 / 267.534787 |
| direct | 601.000 / 267.534781 | 601.000 / 267.534787 | 601.000 / 267.534787 |

wait/direct 的全部六张 AXImage frame 与两组 14参考相差小于 0.00001 点。immediate 的身份也为 Glen，但中心相差 35/36 点，不能宣布三组均在 1 点内。三组数据中的 immediate 都先从 900×652 实际 resize 到 920×668；wait/direct 启动时已恢复至 920×668。Inspector 退出、首次布局与窗口恢复仍混杂，不能指定单一原因。

精确原 GUI SHA256：`d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c`；CLI：`31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5`。后台运行副本采用唯一 bundleID 和 ad-hoc 签名，完整 GUI hash 因此不同，但各 section 与归一签名存储 payload 相同。原 exact app/CLI 留给父任务交付，此分析没有替换现有应用。

本机 13 为 inactive/2x，两组 14参考为 active/1x；同 AX 几何不等于相同 active 色彩/材质。本次未测后续 Last/resize，也没有内部 logger 或物理 gesture。仍需保留首次 Last、加宽窗口、重现/动态目标尺寸及物理手势的未等同边界；不得硬改初始 draft3，或把首次 anchor 变换套到所有后续目标。

## 同一原件的14复核与当前采集器对照

[run40071892408](../Evidence/macOS14-film-clean-e48fff46-40071892408/README.md)使用与13完全相同的e48原始GUI（d44f051c…）与CLI，在normal/active14上成功采集三组、完整6图与4次稳定buffer。wait/direct的全部frames与旧f9/14及上游14一致；immediate本次却是Glen677.0、宽256.153006，Madras407.0。不能把“运行成功”改写为三路径视觉保持。

该次使用新增startup gate的collector3f434/79da4a84，而旧14参考使用早期版本，因此补了一次[旧f9/current-harness控制run40072273422](../Evidence/macOS14-film-f9-current-harness-40072273422/README.md)。同一当前collector与harness25e下，旧f9的immediate仍为Glen565.0，三组全部6图的frame都与其旧observer记录逐值相同；wait/direct也与e48/current14一致。故startup gate变化单独不足以解释已观测677，但每个跨源码/构建/作业序列只有一次，尚不能给具体补丁或原生机制定因。

两次current14的后续resize记录均从900宽改为920×668，但启动ready采样时e48的CG外框为900×652、f9为900×600；两者wait的ready均920×616、direct均920×668。不能把不同阶段简化成完全相同的首开高度或恢复历史。首个完整AX只出现在Film选择后约.498/.873秒，均已见709/240，前段截断，不能补造当时viewport/insets。13clean的601相对旧14immediate差35/36pt，相对本次e48/14差−76pt，应保留各自证据身份。下一小步是同一14 VM内、独立bundle恢复历史、同observer的有界A/B/B/A配对，先验证差异可重复性；不设补偿常数，不提前改default/nearest或移植到11。
