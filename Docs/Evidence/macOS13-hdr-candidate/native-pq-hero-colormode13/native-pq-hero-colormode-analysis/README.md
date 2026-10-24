# ImageRenderer.colorMode：default / extendedLinear 离线结果

Root 依次提供两次真实 macOS 13.7.8 (22H730) 采集后，本目录使用同一个冻结 analyzer 分别完成 68 组分析，再与旧 archive13 及实际 macOS14 基线作比较。**default 控制逐 ROI 完全复现旧13；extendedLinear 仅产生很小的 hero 像素变化，主要 cool812 跨宿主残差保持原值，不能据此判定视觉等效。** 本 agent 只读取 report/原 PNG，没有编译、运行 UI/CI、读取 NSImage、安装依赖或更改原输入/归档。

## 输入和边界

- default：`../native-pq-hero-colormode/runtime13-default-control/report.json`，记录 environment/selected=`default`、assignment_requested=false；原窗口 1.710865 秒。
- extended：`../native-pq-hero-colormode/runtime13-extendedLinear/report.json`，记录 environment/selected=`extendedLinear`、assignment_requested=true；原窗口 1.618328 秒。配置字段不是额外 setter 执行计数。
- archive13：`../../outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/native-pq-hero-baseline13/analysis/baseline-analysis/analysis.json`。
- 实际14参考：`../native-pq-hero-crosshost/host-analyzer/sdk26-14-analysis/analysis.json`，其归档为 `macOS14-hero-snapshot-40080838898`。实际 OS14.8.9 (23J631)，ROI320×180 pixels；本次13 ROI640×360 pixels，均为320×180 points。

两次13 runtime均记录 front439→439、normal三项均false、cache unchanged、live Metal=0、两phase各5个连续相同buffer、current/potential headroom=1/2。离线核对 report/PNG hash，并以 PNG 实际 ICC 归一化；上述运行状态由保留 runtime report/source/log 支持，本分析没有重新测量缺失的原 buffer 或 native object。

`provenance.json` 保留所有输入实际解析路径、字节数、SHA及运行配置；没有复制原PNG。default control 与 extended 使用本轮夹具；14参考使用此前基线 binary，不能写成本次 colorMode 的 same-binary 跨宿主试验。

## default 控制与几何

`default-vs-archive13/comparison.json`：两phase×六ROI，**12个raw及12个ICC→sRGB normalized均完全同像素**。

`mode-comparison.json`：default→extended 的全部12个ROI实际 frame、两phase的capture/root/window几何逐值相同。两phase的 body-named、body-custom、oracle-top、oracle-bottom共8个ROI在raw/normalized均exact；两phase各自重复同一结果。变化仅见两个flight panes：

| ROI（两phase结果相同） | 不同RGB像素 /230400 | raw全RGB MAE / max | normalized全RGB MAE / max |
|---|---:|---:|---:|
| flight-named | 1394 | 0.002060185 /1 | 0.004438657 /3 |
| flight-custom | 2475 | 0.003699363 /1 | 0.007952836 /3 |

两次模式各自的六ROI跨phase均raw/normalized exact。body只与同排 oracle-top exact；不能推成上下oracle都exact。完整68组比较和10patch/ramp结果分别在 `default-analysis/analysis.json`、`extended-analysis/analysis.json`，各自的 `ramp-column-means.json.gz` 保留全部原列均值。

## 相对实际14的同算法残差

每patch/channel先计算 `Dhost=mean(hero)−mean(body)`，再比较 `D13−D14`。以下单位为编码8-bit sRGB code values（范围0–255）；是10patch×RGB均值残差统计，**不是整窗口/整图pixel MAE，也不是线性光或nits**。不跨1×/2×硬resize，不拟合图像、ramp或阈值。

| phase/source | default残差绝对均值 | extended残差绝对均值 | extended−default | 最大残差（两者相同） |
|---|---:|---:|---:|---:|
| p0 named | 5.210863095 | 5.204916438 | −0.005946658 | 112.616328984 |
| p0 custom | 5.223883929 | 5.213095238 | −0.010788690 | 112.618732830 |
| p1 named | 5.224399038 | 5.218452381 | −0.005946658 | 113.048334478 |
| p1 custom | 5.236956273 | 5.226167582 | −0.010788690 | 113.048334478 |

