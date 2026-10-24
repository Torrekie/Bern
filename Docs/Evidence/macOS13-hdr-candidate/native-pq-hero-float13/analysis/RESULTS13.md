# 实际macOS13 off/on：whole-buffer结果

冻结分析器对actual off/on两报告均成功，行方向始终unknown，`semantic_patch_values_emitted=false`。本页只报告原始RGBA binary16存储值的全buffer统计，不定位patch、推方向、换算nits或推断原因。

原冻结7文件及`SHA256SUMS`保持原字节；准备README/provenance中的“尚无真实输入”是历史状态，当前执行以本页、`actual13-summary.json`和`actual13-provenance.json`为准。没有改分析器源码、runtime fixture、产品、harness、docs/index，未启动UI/编译/CI，也未派新agent。

## 实际门槛和来源

同一保留binary的纯文件hash、build fingerprint及两run receipts一致：

`84efaed4e15e9f24b95d84d0e352131ab3f418ed9e42e158d53c9e0b4f885313`

实际OS13.7.8，两run success/exit0；normal首尾全false、front9292→9292、cache深比较保持、activation0。所有samples/captures的own PID/window identity一致、nonkey/inactive、无MTKView/coordinator flight/timer；两phase各至少5个相同rawbuffer记录。原report/两PNG/receipt及rawfile重新核hash，实际on raw格式与两个primary deferred descriptors及ICC profile SHA/长度均通过冻结门槛。

| 项目 | off | on |
|---|---:|---:|
| 窗口秒数 | 1.839629054 | 1.928040028 |
| Outer进程秒数 /上限 | 2.848413125 /15 | 2.593056458 /15 |
| primary /cleanup调用数 | 2 /2 | 2 /2 |
| provider copies | 0 | 2 |
| retained peak /after export | 0 /0 | 2 /0 |
| raw records /bytes | 0 /0 | 2 /3686400 |
| 导出秒数 | 0.000029750 | 0.033125417 |

on两文件各640×360、row5120、16bpc/64bpp float、bitmap4353、byteorder4096、premultiplied-last alpha1、pixel-format0；每个文件精确1843200bytes，无row padding。二者总量3686400bytes，小于4MiB。off并非没有hook调用，而是没有retain/provider read/raw导出。

- `snapshot-named.bin` SHA=`edc1c9380bbf86e35c9830359428b715953cccd0f5952b10ade269923a6a2469`
- `snapshot-custom.bin` SHA=`314b9001c1c47eea9f39a23fd6c697d1bcb66cfcda83dbc01153149c2d36e67c`

没有复制raw/PNG/binary；原件仍由root保留在fixture工作目录。root的v2→off与off→on两份PNG控制各记录12个ROI raw/normalized exact；本任务独立核对其当前baseline/candidate report SHA、12个唯一rows和zero指标，没有重复运行ICC图像比较。该观察不构成普遍零observer效应保证。

## 未定方向的全buffer RGBA

每源230400 pixels，以下均为**原存储half数值**，不clamp、不unpremultiply、不应用ICC/transfer function、不颜色转换、不缩放。min/mean/max有限值统计；本次全部分量均finite，NaN/+Inf/−Inf均0。

| Source/channel | min | mean | max | <0 count | >1 count |
|---|---:|---:|---:|---:|---:|
| named R | −1.9687500000 | 1.5679578145 | 3.0644531250 | 30720 | 174840 |
| named G | −1.0048828125 | 1.5538953145 | 2.6054687500 | 30720 | 190200 |
| named B | −0.9838867188 | 1.2835502625 | 2.5898437500 | 46080 | 159480 |
| custom R | −1.9677734375 | 1.5677282333 | 3.0644531250 | 30720 | 174840 |
| custom G | −1.0048828125 | 1.5537171046 | 2.6054687500 | 30720 | 190200 |
| custom B | −0.9838867188 | 1.2835493088 | 2.5898437500 | 46080 | 159480 |
| 两源 A（各自） | 1 | 1 | 1 | 0 | 0 |

两源alpha各230400个sample全部为精确1.0位模式0x3c00；没有自动修改alpha。完整精度、unique-bit计数/位频摘要hash在`host13-on-unknown/analysis.json`，小型汇总在`actual13-summary.json`。

这些whole-buffer统计不依赖上下行候选选择，但不能据此将差异归属某个颜色patch、推断OS/renderer根因或绕过scale/边界取样限制。两套top-down/bottom-up仅坐标候选，没有候选patch数值，也没有跨host语义比较。

## 执行和完整性

只执行两次冻结命令，输出`host13-off-unknown/analysis.json`与`host13-on-unknown/analysis.json`，exit0。分析器源码SHA仍为`b616c42b192c13b7fee3d903d90e9553f389c6ac4b6f7da8cc96996877fcca2a`；原7文件准备清单SHA仍为`70f318fbdb56d08c550c7de3deaaa4141e7ca0d986a59741cc89943770d9c122`。

`actual13-provenance.json`记录实际原输入/控制来源和哈希。`ACTUAL13-SHA256SUMS`覆盖本工作目录当前全部文件（除自身）；原`SHA256SUMS`保留准备freeze合同，不改写。方向、14 raw及语义比较仍待独立依据/实际输入；本结果不验收完整flight或物理显示。
