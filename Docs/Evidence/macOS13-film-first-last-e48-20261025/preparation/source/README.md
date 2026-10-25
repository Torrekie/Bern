# e48 Film direct → first Last：本机 13 源码候选

此包仅准备源码，未编译、未执行、未采集；不包含 wrapper、prepare、identity locks 或新的产品实现。唯一目标是 fresh original e48 Gallery 的两次 Film 终态：直接进入 Film，再激活第一次 Last。不执行 First、Last-again、宽度变化、Inspector、wait、trace 或历史矩阵。

## 接口与输出

未来调用接口为 `FilmFirstLast APP CLI OUTPUT`，仅 macOS 13；`APP` 必须是外层已核验并私有隔离的 Gallery.app。原 e48 交付应由外层绑定完整 GUI/CLI 身份（GUI d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c；CLI 31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5），不能仅把本源码的 `BERN_SOURCE_SHA` 检查当成产物证明。

显式环境：`BERN_SOURCE_SHA=e48fff46b3a92a28465ad74295bd273a9d69af7d`、`BERN_FRAME_LOCAL_EVENTS=own-pid-active13`、`BERN_PICTURE_FOCUS_GUARD`、`BERN_PICTURE_WATCHDOG_FRONT`；禁止 Row ledger 和 scroll trace 环境。外层必须预建隔离 OUTPUT、捕获原前台的强 kernel receipt，并及时写入 OUTPUT/ownership.json，绑定 collector PID、唯一子 PID、私有 CFID、规范 executable path 和 kernel start。Guard 仍使用已验证的 `dev.bern.frame13.*` 私有 Gallery 约束，拒绝原 `dev.bern.gallery`。本包没有实现这些外层前置，不能独立宣称安全就绪。

保留原 direct 前置动作：英文、Light、窗口 920×668、解析 `.pages`、Patterns raw-stable、select Film、Film raw-stable/AX，然后解析唯一 enabled `.to_last` 并 activate、Last raw-stable/AX。共有 `setup-patterns.png`、`direct-film.png`、`direct-last.png` 三张 PNG，但只有 initial/last 两个 Film 终态。`report.json` 保存完整命令 stdout/stderr 引用、startup、activation、heartbeat、两终态、前台及强 cleanup 收据。没有把初始中心、Last 目标位置或宽度结果写成成功条件。

## 复用与有意差异

`source-proof.json` 按输入 SHA 和实际字节检查绑定以下来源：

- 原 6c4d Film collector：`target/window/image/stable/attribute/axSample` 完整连续函数块、now/frontState/handle 原字节。stable 仍是原 raw-buffer 四次连续相等、8 秒上限；完整复制的 inactive 分支被固定 active 常量隔离。CLI 保留原唯一 enabled suffix 解析与每命令 8 秒 cap，仅替换 environment 名、75 秒 uptime deadline 名、startup 时允许非前台的 pause 参数；另逐字复用 Frame CLI 的 own-Process defer，在新接入的 healthy/foreground 错误抛出时结束该 CLI，避免遗漏子进程。原可选 observe 接口未调用。
- 本机 614269 Frame collector：requestActivation/healthy/pause 与 own-window heartbeat 函数原字节；只删未使用的 mainWindow 函数。采用该来源的 18 秒 registry + own CG window startup、startup 后一次 activation、随后原 0.5 秒 heartbeat timer和总 75 秒健康门槛。没有新 timer，没有物理键鼠事件；heartbeat 的 own-PID mouseMoved 不证明真实物理输入。
- 本机 614269 最终 defer：仅删两条无 Row 的 ledger-log 检查，其余原字节。保持原前台强 receipt 绑定、ownership.json 握手、独立 Guard、先 restore 后 stop、7 秒 Guard 等待、确认子进程结束后 IPC 删除及失败锁存。FocusGuard.swift 完整原 ab78 字节。旧 Film 的 stop-before-restore 函数和 defer 均未复制。

新增 terminal 检查只读取原 AX 样本：每次 stable PNG 后单次 2 秒 AX walk，要求不 truncated、六个 AXImage 名字各一次、完整 finite 且正宽高 frame。保留原 AX 屏幕坐标和 capture bounds origin，二者不原子、不移动/缩放坐标；没有新增布局测量或内部滚动状态读取。检查 page 仍为 Film。缺图或失败样本原样留在 `incomplete_terminal_ax`，不补造数据。

与 14 collector 的 startup、active heartbeat、总 deadline、report schema 和采样时序不同：不再执行 select 的 first-second AX observe loop，不再解析本次不用的 `.show_details`。保留两 Film 终态，不执行旧 followup 余下四步。因而不得声称“同 collector”，也不能仅由同 e48 产品二进制推断相同观测。实际 14 参考 40165343690 由 root/独立 reviewer 另行绑定；本包不解释其位置结果或改写旧证据。

## 未决与停止边界

只运行了离线文本/字节断言，没有 Swift 编译或运行验证。下一步先由 root 审源码和外层契约，再决定唯一编译/真实运行。外层 watchdog、双向路径隔离、exact ownership 创建、私有 prefs 清理尚未接线。此前 defaults delete 的 5 秒 timeout 原报告保持 false；此包未放宽 cap，也未声称缺失域的只读 preflight 能证明 delete 健康。任何 core 修改需重新绑定 proof/hash；不在本包扩新矩阵、旧 observer gate、产品补丁或远程工作流。
