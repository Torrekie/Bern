# 实际 hero CGImage metadata：本机控制与同一二进制13/14

本目录归档已完成的公开 metadata 采集与控制。**eager-v1 的p0有微小像素差异、p1全同；deferred-v2 及新SDK二进制的13控制各自12个ROI全同。原因未证实，不据此推断零 observer effect。** 同一新SDK二进制在13/14记录到相同的snapshot色彩profile/格式（设备scale造成尺寸/rowbytes差异）；这不是图像内容、数值范围或跨系统像素等效结论。

归档仅复制/核验现有字节；未运行保存脚本、编译、应用/UI/CI、图像对照算法或profile转换。工作原件未改，未复制3个编译可执行文件及传输tar；模块/cache也不纳入。归档构建阶段未读取后续离线分析；root现已追加独立分析，见末节。

## 1. 本机 SDK14.2 的观察点控制

`local13-observer-controls/` 保留 eager-v1/deferred-v2 的实际编译源码、Driver、provenance、原report/PNG、运行与编译日志、指纹和root控制结果。目标 ARM64/min13、Swift5.9.2、SDK14.2、`-O`/2jobs；继承原gain-map与未使用clock诊断适配，coordinator timer始终为0。

首次编译失败日志 `build-attempt-1.log` 原样保留：Swift拒绝C拼写 `CGColorSpaceIsWideGamutRGB`，要求公开Swift属性 `space.isWideGamutRGB`。后续冻结eager源包含这项导入名修正；首个被拒版本的错误行保存在原日志，不伪称单独完整冻结了失败前的全部源码。

v1在snapshot拿到已有CGImage后立刻读取标量、分类色彩空间并导出/hash/base64 ICC。v2仍在该点只读图像标量并暂存CGColorSpace引用，不保留CGImage/NSImage；全部PNG采集及原窗口清理完成后，才分类、导出和序列化profile。v2的主数组在原清理前冻结，cleanup新增记录另存。没有colorMode setter、第二次renderer图、provider读回、image转换/relabel或NSImage再缓存。

|运行|窗口秒数（原report）|front|主/cleanup记录|原控制结果|
|---|---:|---|---|---|
|local eager-v1|3.2805800437927246|1390→1390|2/2|p0六ROI不同；p1六ROI全同|
|local deferred-v2|1.7255640029907227|1390→1390|2/2|12ROI raw+ICC→sRGB全同|

eager-v1 相对原13基线的p0 ICC→sRGB RGB指标如下（0–255编码值，不是线性光/nit）；p1每项MAE/max均为0，raw与normalized exact：

|p0 ROI|MAE|max|
|---|---:|---:|
|body-custom|0.16038049768518517|3|
|body-named|0.16038049768518517|3|
|flight-custom|0.10821903935185184|3|
|flight-named|0.10484085648148149|3|
|oracle-bottom|0.16055410879629628|3|
|oracle-top|0.16038049768518517|3|

包括独立oracle在内的各pane均有p0差异；归档不将其归因为某个特定分类/ICC调用。后续v2对照全同只是所保留这次运行的结果，不是一般零观察影响保证。root原始对照表及 `compare-control.py` 均保留，归档者没有重跑像素计算。

## 2. CI40086541042 与同一新SDK二进制

`same-binary-13-14/` 保留成功run的build环境/命令/日志、signature/LC信息、原tar校验元数据、去除可执行文件后的解包源码、原package清单，以及同binary13和远程14的原报告/PNG/root验证。原CI harness SHA `ad1ae1a6c2acf493449b043c4cd867546f82cd7b`；构建 macOS15/Xcode26.3，Swift5模式，ARM64/min13，LC SDK26.2。产品原提取锁 b08db54；compiled fixture 的观察点适配已在provenance显式标识，exact副本与9dd相同不等于编译文件完全无改动。

- 原binary SHA256：`e4b389d9b91035b42add5725358ae3404ac901a1da5786c4767291e47ac7be14`。
- 原tar SHA256：`6505b5c7f97c49cb0586b7ba4acdb33b5b638e7034c9aa96d89db11d68c34ee4`。
- root原记录中的strict signature/ARM64/min13检查通过；本次只核验字节与已记录指纹，没有再次执行binary或签名工具。

|宿主|OS（原report）|窗口秒数|front|current/potential headroom|主/cleanup|
|---|---|---:|---|---|---|
|13|Version 13.7.8 (Build 22H730)|2.41300892829895|1390→1390|1/2|2/2|
|14|Version 14.8.9 (Build 23J631)|2.4760600328445435|332→332|1/1|2/2|

