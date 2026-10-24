# 真实hero的下一样本采集：端点控制相同，中图仍未同步

[CI40107406624](https://github.com/Torrekie/Bern/actions/runs/40107406624)构建与14采集成功，源码提交`151609a950f95403ecdeb9451e99693f5628ee5a`，harness `e3999727ec919508402ed1ecc40cc48dc7c7fc4f`。新SDK26.2/Swift6.2.4只构建一次arm64/min13，原签名binary `fca470c9174bd11d9fc6220fa61643b7ad2338a2bb4bc34e560b3de3cb5c6e23`在14/13各运行一次。包、18成员/source map、最低系统/SDK/架构与严格签名在13运行前核验；本机未编译、重签或创建模块缓存。原收据和最终CI状态保留。

独立source/workflow只改变observer：首个.2<p<.8真实live样本存scalar arm，不拍图；经过下一次原有outer-loop的RunLoop.run与采样，须同一flight/timer/实际overlay parent仍live，才拍唯一中图。capture index必须等于arm+1，失去live即incomplete，不寻下一band或重试。capture p允许超过.8，但本次两边都未实际覆盖该分支。原完整Hero、scene/key/图、clock/draw/finish、before/settled五stable、3PNG/512sample/normal/cache/front/noMTK/窗口界限均保留；没有产品颜色/层/动画修补。

| 宿主 | arm→capture index | arm→capture p | 样本间隔 | 窗口秒 |
| --- | --- | --- | --- | --- |
| 13 | 9→10 | .278344256→.368317506 | 19.179375ms | 1.434776 |
| 14 | 7→8 | .609194287→.714572322 | 27.410500ms | 1.951298 |

[原生离线复核](native-analysis/README.md)重用锁定workflow门槛，仅路径/OS适配，两份报告PASS。31输入hash、同binary、one flight identity、原timer/frame/progress变化、真实finish后flight/timer/临时view归零、source离开原层级通过。weak source仍未dealloc，不能称释放完成。normal三项false、cache不变、前台保持13:9292/14:333、own-window/nonkey/inactive/noMTK与端点五stable通过。CG调用区间4.139292/6.810167ms不是presentation timestamp。

[限定像素结果](pixel-analysis/RESULTS.md)保留14输入hash与原六张PNG/ICC：same-host旧→新before/source、settled/destination四项控制的原RGB和perceptual intent0归一sRGB全部exact。新before→settled的同尺寸opaque ROI仍为13 sRGB MAE0.294106/255、max5；14为0.271169、max2，均非exact。该结果支持本例端点内容保持，不通过跨宿主颜色或完整动画。

root目检原mid：13已有位移，14仍在source。固定root12pt几何inset且全opaque区域的非白内容bounds分别[109.5,85,429.5,265]与[16,24,336,204]，并非精确flight配准。实际capture sample逻辑root原点分别(139.754682,105.029851)与(256.096300,181.205911)，CG前后native bracket仍是该进度/位置。`trigger_state/progress`在新schema中明确指arm，不能误读成capture sample。再给一次原循环机会仍未建立画面/状态同步，中间帧、配色、运动过程及全应用一致性未验收；不归因CF、CA、WindowServer或系统版本。

源码审查见`code-review`，driver/CI草稿及实际source/构建元数据分别保存。继承界限保持：7.2s只在outer-loop入口检查；硬watchdog可以minimal report加_exit绕过defer，完整arm/attempt只在正常defer且写report成功时保留。本次实际窗口均未接近这些界限，没有修改watchdog来改善结果。

下一[正常AppKit事件循环提案](next-app-loop-plan/README.md)尚未实现/运行：用唯一NSApplication.run入口和只负责原采样状态机的MainActor observer timer，保持原Hero clock、scene、单次action、arm/schema、3PNG及所有门槛；terminal后stop并正常返回defer。它更接近实际应用的事件分派，但执行模型及调度本身是新变量，不是显示同步保证或已证实原因。不继续累加手动等待、强制flush/layout/display或修改进度来凑图。

原binary/tar与逐字归档work重复副本已清理，见`cleanup.json`；原包清单含已删文件，现存完整清单以`SHA256SUMS.final`为准。六原PNG/ICC、源码、报告和逻辑结果保留。其它Film/chrome/Picture/Frame/交互/HDR门槛未通过，goal保持active，11/Swift5.3/Objective-C/iOS仍延期。
