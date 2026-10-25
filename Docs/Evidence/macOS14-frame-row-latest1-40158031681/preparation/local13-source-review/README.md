# Local13 latest1：独立源码审查（冻结）

结论：已读四核心无剩余阻断性源码发现。未执行 helper、编译、App 准备/签名、UI、CI 或清理；不是本机运行/桌面恢复验收。

- Collector **76499825…83afbd0**、Guard **ab78c7d3…e19345d**、prepare **4a0126eb…eda5af**、run **edcedde9…6631b78**；全 SHA/来源与行号在 review.json。
- 已独立确认只替换新基线 **3613df83…1d974** 的最终 defer `[38562,40863)`。prefix38,562B/suffix10,538B均 exact，逆换还原完整新基线；原 latest1 consumer/时间/IO/hash、media/awake/CG/stable4、suffix退出规则不变，未误用旧dcbd源。
- prepare 和 run 都双向隔离 fresh output/watchdog 与实际输入，不能用输出覆盖输入或把输出放入输入树。
- exact owned-child cleanup 未核准或缺精确 IPC 路径时失败，保留 prefs/IPC；不把无 receipt/改 path 当作已退出。null/未核前台拒绝 fallback kill；只清 private domain 和 collector 精确路径。
- 外层在 launch 前取得原前台强收据；collector defer 将 captured NSRunningApplication 的 PID/bundle/path 与之关联并记 SHA，再由原 Guard live-kernel 核实后恢复/停止。没有将 defer-time kernel 冒充 collector startup kernel。
- Guard 与旧 Gallery 适配逐字相同。A/B 必须用同一新本机 helper binary；actual14 的 reviewed gate/build/两 report/PNG 哈希是运行前置条件，旧失败 cohort 不可代替。

时间精度：外层等待 collector 的上限95秒，随后还有清理；内部 collector 原 deadline75秒留在 exact prefix。作者已在最终 README 明确此区别，六个其它文件未变。最终作者 manifest：397a6211…1d65e27。

身份/交接/原前台不匹配时可能保留自有 child/IPC 并失败，不能声称自动清理已完成。Root 仍负责实际14前置门槛、二进制/签名与本机 UI/前台恢复验收。
