# Film observer：下一执行门槛（只读冻结）

40175193229 的失败永久保留；40176620054 的完整产品构建与交付来源已通过。后者仍没有 native 运行、诊断 JSON 或观察影响验收。本审查只核源码顺序与下一入口缺口，不重复 tar/Mach-O 审查，不表示可以直接执行。

冻结 core b9 第8–9行仅在 macOS 13 且环境变量存在时启用。c4 采集器第394–410行是：初始 PNG→AX→inspect；查找 Last 目标的 inspect→activate→Last 稳定 PNG→终端 AX→checkedFilmControls 的 inspect→window list。该末次 inspect 才是预期导出点；不得在 Last 动作与原 PNG/AX 之间插入产品 inspect。PNG 与 AX 不同时，不能补造 PNG 的绝对时间。

core 第156行起导出的是“首个请求之后的首次 inspect”，并不天然指 Last 6；且写盘前即消耗唯一机会。后续必须核同一 owned PID、唯一请求、typed wanted/position/target 与 Last 6 关联，完整五槽、身份/finite/cap/diagnostic_complete，以及 terminal 时间与原 AX、inspect 命令的顺序。提前导出、缺文件或错误均停止诊断，不重试或借其它请求。原 capture/cleanup 成功与诊断有效是两个真值，不能互相覆写。

最小入口缺口是新锁定的私有 App/强 kernel 适配，而非产品补丁。旧 run-film13.py 第20–21行锁 GUI d44 与 CLI31a，不能换入新 App 后继续沿用其 locks。新 App 应绑定成功 manifest、全部成员与 GUI e2fb；CLI 仍明确绑定原31a，不能将此次重建但未交付的 CLI 称为原 CLI。需要 fresh 私有身份、原前台 kernel/owned child 握手、restore-before-stop、IPC/prefs 清理与原5秒 cap；本轮不实现这些适配。退役 tar/旧 alias 均不可执行；需要时重查既有 artifact12592821357 的可用性与下载来源。

下一次获准的 native 单元仍限 initial/首次 Last，先按预声明的同端点控制核观察影响，才可解释诊断；不在这里新增 off/on 矩阵、位置容差或成功判据。若端点控制或诊断关联失败即停。14 仅用40165343690 的首次 Last 参考，不混 repeat Last，也不期待13-only core在14输出。当前−14.5pt差仍未解释，不改默认值、anchor或offset。

本轮未实现、执行、编译、调用 Git/CI/native/UI；不重开已停止路线。输入哈希见 review.json，均为本次读取时快照。
