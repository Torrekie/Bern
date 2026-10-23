# 原始 PQ ramp 与 macOS 14 截图：无拟合数值对照

2026-10-24。只读产品；仅新增本目录的小型 Python 分析及结果，没有构建、下载或打开 UI。

## 结果

**BT.2408-6 Annex 5 的标量 EETF，固定 `LB=0、LW=1000、Lmin=0、Lmax=203`，输出按 203 nit 归一化，与现有 macOS 14 整段中性 SDR ramp 在 8-bit 量化范围内吻合。** 全 192 列 × 3 通道、每列平均 23 行：MAE **0.0994/255**，RMSE **0.1218/255**，最大绝对差 **0.3987/255**。没有优化任何曲线参数、横向相位或 ROI 位置。

这是可以独立实现并继续验证的具体候选；不是 Apple 实现身份、彩色处理或 HDR 实机验收已经确定的结论。BT.2390/BT.2408 共用的这类 EETF 也不能由截图区分为某份规范的具体修订。

## 输入与采样

- `examples/showcase/images/hdr-pq.png` 与上游 `ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee` 的文件逐字节一致；SHA-256：`96f80d2f1c06070dac29e3b7e2924a6aed8e54286bc73921f62cf75420a599ed`。
- 直接解析 PNG、校验每个 CRC、解压并反滤波，读取 640×360 的 RGBA16 原始数值，归一化为 `u16/65535`。不通过 ICC A2B 查表取得源亮度。CICP 为 `09/16/00/01`，即 BT.2020 / PQ / RGB / full range；alpha 全部为 1。
- 标准 PQ EOTF 解出顶左 **203.016424 nit**、顶右 **812.055272 nit**。原始底部 `y=240..<360` 每行相同，为单调 ramp；RGB 编码最大差 1 LSB16。
- PNG 只有 IHDR / iCCP / cICP / eXIf / IDAT / IEND，无 mDCv、cLLi。ICC 仅 desc / cprt / wtpt / A2B0 / B2A0 / chad / cicp / lumi；现有 ImageIO properties 也未提供母版/内容峰值。**1000 不是读取到的峰值元数据，是与数据吻合的 ISO reference / 14 缺省候选。203 来自 ISO 默认内容白，不来自 `lumi=100`。**
- A14：`Docs/Evidence/macOS14-reference-normal/images-layout-light.png`，920×668。PQ 图片准确边界 `[435,330,192,108]`；右上白块的纵向连续区为 `330..<438`。
- 采样 ROI 为 `[435,409,627,432]`。先将 PNG 内嵌 Display ICC 经 LittleCMS 转到 sRGB，再对 23 行逐列平均；保留三个通道分别比较。
- 固定像素中心映射 `source_x=(i+0.5)×640/192−0.5`，在源线性 nit 上插值。全部 192 列对应 **1.483…810.481 nit**；所以“整段”指整个屏幕可采样 ramp，不意味着已测到零附近的连续黑位。

## 预先明确参数的候选

这里所有误差使用去除两端各 2 列的 188 列，以同一几何和 ICC 流程比较。峰值选项只取 ISO reference 1000、观测 asset peak 812.055、Annex 未知母版 fallback 10000；不是搜索/拟合得到的参数。812 只是观测内容峰值假设，不能当作真实母版峰值。

| 模型 / 源峰值→目标峰值 nit | MAE /255 | RMSE /255 | 最大差 /255 |
| --- | ---: | ---: | ---: |
| Annex 5：1000→203 | **0.098** | **0.119** | **0.383** |
| Annex 5：812.055→203 | 1.422 | 1.834 | 3.582 |
| Annex 5：10000→203 | 24.846 | 26.214 | 34.542 |
| Annex 5：1000→100 | 8.987 | 15.722 | 45.199 |
| Annex 5：812.055→100 | 10.304 | 17.048 | 47.017 |
| Annex 5：10000→100 | 18.261 | 18.935 | 27.673 |
| BT.2446-1 Method A：规范固定 1000→100 | 35.828 | 39.308 | 60.772 |
| 无映射：线性 nit/203 后剪切 | 5.382 | 8.689 | 25.826 |
| 无映射：线性 nit/100 后剪切 | 15.445 | 25.204 | 69.123 |

Method A 仅实现中性轴：等 RGB 下色度修正为零；表 2 的 SDR gamma 输出先按 2.4 解码，再编码为 sRGB 比较。结果排除的是所列参数与方法，不是排除所有 BT.2446 方法/可调情形。[ITU-R BT.2446-1，Table 2](https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2446-1-2021-PDF-E.pdf)

最佳候选的 knee 在 **87.8363 nit / ISO-relative 0.432691**。203.016-nit 左灰块预测 **228.9933**，现有 A14 块均值约 **228.9286**；812.055-nit 右灰块预测 **254.9368**，A14 约 **254.8313**。不是只匹配这两个锚点：knee 以下和以上的整个 ramp 同时匹配。

## 鲁棒性与不可识别项