两者记录的normal三项前/后均false，cache unchanged、非key/inactive、Metal0、coordinator flight/timer0，每phase≥5连续相同原buffer。13同binary相对原13基线的12个ROI raw及ICC→sRGB均exact。远程14的report及root gates通过，**不把metadata同一性写成13/14像素等效**。

## 3. 公开表面描述的实测范围

两主key `baseline-body-named` / `baseline-body-custom`（以及保留的cleanup记录）均是如下profile/格式。v2色彩描述阶段为 `after_existing_window_teardown`：

|字段|13|14|
|---|---|---|
|CGImage尺寸|640×360|320×180|
|bytes/row|5120|2560|
|bits/component / bits/pixel|16 /64|16 /64|
|float components|true|true|
|alpha / bitmap / byte-order / pixel-format raw|1 /4353 /4096 /0|相同|
|space / model / components|kCGColorSpaceExtendedSRGB /1 /3|相同|
|wide / extended range|true /true|相同|
|2100 TF / PQ / HLG flags|false /false /false|相同|
|snapshot ICC长度|3144 bytes|3144 bytes|
|snapshot ICC SHA256|`2b3aa1645779a9e634744faf9b01e9102b0c9b88fd6deced7934df86b949af7e`|相同|

每条ICC base64完整解码后核对3144字节/SHA；未打印base64、未构造新的色彩空间或绘图。浮点/extended标志是格式/坐标范围描述，不能证明样本大于1或仍保留某段高光；非PQ标志也不能反推原源图是SDR。相同ICC/格式不能定位tone-map/clipping发生处或确定唯一原因。

Snapshot的3144-byte ICC与WindowServer PNG的profile是不同证据：PNG内嵌ICC在13为4032 bytes，14为3300 bytes。8张原PNG的SHA、IHDR尺寸、所有chunk CRC及内嵌ICC SHA对原capture字段均核验通过；不同宿主原PNG/ICC均原样保留，没有raw RGB跨profile硬比较。

## 清单、历史scope与后续追加

`ARCHIVE_VALIDATION.json` 包含每copy来源/字节/SHA、排除项及原work仍保留的指纹。核验两个本机fingerprint分别11/12项；eager指纹原来使用通用文件名，receipt明确映射到保存的 `*.eager-v1.*` / `build-eager-v1.log`，不拿v2覆盖它。新SDKpackage原清单26项（含被排除binary）和provenance18项已在完整work包中验证；build与runtime14的 `SHA256SUMS` 是该原package清单的历史副本，**不是各自子目录或当前去binary归档的完整清单**。

顶层 `SHA256SUMS` 覆盖本次实际保留的所有regular文件，唯独不含清单自身。原tar与3个Mach-O仅留hash/大小/构建或运行记录，不复制进证据目录；cache不复制，work原件不删除。原报告、脚本与provenance中的历史绝对/相对路径未重写，其来源到归档的映射见validation。更早的13未插桩基线仍在 `../macOS13-hdr-candidate/native-pq-hero-baseline13`。

本次未等待或读取另一个正在准备的离线分析目录。root后续追加该分析时，应重新生成最终顶层清单；本次冻结SHA只对应当前阶段。全部结论仅限固定同图from/to两端点及所记录运行，不扩展为实际flight/生命周期、High/HLG、整个app或物理HDR验收。


## Root 追加的同源离线分析

[`analysis/README.md`](analysis/README.md)保留新13与新14各68组比较、原始PNG/ICC到sRGB归一、完整十色块及gray-ramp统计。原13对新13、新14对历史40080838898的两phase×六ROI在raw及normalized均精确相同；十色块/ramp也无变化。没有缩放、拟合或按像素阈值配准，结果只适用于保留的实际区域，不是全窗口PNG或普遍零观察效应证明。

新同binary的四组跨宿主signed `H−B` 十色块残差逐项复现历史；均值5.210863/5.223884（p0 named/custom）、5.224399/5.236956（p1），最大113.048334/255，主要色差依然存在。该统计为色块均值的残差差，不是整图pixel MAE或物理亮度。不同VM/进程与实际ICC/headroom/scale上下文原样保留。

原`ARCHIVE_VALIDATION.json`描述归档构建阶段88份copy/91个文件的范围；本节追加16个离线分析文件后，当前顶层`SHA256SUMS`重新覆盖全部现存regular文件。原始runtime/源码/PNG字节没有改写。
