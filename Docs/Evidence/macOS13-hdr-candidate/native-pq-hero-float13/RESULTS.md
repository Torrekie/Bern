# macOS13 原始 hero snapshot float：本机 off/on 证据

本目录保留已完成的同机控制与原始 CGImage provider 字节。两次采集及冻结分析器均成功；这一步确认能在原窗口采集和清理结束后导出实际 snapshot 的原始数据，不判定13/14差异的原因，也不验收完整 hero flight 或物理 HDR。

- `fixture/`：不可变 v2 基线、实际组合源码、SDK14.2局部适配、精确差异、构建指纹、off/on 两份报告、四个原始 PNG 及两份完整 `.bin`。
- `analysis/`：13个冻结文件，包括分析源码、合成验证、实际 whole-buffer 结果与两阶段历史清单；原有“尚无真实输入”等说明保留其准备时点含义。
- `controls/`：原有比较脚本及 v2→off、off→on 的实际控制结果。历史 smoke 也原样保留，但当前结论使用具名两份实际结果。
- `validation.json` 和 `archive-provenance.json`：归档时的独立离线哈希、布局、PNG/ICC、报告与来源核验。未重新运行图像比较、分析器、应用或编译。

## 实际采集

同一 arm64/min13、SDK14.2、Swift5.9.2/Swift5模式 `-O -j2` 可执行文件的 SHA256：

`84efaed4e15e9f24b95d84d0e352131ab3f418ed9e42e158d53c9e0b4f885313`

保留的 build fingerprint 记录 strict ad-hoc/linker signature 校验成功。可执行文件和模块缓存未复制进证据目录，work 原件留给 root 清理；构建日志、命令入口和指纹均保留。

| 实际字段 | off | on |
|---|---:|---:|
| PID | 82459 | 89757 |
| 前台 PID 首尾 | 9292→9292 | 9292→9292 |
| 窗口秒数（上限7.9） | 1.839629054 | 1.928040028 |
| 外层进程秒数（上限15） | 2.848413125 | 2.593056458 |
| primary / cleanup 调用 | 2 / 2 | 2 / 2 |
| provider copies | 0 | 2 |
| 留存图像峰值 / 导出后 | 0 / 0 | 2 / 0 |
| 原始记录 / 总字节 | 0 / 0 | 2 / 3,686,400 |
| 导出秒数 | 0.000029750 | 0.033125417 |

两次 OS13.7.8、exit0、success=true；normal首尾三项全false、activation0、cache保持。两阶段各至少5个连续相同 WindowServer buffer，own PID/window身份有效，窗口 nonkey/inactive；无 MTKView、coordinator flight 或 timer。上述来自实际报告，不沿用早期实验的前台 PID。

## 原始数据与控制结论

两个 snapshot 均为640×360、rowbytes5120、16bit float/RGBA64、bitmap4353、16Little4096、premultiplied-last alpha1、pixel-format0。每份精确1,843,200字节，总量小于4MiB，且与对应 primary metadata 的布局一致；没有转换、重标记、裁切或省略 provider 字节。

- `fixture/runtime13-on/snapshot-named.bin`：`edc1c9380bbf86e35c9830359428b715953cccd0f5952b10ade269923a6a2469`
- `fixture/runtime13-on/snapshot-custom.bin`：`314b9001c1c47eea9f39a23fd6c697d1bcb66cfcda83dbc01153149c2d36e67c`

原有 v2→off 和 off→on 控制结果各记录12个 ROI raw/ICC→sRGB完全一致（MAE/max0）。归档核验重新确认了控制结果对应的报告 SHA、12个唯一区域和零指标；未再次执行 ICC 比较。四份本轮 PNG 的文件 SHA 也完全相同。实际 off/on 结果支持本次画面控制，不能推出普遍零 observer effect；on确实延长了原CGImage生命周期并在清理后读取provider，引用计数归零也不等于证明对象已经析构。

冻结分析器仅输出未定方向的 whole-buffer binary16 数值：RGB含负数和大于1值；全部分量有限，两源每个alpha均精确1。精确数值在 `analysis/RESULTS13.md` 和 `actual13-summary.json`。上下行方向仍未独立证明，未输出语义 patch 数值、不换算nits、不clamp/unpremultiply、不作跨OS匹配或归因。

## 清单范围与可复核性

`fixture/SHA256SUMS` 是原27项**源码准备**清单，刻意不覆盖后来构建/运行结果；`analysis/SHA256SUMS` 是原6项准备清单，`analysis/ACTUAL13-SHA256SUMS` 覆盖其12项实际分析内容。三份历史清单均逐字保留并通过核验。原报告中的绝对work路径与源码说明保留原始来源，不能当成归档后文件的现存路径要求。

顶层 `SHA256SUMS` 才是本次完整归档的最终清单，覆盖除其自身外的全部文件。所有内容均为 regular files；字节完全相同的PNG仅在本归档内部共享inode，保留全部路径与字节，未与work原件建立链接。未修改work、产品、harness、Acceptance、git index，未执行编译、UI或CI。
