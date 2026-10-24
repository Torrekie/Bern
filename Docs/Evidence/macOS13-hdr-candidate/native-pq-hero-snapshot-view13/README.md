# 同一snapshot的NSImageView未解决Hero主色差

本机macOS13.7.8的单变量静态对照已完成，未修改产品，也未触发新14 CI。仅named Flight改用系统NSImageView显示**同一个实际ImageRenderer snapshot NSImage**；custom仍走原Flight.draw，body/oracle、实际overlay、几何及原采样循环保留。[源码准备](source-preparation/README.md)、[独立源码审查](code-review/README.md)与[运行/构建说明](fixture/README.md)记录全部边界。没有绕过snapshot、换回原CGImage、重缓存、自定义tonemap、图层setter或新增自定义显示控件。

SDK14.2/Swift5.9.2以arm64/min13、语言模式5构建一次，binary SHA256 `514079a0f294f1bc47e761e37b281f7d18271c9ecae6ab31e1b1f416f8679f1b`，原ad-hoc严格签名通过。继承原静态fixture的SDK14 gain-map/unused-clock适配，未把此例扩称真实coordinator或完整应用。control先运行并通过[冻结13控制](fixture/frozen13-vs-control.json)全12ROI原RGB/ICC归一exact，才运行candidate一次，无隐式重试。

[独立native核验](native-analysis/README.md)通过21输入/组装、同binary、normal/cache/前台保持、five-stable/noMTK/managerFlight0/timernil及existing-overlay坐标往返0pt。两窗口1.787775/1.607795秒；candidate四阶段保持同child/flight/image、320×180、stock scale/frame/animation配置和原parent/window。orderOut后child.image=nil、detach与helper weak refs清理通过，不证明所有NSImage dealloc。原entry/report覆盖、try?写与hardwatchdog绕defer限制由fresh-output wrapper和实际完整输出分别核验，没有扩修旧harness。

root已目检原control/candidate p0 PNG，candidate图像正确呈现在named Hero区域。[两组ROI比较](fixture/control-vs-image-view.json)只有flight-named两phase改变：raw fullRGB MAE0.103565/255、max1；ICC→sRGB perceptual intent0 MAE0.086730/255、max1。其余10ROI在raw/sRGB都exact，嵌入ICC相同。该结论只比较六个图像ROI，未把窗口其它文字/chrome宣称逐像素相同。

[完整像素分析](pixel-analysis/README.md)保留所有十patch、灰阶和signed H−B，不只看cool812或单个平均。重新分析冻结14原图，归档统计逐值匹配。D=Hero−body，30通道的平均|D13−D14|及最大值如下（单位均为8位sRGB等级）：

| phase | 平均：control→candidate | 通道改善/恶化/不变 | 最大：control→candidate |
| --- | --- | --- | --- |
| p0 | 5.210863→5.272487 | 4/19/7 | 112.616329→112.724330 |
| p1 | 5.224399→5.216157 | 13/10/7 | 113.048334→113.156336 |

**主要色差未解决，停止这个限定显示组件方向，候选不合入产品。** max1变化的内部原因未指定；13/14显示ICC、倍率与余量不同，跨宿主差也不能唯一归因系统版本。旧“原CGImage→NSImageView匹配body”与本例实际snapshot输入不同，14 Hero本身也不等于14 body。本轮不扩展custom、alpha、方向/fit/aspect/corner、跨图crossfade、真实动画/中断、High/HLG/物理HDR或完整应用验收。

下一步只读检查已有raw float导出能否建立平坦内区的行/通道语义，见[下一边界计划](next-boundary-plan/README.md)；尚未执行新的语义像素算法。其它macOS13未通过项保留，goal active，不进入macOS11/Swift5.3/Objective-C/iOS。四项原交付binary hash和两app严格签名保持。自有binary/cache57,493,320B已删除，重复work副本逐字核验后清理，见`cleanup.json`；数字为逻辑文件量，非APFS实际回收或磁盘净变化。原PNG/ICC、日志、源码、数值分析均保留，当前现存清单为`SHA256SUMS.final`。复跑应将fixture源码复制到新的scratch，归档只读。
