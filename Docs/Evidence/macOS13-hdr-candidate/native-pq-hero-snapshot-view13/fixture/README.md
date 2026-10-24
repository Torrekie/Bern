# 同一 Hero snapshot 的系统 NSImageView 对照

这是本机13的限定静态诊断，未修改产品。实际 ImageRenderer 产生的同一个 NSImage 直接交给系统 NSImageView，仅替换 named Flight 的显示；没有换回原 CGImage、再次缓存/渲染或创建自定义显示控件。默认 Flight、custom Flight、body/oracle、overlay parent、几何、原显示/采样循环均保留。NSImageView 使用 scaleAxesIndependently、frameStyle none、animates false；父 Flight 的 fixture-only false flag 只在候选 named 分支跳过原 draw，避免双重绘制。

新私有缓存下 SDK14.2/Swift5.9.2、语言模式5、arm64/min13、O/j2 构建成功，严格 ad-hoc 签名通过。二进制 SHA256 `514079a0f294f1bc47e761e37b281f7d18271c9ecae6ab31e1b1f416f8679f1b`，两mode运行前后保持。使用旧静态诊断已经明示的 unreachable gain-map 与 unused-clock 适配，未调用实际 Hero coordinator，不能当作完整应用或真实 clock 的构建/运行验收。只有既有 ProductImage switch 两条编译 warning，原 build.log 保留。

control 先跑一次并通过全12ROI原RGB/ICC intent0→sRGB exact 的冻结13-overlay控制，才启动 image-view 一次。wrapper均新建自有目录，无隐式重试、激活或host defaults修改。control/candidate窗口分别1.787775/1.607795秒；wrapper耗时2.136631/1.820201秒。源码原入口 deadline7.2s、独立watchdog7.9s与wrapper15s未延长。

原PNG已由root目检，候选 named Hero 内容呈现，颜色主差仍明显。control→candidate仅两个阶段的flight-named ROI改变：ICC归一 fullRGB MAE0.086730324/255、max1/255，均非exact；其余10个ROI原RGB/ICC归一exact。该微小变化不能指定为某个内部取整步骤的结果，也不构成主色差修复。

原native门槛、same actual NSImage identity/320×180 geometry、stock child/parent/window与cleanup的独立检查见归档的native-analysis；完整色块/灰阶与冻结14 signed H−B残差比较见pixel-analysis。无需为本轮已明确的显示差异再触发14 CI或真实flight。原14 Hero本来也不等于body，不能只以匹配body为目标。

source-preparation保存冻结的两patch/manifest，source-provenance记录来源与实际拼接输入，build-fingerprint保存真实工具链/SDK/minimum/签名。此fixture只是 opaque/up/same-aspect/corner0、from===to、p0/p1的named atlas。SHA precondition只锁夹具输入，不是产品白名单或通用alpha证明；custom仍为控制，不从named结果推广到它。helper弱引用原child/flight/image，orderOut后置child.image=nil并移除child，仅证明helper/child清理，不声称所有NSImage已dealloc。

继承的legacy report.scope提及原Flight.draw：image-view/named实际以native_display记录的skip为准。普通catch在成功写report时留partial/error；原binary本身不拒绝旧report/PNG，最终write是try?，硬watchdog会_exit并可无report；本轮fresh-output wrapper、实际exit0/完整report和PNG指纹分别核验，不能把这些边界泛化成所有失败均保存完整报告。helper无provider/display/layer新增读取或setter，不等于整个原截图harness不读provider，也不宣称零observer效应。

原可执行文件和owned module cache完成后清理；保留原PNG/ICC、日志、源码、报告、独立分析和cleanup收据。四项既有交付binary hash和两app严格签名保持。完整颜色/动画、其它方向/alpha/fit/corner/跨图crossfade、High/HLG/物理HDR和完整macOS13阶段仍未通过；goal active，不进入macOS11/Swift5.3/Objective-C/iOS。
