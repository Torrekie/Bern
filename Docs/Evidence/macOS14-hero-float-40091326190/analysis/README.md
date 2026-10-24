# Same-binary13/14原始binary16全buffer离线结果

四份actual off/on报告均通过冻结分析器，全部保持`row_direction=unknown`、`semantic_patch_values_emitted=false`。13新SDK raw与旧SDK13两个raw的长度/SHA完全相同；14 named/custom两文件彼此逐字节相同。两host的snapshot ICC/格式相同，但whole-buffer均值及按分母比较的部分计数不同。结论止于实际renderer-return对象raw导出边界，不归因唯一OS、具体颜色patch或可见主差原因。

本目录是fresh工作包，未改旧13分析、runtime夹具、产品、旧归档或docs/index；无spawning、UI、编译或CI操作。没有复制原raw/PNG/binary。原始导出发生在已有teardown之后；本任务只读取保留文件。

## 输入来源与控制

CI40091326190保留package binary纯文件hash与root package verification、14 binary记录及四份actual run receipts一致：

`38d0bf9bd54ae60bd7699e3e02a149e591968a3f63cce3d3968af0b9e647a517`

package23项hash、tar SHA=`fcfdb7616bd1865b76d4524ea281d360d0c679fcfd73ff51d779a6922bc7603f`重新核对通过。strict signature/arm64/min13读root的既有检查记录，本任务没有重跑工具链。

actual OS13.7.8 (22H730)与14.8.9 (23J631)，四run success/exit0；normal首尾全false、front各自保持、cache深比较保持、activation0；samples和captures own PID/window identity一致、nonkey/inactive、无MTKView/coordinator flight/timer；各phase至少5个连续相同buffer记录。原report/PNG/raw/receipt哈希复核。

| Host/mode | 窗口秒数 | Front首尾 | Raw bytes | provider copies | current/potential headroom |
|---|---:|---:|---:|---:|---:|
| 13 off | 1.608554959 | 9292→9292 | 0 | 0 | 1/2 |
| 13 on | 1.563573956 | 9292→9292 | 3686400 | 2 | 1/2 |
| 14 off | 2.200559974 | 322→322 | 0 | 0 | 1/1 |
| 14 on | 1.851788044 | 322→322 | 921600 | 2 | 1/1 |

所有mode primary/cleanup调用数均2/2；off peak0/after-export0，on peak2/after-export0。四个root PNG控制：metadata14→new14off、14off→on、metadata13→newSDK13off、13off→on，各12个ROI raw/normalized exact。本任务核对其实际baseline/candidate report SHA、12个唯一rows与zero指标，没有重复执行ICC图像比较；不把该观察外推成普遍零observer效应。

## Raw和ICC

| Host/source | Size /row bytes | 字节数 | SHA256 |
|---|---|---:|---|
| 13 named | 640×360 /5120 | 1843200 | edc1c9380bbf86e35c9830359428b715953cccd0f5952b10ade269923a6a2469 |
| 13 custom | 640×360 /5120 | 1843200 | 314b9001c1c47eea9f39a23fd6c697d1bcb66cfcda83dbc01153149c2d36e67c |
| 14 named/custom（各自） | 320×180 /2560 | 460800 | 807393b1503ad04a08e2dc09cac516e9d2abfcd86c9db3b15ec2761230201962 |

13上述两个SHA与旧SDK13实际文件重新核对相同；这只证明本case旧/新SDK13的raw观测一致。14两源除SHA相同，还直接比较完整文件bytes相同；不推成所有named/custom输入等效。

四run primary descriptors的ICC base64均严格解码为3144bytes，SHA统一为`2b3aa1645779a9e634744faf9b01e9102b0c9b88fd6deced7934df86b949af7e`，space为kCGColorSpaceExtendedSRGB。on原格式均16bpc/64bpp float、bitmap4353、byteorder4096、premultiplied-last alpha1、pixel-format0，无row padding；这里没有应用ICC或transfer function。

13每源230400 pixels、14每源57600，实际像素量比4。以下4倍只用于aggregate count上下文，不生成、重采样、对齐或逐像素比较两host图像。

## 未标注语义的全buffer分布

全部存储RGBA sample均finite；NaN/+Inf/−Inf全0。每源alpha全部为精确1.0/0x3c00，均值/min/max均1。RGB min/max中，13 named与14两源相同：R −1.96875…3.064453125，G −1.0048828125…2.60546875，B −0.98388671875…2.58984375。13 custom仅R min为−1.9677734375，其余上述极值相同。

| Stored channel | 13 named mean | 13 custom mean | 14两源 mean | 14−13 named | 14−13 custom |
|---|---:|---:|---:|---:|---:|
| R | 1.567957814535 | 1.567728233337 | 1.568117078145 | 0.000159263611 | 0.000388844808 |
| G | 1.553895314535 | 1.553717104594 | 1.554054578145 | 0.000159263611 | 0.000337473551 |
| B | 1.283550262451 | 1.283549308777 | 1.283709526062 | 0.000159263611 | 0.000160217285 |

| Channel（每host两源计数相同） | 13 <0 | 14 <0 | 13 >1 | 14 >1 | 13 >1−4×14 >1 |
|---|---:|---:|---:|---:|---:|
| R | 30720 | 7680 | 174840 | 43680 | 120 |
| G | 30720 | 7680 | 190200 | 47520 | 120 |
| B | 46080 | 11520 | 159480 | 39840 | 120 |

负值counts逐项恰为4倍；>1 fractions的13−14差每RGB channel为120/230400≈0.000520833333。全精度、每源每channel count fractions、unique-bit计数和mean/min/max差值在`whole-comparison.json`、`summary.json`；每raw完整结构/bit摘要在对应`host*-on-unknown/analysis.json`。

这些统计对row reversal不敏感，但不能消除1×/2×取样、缩放边界或宿主环境上下文。没有按颜色选方向、没有semantic patch数值、跨host对应像素比较、位置配准、拟合或自动pass阈值；也没有clamp/unpremultiply/颜色转换/nits换算。

## 结论与完整性

同一分发binary下，在保留的实际renderer-return CGImage provider导出数据中已能观察到不完全相同的全局分布。因此“相同格式/ICC”不足以证明payload分布相同；这里确认的是snapshot raw边界的观测。方向、具体patch、导致可见不一致的路径、OS/显示headroom/取样的独立因果均未确定，不将这些小的聚合差值直接解释成可见主差。

`analyze_float.py`与既有冻结版本逐字相同，SHA=`b616c42b192c13b7fee3d903d90e9553f389c6ac4b6f7da8cc96996877fcca2a`；atlas spec SHA=`39ca622a45c0120d08e90daa7a17a0145be1b79485decb4619a0e5a3f23cadaf`。四次使用默认unknown方向成功执行，原门槛未放宽。`compare_whole.py`只读取两份on分析做全buffer摘要差值/计数分母对照，并明确same-binary来源由外部package/receipts证明。

`provenance.json`列所有原输入、raw/PNG/receipts/package/tar/control哈希和复现命令；`SHA256SUMS`覆盖本目录源与结果（除自身）。没有复制raw/PNG/app/cache。尚未验收完整flight、应用整体或物理显示。
