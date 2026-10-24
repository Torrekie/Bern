# 同一binary13/14：真实hero静态端点的backing标量

[手动CI40095339192](https://github.com/Torrekie/Bern/actions/runs/40095339192)的build及measure均成功，harness `0590f49e095f1eabe7553816615c67d53ad171d2`，源码提交 `8b96b8c`。macos-15的Xcode26.3 / Swift6.2.4 / SDK26.2仅构建一次arm64/min13；原签名binary `86130e8e33a7170156d893147ff34878cd58409c284a06001a49c20b1b9b9d3f`随后在14与13各运行off/on，不在14重编、不在13重签。原28包成员/source map/归档hash/严格签名/min13已在13独立核查。

`same-binary-13-14/`保留构建环境、原源码、四进程/八原WindowServer PNG与ICC、原receipt/元数据及四控制JSON。CI成功只表示采集/schema门槛通过。父任务另实算了旧float-off→新backing-off、off→on，13及14四组各12ROI原始RGB与ICC归一全部精确相同；[独立标量摘要](analysis/README.md)核对控制记录及55输入hash，不声称又重算像素。每进程snapshot浮点导出始终off，新增原snapshot provider copy/retained peak/raw bytes均0。

| 采集后的公开属性 | macOS13 | macOS14 |
| --- | --- | --- |
| 两FlightView / FixtureRoot的contentsFormat | AutomaticAppKit | RGBA8 |
| 既有真实manager overlay / NSThemeFrame | RGBA8 | RGBA8 |
| layer class / scale | _NSViewBackingLayer / 2 | NSViewBackingLayer / 1 |

所有被记录view均wantsLayer=false、canDrawSubviewsIntoLayer=false、layer present、delegate为对应view。flight/root用draw路径，overlay/frame报告wantsUpdateLayer=true；完整祖先、geometry和原class/identity字符串见原JSON。13与14显示尺度、ICC、潜在EDR余量仍不同；不能从format字符串认定实际存储或唯一OS原因。局部旧SDK13与新SDK13非class标量一致，Swift模块/private class拼写差异如实保留。

四进程normal false、缓存不变、前台13为1390/14为309保持，noMTK/noFlight/noTimer/非key/非active/五stable均通过；window off/on在13为1.652236/1.663753秒，14为2.219975/1.777357秒。getter只在全部PNG与原final guards之后、原teardown之前运行，无法证明前PNG值持久或普遍零观察效应。夹具此时仍是root-mounted静态p0/p1同图端点，不是真实飞行动画、生命周期或完整应用验收。

本机后续已单独完成[root→真实existing overlay静态路由对照](../macOS13-hdr-candidate/native-pq-hero-static-route13/README.md)，13端点仍全部exact；14路由对照待完成。未给产品加入backing setter、颜色拟合、layer创建或其它未证实修复。

清理已用完的三binary、传输tar、复用module cache和逐字归档的work副本，见[收据](../macOS13-hdr-candidate/hero-backing-route-cleanup-20261024.json)。原CI包manifest保留已删binary条目及原hash、tar checksum保留取证；最终现存文件以 `SHA256SUMS.final`为准。`ci-preparation/`为准备阶段的冻结记录，不能当CI执行证明；实际执行由四份receipt/构建元数据支持。恢复源码到新的自有work后再构建，不向冻结归档写cache。
