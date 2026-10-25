# macOS13 native logic/API：只读审查

2026-10-25。按新验收：Bern 生成符合目标平台逻辑、可读可用的 UI 即可；细微系统配色、间距和动画轨迹不要求跨版本像素复现。只读当前 accepted 四模板、PopoverButton 生成条件与既有 API inventory；未实现、编译、运行、调用 Git/CI/native，未重开 observer/像素路线。

**结论：本范围未发现能由源码证实、必须修复的 macOS13 独有功能删除。** 多数 unavailable API 已有真实替代；“替代存在”也不等于所有原生交互已验证。以下明确区分能力边界、覆盖缺口和非缺陷，不把旧视觉 gate 继承为阻断。

路径缩写根为 `outputs/Bern/crates/bern-backend-swiftui/templates/`：C=BernCompatibility.swift，S=BernStyle.swift，R=BernRuntime.swift，A=BernAppKit.swift。行号绑定下方文件哈希，不套用旧 inventory 的行号。

## 有源依据的功能边界与最小验证

| 分类 | 当前源码事实 | 最小必要验证 / 判定 |
|---|---|---|
| 已声明共有能力限制，非已证13回归 | S1016–1053：15前 Search 不连接 searchFocused；shortcut/外部 focus 只置 focused=true。R1639–1643 调 closure 后回成功，没有 firstResponder 确认。13与14同分支；本轮未独立核固定上游的低版本承诺。 | 不自动修补或阻断13。CLI ACK不能充当焦点成功。先在现有可见 Search 原生输入普通文本，核模型 query 与结果/错误链；若要承诺13程序化焦点，另明确能力合同再验证。不得把 CLI edit 当原生输入证据。 |
| 交互覆盖缺口，未证明 bug | S1282–1290、5287–5299：styled sidebar 的13局部键盘 monitor 限本窗口/聚焦且拒修饰键，只排除 marked-text editor。A1279–1337：scrubber monitor 拒全部 NSTextView，并可拆卸。两者都是真处理，过滤不同本身不足判缺陷。 | 原 Planner styled sidebar / Showcase 媒体各一次：聚焦后箭头改变正确值，焦点进文本/输入法及另一窗后不抢键；disabled 不修改值。优先核状态/事件接收者，不核焦点环像素。 |
| 可用布局覆盖缺口 | S5221–5240：13 Inspector 用系统 HSplitView，按 binding 插入面板，约束宽度；没有自行保存拖后宽度。A693–733：sidebar ideal 只在无旧恢复记录的条件下预置一次后释放，尊重用户布局。 | 原 Gallery show/hide、拖 divider、窄宽时内容仍可读可达；控件和主内容不能被不可恢复挤掉。无需要求面板/侧栏宽度等于14。源码不能证明 Inspector 用户宽度在所有重建中保留，也不能据条件插入就认定丢状态。 |
| 动画/手势覆盖缺口 | S2648–2743：13 nudge 用真实 AnimatableModifier 终值及 request/mount guard 回弹，卸载清理；S2747–2794：13 MagnificationGesture 与14 MagnifyGesture 都执行 start×倍率/clamp、结束 commit。 | 现有原例确认手势修改绑定、一次结束只 commit 一次、取消/离页不留下卡住的比例，Reduce Motion 可完成同一状态转换。接受短峰值/速度曲线差异；无须重开 Film落点、短帧采样或 observer。 |
| 明确平台能力差异，非普通色差结论 | R2228–2273、2287–2295、2399–2411：13区分潜在/当前EDR，系统 SDR 转换和无Metal NSImageView 后备存在；High明确可能受当前headroom裁切，不复制14 tone mapper。 | 不再以色差/全ROI exact阻断。仅若实际内容不可读、空白、方向/fit错误才归具体功能缺陷。High/HLG/alpha等不能由旧opaque-PQ小样本宣称全覆盖；当前不为它重开已停实验。 |

## 已有实质替代，不能误判 no-op

