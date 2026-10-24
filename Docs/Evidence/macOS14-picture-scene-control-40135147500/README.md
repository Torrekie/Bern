# 完整 Picture Scene 的未插桩 macOS 14 control

CI [40135147500](https://github.com/Torrekie/Bern/actions/runs/40135147500) 成功：复用已交付的完整 9dd Showcase，首卡 **125pt**、HDR 卡 **147pt**。这完成了真实 Scene 布局观察的前置重现门槛；macOS 13 的对应卡高差、内部环境和 observer 影响仍待验证。

## 精确来源与运行

产品 source `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`，原 build run `40066468884`，原 build harness `1c4ef533cc62bb57ef73cfd98df13434bd40b304`；本轮 capture harness `d72cb5f9bcec8a90fa394bca1060ed0f392ba8f3`。内层 `showcase.tar.gz` SHA256 为 `fb5fd66e8247d1adada07411cb8368de716cc8e251f6ecf70968678b3d74662b`。外层 build artifact ZIP、内层 tar 和本轮 evidence ZIP 的 digest 分别见 [独立复核](independent-review/review.json)，不互相替代。本机没有下载 App/tar；本轮只下载约1.02MB证据 ZIP，工具解包后移除了 ZIP。

原应用用 Swift6.2.4/SDK26.2/min13/arm64 构建。本轮仅在 macOS14.8.9(23J631) 执行，未重编、重签或插入内部 observer。现成 `macos13-compare.yml` + `macos14-reference.swift` 保留原英文/en_US、920×668外框及 Controls→Text/Buttons/Inputs/Query→Layout 页面和动作顺序。实际 Layout 为 own PID1853/window24、唯一 main#1、active、1×、920×668 PNG，normal三项均false；完整原始元数据见 [raw/result.json](raw/result.json)。

## 原始截图与测量

13张选定截图均逐文件等于历史 B14 的对应 PNG，见 [完整哈希对照](historical-full-slice-comparison.json)。这指13张截图，运行系统是14。历史 B14 产品 source 为 `fa820f706e5faf1bae8b8f07e23545842a1648b7`；源码和编译 SDK 不同而所选文件相同，不证明全部功能或系统差异的因果。

[图片页原图](raw/images-layout-light.png) SHA256 为 `dfe053e307e033d0a4e583a88d34a4b60f428318f63e1954a500f14bb2016780`，与历史 B14 原图逐字相同。两卡完整边缘可见：首卡半开边界 `[161,98,900,223]`，HDR `[161,321,900,468]`，高度125/147pt。独立 [测量与说明](measurement-review/README.md) 复用旧 ICC→sRGB、15 ROI 和 x800 分段算法，全部 ROI/分段均与旧 B14 一致；x800 扫描本身不是通用 native-card bbox detector。原采集器在 Layout 只等0.8秒，没有五帧稳定门槛。

原 collector 80条 CLI 中，两次新进程首次 sessions 轮询返回3，之后各自成功就绪，其余78条均0。[root validation](control-validation.json) 保留最初误设“所有status0”的检查修订；这不是应用采集失败或重跑。该文件的边缘待测措辞属于测量前记录，最终测量见上；`artifact_archive_sha256` 在其中特指内层 tar。最终 [独立复核](independent-review/review.json) 未发现阻断性不一致，并交叉核对本机原件16成员和既有交付 map。

## 下一门槛与清理

[源码差分索引](source-delta/README.md) 确认页面、Scene、FormRows/Grid 等区块保持；共享 BernImage 包装仍有源差，未指定根因。先导出精确9dd实际生成的 BernGenerated.swift，再在同一生成树的 Form/首Grid row/HDR row 追加只读公开 background/anchor 环境与 resolved frame 观察。观察后首卡/HDR必须保持125/147；若改变，则记录 observer 影响并停止该环境解释。不新增 Scene、固定行高、字体补偿或负padding。

[清理收据](cleanup.json) 记录：13个新下载 PNG 全部逐字核验后改为指向既有原件的相对符号链接，去除1,089,769逻辑字节重复文件；私有work目录移至本唯一归档并保留work别名。首次移动只读准备目录遇到EACCES，恢复仅临时增加本任务目录owner-write，逐项核验后恢复原mode；文件内容未变。磁盘/APFS实际回收量未测量。原始CLI输出、环境、日志、测量、review及全部可解析原PNG内容保留。
