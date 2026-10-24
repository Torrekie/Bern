# PQ hero：跨宿主离线残差比较

本目录只做保留 report/PNG 的离线分析；没有修改旧归档、编译、读取NSImage对象、操作UI或触发CI。已实际分析新SDK构建的13和14保留report/PNG，`compare.py`亦已用两份实际结果运行成功。原始report/PNG及旧baseline归档保持未写；每侧完整68组比较及跨宿主残差报告均在本目录。

## 冻结 analyzer 的14/1×兼容审查

原 `work/native-pq-hero-analysis` 已经是旧归档的symlink；不能直接用它的HERE约束往旧目录追加14结果。本目录 `host-analyzer/analyze.py` / `atlas-rois.json` 是**逐字复制**的冻结版本，SHA分别为 `98243090f0b45fe18baed3d89d4e382c7d8f7c02662a930cfda8c87c3b0f39d4` / `39ca622a45c0120d08e90daa7a17a0145be1b79485decb4619a0e5a3f23cadaf`；所有新输出只放fresh work子目录。

源码没有OS13 hard gate。每宿主只要求cache before==after及两源file SHA锁，14 derived字段为nil不妨碍分析，也没有要求跨宿主cache字段相同。report须同schema、两phase成功/5equal buffers、六个320×180pt pane、8-bit RGB/RGBA PNG、嵌入ICC、opaque、整数ROI及其SHA。

1× pane为320×180像素时：10个128×120源patch去8像素边界后，映射为56×52截图像素内区，首块 `(4,4,56,52)`、最后块 `(260,64,56,52)`；ramp源 `(4,260,632,80)` 映射为 `(2,130,316,40)`，亦即x[2,318)、y[130,170)。全部边界是整数；代码按实际report frame映射，不缩放截图、不猜ROI。每宿主两phase内像素尺寸仍须相同，13的2×640×360与14的1×320×180不做跨宿主全图/列像素强行比较。

## 新SDK binary在13的实际结果

root提供binary SHA `f50acd4dee545befeaafa500532c76dd9cd094c46e68e700ce403ce32f8aead2`；本子任务没有读取其可执行文件重新验证binary身份，build/transfer/section/signature证据由root保留。真实输入为 `work/native-pq-hero-ci14-40080291082/runtime13/report.json` 及两个原PNG，已用fresh analyzer读取，报告在 `host-analyzer/sdk26-13-analysis/`。

相对旧SDK13，两phase×六个ROI逐一比较：**12/12 raw RGB和12/12 ICC→sRGB RGB均逐像素相同**，各640×360，对应嵌入ICC也相同。逐ROI原始/normalized hash与shape对照完整保存于 `old-vs-sdk26-13.json`。因此新SDK13仍有与旧链完全相同的hero端点像素差异；这没有预言14结果或指定根因。新13完整68组指标保存在新analysis.json。

## 实际14与跨宿主结果

实际14输入来自 `work/native-pq-hero-ci14-40080838898/runtime14/report.json`；1×六个ROI均320×180，源坐标映射通过，Pillow/LittleCMS版本与13相同，无ICC哈希警告。源cache账本14的derived=nil未被误当成失败。

14中body-named与同排oracle-top逐像素相同，body-custom与oracle-top有小差异（normalized fullRGB MAE0.280619、max2；patch均值MAE0.001293、max0.007212）。14自身hero→同排oracle-bottom也不相等：progress0 named/custom fullRGB MAE15.036186/15.060961、progress1均15.032037，max均97。这不支持把“13 hero必须等于live body”直接当作已证实14行为。

按指定的signed `Dhost=mean(hero)−mean(body)`，再做 `D13−D14`，结果如下。均为10patch×RGB的**均值残差**统计，不是fullRGB像素MAE。

| phase/source | 13 H−B绝对均值 |14 H−B绝对均值| D13−D14绝对均值/max |
| --- | --- | --- | --- |
| progress0 named |19.973907|14.951694|5.210863 /112.616329|
| progress0 custom |19.986802|14.951774|5.223884 /112.618733|
| progress1 named |19.973907|14.900675|5.224399 /113.048334|
| progress1 custom |19.986802|14.899908|5.236956 /113.048334|

最大cross-host项均为cool812的R。14 flight本身跨progress0→1存在小差异：named fullRGB normalized MAE0.132020/max1，custom0.131447/max2；14 body和上下oracle分别跨phase都exact。13六ROI分别跨phase全exact。这里只记录差异，不指派原因，不拟合修复曲线。完整每host/每phase/每patch signed数据见 `crosshost-result/comparison.json`。

### 对旧分析文字的勘误

我早先旧baseline README将primary同排结果错误扩写为“body与上下两个oracle都exact”。**exact只适用于13 body→oracle-top。** 旧analysis.json原始计算一直正确：13 oracle-top→bottom normalized fullRGB MAE0.294106/max5，133032/230400像素不同，但patch均值差仅MAE0.000755/max0.002747；14上下oracle亦有小差异（MAE0.281574/max2）。本次未改旧归档，以上勘误及完整原指标应一并阅读。新/旧SDK13逐ROI raw/normalized全部exact的比较结论保持成立。

## 重跑

使用现有同一Pillow/LittleCMS解释器，对原14 report做离线分析，选择尚不存在的输出子目录：

```sh
python3 work/native-pq-hero-crosshost/host-analyzer/analyze.py \
  work/native-pq-hero-ci14-40080838898/runtime14/report.json \
  --output work/native-pq-hero-crosshost/host-analyzer/recheck14-analysis

python3 work/native-pq-hero-crosshost/compare.py \
  work/native-pq-hero-crosshost/host-analyzer/sdk26-13-analysis/analysis.json \
  work/native-pq-hero-crosshost/host-analyzer/recheck14-analysis/analysis.json \
  --output work/native-pq-hero-crosshost/recheck-crosshost-result
```

如果原report搬家，compare.py支持 `--report13/--report14` 指向字节不变的真实report并验证它与analysis保存的SHA相同。脚本检查report真实OS字符串与expected OS；两侧atlas spec/analyzer版本及Pillow/LittleCMS版本须相同。不会制造尚未采集的宿主数据，不会把旧SDK13当成新SDK same-binary证据。

每相位、named/custom、10patch、RGB通道分别计算：

`Dhost = ICC-normalized mean(hero) - ICC-normalized mean(body)`

`cross-host residual = D13 - D14`

保留每宿主body/hero/上下oracle的实际均值，另列 `body−own oracle-top`、`hero−own oracle-bottom` 控制残差；输出signed逐patch差值及其绝对均值/最大值。汇总是**patch均值残差**统计，不是整幅图pixel MAE。单位是8-bit encoded sRGB codes/255，不是nits。没有拟合、灰阶列对齐、跨宿主rawPNG相等要求或预设等效阈值。

比较脚本不独立验证same-binary身份。report中若有binary hash字段只作为原记录携带；root须保留独立构建/传递验证。显示ICC、headroom、像素倍率和rasterization都保留为上下文，`D13−D14` 非零或为零都不能单独证明某个原因、全UI等效或flight lifecycle。这里仍只是from==to、固定320×180的snapshot/draw端点，不涵盖进入/离开、几何动画、隐藏恢复、retarget/reversal或High。
