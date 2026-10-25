# Frame Row ledger：独立源码审查（冻结）

结论：最终源无剩余阻断性发现。此结论仅限源码和 guards，不是编译、真实运行、像素或布局验收。

审查绑定 `patch.py` **81532266…b833b6ed**、`RowLedger.swift` **680fbf70…827bdbf**；最终 `FrameClosed.swift` **dcbd5405…b2f2cd3d**、`PixelGate.swift` **10ca1789…0a41a253**。完整路径、字节数、SHA 和行号在 review.json。

原测量/数学保留

- 只给真实 e48 Gallery Frame Row 加一个 diagnosticID，精确锁定原 Generated 81,110B 和 Style 210,785B；不以旧 f9 产品代替 e48。
- 非 spacer 原三次 sizeThatFits（0/nil/infinity）、一次 dimensions、一次 place 的相对顺序与原分支保留；spacer 仍不执行对应查询。现有宽度分配、gap、top、extent、place 参数及 x 推进未重算或替换。
- raw 在原查询后复制；normalized 从原 Item 复制；dimensions 从原对象复制；placedX 在原 place 后、x 推进前复制。完整记录一一对应同一次 place→arrange→widths 调用和真实 Subviews ordinal，不假定 builder 数量等于 Subviews 数量。
- 原 place 全循环及最终 x 推进完成后才检查 arm、构造 JSON 和写盘。不存在额外布局查询、Observable 状态或 UI 修改；仍有分配、时钟及 I/O 成本，须实际无 observer 像素对照后解释。
- offered≠extent、row_size.width≠bounds.width 均可能合法。原 row length 是 sum(extents)+sum(gaps)；finalX 为逐项累加，独立复算应允许浮点顺序误差。这些是 Layout 请求参数，不是 native frame/bezel/ink。

最终 guards

- Helper 最多64完整 placements、65,536B；溢出/不完整标 truncated；I/O 错误写 stderr，旧成功 prefix 可能留存。
- Collector 锁 exact e48、CI14/显式 own-active13、原 source-bound Ready→Paused0、awake、own-PID window round-trip、ICC 和 stable4；只采 closed。arm 绑定新目录/PID/stage/token，last complete placement 必须不晚于实际 stable image sample begin。
- 已修正 cleanup 后仍 exit0、live child 仍成功、live child 时删 IPC 三项。退出依据 defer 后状态；仍有子进程时失败并保留 IPC。只在 own front 时请求恢复原 live 应用，然后才停止自有子进程。
- 已修正旧有效 ledger prefix 掩盖 I/O 失败：完成前和 cleanup 后均检查 bounded application.log 的 BERN_FRAME_ROW_LEDGER_IO_ERROR；命中/读失败均失败。
- PixelGate 已将实际 PNG SHA 与 capture 绑定并记录两实际 SHA；decoded ICC SHA 也绑定 capture。相同 OS/canvas/descriptor/ICC、scale1或2，control off/observer on，逐 active bytes 比较，无重采样/色彩转换。
- 通过条件是预声明固定半开 Frame ROI `[211,52,920,668]` points；整窗差异单列，不能称 whole-window exact。

边界与验证

有限 prefix 的 end_state 仍是 not_observed，不证明 settled 或 app lifetime。placement-before-sample 不是呈现同步 fence；之后若发生 placement 会保守拒绝。固定 ROI 也不证明覆盖每一 native 边界。旧 f9 仅提供共同 collector 源基础。

本 reviewer 只读源码/哈希并做 Python AST parse，没有执行 patch/helper、编译、UI、CI 或 fixture。Root 的 typechecks.json 将最终两 Swift 和 Row 抽取源绑定到 SDK14.2/min13/Swift5、三项 exit0；这是 root 的定向 typecheck 收据，不是本 reviewer 重跑或完整产品构建证据。