| 复核 | MAE /255 | 最大差 /255 |
| --- | ---: | ---: |
| A14 全部 192 列 | 0.0994 | 0.3987 |
| A14 另取 `y405..<410` | 0.1672 | 0.6250 |
| A14 另取 `y423..<435` | 0.1139 | 0.4202 |
| B14 实际图片 y331，ROI 同步下移 1 点 | 0.0968 | 0.3665 |
| B14 与 A14 对齐后的 ramp 本身 | 0.0220 | 0.0870 |

B14 为 `Docs/Evidence/macOS14-port-comparison/showcase-images-layout-light.png`，其白块连续区实测 `331..<439`，没有为降低误差移动横向位置。A14 每列原始行间标准差平均 0.476、最大 0.701 code；模型与列均值的亚 code 残差处于截图的量化/抖动幅度内，但不称逐像素相等。

ICC 的 perceptual / relative / saturation / absolute 四种 intent 对该中性样本给出相同结果。改为在 PQ 编码域插值再解码，MAE 0.0978，结论不变。最佳模型的线性 sRGB RMSE 为 **0.000952**。

`LB=Lmin=0.0005` 给出同样的曲线；仅将目标黑改为 0.0005 时，MAE 0.1023，差异也很小。这组 ramp **不能辨认绝对黑位**。它同样不能辨认逐 RGB、maxRGB、luminance、ICtCp 等彩色应用方式；这些方式在中性轴可以一致。[ITU-R BT.2408-6，Annex 5](https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2408-6-2023-PDF-E.pdf)

## 可复用的独立实现候选

`analyze.py` 中 `pq_eotf` / `pq_inverse` 是 BT.2100 的标准 PQ 公式；`annex5` 为已核 Annex 5 Step 1–5。函数返回 `Lout/Lmax`。公式与元数据区分也见[研究说明](../../../Implementation/macOS13-HDR-Tone-Mapping.md)。[ITU-R BT.2100-2，Table 4](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.2100-2-201807-S!!PDF-E.pdf)

将该标量模型延伸为随 headroom 变化的独立候选时，必须保持固定内容白单位：

```text
L = PQ_EOTF(sourcePQ)
if Hd >= 1000/203:
    EDR = L/203
else:
    targetPeak = 203*Hd
    EDR = Annex5(L, LB=0, LW=1000, Lmin=0, Lmax=targetPeak)*Hd
```

即 `EDR=Lout/203`，不能把 `Lout/targetPeak` 直接写入 layer，否则 HDR 峰值会再次被压到 1。layer 应接收 linear BT.2020，不再 PQ 编码或 gamma 编码。

| 假设当前 `Hd` | 输入 203 nit 的 EDR | 输入 812 nit 的 EDR |
| ---: | ---: | ---: |
| 1 | 0.783457 | 0.999435 |
| 1.5 | 0.978249 | 1.498521 |
| 2 | 1.000000 | 1.996624 |
| 3 | 1.000000 | 2.983578 |
| 4 | 1.000000 | 3.878328 |
| 1000/203 | 1.000000 | 4.000000 |

**表中 `Hd>1` 是公式预测，尚无对应 14 HDR 截图/线性读回证明。** 源/目标峰值的选取可能还涉及系统 metadata 缺省和 headroom 策略，不能由一个 SDR 条件确定。即使 13 自有窗口显示符合该表，也只验证该独立实现及单位，不等于验证 Apple 14 HDR 行为。

本实验对规范输入域内做有界计算：源均在 0…812.056 nit，未遇到源高于 LW 的情况；脚本将归一化 x clamp 到 0…1。该越界选择不是已验证的 Apple 行为。目标峰值达到/超过 LW 时直接返回原线性内容，避免 `k=1` 导致 spline 分母为零。

## 最小下一验证

1. 先以 CPU float→linear BT.2020 的独立实现，在 13 自有窗口验证 Hd=1 的整 ramp，以及实际 Hd≈2 时白位/峰值约为 1/2；用 GPU 读回排除 PQ 单位或归一化错误。此项已完成独立已知输入实验，见[原型与限制](../prototype/README.md)；并未进入产品。
2. 在真正 14 的 HDR 可用条件下，用同一源、同步记录当前 Hd，对照上表与完整 ramp。需要分辨“直接改变 Annex5 目标峰值”与“在 SDR/HDR rendition 间插值”等不同 headroom 策略。现有 SDR WindowServer 图不能闭合此项。
3. 另用少量 BT.2020 高饱和色块/通道不等的 ramp 分辨颜色应用空间与 gamut 处理；不将中性轴匹配推广为彩色等效。
4. 逐一改变 diffuse white、MDCV、CLLI，确认缺省与优先级；固定当前 asset 的 1000 候选不能推广为所有文件的硬编码峰值。

可从工作区根目录复跑：`python3 outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/numeric/analyze.py work/HDR-tone-rerun`。输出到独立 scratch 的 `report.json`、逐列 `ramp.csv`；默认不传输出目录时重建本归档内的分析结果。分析只读同仓库的既有参考与资源，不构建或打开 UI。