- C7、28–33、76–83：Mac 使用 ObservableObject/对象环境及 Canvas 显式订阅；C89–137 保留 previous 与最新 action box，13 old/new/initial 有真实回调。没有发现确定状态遗漏；重入/重挂载全时序不由这次源码审查认证。
- R2021–2055：13 空白/错误页仍有标题、说明、actions 与可访问容器；不是删掉 ContentUnavailableView 后留下空页。长文窄宽只需可读/动作可达，不要求14排版。
- A140–152、648–665：13 settings registration 的 content 分支由 host 的 showSettingsWindow:/showPreferencesWindow: 接替；激活使用13 API，设置功能没有随 modifier 一起消失。
- S2146–2184、2400、2464–2492、2500–2606：旧坐标空间、item 几何注册、ScrollViewReader、用户接管清 target 均存在。scrollTargetLayout 的 self 有其它注册接替。S4944–4947、5112–5149 明确13在惯性后校正、14在目标阶段选点；这是实现/轨迹差别，不能由末尾几pt差直接认定功能 bug。
- S3397–3415 与 A1348–1459、生成器 `src/swift/controls.rs:289–307`：普通未约束图标 PopoverButton 已走系统圆形 NSButton；enabled、shortcut、单次 action 和可访问标识都有接线。旧 inventory 将 volume 当首个未实现桥接对象的段落已过时。其它形状族 S5207–5268 仍由真实 Button 驱动，只替换边框画法。
- A739–940：13为真正 CoreVideo vblank→调用者 runloop 的时钟，并有停止/解绑；不是固定计时器模拟。实际消费者见 A1132–1144，自定义 media kernel 覆盖不足；普通视频成功不能认证全部时钟语义，本轮无源证据表明 UI 故障。

## 移出阻断与建议

系统选中色/材质、默认控件尺寸、extraLarge用large+padding（S5325–5333）、13.0–13.2 popover背景（S5305–5314）、同平台Form的默认间距（S4860–4865）均不得仅因外观不同判移植失败。toolbar title hiding（S941–950）、TextRenderer（S1802–1840）等15+能力在13/14共同降级，也不能当13新增回归。

open_at 有真实首次有效尺寸定位及最多8次布局重试（S5027–5040、5321–5323）；异步内容、后续resize的完整defaultScrollAnchor合同未证明，但无现有原例触发证据，不据此扩新fixture。全应用实际键鼠/焦点、可用布局与状态转换仍需少量功能覆盖，源码审查不宣布全阶段完成。

下一优先项仅为现有页面的真实输入/焦点→模型→结果链；随后按确实未覆盖的键盘或 Inspector 可达性选一项。只在出现可复现功能失败时定点修补。旧14.5pt、颜色/ROI、Rowledger与observer诊断全部保持历史结论，不重标PASS也不重启。

## 输入字节快照

既有 inventory 是旧5226454审计并附f9进展；本报告以当前源码覆核上述边界，不把其旧“待像素等同”要求搬入新合同。

- `outputs/Bern/crates/bern-backend-swiftui/templates/BernCompatibility.swift` SHA256 `7f46dcf0d23d280465ea5139c21a760fed047c3a3b383a203f9b642fc1a8807d`
- `outputs/Bern/crates/bern-backend-swiftui/templates/BernStyle.swift` SHA256 `3912ecdbe102508771174df91f4d7baa153cca9925d89f6e68cdffc2e90cbd89`
- `outputs/Bern/crates/bern-backend-swiftui/templates/BernRuntime.swift` SHA256 `255bacb40db71fa17a8bd9ecaefc1b72c187864295221727c28653a09839e16e`
- `outputs/Bern/crates/bern-backend-swiftui/templates/BernAppKit.swift` SHA256 `5921238de799177589a7ee325afcc9380bdc8a896aeb862cd4129f5fd5a04598`
- `outputs/Bern/Docs/Implementation/macOS13-Remaining-API-Audit.md` SHA256 `0c4de0cceb725609fd2e8d0ad7a2a44c965a70b1768c08bb1b2757d2f6701abe`
- `outputs/Bern/crates/bern-backend-swiftui/src/swift/controls.rs` SHA256 `c50078af414f19fda0f4013802238677ae2ffc1a69062350f3f7fcfdf78cf2bd`
