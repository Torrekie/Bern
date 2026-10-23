# macOS 14 ISO HDR tone mapper：公开规范与 macOS 13 可复现边界

2026-10-24。仅文献与 SDK 头文件核查；没有修改产品、编译、运行 UI 或重做 HDR 实验。

## 结论

**可以在 macOS 13 实现某个明确指定的 ITU 算法；目前核查到的 Apple/ITU/ICC 一手资料，不能唯一确定 macOS 14 的 ISO HDR 默认 mapper，因此不能据此承诺完整视觉等效。** 这不是“13 没有 HDR→SDR mapper”的结论。团队已实测：严格识别 CICP 后，以对应命名 PQ 空间交给 13 的系统 SDR 输出，两个灰块约为 229/255，与 14 参考接近；尚未闭合的是 High 模式随当前显示 headroom 自适应保留 HDR 的行为。

Apple 的 WWDC24 10177 在 9:12 列举 BT.2408、BT.2446、BT.2390；16:57 将 iOS 17/macOS 14 的 ISO HDR 路径称为 ITU 默认全局映射；17:12 则明确区分新一代 Reference White Tone Mapping Operator。该介绍没有把旧路径绑定到某一规范版本、方法、参数表或颜色处理空间。不能用 15 的新 operator 来定义 14 的目标。[Apple WWDC24 10177](https://developer.apple.com/videos/play/wwdc2024/10177/)

## 必须分开的量

| 量 | 含义 | 不能直接代替的量 |
| --- | --- | --- |
| PQ 信号 `N` | 编码值；经 EOTF 得显示参考的绝对 cd/m² | 线性 EDR、sRGB 截图灰值 |
| `Wc` | 内容的标称 diffuse/reference white；ISO HDR 默认 203 nit，可被适用元数据覆盖 | ICC `lumi`、母版峰值、屏幕当前白位 |
| `Lpk` / `Hc` | 内容峰值及内容 headroom，`Hc = Lpk/Wc`；stops 为 `log2(Hc)` | PQ 可编码上限 10000、设备 potential headroom |
| EDR `1` / `Wd` | 当前 UI/SDR 白；物理亮度 `Wd` 会随显示状态改变 | 固定 100 nit 或固定 203 nit |
| `Hd` | 当前显示峰值相对当前白位的比率；`Hd = LdisplayPeak/Wd` | 内容 headroom、硬件 potential headroom |
| `LB` / `LW` | 某些 ITU 算法所需母版显示黑位与峰值白位 | 内容 diffuse white `Wc` |

ISO HDR 的 203-nit 默认及 optional diffuse-white override 见 WWDC23 3:58–5:25；它并不规定当前屏幕的 UI 白必须实际发出 203 nit。[Apple WWDC23 10181](https://developer.apple.com/videos/play/wwdc2023/10181/)

EDR `1` 是 SDR/UI 白，物理亮度动态变化；大于 `1` 的部分由当前 headroom 限制。Apple 在旧 PQ 视频解码示例中使用的 100-nit 归一化，属于该工作管线的参考单位，不能推广为所有 ISO 静态图的 diffuse white。[Apple WWDC21 10161](https://developer.apple.com/videos/play/wwdc2021/10161/)

ICC `lumi` 是发光设备绝对亮度的 XYZ 型标签，不能仅凭其 Y=100 就断定 ISO 内容 diffuse white=100。CICP 描述编码，不单独给出内容峰值或 diffuse white。[ICC.1:2022，§9.2.33、§9.2.17](https://www.color.org/specification/ICC.1-2022-05.pdf) 当前 ICC registry 另有专门的 Content HDR Reference White Luminance 元数据；其语义与 `lumi` 不同。该条目是后续登记，不能倒推 14 的解析实现。[ICC CRWL registry](https://registry.color.org/dicttype-metadata/crwl)

以本任务输入为例：**只有在已确认解码单位是 100 nit 的条件下**，`2.03/8.12` 才约对应 `203/812 nit`，再以 ISO 默认白归一化为 `1/4`。这仅是单位转换：

```text
x100 = L/100
xISO = L/203 = x100/2.03
```

它不等于 tone mapping，也不能推出输出应为 `1/4`、229/255，或推断系统实际采用何种内容峰值。`Lpk` 仍需由有效元数据或明确的分析规则取得。

## 可以精确实现的公开数学部分

### 1. PQ 绝对亮度

以下是 BT.2100 的 PQ EOTF 与逆 EOTF；`L` 单位为 cd/m²，`N` 在 0…1。它解码绝对亮度，本身不完成显示余量压缩。[ITU-R BT.2100-2，Table 4](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.2100-2-201807-S!!PDF-E.pdf)

```text
m1 = 2610/16384
m2 = 2523/32
c1 = 3424/4096
c2 = 2413/128
c3 = 2392/128

P(N) = 10000 × [max(N^(1/m2) − c1, 0)
                / (c2 − c3×N^(1/m2))]^(1/m1)

Q(L) = [(c1 + c2×(L/10000)^m1)
        / (1 + c3×(L/10000)^m1)]^m2
```

`Q` 是逆显示 EOTF，不应与包含场景 OOTF 的完整摄像 OETF 混称。

### 2. 一个完整指定的 ITU 候选：BT.2408-6 Annex 5

这是**可实现候选，不是已确认的 Apple 14 算法**。该修订日期为 2023-03。输入是 PQ 分量 `N`；母版黑/峰值为 `LB/LW`；目标显示含环境光的黑/峰值为 `Lmin/Lmax`。用上面的 `Q`：

```text
D = Q(LW) − Q(LB)
x = (N − Q(LB))/D
b = (Q(Lmin) − Q(LB))/D
p = (Q(Lmax) − Q(LB))/D
k = 1.5×p − 0.5
t = (x − k)/(1 − k)

z = x                                      (x < k)
z = (2t³ − 3t² + 1)×k
  + (t³ − 2t² + t)×(1 − k)
  + (−2t³ + 3t²)×p                         (k ≤ x ≤ 1)

u = z + b×(1 − z)^4                        (0 ≤ z ≤ 1)
Nout = u×D + Q(LB)
Lout = P(Nout)
```

规范允许在母版范围确实未知且无法合理推定时采用 `LB=0, LW=10000`；这不能被称为 Apple 默认。该 Annex 还允许多种颜色应用空间；相同标量曲线不保证彩色像素相同。参数范围、超范围输入、无压缩情况须按所选完整规范处理。[ITU-R BT.2408-6，Annex 5，印刷页 58–60 / PDF 页 59–61](https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2408-6-2023-PDF-E.pdf)

另一项被 Apple 列举的 BT.2446-1 自身即有 A/B/C 多种方法，涉及不同转换亮度、颜色表示和修正流程。因此“ITU global”不足以唯一选出以上 Hermite 曲线。[ITU-R BT.2446-1，Table 1 及各方法章节](https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2446-1-2021-PDF-E.pdf)

### 3. ICC 2024 baseline 提案不能当作 14 的实现证明

ICC Tokyo 2024 的原始会议材料包含题为 *Proposed ISO 22028-5 Annex* 的完整演示。第 144–150 页提议按 PQ/HLG 解码，以 `CCV → CLLI → MDCV → 1000 nit` 选峰值、以元数据或 203 nit 选白位，再使用 Reinhard/maxRGB；第 160–162 页讨论按 gain-map 权重适配中间 headroom。它明确属于拟议 informative annex，并把多种 ITU 方法列作比较对象。不能把这个后来的建议回填成 macOS 14 的旧默认实现。[ICC HDR experts Tokyo 2024，PDF 页 115–165](https://www.color.org/events/hdr/tokyo2024_expert_day/HDRexperts-Tokyo2024.pdf)

## macOS 13 原生能力与尚缺的契约

| 公开能力 | 文献/SDK 确认 | 对本任务的限制 |
| --- | --- | --- |
| `CIImageOption.toneMapHDRtoSDR` | macOS 11+；只对被识别为 HDR 的输入 CGColorSpace 生效；默认 false | 公开接口没有公布曲线。自定义 ICC 未被识别时无效，不能推出 13 不支持映射。[Apple CIImageOption](https://developer.apple.com/documentation/coreimage/ciimageoption/tonemaphdrtosdr) |
| SDR 目标色彩管理 | Apple 的旧系统兼容建议包括 SDR CGContext / Core Image 输出 | 必须验证具体输入、目标空间与实际输出；团队已有 named-PQ 灰块成功实测。[Apple WWDC23](https://developer.apple.com/videos/play/wwdc2023/10181/) |
| `CAEDRMetadata.hdr10` | macOS 10.15+；`C(nit)=opticalOutputScale×linearBufferValue` | 100-nit scale 是 HDR10 参考管线示例；该接口没有承诺复用 14 ISO 静态图 mapper。[Apple CAEDRMetadata](https://developer.apple.com/documentation/quartzcore/caedrmetadata/hdr10(minluminance:maxluminance:opticaloutputscale:)) |
| 当前屏幕 headroom | `maximumExtendedDynamicRangeColorComponentValue` macOS 10.11+；会动态改变 | 不能改用 `maximumPotential…` 作为当前值。仅有 headroom 不足以获得全部绝对亮度/黑位/环境光参数。[Apple NSScreen](https://developer.apple.com/documentation/appkit/nsscreen/maximumextendeddynamicrangecolorcomponentvalue) |

Availability 与语义同时核对本机 Apple MacOSX14.2.sdk 中 `CIImage.h:100–110`、`CAEDRMetadata.h`、`NSScreen.h:76–82`。没有把新 SDK 可编译等同为旧系统具有新算法。

要忠实实现一个**指定** mapper，至少要固定：编码/CICP/范围与 ICC 等价性、内容白位、有效峰值来源、母版黑/峰值、当前显示余量、显示/输出空间、颜色应用空间及 gamut 处理。要声称等同 Apple 14，还须确定其方法/版本、元数据缺省与优先级、前后台及余量变化策略；本次核查没有找到完整对应契约。

## 当前证据能验证到哪里

本任务给定的 14 SDR WindowServer 灰块均值 228.93/254.83，以及 13 named-PQ 约 229/255，为团队既有实验输入，本次未重跑。它们是带输出色彩描述的编码像素，不是绝对 nit，也不是线性 EDR 值。比较前仍须按各 PNG ICC 转换到共同空间，排除边缘混色、透明度与量化抖动。

两个灰块不能识别整条曲线；同一显示状态下的 0…4 灰阶 ramp 可检查膝点和高光压缩，但仍不能区分彩色应用空间或显示余量适配。最低后续验证应覆盖：

1. 固定源、元数据和输出 profile，比较完整灰阶 ramp，分别记录 `Hd≈1`、中间值及大于内容余量时的输出；同步记录 app 前后台与亮度状态。
2. 分离内容白位、内容峰值、母版峰值三项，逐项改变，检验缺省/优先级；不以 `lumi=100` 替代内容白位。
3. 使用中性和高饱和色块，检查 gamut、色相和通道剪切；灰阶一致不等于彩色一致。
4. 截图仅能验证 WindowServer 输出。物理 nit、面板峰值及感知亮度等效仍需实际 HDR 显示设备与测量条件，不能由 SDR 截图闭合。

因此，当前可保留已经验证的 13 原生 Standard 路径；High 的当前余量适配应继续标为独立验收项。若选择某个 ITU 算法，可明确以规范为依据实现并校验；没有依据把拟合曲线、Reinhard 或某组 Hermite 默认参数直接称作 Apple 14 等效实现。
