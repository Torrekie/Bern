# External Showcase toolbar acquisition — prepared only

这是一份待 root 审查的外部单文件 Swift 采集器，没有编译、Swift parse/typecheck、启动 UI 或触发 CI，也未改产品。调用合同为 `showcase-toolbar-probe APP CLI OUTPUT`；OUTPUT 必须尚不存在。A/B 必须由 root 使用**同一个 observer 二进制**分别执行，外层准备独立签名身份、验证代码 section/来源、清理各自 app/偏好/saved-state 和设置 `BERN_SOURCE_SHA` / `BERN_TOOLBAR_VARIANT`；observer 自身不改 defaults/TCC。

## 复用和局部调整

直接沿 `.github/scripts/gallery-film-probe.swift` 的 Process/CLI 原始日志、独立 IPC、唯一 session、15秒绝对 startup gate、指定 CGWindowID 的 raw-buffer 稳定和有界 AX breadth-first 实现改写。输入文件的读取时 HEAD/hash 见 provenance。没有共享测试框架、新 native logger、注入、宿主 window、NSToolbar/NSView 访问或额外产品动作。

限定为 macOS13，要求现有 AX trust、Screen Capture preflight，以及 reduce motion/transparency/increase contrast 全 false。仅观测用户现有 normal profile，不请求授权、不修改偏好。只接受与外层 wrapper 约定的 `dev.bern.toolbar13.` owned 前缀，A/B 分别为 `dev.bern.toolbar13.a.<uuid>` / `dev.bern.toolbar13.b.<uuid>`，并拒绝已经运行的相同身份；fresh bundle/domain 的准备和审计仍是外层职责，observer 不凭文件不存在宣称完全无历史。

单次启动 Showcase（英文参数、app-local `BERN_APPEARANCE=light`），删去 snapshot/trace/motion/render/dev-signals/injection 环境 override；不改变全局外观。**Light 仅为环境请求；应用自身 theme 可能覆盖它，未断言实际有效 Light。本轮只用于同一设备 A/B 几何比较，不据此声称配色或像素等效。**记录立即原前台对象、源标识、actual startup-ready 每次 CLI window list 和全部自有 CG bounds。未达到 transport session + registered main + own visible alpha>=.99 window 前不选择页面/请求前台。此后激活自己的 app、设置现有 language binding、真实 CLI resize 920×668，再依次程序选择 Buttons→Text→Controls→Buttons；不做物理键鼠/IME、collapse、toolbar action、拖拽或 Inspector。

每阶段保存 select/inspect CLI 原始 stdout/stderr及实际开始/返回时间，own WindowServer raw ID/owner/bounds/active front；连续4次完全相等比较要求至少5张 raw buffers，并同时比较几何、像素 metadata、color-space name。保存实际 CGWindowID PNG，不用 snapshot-dir 代替。首轮目标框未达到920×668会失败，不补偏移或强制原生栏宽。

AX 以2秒预算、512节点上限遍历全部发现的 AXChildren，保留父子 node indices 及 role/subrole/title/description/value/help/identifier/enabled/focused/selected/frame；对 unsupported/noValue 明确记 error code。保留 focused UIElement/focused/main window 的外部属性，截断或真实查询错误会把阶段记为失败并保留 partial。**完整指全部发现的树节点和列出的属性，不是所有可用 AX 属性；AX frame 不是 glyph ink，也不是 native toolbar item frame；AX focus 不是真实 NSResponder firstResponder。**

## 有界与退出

工作截止为启动后115秒，保留5秒停止自有 Process 和恢复立即原前台；每CLI≤8秒、startup≤15秒（从记录的 `app_launch_start_uptime`、即调用 Process.run 之前计时，不在 run 返回后重新起算）、每截图稳定≤8秒、每末态AX≤2秒。CLI 超时 SIGKILL 自己启动的 CLI；app 只终止本次创建的 Process，必要时 SIGKILL；自己的 IPC 目录才删除。停止前若仍是自己的 app 在前台，就恢复立即原前台并验证；若用户已转到其它前台，不覆盖用户选择，记录未请求的原因。已退出的原前台无法恢复会明确失败。

上述截止由 run-loop / AX messaging timeout 协作执行。**同步 WindowServer/OS 调用或本地I/O无法由 Swift 循环强行中断**，同旧 observer 一样不能单凭源码保证墙钟120秒。root 外层必须提供120秒进程界限和精确自有路径的 app/CLI/observer 兜底清理与焦点恢复；被外层杀死时以已落盘 partial 为准，不猜最终状态。若外层不具备这些条件，应先停止，而不能当作严格120秒验收执行。

任何 acquisition/cleanup/deadline 失败返回1，保留 `result.json`、已写日志和PNG，不重试后续阶段；输出目录尚不能安全创建时不覆盖已有文件。`success=true` 仅表示这次采集合同完成，**不是 A/B UI 等效、色彩相等、物理输入或产品修复通过**。

## 静态审查结果

准备时检查了所有 runtime mutations：只有 own app/CLI Process、own-app activate/原前台恢复、现有语言与sidebar/resize binding、fresh IPC 和 output 文件。没有 UserDefaults/defaults/AX permission prompt/TCC、NSView/NSToolbar、截图替代或native logger创建。源码来自适配而非未改的 Film observer，因此首次编译可能发现类型/链接问题；当前没有编译成功或运行成功证据。root 审核后才可执行。
