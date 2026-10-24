# Actual snapshot float cohort：完成与边界

同一分发binary在13/14的实际snapshot raw中已有小的全buffer分布差异；格式与ICC一致不足以证明payload分布相同。该观测止于实际renderer-return CGImage的post-teardown provider导出边界，不能定位语义patch、选择行方向、唯一归因OS或解释可见主差。本实验未修复产品，也未验收UI、完整flight或物理显示等效。

## 来源、构建和四次实际运行

[CI40091326190](https://github.com/Torrekie/Bern/actions/runs/40091326190)成功，harness commit为`dd0aa9551ce82d318807b2faa4967e22484a64ad`。package保留实际source、命令、环境及build/signature记录；新SDK26.2/Swift5 language/arm64 min13构建，14 job不重建；root在13运行同一binary。

binary SHA：

`38d0bf9bd54ae60bd7699e3e02a149e591968a3f63cce3d3968af0b9e647a517`

tar SHA：

`fcfdb7616bd1865b76d4524ea281d360d0c679fcfd73ff51d779a6922bc7603f`

归档前保留实物纯hash、23/23 package manifest项、root-package-verification、14 binary记录和四run receipts均复核一致。strict signature/arm64/min13读取root原检查exit0记录；归档未重跑工具链。binary558080字节与tar234166字节按要求排除，SHA/源/收据保留；不能再以本档不存在的实物重新验签。

| Actual host/mode | 窗口秒数 | Front首尾 | raw bytes | provider copies | peak /after-export | current/potential headroom |
|---|---:|---:|---:|---:|---:|---:|
| 13 off | 1.608554959 | 9292→9292 | 0 | 0 | 0 /0 | 1 /2 |
| 13 on | 1.563573956 | 9292→9292 | 3686400 | 2 | 2 /0 | 1 /2 |
| 14 off | 2.200559974 | 322→322 | 0 | 0 | 0 /0 | 1 /1 |
| 14 on | 1.851788044 | 322→322 | 921600 | 2 | 2 /0 | 1 /1 |

Actual OS13.7.8 (22H730)与14.8.9 (23J631)。四run success/exit0，primary/cleanup hook counts各2/2、normal三项首尾false、cache深比较保持、activation0；samples/captures保持own PID/window、nonkey/inactive、front、无MTKView/coordinator flight/timer，每phase至少5个连续相同buffer记录。原report/PNG/raw/receipts哈希均核对；窗口7.9秒watchdog和外层15秒流程来源保留。

normal_after按原driver在teardown前读取，frontmost_after在teardown后读取；不是独立进程退出后的桌面normal探针。off仍执行hook/count，但不retain CGImage或读snapshot provider；on只保留两primary renderer-return对象，cleanup计数不retain，原PNG及原teardown之后才导出provider并释放fixture引用。对象lifetime/provider访问发生变化，不能外推普遍零observer效应。

## PNG控制和raw身份

当前四个root控制（均12个唯一ROI raw及ICC-normalized exact）为：

- `v2-vs-float-off14.json`：既有metadata14→新14off。
- `float-off-vs-on14.json`：新14off→on。
- `v2-vs-float-sdk26-off13.json`：既有metadata13→新SDK13off。
- `float-sdk26-off-vs-on13.json`：新SDK13off→on。

本归档核对当前baseline/candidate report SHA与12 rows/zero指标，没有重复运行ICC图像比较。controls中的其它local SDK13/smoke记录属于保留历史，不拼接为本cohort运行。

| Raw | width×height /row bytes | bytes | SHA256 |
|---|---|---:|---|
| 13 named | 640×360 /5120 | 1843200 | edc1c9380bbf86e35c9830359428b715953cccd0f5952b10ade269923a6a2469 |
| 13 custom | 640×360 /5120 | 1843200 | 314b9001c1c47eea9f39a23fd6c697d1bcb66cfcda83dbc01153149c2d36e67c |
| 14 named/custom（各自） | 320×180 /2560 | 460800 | 807393b1503ad04a08e2dc09cac516e9d2abfcd86c9db3b15ec2761230201962 |

当前13两个raw与旧SDK13实物各自比较完整bytes、长度和SHA均相同；这只是本case证据，不能推成SDK在其它条件无影响。旧raw不重复复制或链接入本档，当前13同字节raw已保留。14 named/custom完整bytes相同，二者在本归档内部共享inode；不能推成任意named/custom输入相同。

四run snapshot primary ICC严格base64解码，均3144bytes/SHA=`2b3aa1645779a9e634744faf9b01e9102b0c9b88fd6deced7934df86b949af7e`、kCGColorSpaceExtendedSRGB。raw精确16bpc/64bpp float、bitmap4353、16Little byteorder4096、premultiplied-last alpha1、pixel-format0，无padding。capture PNG ICC、headroom、scale、原descriptor和完整context仍在原report及analysis中；snapshot profile与窗口PNG profile不能混为一层。

## 未定方向的whole-buffer结果

冻结分析器四次默认unknown方向均通过，`semantic_patch_values_emitted=false`。没有clamp、unpremultiply、ICC/transfer应用、颜色转换、nits换算、rescale、配准、拟合或按颜色翻转。13每源230400 pixels、14每源57600；4倍只作统计分母背景，不生成跨host像素对应。

四raw全部sample finite，NaN/+Inf/−Inf均0；alpha各自每个sample均精确1.0/0x3c00。13 named与14两源RGB极值相同：R −1.96875…3.064453125，G −1.0048828125…2.60546875，B −0.98388671875…2.58984375。13 custom仅R min为−1.9677734375，其余上述极值相同。

| Stored channel | 13 named mean | 13 custom mean | 14两源 mean |
|---|---:|---:|---:|
| R | 1.567957814535 | 1.567728233337 | 1.568117078145 |
| G | 1.553895314535 | 1.553717104594 | 1.554054578145 |
| B | 1.283550262451 | 1.283549308777 | 1.283709526062 |

| Channel（各host两源计数相同） | 13 <0 | 14 <0 | 13 >1 | 14 >1 | 13 >1−4×14 >1 |
|---|---:|---:|---:|---:|---:|
| R | 30720 | 7680 | 174840 | 43680 | 120 |
| G | 30720 | 7680 | 190200 | 47520 | 120 |
| B | 46080 | 11520 | 159480 | 39840 | 120 |

14−13 named的RGB mean均+0.00015926361084；custom R/G/B分别约+0.00038884480794/+0.00033747355143/+0.00016021728516。负值counts恰4倍；>1 fraction差各120/230400≈0.000520833333。全精度、unique-bit摘要与count fractions在analysis中。

`root-whole-buffer-check.json`独立以stdlib struct<4e解码；归档将其四行全部min/mean/max/<0/>1/alpha1字段与冻结analyzer逐项匹配通过。该核对没有挑选row或semantic patch，也不能消除native1×/2×采样/边界、headroom和宿主context差异。

相同format/ICC并未消除raw层观测差异，但小的全局差值不能直接归为可见主差。方向、具体位置、源解码/renderer/宿主背景等因果没有在本实验独立隔离；不引入后续层级审查或候选推测。

## 归档、清单与清理

目录映射严格为`same-binary-13-14`、`analysis`、`controls`，共90个原文件逐字保留；新增本页/README、validation/provenance及最终清单。所有work原件保持，由root随后清理。

只对本新档内完整SHA和bytes相同的PNG/raw建立4组内部硬链接，避免2716871逻辑重复字节；未链接work/旧archives。13四张PNG全文件相同，14各phase的off/on PNG全文件相同，14两raw全文件相同；没有把不同phase的14PNG强行合并。该逻辑去重量不是APFS物理回收测量。

最终顶层`SHA256SUMS`覆盖所有现存文件，除自身；source/package/analysis原清单保持原字节，含有意排除binary/tar的历史引用。所有旧archive、产品、harness、Acceptance、索引和发布未改，未编译或运行UI/CI。该档不推进macOS11/Swift5.3、ObjC/iOS阶段，不承诺完整flight、UI或物理显示parity。
