# Closed-only Frame row collector boundary (read-only proposal)

使用确切代码基底：
`outputs/Bern/Docs/Evidence/macOS13-frame-volume/paired-f9-aot/gallery-frame-reference.swift`
44721B / `77e4bb6849ea226cb4bcc4bacac7b08197e8f5a18f4aa991752d81cea44c4db8`。
其baseline.swift与当前repo collector逐字相同（41324B / `910501ef…0b486`）。
这里只复用collector实现；f9产品、原图、行宽和已通过结果都不能当e48 control。
Root新写私有FrameClosed.swift；本审查不创建collector/probe或改repo。

## 必改的最小段落

1. 保留原7argv：`APP CLI OUTPUT EXPECTED_OS LABEL SOURCE_SHA`，EXPECTED_OS13/14。
   用同一冻结collector执行original e48 control与同SDK observer；各host的A/B不能换collector。
   最好连AOT binary也锁同一份。保留私有短/tmp IPC、en/en_US、Light、normal三flagsfalse、
   920×668 outer、同一window.move，以及原catalog派生命令，不强制sidebar/divider宽度。
2. 以f9代码:391的`capture("frame-closed-light",ids:[mainID],canvas:outer,open:false)`为末次
   截图。删除:392–408的open AXPress、popup等待、open composite、isolated popup及dismiss。
   在closed capture成功后仅作root要求的capture时间收据/`frameStage("closed-end",open:false)`，
   然后success+save；唯一PNG仍为frame-closed-light.png，captures应恰好1，无open/dismiss stage。
   不必为减少死代码而改AX/helper数学或capture函数；unused open分支可以留着不执行。
3. root显式trace-arm若放在既有Frame选择之前，须在A/B保持同一collector路线与顺序，
   不能因observer多等待稳定、第二次选择Frame或补一次capture；arm不修改产品状态。
   report应明确closed-only/synthetic-own-PID-input范围，不再宣称AXPress/popover验收。

## 必须原样保留的前缀与门槛

- f9:23–25、318–319：本机13只显式`BERN_FRAME_LOCAL_EVENTS=own-pid-active13`；14 CI走真实
  GITHUB_ACTIONS/CI。不得在本机伪造CI。:329–343在统一18s内同时等session、main registry、
  唯一可见own-PID/layer0 CGWindow；:344之后才请求activate，继续记录activation请求。
- :99起own-active-PID mouseMoved heartbeat，native→CG→native windowNumber一致、onscreen、
  alpha≥.99，丢front/window即停；这是synthetic输入，不是物理鼠标验收。
- 原Frame挂载与异步player discovery8s保留；绑定player_id=`main/clipTarget`、owner、source-bound、
  sourceURL、sourceVersion，error/request failure检查和bundled tides SHA全部保留。
- 必须真实Ready→play/pause/seek→Paused(position0)，不能通过直接改report假造Paused。
  保留完整>3.2s awake循环、volume始终closed、同clip与volume身份及native geometry；
  heartbeat字段本身不证明idle已被唤醒，原awake gate才提供结果证据。
- capture原8s、raw CGWindowID slots/owner exact round-trip、same bounds、alpha、非空、ICC保持。
  stable4指至少5个buffer中的4次连续相等比较，不能改为4个buffer或新增motion/PNG fallback。
  保存原WindowServer PNG，Finalize及ICC回读成功后才有capture成功，不插新的像素算法。
- 原75s cap、每CLI8s、原始partial/error、所有CLI/媒体/窗口/heartbeat/stage收据均保留。

## 来源、原图与退出边界

Root先核original e48 build40070407306的source、GUI/CLI、SDK26.2/min13及资源实际收据，
再同collector跑14 original→observer。必须先满足root的原PNG不变gate再解读row ledger；
若sidebar/focus/编码/ICC或其他区域有差异，保留并停止，不裁ROI、平移或松阈值掩盖。
通过14后，才把同一observer binary用于13；e48原control也须用同一collector新采，
不能用旧f9的105/107、240/238等数值代替e48结果。

旧f9 defer:308–314仍是stop后按PID恢复，未具备本轮kernel身份guard及先恢复后停止顺序。
本机root应复用已有private bundle/path/PID/kernel-start的FocusGuard/外层看护，且在仍own-front
时先恢复原live身份再精确stop，保持用户已切换front的选择；不把旧defer说成已有强身份清理。
这属本机执行边界，不在本提案中另写通用watchdog。CI disposable环境与本机清理收据分开。

## 已知教训及e48 source事实

旧f9本机解释器因CryptoKit JIT符号失败在顶层前退出；AOT随后一次成功，不能把解释器失败
当产品失败，也不能靠重跑产品补证。旧SDK准备断言与collector实际SDK不同的问题要读实际
LC_BUILD_VERSION解决。session运输出现早于UI/player就绪、AX identifier哈希去重、NSNumber
伪装raw window slots、仅发事件而不核idle结果，均不可回退到旧未验证实现。
旧14/13参考还有真实sidebar灰/蓝及Frame Caption/Size像素残差，不能凭几何近似称原图相等。

本轮真实e48 Generated已独立核：81110B / f72cb1c6…ef1653；Frame1248–1353，slice9021B /
9e67b689…6d4a67。真实Frame row是BernRow(spacing12)，Caption split、Size menu、Volume，
以及条件帮助文本；!idle时出现，外层padding40，Frame强制dark。源码不提供实际行分配宽度。
当前ledger首版目录尚未出现；后续仅审其measurement次数/不变量，不在这里预造observer。
