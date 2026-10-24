# PRIVATE：AppKit observer Driver source review

**PASS — bounded source review only.** Root确认作者最终Driver SHA256=`571354d2cee32df6bac30fab4ce338bb6dce85b07f2adeffa08df24022530270`，与本次审读的469行源码相同。对照基线为延迟observer Driver，SHA256=`b9d6b699af43128b0658ecb9e81df8ef346e6f9b3be253c07cca80968bcd8ec6`。未发现新增明显Swift类型、引用寿命或控制流阻断问题。当前尚无本review提供的compile或native run-return证据；root将在单次CI中验证实际返回。

- **搬运一致性：** lines1–173的scene/helpers完整字节相同；新`sampleOnce`与旧loop body仅去缩进、`continue→return`和两处shot后terminal guard后逐字相同；最终lifecycle/cache/native gates去缩进后逐字相同。原arm/schema、band、相邻actual sample/同flight、三PNG、endpoint各五稳定buffer及单次model action保留。无新增Hero时钟、进度、visibility、frame、layout、flush或display控制。
- **引用寿命（174–224、265–379、457–458）：** run栈的强`state`跨`app.run()`并由defer使用；window/host/model受其拥有，manager/source/flight仍弱。anchors/source/destination是单次sample局部，action前`anchors.removeAll()`仍保留。load仅一次Task，弱self在await后才解包，并拒绝terminal后的完成；不会迟到建窗。observer timer的target持有关系在finish中invalidate并置nil，正常异常返回也有cleanup兜底。watchdog handler以`[output = self.output]`捕获URL值，内部没有跨线程读取instance property或持有state。
- **采样与界限（213–264）：** 唯一`app.run()`；delegate launch建一个default-mode selector Timer，名义60Hz。每callback同步执行至多一个sample，无逐tick Task、补采循环或手动RunLoop。depth门控遇到重入即terminal失败。preload完成时间需在3秒内，callback未完成时也检查3秒限期；window开始后独立global watchdog仍7.9秒，collection为7.2秒callback入口门槛，sample512、readiness1.5秒不变。`makeWindow`后本callback返回，下一callback才开始原采样body。`continue→return`均只结束当前step；settled完成后同callback执行final gates再finish。
- **停止与普通partial（395–466）：** finish幂等地设置terminal/result，停并清sampler，调用stop，再固定投递一次own application-defined wake。wake仅terminal后，无补充动画/sample/截图。`app.run()`之后才调用`noteLoopReturn`并检查launch/entry/return/stop/wake各一次、无reentry/terminal后callback；随后正常return触发原cleanup/report defer。若run意外返回，contract失败且cleanup仍执行。callback错误统一finish；已有report拒绝逻辑和PNG拒绝覆盖保留；arm/attempt在shot前保存，capture完成仍在PNG finalize/read/hash成功之后。report写失败和最终normal/front失败仍影响进程退出码。

源码库存：手动`RunLoop.main.run`0；`app.run`1；Task1（只load）；selector Timer1；global watchdog1；stop1；postEvent1；model action1；CG acquisition1；shot/save各2调用点。新`execution_model`的实际24字段列在`review.json`。

必须保留的解释边界：

- `sampler_callback_count`包含preload callback，不等于actual samples数量。旧policy串`first_band_arm_then_next_original_loop_sample`为保留schema；新execution model下它指下一observer callback的相邻actual sample。
- `sampler_invalidated_before_stop`是源码路径flag，不是`Timer.isValid`查询；wake字段记录创建/投递，不证明事件被处理。源码可证明记录顺序和正常返回可达性，实际run返回须由新receipt/报告核验。
- 7.2秒是入口deadline，仍不是capture严格完成时限；主线程阻塞时该入口门槛不能自行执行。window global watchdog和外层wrapper承担独立边界。外层wrapper未在本次两Driver审查中重审。
- hard watchdog仍写minimal report并`_exit`，绕过defer；完整arm/attempt只适用于正常defer且report写成功的路径。此继承限制未修。
- 更换执行模型本身有observer effect。该review不证明手动RunLoop为旧现象原因，也不提供CF/WindowServer归因、像素/颜色/同步/动画或13等效验收。

仅执行源码读取、差异/字节比较和小型私有记录。未写新Driver、改产品、编译/typecheck、运行测试/UI/CI或扩展API研究。记录时间2026-10-24T16:12:47Z。README、review.json、SHA256SUMS在manifest生成后设为只读，目录冻结；无source或图片副本。