在这项指标中均值仅微降，最大残差没有改善。默认与extended的完整实际13/14 patch均值、signed H−B、signed跨宿主残差分别保留在 `default-vs14/comparison.json`、`extended-vs14/comparison.json`；不能把14 hero等同于14 body。

以下为代表patch的实际normalized RGB均值，保留6位，完整精度在JSON。13两phase值相同；14分别列p0/p1。

| patch/source | 13 body | 13 default hero | 13 extended hero | 14 p0 body / hero | 14 p1 hero |
|---|---|---|---|---|---|
| cool812 named | (92.488925,255,255) | (254.891999,254.899038,254.887878) | 同default | (118.645261,255,255) / (168.432005,254.898352,254.883929) | (168,255,255) |
| cool812 custom | (92.488925,255,255) | (254.891999,254.899038,254.887878) | 同default | (118.645261,255,255) / (168.429602,254.901786,254.888049) | (168,255,255) |
| red812 named | (255,0,0) | (255,0,16.907881) | (255,0,16.729481) | (255,0,0) / (254.890797,0.133585,0.118819) | (255,0,0) |
| red812 custom | (255,0,0) | (255,0,17.294729) | (255,0,16.971068) | (255,0,0) / (254.891140,0.131525,0.120536) | (255,0,0) |
| white203 named | (228.929773,228.934667,228.917239) | (254.893544,254.899468,254.888994) | 同default | (228.925481,228.939217,228.915522) / (254.890797,254.893544,254.883242) | (255,255,255) |
| white203 custom | (228.929773,228.934667,228.917239) | (254.893544,254.899468,254.888994) | 同default | (228.929945,228.935440,228.922734) / (254.891140,254.898695,254.887706) | (255,255,255) |

cool812 的13 R通道 H−B=162.403073，两模式相同；14 p0为49.786745(named)/49.784341(custom)，p1为49.354739。这正是保持原值的最大跨宿主差；本次没有推断唯一原因。red812的hero B仅微降，white203保持原值。

## 算法、复现与文件

- `analyze.py` SHA256=`98243090f0b45fe18baed3d89d4e382c7d8f7c02662a930cfda8c87c3b0f39d4`，与原冻结版本逐字相同。
- `atlas-rois.json` SHA256=`39ca622a45c0120d08e90daa7a17a0145be1b79485decb4619a0e5a3f23cadaf`。
- `compare_crosshost.py` SHA256=`c151280eb0ced6501197d56e7a8f229d73d4679ab43e931edde68c9312be0d0a`，与已运行H−B算法逐字相同。
- `compare_default.py`核对原report hash/模式/13底线、analyzer/spec/versions和各phase/ROI的hash/shape，raw与normalized分别比较。
- `compare_modes.py`只离线重读两份实际PNG，复用冻结analyzer的frame解析及RGB指标函数，核对crop hash与原analysis；不更改冻结算法。输出同宿主逐ROI几何/像素差和两份已算跨宿主结果的对比。

现有Pillow12.3.0/LittleCMS2.19，使用每PNG内嵌ICC→sRGB（perceptual intent0，flags0），另保留raw profileRGB。640×360源atlas10patch内区112×104、ramp632×80；按report实际ROI严格整数映射，14的1×为56×52和316×40，不重采样图片。两报告没有ICC warning。

可复现的完整命令在 `provenance.json`；输出必须指定尚不存在的本目录子路径。原report搬家时，default比较器接受 `--archive-report/--default-report`，crosshost比较器接受 `--report13/--report14`，仍要求原字节SHA相同。所有输入只读。

`SHA256SUMS`覆盖本目录脚本/spec/README/provenance和全部结果，不包含它自己。没有重复原截图、app、编译缓存或无用临时产物。

Exit0仅代表离线计算成功。from==to固定尺寸端点不代表enter/leave、弹簧几何、hide/restore、retarget/reversal、完整flight lifecycle或应用整体已通过。此处不设自动等效门槛，不将diagnostic合入产品。
