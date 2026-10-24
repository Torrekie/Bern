# 原始RGBA binary16离线分析器（准备完成，尚无真实新输入）

只读取root之后提供的成功report、原始raw导出和原PNG。没有启动fixture、UI、编译器或CI，没有改产品、旧归档、docs/index或runtime夹具，也没有安装依赖。当前唯一执行验证是明确标记的微型**合成**bit/stride/坐标用例；不能当作native运行或视觉验收结果。

默认先验证全部输入，再输出whole-buffer结构统计和top-down / bottom-up两套坐标候选。**不按颜色自动选方向、翻转、对齐或把候选patch当成语义结论。** 只有调用者显式指定方向并给出独立证据文件，才输出那一方向的10patch/ramp数值；分析器只保存证据路径/长度/SHA，无法代替人工审查证据是否成立。它不进行跨宿主语义patch比较。

## 调用

未知行方向（首轮应使用此模式）：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 work/native-pq-hero-float-analysis/analyze_float.py \
  /ABS/PATH/actual-runtime/report.json \
  --output work/native-pq-hero-float-analysis/host13-on-unknown
```

输出目录必须尚不存在，且在本分析工作目录内；不写入runtime输入树。`off`成功报告也可调用：检查records为空、provider-copy0、retained-peak0并保留实际observation counts，输出没有raw数据数值。不要把off误写成没有hook调用。

仅在已有独立行方向依据后：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 work/native-pq-hero-float-analysis/analyze_float.py \
  /ABS/PATH/actual-runtime/report.json \
  --row-direction top-down \
  --orientation-evidence /ABS/PATH/independent-direction-evidence.md \
  --output work/native-pq-hero-float-analysis/host13-on-grounded
```

`bottom-up`表示原buffer row0对应源atlas底边；top-down表示row0对应源atlas顶边。这是坐标映射声明，程序不重排原bytes。证据不能由本次颜色“看起来更像”来挑选。证据文件限64KiB；即使有该参数，程序仍不比较不同host的语义patch。

## 实际schema与前置门槛

按当前`work/native-pq-hero-float-capture/FloatCapture.swift.inc`的完整字段名读取：record使用`bits_per_component` / `bits_per_pixel`，不是早期讨论中的简写bpc/bpp。未知/变动schema明确失败，不猜测别名。

在任何half数值解释前，要求：

- 实际13/14 report成功、两phase完成；normal三项全部false、front保持、cache深比较保持、activation0、无MTKView/coordinator flight/timer、nonkey/inactive、稳定own PID/window ID、每phase至少5个连续相同buffer。原两PNG逐字SHA核对；不会从分析门槛重新证明未保留的连续buffer。
- 源ledger两个SHA锁/EXIF-up与冻结atlas一致；六ROI320×180pt。raw尺寸仅支持当前13的640×360或14的320×180，并与实际body截图ROI尺寸匹配，不据此推成所有设备默认scale。
- `snapshot_float_capture`：requested为原env字符串/null，selected为off/on；success=true/error=null，actual primary count=2，keys恰为named/custom。cleanup只核非负有限count并保留，不要求0。
- on records依次named/custom，两个唯一fixture相对文件；off records为空。source报告provider_copy_calls、total_raw_bytes、4MiB预算和retained-after-export0须自洽；记录retain≤freeze≤provider-read≤release的已报monotonic顺序。
- 精确16bpc/64bpp float、bitmap4353、byteorder4096、premultiplied-last alpha1、pixel-format0。每文件长度必须等于真实rowbytes×height，stride至少width×8且为偶数；**两文件声明总量先核≤4MiB，再读payload**。完整file SHA/长度与两个primary deferred descriptors逐字段匹配，ICC base64严格解码长度/SHA匹配。原raw/report在计算结束再核未变。
- `export_stage=after_existing_window_teardown`只按保留source/记录验证，不把时间字段当作独立native teardown测量。snapshot ICC只作上下文，没有应用该profile或做颜色转换。

任何失败退出非0，不输出成功分析或partial数值结果；不会替source补raw文件、忽略失败、改schema、猜格式或用ImageRenderer重新生成。原路径安全/文件预算/不可覆盖门槛不放宽。

## 原bits、统计和方向

按原uint16 little-endian位模式解码IEEE754 binary16的存储RGBA；不clamp、不unpremultiply、不颜色转换、不归一化、不rescale/fitting、不推nits。保留原raw文件SHA，逐通道输出unique位模式精确计数、≤64时完整hex列表、最多32个排序样本、完整位频histogram的SHA。histogram本身不展开为巨大JSON，更不输出逐像素JSON。

whole-active-pixel范围使用所有行、排除stride padding；完整文件SHA覆盖padding，padding另记byte count/SHA。min/mean/max明确只对finite数值，NaN/+Inf/−Inf分别计数；<0/>1包含相应infinity、排除NaN。负零与正零位模式分开；alpha报告是否每个sample均为精确1.0（0x3c00），不自动修正alpha或丢弃异常值。

源atlas640×360，10patch内区112×104、ramp632×80；只整数映射到实际raw尺寸。320×180时patch56×52、ramp316×40；非整数边界拒绝，不round/插值。unknown只列两套半开raw row box候选，不产生semantic patch值；whole-buffer差异也不能自动定位patch原因。已知方向的patch/ramp使用同一bits/数值摘要，原数据不翻转。

输出`analysis.json`硬限512KiB；原report限2MiB，raw总量4MiB，方向证据64KiB。库仅Python标准库（Python3.9+），没有numpy/Pillow安装需求。

## 合成验证及保存范围

`test_synthetic.py`人工构造2×2个RGBA binary16像素和row padding，检查subnormal/finite极值、负零、不同NaN payload、Inf、<0/>1、alpha1、padding不入像素、截断/短stride失败、两方向坐标及非整数边界拒绝、非finite JSON拒绝、未知bitmap在文件读取前失败。`synthetic-validation.json`只记录这些合成用例和源SHA。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 work/native-pq-hero-float-analysis/test_synthetic.py
```

`atlas-rois.json`与既有冻结spec逐字相同，并在main硬核SHA。`provenance.json`记录只读schema/spec来源和验证命令；`SHA256SUMS`覆盖本目录准备文件，除自身。未写真实采集结果；root负责off/on原图控制及后续是否运行。相同结构或whole-buffer统计不等于相同UI/完整flight/物理显示或唯一根因。
