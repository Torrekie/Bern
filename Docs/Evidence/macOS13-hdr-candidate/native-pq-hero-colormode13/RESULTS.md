# macOS13 actual hero：colorMode 阴性实验归档

**结论：default 控制复现旧13；仅设置 `extendedLinear` 没有消除相对实际14的主要 hero−body 残差。本实验不构成视觉等效通过，也不提供可合入产品的修复。** 没有指派唯一原因。

本目录保留已完成实验的冻结源码、原始 WindowServer PNG/ICC、原报告与运行/构建日志，以及离线脚本、spec、全部结果。归档只复制和验证现有字节，没有重编译、运行应用/UI/CI、重算图像结果或改写旧资料。编译产物和 module cache 未纳入；work 原件原样留给 root 清理/复用。

## 实际两次13采集

产品提取锁定 `b08db54e01ac2ec54fb84e6f2a70041f1f4c3604`，原始 image/hero 区块与9dd相同；继承本机 SDK14.2 的 gain-map/未使用 clock 适配。colorMode 是夹具的单一公开配置变量，不是产品修改。两次用同一 ARM64/min13 二进制（SHA256 `1135f88706481f23b2ab1634fa60efc6df9a9d9ffa809850d4a85db509adec15`），Swift5.9.2、SDK14.2、`-O`、2jobs。

|配置|setter requested|own PID|窗口秒数（原report）|wrapper秒数|退出|
|---|---|---:|---:|---:|---:|
|default|false|40508|1.7108649015426636|2.315719457983505|0|
|extendedLinear|true|40914|1.6183279752731323|2.121332833019551|0|

实际 OS13.7.8 (22H730)，front439→439；两次 normal 三项始终在记录的前/后检查中为false、cache unchanged、Metal0。两phase各有5个连续相同原buffer，current/potential headroom=1/2。每次固定六ROI、每ROI320×180pt（640×360px）；两次窗口/全部12个ROI几何逐值相同。两模式各自的六ROI跨phase均raw与normalized exact。这里的配置字段不是内部 renderer 格式或 setter 执行次数读回。

`default-vs-archive13/comparison.json` 的12个ROI在 raw 与 ICC→sRGB 域都完全复现旧13。default→extended 的8个 body/oracle ROI也均exact；差异只在两个手动 flight pane，两phase复现相同差异：

|ROI（每phase）|不同RGB像素 /230400|raw RGB MAE|max|ICC→sRGB RGB MAE|max|
|---|---:|---:|---:|---:|---:|
|flight-named|1394|0.0020601851851851853|1|0.004438657407407408|3|
|flight-custom|2475|0.003699363425925926|1|0.007952835648148148|3|

body只与同排 oracle-top exact，不能写成上下oracle都exact。MAE单位为编码8-bit RGB值（0–255），不是线性光或nit。

## 相对既有实际14参考

14参考来自独立已归档基线 `../../macOS14-hero-snapshot-40080838898`，OS14.8.9 (23J631)，同逻辑尺寸的ROI为320×180px。本次13 colorMode 两run使用同一 binary；**与14参考并非本次 colorMode 夹具的 same-binary 跨宿主运行**。未跨1×/2× resize，未拟合阈值/曲线。先算每patch/channel的 `Dhost=hero均值−body均值`，再比较 `D13−D14`；以下是10patch×RGB残差的绝对统计，不是整图pixel MAE：

|phase/source|default残差绝对均值|extended残差绝对均值|差值extended−default|最大残差（两模式相同）|
|---|---:|---:|---:|---:|
|progress-0/named|5.2108630952380945|5.2049164377289365|-0.005946657509158015|112.61632898351648|
|progress-0/custom|5.223883928571423|5.2130952380952325|-0.010788690476190688|112.61873282967032|
|progress-1/named|5.224399038461538|5.218452380952381|-0.005946657509157127|113.04833447802197|
|progress-1/custom|5.236956272893773|5.226167582417582|-0.010788690476190688|113.04833447802197|

cool812 的13 R通道 H−B为162.403073，两模式保持同值；14 p0约49.786745(named)/49.784341(custom)，p1约49.354739。这项主要残差没有改善。red812的hero B只微降，white203保持原值；完整精度和逐patch RGB在 `mode-comparison.json` 与两份 `*-vs14/comparison.json`。不能把14 hero直接视为14 body。

Pillow12.3.0/LittleCMS2.19：每PNG实际内嵌ICC→sRGB，perceptual intent0、flags0，另保留raw profile RGB。源atlas10patch内区112×104、ramp632×80，14按实际1×ROI映射为56×52、316×40；未重采样。所有列均值在两份 `ramp-column-means.json.gz`，每模式完整68组结果在对应 `analysis.json`。固定 from==to 的两个端点不代表真实 enter/leave、弹簧几何、hide/restore、retarget/reversal、flight lifecycle、High/HLG或应用整体已通过。

## 冻结清单与历史范围

- `native-pq-hero-colormode/SHA256SUMS`：原准备阶段24项，已逐项核验；它早于 build/runtime，所以不覆盖后来新增的构建指纹、两次运行和root对照。该目录旧README及 `static-validation.json` 的“prepared only/no compile”同属当时状态，原字节保留；后续实际运行以本RESULTS、`build-fingerprint.json`、两份report/run-receipt为准。
- `native-pq-hero-colormode-analysis/SHA256SUMS`：冻结离线分析15项，已逐项核验；其scope本来不包含runtime原PNG，现由归档顶层清单覆盖。
- `ARCHIVE_VALIDATION.json`：逐copy来源映射/字节/SHA、原 source provenance16项、build fingerprint16项（含排除binary的原SHA）、19项既有外部参考、4个runtime PNG→report SHA及atlas锁核验，和排除项凭证。没有执行任何保存的脚本。
- **顶层 `SHA256SUMS` 为本次最终完整范围**：覆盖本目录所有regular文件，唯独不包含清单自身；原准备清单不被追认为最终清单。

本目录用与work相同的两个子目录名保留相邻关系，所有冻结报告/脚本里的绝对work路径均未改写。`ARCHIVE_VALIDATION.json` 给出新位置；旧13参考仍在 `../native-pq-hero-baseline13`，atlas在 `../color-probe13`，14参考如上，不重复复制。离线脚本与结果可审计；若未来work被清理，重跑 `analyze.py` 时应显式传本归档report和全新output，再让比较器使用新analysis。`compare_default.py` 有 `--archive-report/--default-report`，`compare_crosshost.py` 有 `--report13/--report14`；`compare_modes.py` 使用analysis记录的report路径，需从新路径重建两份analysis后再用。不要为复现而修改冻结JSON或覆盖原结果，也不要将保存的build/run脚本作为自动执行步骤。
