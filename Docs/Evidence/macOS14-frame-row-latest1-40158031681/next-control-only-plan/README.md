# 下一单步：原 e48、未插桩的本机13 closed Frame 基线（仅方案）

判断：独立有价值。它只回答“同一原交付在13的真实 closed Frame长什么样、原collector能否完成”，不回答 ledger数学、observer无扰动或布局已修复。此任务需新 control-only 身份与结果类型，不能当作既有observer门槛已过；root之后决定是否实施。

已核本次14 control：40158031681/a/report.json success=true、row_ledger_enabled=false，normal三项false、Light/captiontrue/closed/Paused0；stable4、6samples，stop0/front343→343。actual PNG SHA ef6951d5…eccfb6b 与报告相符，920×668/1×；全部具体绑定见 inputs-and-decision.json。未读取或解释末尾ledger。

原交付可直接复用：outputs/macOS13/Gallery.app 和 bin/gallery。此次只读重算 GUI d44f051c…49126c、CLI31a75c0a…f379f5，均等于成功14 control；无需再下载原包或observer构建包，不重编产品。源锁 e48fff46…9af7d/原交付40070407306，不从observer源包剥补丁来制造“原件”。

最小代码边界（下一轮独立准备，此轮不实现）

- **Prepare只做一个原control私有copy。** 现prepare-copies.py强制observer App/build且循环两端，不能直接用于plaincontrol。新小入口只收原App/CLI/来源收据与fresh work；不接observer参数、不下载无用包、不造占位输入。保留原strict签名、文件清单、每个Mach-O section及签名storage归一后的非签名字节核对；只允许私有CFBundleIdentifier/对应签名改变，CLI逐字不变，原App/CLI只读。
- **新control-only wrapper，不改旧wrapper。** 现run-local13.py:57–67要求成功14 pair；它必须继续失败，不能删断言来运行。新入口独立绑定本次成功14 control report及实际PNG/ICC/context/SHA，只表达unobserved_baseline_capture；无variant/observer分支、无pairPASS字段。准备新的单group锁和UUID私有CFID，fresh prefs/state，不沿用observer实例。
- **采集Swift不另起路线。** 以3613df…最新collector的原采集prefix/suffix为基准，可复用已审764998…仅final-defer安全适配和ab78c7…Guard的源边界；须新control-only包及编译binary/source/signature收据，不能直接运行旧observer草稿来绕过前置。能复用现存已绑定helper binary则不重编；没有就留给下一轮root决定，只编helper不编产品。
- wrapper必须清除并禁止BERN_FRAME_ROW_LEDGER_OUTPUT_DIR，不创建ledger目录；最终row_ledger_enabled必须false，任何ledger/instrumented App证据都失败。不改已有observer schema、时间、finalSHA、原图或IO门槛。旧40155522534及40158031681 observer继续failed，PixelGate未跑不改为PASS。

下一轮必须守住的 gates

源/二进制：原来源与GUI/CLI SHA一致，实际min13/SDK和strict签名核实；private copy只有CFID/签名变化，原所有section/归一字节及原件复核一致。CFID隔离不等于整个GUI文件字节相同。

UI：仅一次原closed Frame路径，arm64/mac13真实guard、en/normal三false/Light/920×668、真实Ready→Paused0/source身份、原own-PID awake heartbeat与unique own window、原CG/ICC/stable4、closed-end保留；不给用户偏好赋值、无privacy fallback、无divider/固定height/route调整。保留原PNG和实际scale/ICC/坐标；跨OS不强求raw exact，也不按颜色或结果自适应ROI。原collector不提供Caption/Size的Layout子view宽度，不能以截图推它。

清理：保留双向output/watchdog/input隔离、outer95秒等待/内部75秒deadline、PID/bundle/path/kernel-start及collector-parent所有权、原前台收据关联、restore-before-stop与cursor不动；只有exact child cleanup后才清精确IPC/private prefs。缺收据/身份不明/未退出或前台恢复失败即保留并失败，不宣称桌面已释放。

限制/停止：这是含CLI与原awake heartbeat的正常profile事实基线，不是物理用户输入或无人干预idle证明。OS、scale/ICC、私有CFID和CI/本机及cleanup差异须明示；若既有路线不满足前置便停并保留原错误，不加观察器、采集矩阵或新CI。得到单基线后仍不能解除layout ledger门槛。
