# Deferred CGImage metadata：same-binary 13 / 14 离线结果

新binary在13、14的各68组端点比较已完成。新13对original13、新14对历史40080838898均为**两phase×六ROI的12个raw与12个ICC→sRGB normalized全exact**；10patch/ramp差也全部为0。本轮same-binary跨宿主的全部signed H−B patch残差逐项复现历史结果，主要色差仍存在。没有修改旧归档/harness/product/main docs、编译、UI/CI或读取任何NSImage/native pixel provider；仅读取保留report/PNG并离线解码。

## 输入与同一binary来源

原输入：`../native-pq-hero-cgmetadata-ci14-40086541042/runtime13/report.json`、`runtime14/report.json`及各自两PNG。`provenance.json`记录实际解析路径、每个report/PNG/analysis的字节数和SHA；所有原PNG重新验证报告hash。没有复制原PNG。

保留package binary纯文件哈希、root-package-verification、13 run-receipt及14 binary-sha256.txt均为：

`e4b389d9b91035b42add5725358ae3404ac901a1da5786c4767291e47ac7be14`

这些支持同一分发binary在两host运行的记录链。本离线任务没有再次运行签名/Mach-O工具；构建、分发、执行和signature证据仍由该原采集目录保留。`root-control13.json`也核对其candidate report SHA，但该控制本身不独立证明same-binary。

历史14参考是 `../native-pq-hero-crosshost/host-analyzer/sdk26-14-analysis/analysis.json`，归档于 `macOS14-hero-snapshot-40080838898`。它与新14属于不同采集时间、进程/VM上下文及不同binary；本次逐ROIexact是实际观察，不能扩展为普遍零observer效应或唯一根因证明。original13参考是 `native-pq-hero-baseline13/analysis/baseline-analysis/analysis.json`。

## 格式、ICC、scale与环境

实际OS：13.7.8 (22H730) / 14.8.9 (23J631)。每host的两个actual snapshot primary以及独立cleanup记录均保留在原report；`metadata-context.json`只去掉重复base64，并核验所有profile严格base64解码后的长度和SHA。

| 项目 | 13 | 14 |
|---|---|---|
| Snapshot CGImage | 640×360 / row5120 | 320×180 / row2560 |
| 实际ROI | 320×180pt，640×360px /2× | 320×180pt，320×180px /1× |
| Snapshot格式 | 16bpc、64bpp、float | 相同 |
| Snapshot space | kCGColorSpaceExtendedSRGB / RGB3 | 相同 |
| Snapshot标志 | wide gamut / extended=true；PQ、HLG、2100TF=false | 相同 |
| Snapshot导出ICC | 3144 bytes | 相同字节SHA |
| Capture current/potential headroom | 1 /2 | 1 /1 |
| Front PID首尾 | 1390→1390 | 332→332 |

Snapshot ICC SHA为 `2b3aa1645779a9e634744faf9b01e9102b0c9b88fd6deced7934df86b949af7e`。除width/height/bytes_per_row外，两host的primary descriptors逐字段相同；**各host内部**primary与cleanup descriptor数组完全相同。两host的完整descriptor数组因尺寸不同，不能直接声称完全相同。

窗口截图的ICC与上述snapshot ICC是不同层：13 PNG embedded/capture ICC=`e2473ef48182e793b50bd21dd4d1d9b37d26b02b5a38508ded86d836ef9b64d4`，14=`3d40c076ef474f107eb2c08fa5cebe2546e836500f4029ded5db7de763eb5f55`。每PNG按其自身ICC→sRGB归一；无ICC warning。相同snapshot格式/ICC不代表相同pixel payload、窗口输出或宿主headroom。

两host均success、normal首尾三项false、activation0、cache深比较保持、live MTKView计数0，两个phase各5连续相同buffer。此处“无Metal view”并不推成所有底层框架未使用Metal。截图scale/headroom及原front/normal字段均在context保留；离线任务核对保留记录，不重新证明未保留的连续raw buffers。

