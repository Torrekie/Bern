# macOS13 原生逻辑 UI：现有证据审计

新口径：以目标平台正常逻辑、功能可达和可辨识状态验收，允许细微系统版本外观差异。此表只读既有原件，不是新运行或整阶段PASS。当前交付Gallery=e48、Showcase=9dd；旧f9/独立fixture按范围保留，不能自动升级为当前整应用通过。

| 项目 | 状态 | 已知与边界 | 证据 | 最小后续功能检查（未执行） |
|---|---|---|---|---|
|Gallery基本路径|可用，局部|e48原件13.7.8：Patterns→Film initial→首次Last、另一次Frame均成功；不代表Gallery每页。|E1/E2|只补Inspector开关一次，确认关闭后主内容可用。|
|固定窗口布局|已覆盖区域可用|920×668：Frame视频(251,167,629,354)在窗内；9dd卡片x161…900/HDR底472。不能扩为窄窗或任意文字长度不裁切。|E2/E4|当前交付单次缩窄，确认主要操作可达/滚动可用；不对齐14点位。|
|页面/错误恢复|可用（Showcase9dd）|Text/Buttons/Inputs/Layout切换、搜索draft提交、Library错误v1→Retry v2→空结果v3→恢复5项v4，14个check全真；预期invalid_search不是产品故障。|E3|无需再验证像素；真实键盘搜索另列输入缺口。|
|Frame媒体/状态|可用，CLI范围|e48已Ready、play/pause/seek响应、Paused0、>3.2s保持awake、Caption=true/Volume closed；未独立证明实际播放进度持续前进。|E2|界面Play一次，确认进度/画面变化，再Pause确认停止。|
|Film首末内容|可用，非完整手势|e48 active fresh initial放大Glen，首次Last后放大Windowpane；两态六图完整且buffer稳定。14.5pt/浮点不同不再失败，私有Binding未直接读回。|E1/E11|尚未覆盖的First仅做一次到达/可操作检查；不追求落点坐标复刻。|
|原生按钮/弹出层|已有历史功能证据|f9独立系统NSButton：performClick/快捷键单触发、disabled不触发、外部打开与关闭；不是当前e48整页所有按钮/物理输入证明。|E5|当前e48仅补一次Volume打开→改变值→关闭，确认状态一致。|
|动画有可见运动|限定夹具已证|真实Hero/coordinator同binary13的mid/settled已有root目检：非白内容位移、目标非空；不是完整Gallery动画或每种retarget证明。|E6|实际Gallery只看一次Inspector转换有运动且能结束/继续操作，不比较逐帧轨迹。|
|stock13配色/chrome|允许系统差异|语义NSColor/SwiftUI/native split真实13均能绘制；暖色材质、标题/侧栏位置、Caption灰白与14不同不单列失败。fixture不证明全应用可读性。|E7/E2|人工确认文字/图标可辨、选中状态可区分；不强制RGB、bezel或像素相同。|
|实际输入/未覆盖能力|仍缺验证|搜索focus/drag的失败是采集交付门槛：独立NSSlider也未收到mouseDown；不能记成Bern不能拖动。输入法、键盘遍历、drag松手单提交、High/HLG/物理HDR及其余变体未完整验收。|E8/E9/E10|优先一次真实输入能改变当前控件状态；若focus未证，停止并记未知，不重开参数矩阵。|

审过的当前路径没有足够证据确认新的产品功能阻断。旧Film初始Madras问题已有clean e48的Glen实证；历史immediate/wide位置差、卡高4pt、Frame按钮2pt/文字3pt、系统材质色差，不再独立构成失败。缺失输入/完整动画/其它变体的证据仍是真缺口，不能用“像素不再要求”直接补成PASS。HDR需区分能显示/切换与物理亮度能力；不要求13重现14色值。

明确失败须归位：Row记录容量/最终hash、search焦点、早期activation/IPC、偏好清理timeout均保留其原false；它们是诊断/采集/安全结果，并非对应UI产品功能失败。已停observer像素路线不继续。`work/film-observer13-analysis-preparation`（manifest d501cd0b…d3b908）原冻结不改、不执行，标记为被本次原生逻辑口径取代；也不借其strict失败判产品不合格。

证据索引（路径相对workspace；以下SHA256为本轮读取快照，原件未改）：

- E1 `outputs/Bern/Docs/Evidence/macOS13-film-first-last-e48-20261025/raw/report.json` — `e47168e331b8c231755d18add58aaaf56541e59090f29e75d60e6d4486fc5c98`
- E2 `outputs/Bern/Docs/Evidence/macOS13-frame-control-e48-20261025/runtime/report.json` — `60d71641769e1e7630b8d235512f700db416a8a0646cf559cc6bb75f6f5ac480`
- E3 `outputs/Bern/Docs/Evidence/macOS13-picture-scene-observed-9dd/A2-control-and-B-log-off/capture-A2/result.json` — `e3202fb59f4fa872fadcd73e6340ffe7477b400fc490533a08e1ffcbc94d6eef`
- E4 `outputs/Bern/Docs/Evidence/macOS13-picture-scene-observed-9dd/geometry-review/README.md` — `3491ab971a2663094df5daeff1cf139c24cec06f3bc3df9cfe0972a567f3cb54`
- E5 `outputs/Bern/Docs/Evidence/macOS13-popover/component/report.json` — `7f6b0411d1aed8d405b8fa87c71a5ab124910f698b0a0fd29962a8b16b1ecccb`
- E6 `outputs/Bern/Docs/Evidence/macOS14-hero-timing-40132685948/README.md` — `976abd152f20b79e38cc899e24b82785098102d9686890135c103d4c5d866f8f`
- E7 `outputs/Bern/Docs/Evidence/macOS13-window-background/sdk26-content-stable/report.json` — `8ddd69fd30bcc867a2eb6ea2026ba8c7b58812048c1063626895389d9dcec702`
- E8 `outputs/Bern/Docs/Evidence/macOS13-search-native-focus/README.md` — `861497cd1a3364bfa8a8dabba9fcbc0a03df0609e89b89bc4f0ef1434a8ce735`
- E9 `outputs/Bern/Docs/Evidence/macOS13-candidate/input-delivery/report.json` — `78b9153681b5085e8441269c573f4df90c55fced2a1b3ec19e2fd74b3309decf`
- E10 `outputs/Bern/Docs/Implementation/macOS13-Acceptance.md` — `c916cb906ba1838f7fbab7efaaa797f74538e2fc34e3e9255311334f6a7368ae`
- E11 `outputs/Bern/Docs/Implementation/macOS13-Film-Initial-Position.md` — `e059a1e08847be84b749bc9d0cc7722da962c39965ad4b158f70c26de52cffe3`

本轮无原生/编译/CI/网络/Git/图片处理；只读JSON与既有文字、生成此表。不新增实现、运行方案或矩阵；后续检查是建议，未执行。
