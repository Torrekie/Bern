# PRIVATE：下一轮 AppKit 主事件循环提案

这是下轮检查点，不是本轮验收。当前 prepared Driver SHA256=`b9d6b699af43128b0658ecb9e81df8ef346e6f9b3be253c07cca80968bcd8ec6` 在 `finishLaunching()` 后自行调用两处 `RunLoop.main.run(until:)`，没有 `NSApplication.run()`。这项源码事实不是已经证实的原因。

`work/native-pq-hero-coordinator-delay-ci-40107406624` 的13/14报告均 native success。13的arm/capture为sample9/10、progress约.278/.368；14为7/8、约.609/.715。root提供的目检结果为13中间图已位移、14仍在source；本提案没有重新目检图片。一原自然outer-loop机会尚不足建立原生状态与WindowServer图像的同步关系，也不能据此归因CF/WindowServer、解释颜色或宣称动画修复。

建议下一次只把 observer 的执行模型改为正常 `NSApplication.run()` 生命周期。这更接近标准AppKit对NSHostingView应用的事件分派，值得作为隔离实验；它仍不构成提交/显示同步保证。比继续增加手动RunLoop次数、自写`nextEvent`泵或改用display-link更合适的最小入口，是在唯一AppKit启动完成入口建立夹具状态，再让`app.run()`持续分派事件。避免手动`finishLaunching`与run入口重复发起启动。

1. 原`run()`保留拥有资源、最终状态和`defer`的同步栈帧。只把原局部状态和每轮body搬到一个MainActor状态容器：`preloading → before → transition → settled → terminal`。在启动完成后发起原异步load；用其现有完成值推进preloading，保留3秒限期，去掉preload的手动泵循环。load完成后按原顺序取得ledger、建同一window/scene、启动原窗口计时和独立全局hard watchdog。
2. 用一个主线程、default run-loop mode、名义1/60秒的observer timer正常调度原一轮采样body。每次callback最多一个sample，不补偿漏tick、不重入、不为每次采样再包一层异步MainActor任务。它只读取/记录/截图，并执行原before五稳定帧后的那一次`model.atDestination=true`；不调用Hero的tick/finish、进度、可见性或动画调度。新timer绝不成为Hero时钟，也不使用common-mode或display-link引入额外同步策略。
3. 保持当前arm策略：首个严格.2<p<.8的live sample只arm；下一次observer callback的相邻sample才可capture，仍须同一pinned flight、timer和actual-overlay parent，capture p可超过.8。丢失/换ID/缺门槛/超过sample或入口deadline即terminal incomplete，不重arm、不重试。保留全部原capture bracket、PNG/ICC、三图顺序、before/settled各五稳定buffer、单一replacement及native retirement门槛。
4. 正常成功/错误先保存terminal result、禁止后续采样并invalidate observer timer，再在MainActor请求`app.stop(nil)`。`app.run()`返回后才沿原栈执行defer、关闭窗口、写report并决定退出码；不用`terminate`或`exit`替代正常展开。实现时必须确认timer回调中的stop能让run返回；如需唤醒等待，只在terminal后投递一次本进程application-defined停止哨兵事件，不再采样，也不dispatch动画或额外commit机会。callback内所有throw统一转terminal error；保存失败不得标记capture完成或success。
5. 全部原界限不变：preload3s、初始readiness1.5s、collection7.2s、window watchdog7.9s、外层wrapper15s、512samples、3PNG，以及normal/cache/front/nonkey/inactive/fixed-window/no-MTK门槛。7.2秒对应新的callback入口检查，不能宣称截获操作严格在该时刻前完成。独立hard watchdog继续在主线程卡住时终止；原minimal report加`_exit`边界保留，完整arm/attempt证据仅保证在正常defer且report写入成功时保留。

为减少对照混杂，冻结同一asset/原产品与Hero字节、scene/key/位置/action、motion默认值、采样名义频率、arm/schema、capture/save实现、启动外观与所有门槛；两端使用同一新构建原始二进制，保存其源/包hash。只增加执行模型及observer调度元数据和必要terminal状态，不同时修产品、watchdog、色彩、窗口、采样band或截图时序。新的timer和正常AppKit循环本身就是待检验变量，不能称为零observer-effect；若native gate仍过而图像仍滞后，应如实记录，不能叠加flush/layout/display、dispatch barrier、进度控制、再等一轮或重试来追求通过。

本轮仅源码/两份小report只读检查并写此提案；未写新Driver，未编译、运行测试、启动UI或提交CI。未拓展API研究或通用重构。记录时间：2026-10-24T15:38:01Z。
