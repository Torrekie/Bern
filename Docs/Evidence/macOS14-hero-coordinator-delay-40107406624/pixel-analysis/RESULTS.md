# Delayed observer：一次限定离线像素结果

按root资料就绪通知，`analyze.py`只执行一次，exit0；所有10个分析组件均performed。输入14项：新6PNG/2report、旧4个相关endpoint PNG/2report，SHA全部核验。原图未复制或修改，没有派生图、注册、重采样、拟合、UI或CI操作。ICC→sRGB采用原嵌入profile、perceptual intent0、flags0。

| 同一OS的比较 | Raw MAE /max | sRGB MAE /max | exact |
|---|---:|---:|---|
| 13新before source→settled destination | 0.3447728587962963 /2 | 0.29410590277777776 /5 | false |
| 14新before source→settled destination | 0.27116898148148144 /2 | 0.27116898148148144 /2 | false |
| 13旧→新before source | 0 /0 | 0 /0 | true |
| 13旧→新settled destination | 0 /0 | 0 /0 | true |
| 14旧→新before source | 0 /0 | 0 /0 | true |
| 14旧→新settled destination | 0 /0 | 0 /0 | true |

这些endpoint均同尺寸、alpha255，13为640×360、14为320×180；各自对应ICC完全相同。四项旧→新控制支持采集调整没有改变本次endpoint ROI，但不是整个窗口、跨OS颜色或完整动画验收。

固定root四边12pt inset（按真实before source root→截图转换建立像素origin/scale）内alpha均255。新mid的sRGB非白像素bounds，单位root points：

- 13：`[109.5,85,429.5,265]`；实际inset像素box `[24,80,2024,912]`、scale2。
- 14：`[16,24,336,204]`；实际inset像素box `[12,40,1012,456]`、scale1。

这是限定区域内的内容bounds，白色图块可能被排除；没有把native flight rect当像素裁切，没有精确flight边界配准或跨OS异步mid相等门槛。14 bounds仍对应source区域的数值事实不能独自定位原因；root另行目检原图。

| OS | armed index /p /uptime | capture index /p /uptime | CG before→after uptime |
|---|---|---|---|
| 13 | 9 /0.27834425591200473 /257385.46387658335 | 10 /0.36831750591813517 /257385.48305595835 | 257385.48321641667→257385.48735570835 |
| 14 | 7 /0.6091942872454421 /73.33612804166667 | 8 /0.7145723223778195 /73.36353854166667 | 73.36384866666667→73.37065883333334 |

两者captured index均armed+1，identity相同；完整armed/capture state、CG前后state和native ROI保存在summary。两次CG bracket各自native progress未变，不等于WindowServer输出与该状态同步。该调整没有建立同步，也不支持CF-pump/CA/系统版本的唯一归因。

`summary.json`保留完整精度及全部输入hash；`INPUT-SHA256SUMS`引用workspace中的原件，`execution.json`记录脚本/旧参考脚本hash和本次工具版本。顶层SHA256SUMS只覆盖本分析目录（除自身）。结果已冻结；无重复执行图像分析。
