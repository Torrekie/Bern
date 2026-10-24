# 精确9dd真实生成源与观察器准备

CI [40136458675](https://github.com/Torrekie/Bern/actions/runs/40136458675) 成功导出真正 `BernGenerated.swift`：**95,129B**，SHA256 `1d1da3167d9437b2305df1a39099f01f693b1b674f13cd2e4d88bffec2c52083`。它同时包含真实 `BernApplication: App`、Window/WindowRoot、NavigationSplitView 和页面；没有另包 Scene。`layout_page` 在1268–1409行，见 [原生成源](raw/BernGenerated.swift)。9dd本来就没有单独生成的BernApp.swift，没有用模板冒充该文件。

## 生成证据

产品 source `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`，tree `89a5cda2ae6e47b9f1228abde0ec493b617f6a2a`；harness `213b515df0834d73778fe49cd4ad7dcf97d59686`。macOS15.7.9、Xcode26.3/Swift6.2.4/SDK26.2、Rust1.99/jobs2；生成目标配置是swiftui-modern/min13/release，**本轮没有编译Swift产品或执行应用**。

一次诊断hook仅加入精确CLI的generated-files写完后、target.plan之前；环境值1时记录标记并返回。原CLI SHA `63af68fa7f763b118ca34ed432b0f1b9fdfa2b3190582ebde747135303d0fa64`；[实际补丁](raw/cli-generate-only.patch)、原/后哈希、55输入和全tree来源均保留。生成器、模板、Showcase声明/资源未改；两个原产品可执行路径要求不存在。

Rust宿主工具按需编译1m46s，之后检查11组件/2windows并生成20files(20changed)，rc0、标记恰1。cached-before恰有同SHA的旧生成源；准备步骤记录后清除唯一target/bern/macos_modern目录，再得到20changed，支持实际重新生成，不能仅用“cache同hash”替代此链。Rustcache仅restore，没有保存诊断内容。完整生成日志仅2720B，未截断；[独立复核](independent-review/README.md) 检查了joblog、CLI补丁重构、55项Git9dd输入及原7成员清单，未发现阻断。

## 下一次真实Scene观察

[未插桩完整14 control](../macOS14-picture-scene-control-40135147500/README.md) 已重现125/147pt。这里的 [精确补丁](observer-preparation/exact-patch/README.md) 只追加21个form/grid/column/image/caption背景modifier，移除插入后95129原字节完全恢复；没有改Scene、children、Section、FormRows、图片、字体、padding或行高。候选不含helper时SHA `f152c30b1ed4e3107c7198db2652c536ea0f5cddf81a046ecc9b0fed0ea47c10`。

[公开观察helper](observer-preparation/helper/README.md) 187行，SHA `14532e7960a7138ae3be48b26fe08ecb0f0d6b347e6cd7faa76be08eb01709da`。其 [本机独立typecheck](observer-preparation/typecheck/result.json) 用现有Swift5.9.2/SDK14.2/target13通过、零诊断、没有启动UI；71个临时cache文件/49,618,668逻辑字节已删除。完整Swift6产品构建和macOS14/13实际观察仍是后续门槛。canonical诊断代码在`.github/scripts/picture-scene-observer/`，保留原target.plan；静态package review和workflow草稿均归入本准备区，不当作已运行。

实际记录为十项probe继承环境和公开resolved坐标的有界callback样本：最多256条/512KiB/6层祖先，同步I/O可能影响主线程。它不报告稳定终态，不解析Text内部font/proposed size/native card边缘；无输出env也仍存在背景modifier，因此不能冒称关闭export等于原UI。必须在完整原路径/normal/英文/920×668上独立检查所有必需labels、原PNG与首卡/HDR仍125/147；若改变，停止环境解释。原collector Layout等0.8秒，未增加稳定帧门槛。macOS11/Swift5.3/Objective-C/iOS阶段保持暂缓。

## 保留与清理

本机仅下载18,541B的source evidence ZIP，解包后传输ZIP已删除；没有下载App/tar/binary/Rustcache。[清理收据](cleanup.json) 记录旧私有helper草稿5文本/17,898B的删除，canonical已审查脚本在Git9830中保留。原源、实际补丁、输入、日志、review与这次必要准备移至单一归档，work仅保留别名。模块cache清理另见typecheck收据；均不据此声称APFS实际回收量。原始unified patch的空白context保持，避免改动原artifact。
