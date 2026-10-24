# Standard PQ hero 旧链：离线端点分析

已用现有 Python3 + Pillow12.3.0 / LittleCMS2.19 读取真实 `work/native-pq-hero-baseline/runtime13/report.json` 和原始 progress-0/1 整窗口 PNG。没有读 NSImage 对象、改夹具/原图/report、编译或追加 UI/CI。本目录只保存分析代码、坐标规范、哈希及小型离线报告。

## 已采集结果

每个实际 ROI 为640×360像素（320×180pt）；完整RGB、10块内区和632列×80行灰阶均按 report 的整数 screenshot_pixels 裁切。两个 phase 的结果相同：

| 目标减去同排 native oracle | Raw RGB MAE/max | ICC→sRGB RGB MAE/max | sRGB十色块均值 MAE/max | sRGB灰阶列均值 MAE/max |
| --- | --- | --- | --- | --- |
| body-named |0 /0|0 /0|0 /0|0 /0|
| body-custom |0 /0|0 /0|0 /0|0 /0|
| flight-named |16.771081 /113|18.377760 /164|19.973483 /162.400670|15.308933 /69|
| flight-custom |16.774064 /113|18.385720 /164|19.986378 /162.400670|15.307760 /69|

所有数值为编码8-bit RGB code values（/255），不是线性光或nits。两条 flight 各有159539/230400像素与 oracle 不同；normalized 通道MAE分别为 named `[17.641402,12.651957,24.839922]`、custom `[17.640929,12.651558,24.864674]`，通道最大值均 `[164,69,106]`。

两处 body 与上下两个 oracle 均逐像素相等，raw与ICC→sRGB均成立。六个ROI逐一跨 progress-0→progress-1 也全部逐像素相等，raw与normalized共12组跨phase比较。分析总计68组（各phase六ROI对上下oracle，加body对对应flight；另六ROI跨phase，分别raw/normalized），完整逐patch/逐比较指标见 `baseline-analysis/analysis.json`，全部逐ROI灰阶列均值见压缩的 `ramp-column-means.json.gz`。没有ICC哈希警告。

这是**未改的真实 snapshot(in:)→NSImage→原 BernHeroFlightView.draw 端点存在差异**的证据，尚不为差异指派唯一根因。两条 source/target 使用相同 NSImage 的固定尺寸绘制，progress0/1不等于完整 hero flight 生命周期验收；enter/leave、几何弹簧中间帧、hide/restore、retarget/reversal、动态Standard↔High、High/HLG/14、全应用均未因此通过。named也出现差异，不能据此断言只向hero传custom-derived图就足够修复。

## 坐标与色彩处理

`atlas-rois.json` 从旧 `color-probe13/report.json` 的源 atlas 定义提取；读取时验证了两个原始640×360 RGBA16 PNG 的SHA及PNG header：named `3efb40d42933dade20c11d2654d86afd25b1e02c838d9b080bb1233faa36da5b`，custom `fa3fdc43d91518c145c08b01ba6181ec063c68158e57d312a1ff942571c2a12e`。运行时cache ledger的源文件SHA也必须与这两锁一致。

10块源区为5列×2行，每块128×120。严格复用旧 actual-body 分析：每块去掉四边8源像素，取112×104内区；gray-ramp source_rect为 `(0,240,640,120)`，取source `(4,260,632,80)`。再按每个**实际报告**的截图 ROI 缩放坐标边界；不缩放图像，不作配准、阈值对齐、拟合或猜测ROI。若目标边界不是整数像素，脚本失败而不四舍五入。本次确为1:1 atlas-to-screenshot像素，因此内区仍112×104，ramp为632×80。

保留 PNG 原始嵌入 ICC 的编码 RGB，与用该PNG自己的 ICC 经 ImageCms.profileToProfile 转到 sRGB 的8-bit RGB 两套指标；perceptual intent0、flags0。所有输入截图必须为RGB/RGBA8、ICC存在、ROI alpha全255；不隐式丢失16-bit截图精度或推断透明合成。这里16-bit的是源 atlas和runtime报告的snapshot representation；WindowServer PNG实际IHDR为8-bit，二者不能混为同一缓冲。

## 重跑

使用已有带Pillow/LittleCMS的解释器，不安装新依赖：

```sh
python3 work/native-pq-hero-analysis/analyze.py \
  work/native-pq-hero-baseline/runtime13/report.json \
  --output work/native-pq-hero-analysis/recheck-analysis
```

OUTPUT必须是本分析目录下尚不存在的子目录，不得写入baseline/runtime输入树。原PNG/report不会覆盖或改写，默认也不导出重复ROI PNG。输入report须成功完成两phase、每phase报告5个相同raw buffers、源/cache账本不变；脚本独立验证保留PNG文件SHA、尺寸、ICC和ROI。它没有取得原始5帧或实时系统对象，**不声称重新验证**其runtime ownership/前台/noMetal/noTimer/真实运行行为。

颜色或像素不同属于测量结果，脚本仍返回0；非零仅表示输入/schema/分析条件失败，exit0不是视觉验收通过。现有 `baseline-analysis` 不覆盖；重跑使用新子目录。生成的JSON及压缩列均值约0.8MB；未保留额外编译缓存、可执行文件或截图副本。
