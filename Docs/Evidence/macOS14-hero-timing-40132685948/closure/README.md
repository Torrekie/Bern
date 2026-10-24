# Timing checkpoint closed within its acquisition scope

本轮CI40132685948及同binary13运行均取得完整native/execution/strict-timing通过、各3PNG。原端点控制JSON确认：13对应旧13的before/settled、14对应旧14的before/settled，raw RGB与ICC intent0 sRGB均exact且嵌入ICC相同。这里复核原报告/控制结果与代码，未重新计算像素或运行native fixture。独立native实际binary pre/post hash及清理收据另存；不以已清理binary为当前仍存在的证据。

| 实际monotonic区间 | 13 | 14 |
|---|---:|---:|
| Flight.started→原timer注册后的checkpoint |0.128542ms|0.435083ms|
| started→first callback entry |5.678667ms|17.926125ms|
| started→first scalars end |6.126333ms|18.592083ms|
| started→first tick的原now |9.159292ms|159.426667ms|
| first scalars end→first tick now |3.032958ms|140.834583ms|

**本次不确定性已缩小。** 当前14的Flight构造、原visibility事务、overlay挂载与timer注册同属started→post-add的0.435ms包络；first callback的WindowInfo/遍历/匹配/scalars前缀合计约0.666ms，不能解释该轮后续140.835ms。主要未分段区间现在位于first scalars end之后、first tick原now之前，而不是这次原生注册前段或首次标量查询前段。

**仍未知。** 没有callback exit、draw入口/完成或系统分派时间，所以callback剩余尾部、自动drawing及事件分派仍未区分；first applied复用tick开始时的now/p，不是赋值完成或呈现时间。现代码first live progress0的尾部只做原弱flight/几何/arm分支并返回，没有mid截图；这不测量其耗时，也不排除随后自动绘制。不同VM/新进程/新增observer不能把本轮包络回推成旧14那215.326ms的唯一解释，更不能据一次13/14差值认定OS/clock根因或响应性达标。

**这些未知不阻挡按原合同使用已齐的本轮14参考。** 14实际在sample8/p=.674501439 arm、下一sample9/p=.733330075完成中图，之后原native finish、timer/临时view退场和settled五稳定门槛通过；没有改band、期限、clock或重试来取得它。该参考可用于此固定Standard named条件替换的原图/异步状态对照，不能扩大为同步帧、颜色/全动画、响应性或物理HDR等效通过。完整原图可见性仍以root审阅记录为界，metadata不替代目检。

**关闭本轮追时序。** 没有已定位的产品clock错误或不满足本次采集合同的剩余失败；改120Hz Timer、common mode、弹簧或时间尺度会改变行为，现有证据不支持。也不应只为把未归因间隔变小继续盲CI。保留旧失败与当前未知，回到实际尚未通过的UI：SDR recipe仍有色块/灰阶退化，生产dynamicRange→hero意图尚未传递，Picture Scene布局尚未隔离；当前reference不替代这些颜色/布局验收。本说明不制定新测量矩阵。

已读原输入：work/hero-timing-20261025/runtime13|14/report.json及endpoint-controls.json、冻结hero-timing-probe Driver/Hero、独立native review。无编译、UI、CI、source或旧档案改动。
