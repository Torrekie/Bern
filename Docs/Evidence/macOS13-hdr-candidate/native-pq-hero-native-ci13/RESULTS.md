# macOS13固定nativeCI转换：阴性结果

公开Core Image转换仅让hero端点产生很小的像素变化，未改善与实际14参考之间最大的cool812 R残差。本实验停止于诊断，不合入产品，不追加模式矩阵、拟合曲线或14 CI。body及oracle保持原像素，不能由此推成完整flight或应用等效。

## 精确来源和实际构建

夹具来源为`b08db54e01ac2ec54fb84e6f2a70041f1f4c3604`提取链，image/hero片段与9dd相同；保留原SDK14 gain-map编译guard和unused-clock failguard。准备的25项清单SHA为：

`3935f2c5c781786d5449ca4df6b53e1228bd25cb1665b91a10f233cc17d34632`

25/25项归档前仍匹配。该清单、source-provenance和准备README/static-validation是历史准备事实，不能冒充最终运行状态。归档保存其原字节，实际后续状态由本页、build/runtime receipts和最终顶层清单说明。

root实际执行`root-build.sh`，共享`../native-pq-hero-colormode/modules`；**prepared build.sh未执行**。实际entry SHA=`3d219518d3cc16a3abc3bfe5c4b57dca1dffab5b58a9e1c862d8b66aa46ea6d2`。构建为Swift5.9.2/SDK14.2、Swift5 language、-O/-j2、arm64 min13，环境、警告日志、原命令源及fingerprint均保留。fingerprint的17/17文件哈希匹配；它把prepared build.sh作为source纳入，并不证明执行该文件。

保留binary在归档前纯文件哈希与fingerprint、两run receipt及root最终verification均一致：

`b10872e101db7bdec3fe34eeee57d1d50cc63439d731b86a6f64f846d86ce6d1`

strict signature和Mach-O结果读取root原记录；本归档未重跑工具链或UI。binary未复制入本目录，签名/编译/运行来源由保留fingerprint及收据证明；归档不能再从不存在的binary重验签名。

## 两次实际运行

| 项目 | default control | nativeCI |
|---|---:|---:|
| 实际OS | macOS13.7.8 (22H730) | 相同 |
| Exit / success | 0 /true | 0 /true |
| 窗口秒数 | 1.622786045 | 6.790791988 |
| 外层进程秒数 /上限 | 2.216220459 /15 | 8.953642500 /15 |
| CIContext | 未创建；sources0/outputs0 | 已创建；sources2/outputs4 |
| Front首尾 | 1390→1390 | 相同 |
| normal三项首尾 | 全false | 相同 |
| cache深比较 | 未变 | 未变 |

两次原始数据均为两phase，各5连续相同buffer；10个samples均无MTKView、无coordinator flight/timer、nonkey/inactive，own PID与receipt对应，原PNG hash全部匹配。current/potential headroom=1/2；ROI320×180pt/640×360px，默认与selected全部12个报告ROI frame相同。原collection7.2秒/window watchdog7.9秒、外层15秒门槛保留。

normal_after是原defer在窗口teardown前读的字段，frontmost_after在teardown后读；没有独立进程退出后的桌面normal探针。归档前仅对自有可执行路径作只读匹配进程检查，未发现仍运行实例；这不等于所有文件writer或整个桌面状态审计。

selected实际两源都采用`actual_cached_legacyStandardPQImage`。固定SHA锁的opaque/up640×360、fill320×180pt@2×/corner0路径，执行`CIImage`显式input colorSpace→`CIContext.createCGImage(.RGBAh, extendedSRGB)`，随后沿原`NSImage(cgImage:size:)`及Flight.draw。无filter、exposure、手写tone mapper、硬拟合或resize。现有no-Metal gate仅计MTKView，不能推成CIContext内部不用GPU/Metal。

四条nativeCI输出均640×360、16bpc/64bpp float。报告在原teardown后组装；数组没有每条phase/cleanup标签，不能仅靠四条记录给后两条精确定时，或把它们当四个独立测量phase。只从固定两PNG端点作比较。

## 像素与14参考

default对original13 baseline，两phase×六ROI共**12个raw与12个ICC→sRGB normalized全部exact**，同时没有创建CIContext。归档任务重新读取原PNG、按自身ICC转sRGB，并逐ROI复算，结果与root控制一致。

nativeCI对同一original13 baseline仅hero变化；body-named/body-custom及两oracle在两phase均raw/normalized exact。两phase的变化值相同：

| ROI | normalized全RGB MAE | max code delta |
|---|---:|---:|
| flight-named | 0.010739293981481482 | 3 |
| flight-custom | 0.018699363425925927 | 3 |

这两值是**同宿主selected对原13的fullRGB pixel指标**。它们不等于下表跨宿主patch均值残差。全部raw/normalized逐ROI复算结果在`archive-validation.json`；原root核对JSON仍逐字保留。

`analysis/nativeCI-analysis/analysis.json`保留冻结算法的完整68组、10patch/ramp，gzip保留ramp列均值。`analysis/nativeCI-vs14/comparison.json`用既有实际14参考，在各自实际1×/2×采样下计算每patch/channel：`Dhost=mean(hero)−mean(body)`，再比较`D13−D14`。不跨host硬resize、不拟合、不设自动pass。单位为编码sRGB code values（0–255），不是nits、线性光或全图pixel MAE。

| phase/source | default abs mean(D13−D14) | nativeCI abs mean(D13−D14) | max abs残差（不变） |
|---|---:|---:|---:|
| p0 named | 5.210863095 | 5.197985348 | 112.616328984 |
| p0 custom | 5.223883929 | 5.198111264 | 112.618732830 |
| p1 named | 5.224399038 | 5.211521291 | 113.048334478 |
| p1 custom | 5.236956273 | 5.211183608 | 113.048334478 |

均值微降，cool812 R最大残差保持原值。这不足以支持产品采用。14参考来自另一采集/VM/binary；本selected nativeCI没有在14运行。记录snapshot输出请求和标量也不能推成其payload、profile或主差原因已经被证明。

## 因果及范围限制

准备README原文的“eager-profile-observer disturbance”保留于历史source副本，但**原因未知，未证明由eager observer导致**。本实验既不作该因果归因，也不把之后metadata控制exact扩展成普遍无observer效应。归档顶层README已给显式修正，不能脱离该修正引用准备版措辞。

这是same-image from==to、固定尺寸端点，未验收完整coordinator flight、enter/leave、几何动画、hide/restore、retarget/reversal、其它orientation/alpha/HLG/gain-map输入、真实物理输入或完整应用。没有推进macOS11/Swift5.3、ObjC或iOS。

## 清单和清理边界

`fixture/`与`analysis/`是54个有界非binary文件的逐字副本，包括4张原PNG；所有copy前后SHA一致。compiled executable528304字节被排除，modules/cache未复制。工作原件全部保留，未替root清理。

顶层`SHA256SUMS`覆盖本目录所有现存文件（除自身）；子目录原清单保留各自历史范围。`archive-provenance.json`列全部copy来源、哈希和排除项；`archive-validation.json`列source/fingerprint、原PNG、独立解码ROI复算、runtime及postrun限制。Acceptance、产品、harness、索引及发布均未更改。
