# 真实 Hero SDR 转换：13 原生检查通过，14 参考未采齐

[CI40129608288](https://github.com/Torrekie/Bern/actions/runs/40129608288) 的 build 成功、measure14 失败。源码提交 `dcf1fdb3ef1a3f689898d08af4e3065b0646b481`，harness `ac426048bcea23eafa8aefe75c4620590e140dc5`。Xcode26.3/Swift6.2.4/SDK26.2 一次构建 arm64/min13，compile.log 为空；同一原签名 binary `999b31d0bff0fe3079c3fc2abb5a816769361d0d603286c73e8b21c3f6aa64c8`（654256B）在本机13.7.8运行 default 和 baked-pair，并在远程14.8.9运行 default。没有本机编译、重签、SDK/模拟器安装或第二次 CI 尝试。

本轮只验证一个私有 Standard named-PQ 同 key 条件替换。原 Hero timer、tick、弹簧、两条 NSImage.draw、Scene、NSApplication.run/default-mode sampler、arm-next-sample和所有期限保留。每个实际 snapshot 独立记录 ordinal/anchor/rect，以弱 NSImage 身份对应实际 Flight.from/to；default 无 CI，候选一个 context、两次独立 exact-extent RGBA8/sRGB 转换，不按 key 或可能复用的 CG 地址去重。没有新 UI 控件或产品改动。[源准备](source-preparation/README.md)、[独立源码审查](code-review/README.md)、[CI准备](ci-preparation/README.md)保留具体边界。

## 本机13

default 的原 native/execution gate、新 SDR gate、旧13对应端点控制均 exit0，之后才生成 `default13-ready.json` 并启动候选。候选同样全部 exit0。四个对应端点比较（old13→default 两个、default→candidate 两个）的原 RGB 和 ICC intent0 归一 sRGB 均逐像素相同；不要求 source 与 destination 彼此 exact。原图、测量 ROI、ICC、收据与校验输出保留。

两次运行均为原实际 single flight，frame/progress改变，3PNG、端点五次稳定、normal三项false、前台9292→9292、activation0、缓存不变且无MTK。finish后 flight/timer/临时view归零，destination唯一attached；本例源weak为nil。两实际快照、候选两转换/一个context均对应真实 Flight 端点，cleanup一次走原像素、未新增转换。helper refs清除不等于全局dealloc。

|13模式|触发→Flight.started|触发→首次live观察|源转换|目标转换|窗口持续|
|---|---:|---:|---:|---:|---:|
|default|27.438ms|47.968ms|未请求|未请求|1.314903s|
|baked-pair|58.058ms|69.424ms|47.474ms|2.598ms|1.178645s|

这是各一个新进程的观测；第一次转换含 context 创建，不证明全局冷缓存。两轮 ImageRenderer/准备耗时也不同（源22.856/4.533ms），不能把模式间差值归为纯 CI 成本，或用总窗口时间推导候选更快。首次live观察不是首次显示帧。完整原始uptime与分段值见 `timing-summary.json` 和各 report。Departure.time 在源快照返回后才记录、有效期检查在目标快照之前，两转换之和与0.3s不可直接比较。

Root目检完整原始 before、两个mid与候选settled：两mid均有可见非白内容位移，候选最终目标非空，未见分离的额外源/目标副本。白色格与背景部分不可区分，不能据此认证完整像素覆盖、所有重绘或亚像素裁剪。两mid实际进度不同（capture约.338/.371），不进行配准或跨模式/跨OS整图色差比较；见 `visual-observation.json`。这不是完整动画等效验收。

## 远程14明确未完成

这次14确实运行了同一 binary，default记录两个原始快照和一条真实flight，context/conversion均0。触发→started18.706ms，started→首次live观察215.326ms；first live sample进度0，下一live sample已为.845710569，未进入原(.2,.8) arm区间。197个样本后触发原collection deadline，wrapper exit1，仅有before PNG，arm/capture/settled均缺失。不是编译失败、runner公告停用或无法启动14；原因的更深归属尚未确定。

原期限、采样区间及错误均保留；CI的set-e在wrapper失败后停止，后续全量gate没有执行。`runtime14/report.json`、原收据、before PNG、`measure-job.log`及最终API状态保留。独立离线复核的真实结果见 `native-review/`，不能把本机13通过或14两snapshot元数据齐全扩充为新14参考通过。未重跑 CI 或放宽门槛。

## 结论与下一步

本轮取得两实际快照的本机可运行性、生命周期及同步成本证据。上一轮静态SDR方案仍是均值改善而若干通道/ramp退化；这次没有新的颜色等效结论。当前产品 Runtime→Style→Probe 尚未传递 display intent，private Standard Scene也不替代产品正确门控。候选仍不进入产品；High/HLG、其它几何/alpha/方向、retarget/reversal、物理HDR与完整动画均未验收。

下一步保留这次14缺样失败，先按[最小观察计划](next-observer-plan/README.md)界定默认路径首次tick/观察之间的空档；原snapshot与before PNG按调用顺序在空档外，现有数据仍未区分挂载、事件分派、sampler查询与弱匹配耗时。只考虑少量内存标量时间标记，保持原采集门槛；有新证据支持具体改变时再安排新的远程采集，不扩矩阵或盲重试。产品采用仍需颜色和明确intent路由两个独立门槛。macOS13整阶段及其它Film/chrome/Picture/Frame/输入等未通过项保留；goal active，不进入11/Swift5.3/ObjC/iOS。

独立复核已实际读取binary的前后字节并重验全部原断言：两次13的原native/additive为0/0，14为1/1，总状态`two13_native_pass_14_partial`。原binary/tar在此后按`artifact-cleanup.json`清理，共912310逻辑字节；未创建本机编译缓存。工作副本与内部重复文件的后续清理见`cleanup.json`，以最终现存清单`SHA256SUMS.final`为准。保留的原包历史清单可包含已按收据删除的文件，不能当作仍存binary的证明；逻辑字节不是APFS实际释放量。
