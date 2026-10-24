# 一次真实hero协调：原生生命周期通过，中间帧未验收

[CI40103369574](https://github.com/Torrekie/Bern/actions/runs/40103369574)的build/measure成功；本次复核两远程artifact均未expired，原状态见`ci-jobs.json`与`ci-artifacts.json`。源码提交`fe7f30d21494a290f363572c6556a138804fb1ba`，harness `2e43bfb86126c8a03d85e0af45a0451ed3c5ed17`。SDK26.2/Swift6.2.4构建一次arm64/min13，原签名binary `5739a0405bf78c04e71a46116c99fd48a7fa7b0b659bf8e97744ee3982ecea36`在13/14各运行一次。包、18成员/source map、架构/min13/SDK和严格签名均在13执行前验证，原收据保留；未重签或在14重编。

夹具复用实际BernImage、缓存、完整原Hero与原计时回调。一个非空key的source/destination在普通SwiftUI条件分支中使用不同.id与位置，单次状态变化触发真实dismantle/update；没有手调enter/leave/tick/finish、创建manual Flight或改visibility/frame/progress。仅弱引用原anchor与实际Flight、记录scalar，并检查实际root/overlay子树。产品源码没有加入新渲染器、layer请求或颜色修补。

| 宿主 | 窗口秒 | live样本 | 中图trigger p | trigger逻辑root原点 |
| --- | --- | --- | --- | --- |
| 13 | 1.546953 | 37 | 0.2872209362 | (112.506235,87.188606) |
| 14 | 2.044402 | 20 | 0.6920757961 | (248.537468,176.256675) |

[独立native复核](native-analysis/README.md)通过：normal三项false、cache不变、前台保持（13:9292、14:309）、非key/非active、自有窗口/PID、noMTK、单一真实flight identity、live timer及frame/progress变化、实际结束后flight/timer/临时view均归零。source已离开原层级，但weak source未dealloc，两边均false，不能宣称释放完成。before/settled各五stable，两端各保留三张原PNG。原生门槛通过不等于像素或整阶段通过。

[限定像素检查](pixel-analysis/README.md)及原图目检确认本例起点/终点内容可见。完全opaque、同宿主的source→destination ROI在ICC归一sRGB后，13 MAE0.294106/255、max5；14 MAE0.271169、max2，均不exact。不同缩放/ICC宿主没有做异步mid逐像素相等比较。

中图在13已位移，固定12pt root inset中的非白内容bounds为[80.5,66,400.5,246]；14仍在source位置，对应[16,24,336,204]。这只是内容bounds，非完整flight配准。相应native capture前后bracket仍保留上述逻辑进度/位置；这些时刻没有建立与WindowServer画面的同步。中图、运动过程及颜色等效因此未通过，不能唯一归因RunLoop、CA、WindowServer或系统差异。v1 whole-root bounds受圆角/透明窗口角污染，已明确不解释，原JSON不回写。

下一最小步骤为[一次自然迭代后的采样](next-sampling-plan/README.md)：首次band仅arm scalar，恰下一次原循环自然RunLoop/sample后才拍唯一mid；分开保留armed/captured index、state与uptime。失去同一live flight即incomplete、不重试、不强制flush/display/进度；captured p可真实超过.8。此改变尚未实现/运行，只给普通提交路径增加机会，不证明根因或同步已解决。before/settled及其它原门槛不放宽。

`local-static-preflight`仅是本机SDK14.2/Swift5.9.2、target14的typecheck；为旧SDK跳过13不可达gain-map代码，保留原Hero未guard的clock。没有本机min13构建/可执行文件，其通过不能替代本次新SDK同binary运行。执行前草稿见source/ci-preparation，实际行为以same-binary-13-14原收据为准。

原PNG/ICC、报告、源码/构建元数据保留；原binary/tar和已用完module cache已删除，work副本逐字校验后换成归档symlink，见`cleanup.json`。原包清单包含已删binary/tar，最终现存文件以`SHA256SUMS.final`为准。Film/chrome/Picture/Frame/交互/HDR和完整动画仍未通过；macOS13 goal保持active，不提前进入11/Swift5.3、Objective-C或iOS。