## Same-binary signed H−B

每patch/channel `Dhost=mean(hero)−mean(body)`，跨宿主残差为 `D13−D14`。完整10patch原始body/hero/oracle均值与signed向量在 `crosshost-result/comparison.json`。以下是10patch×RGB均值残差的绝对汇总，单位为编码8-bit sRGB code values（0–255），不是全图pixel MAE、线性光或nits。

| phase/source | 13 abs mean H−B | 14 abs mean H−B | abs mean (D13−D14) | max abs (D13−D14) |
|---|---:|---:|---:|---:|
| p0 named | 19.973906822 | 14.951694139 | 5.210863095 | 112.616328984 |
| p0 custom | 19.986801740 | 14.951774267 | 5.223883929 | 112.618732830 |
| p1 named | 19.973906822 | 14.900675366 | 5.224399038 | 113.048334478 |
| p1 custom | 19.986801740 | 14.899908425 | 5.236956273 | 113.048334478 |

最大分量仍为cool812 R：13 body92.488925 / hero254.891999，D13=162.403073；14 p0 body118.645261，hero168.432005(named)/168.429602(custom)，D14=49.786745/49.784341；p1 hero168，D14=49.354739。没有把14 hero当作14 body，也没有拟合补偿或设自动等效阈值。

## 对照与完整输出

- `sdk26-13-analysis/analysis.json`与`sdk26-14-analysis/analysis.json`各保留冻结格式的68组比较、10patch和ramp；相邻gzip保留逐列均值。
- `current-vs-original13.json`：12 raw+12 normalized ROI全exact，同尺度比较的10patch/ramp指标全部0。
- `current-vs-historical14.json`：同样全部exact，所有ROI实际frame相同；不据此声称整PNG/所有系统状态相同。
- `summary.json`：上述布尔结果和四组残差汇总；全部signed patch rows已与历史跨宿主JSON逐项比较相同。
- `metadata-context.json`：实际scale、截图ICC/headroom、snapshot descriptor/ICC解码和same-binary来源。

13的body-named/custom均与同排oracle-top exact；14的named body与top exact、custom body有小差异，详见原68组。不能写成body与上下oracle均exact。13六ROI跨phase均exact；14flight跨phase的小差异照实保留，不用采集门槛筛掉。

## 冻结算法与复现

`analyze.py` SHA=`98243090f0b45fe18baed3d89d4e382c7d8f7c02662a930cfda8c87c3b0f39d4`；`atlas-rois.json`=`39ca622a45c0120d08e90daa7a17a0145be1b79485decb4619a0e5a3f23cadaf`；`compare_crosshost.py`=`c151280eb0ced6501197d56e7a8f229d73d4679ab43e931edde68c9312be0d0a`。三份与既有冻结文件逐字相同。

`compare_retained.py`仅作同OS同实际pixel-size比较，重读原PNG/ICC，复用冻结analyzer的RGB/patch/ramp函数，并核对crop hashes与原analysis；不改变每host68组格式。所有命令及输入指纹在`provenance.json`，须指定新的本目录输出路径。使用现有Pillow12.3.0/LittleCMS2.19；原PNG ICC→sRGB perceptual intent0/flags0，raw另存指标，不安装依赖、不resize/注册/拟合。

源atlas640×360，patch内区112×104、ramp632×80；严格按每report实际ROI整数映射，14的1×为56×52与316×40，没有跨scale重采样。`SHA256SUMS`覆盖全部当前源/报告文件，不包含自身；没有重复app/截图/编译缓存或无用中间产物。

本范围仍是from==to固定尺寸snapshot/draw端点，不验收完整协调flight、enter/leave、几何动画、hide/restore、retarget/reversal或物理显示。Exit0只表示离线计算完成；相同metadata与本轮控制exact均不足以确认全应用视觉等效或唯一原因。
