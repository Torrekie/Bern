# 原始 e48 Film：macOS13 initial → 首次 Last

仅完成一次本机采集与有限离线对照；未修改产品，完整 macOS13 等效验收仍未通过。这里记录的是原 e48 port 在13/14的差异，14参考不是未修改上游 ffb 的独立验收。

## 实际输入与采集

- 原 Gallery/CLI：source `e48fff46b3a92a28465ad74295bd273a9d69af7d`，GUI `d44f051c…49126c` / CLI `31a75c0a…379f5`。交付产品SDK26.2/min13保持原样，没有重编产品。
- 本机13.7.8/arm64，普通辅助显示配置三项false，Light，own-PID active heartbeat；不声称物理输入送达。严格私有标识副本只改CFID/签名，40个Mach-O section及签名存储长度归一后的其余字节相同。
- 新外部采集器c4a1bd81…，复用原Film抓图/CLI与已审查的Frame前台/强kernel清理。编译用Swift5.9.2、请求14.2头文件、target13；实际helper内嵌SDK为13.0，不能写成14.2。外层95s/内层75s、CLI8s、原始buffer连续相等4次、terminal AX2s及defaults delete5s上限保持。
- 单次执行：wrapper0/10.444415s、collector0/8.599078s。仅Patterns setup PNG、Film initial与第一次Last两终态，没有First/repeat/resize/immediate矩阵或重试。27条CLI前两条sessions为3，其余25条为0；终态各6个唯一完整AXImage。
- 14数据前置固定到[40165343690参考](../macOS14-film-e48-endpoints-40165343690/reference.json)，SHA `8921655d…e8f50`；只比较其initial_setup与首次Last，未用重复Last替换。两端collector/startup/heartbeat/采样时序不同。

## 位置差异

[冻结方案](analysis-plan/README.md)和[离线结果](analysis/RESULTS.md)保留12张图的原screen/窗口origin-relative xywh及13−14逐字段原浮点差。initial四个未放大图的relative xywh精确相同；Madras/Glen的非零浮点差原样保留，没有按容差归零。

首次Last前五图的relative x均为−14.5pt，Windowpane为−14.504430837515656pt，其relative y/width/height差为−0.0029354298540056334 / +0.008861675031312188 / +0.0049846922050562625pt。这是本次观察，不是系统根因、可接受阈值或补偿量。14自己的首次与重复Last也不同，不能拿repeat结果代替本次比较。

两端capture均920×668pt；13原PNG1840×1336/2×、ICC4032B，14原PNG920×668/1×、ICC3300B。只读PNG/ICC元数据，没有像素解码比较、缩放、颜色转换、ROI或拟合。AX walk发生在PNG之后，二者非同时，稳定端点不代替完整动画。root另直接查看了原13两图和14首次Last图。

## 清理与独立复核

[collector](raw/report.json)与[外层watchdog](watchdog/watchdog.json)均success=true。PID25080/kernel1792908958.713508绑定到collector25075；Guard先恢复原PID1390/kernel1792598787.261710，再终止自有应用，termination0。post-inspect own=null且原前台kernel一致；exact-child、IPC、private prefs/state absence均通过，defaults delete0。历史其它cohort的5秒timeout false不变，也不声称CFPreferences daemon cache已刷新。

桌面lease8897460E…已释放，物理cursor位移0、配置不变；空overlay清除前visible=true与clear-only后两次false收据均保留。没有停止外来进程。独立[core源码](reviews/source/review.json)、[driver/实际准备](reviews/driver/review.json)、[runtime清理](reviews/runtime/runtime-result.json)及[离线数据复核](reviews/analysis/review.json)均按各自有限范围记录，不能扩大为整个移植通过。

自有私有App与两个helper在完整peer读取、精确hash及lsof空后退役4,197,882B；编译module cache先已退役49,735,931B，共53,933,813B逻辑文件，见[清理收据](receipts/cleanup.json)。原Gallery/Showcase四个交付可执行文件哈希不变。这个数字不代表APFS物理回收量。原始截图、JSON、源码与小收据保留。

## 范围与后续

本轮没有产品修复或采纳候选，没有新CI或下载。下一步先在固定源码中审查显式Last的程序化滚动/anchor与现有几何证据之间的关系；证据不足时明确缺口，不调整默认3、nearest、anchor、间距或套14.5pt补偿。此前停止的Row、颜色、搜索与Scene路线不重开。物理手势、完整动画、历史/resize以及其它macOS13 UI门槛仍未验收；macOS11/Swift5.3、Objective-C和iOS继续延期。

本目录是唯一canonical证据。work中的相对别名只供读取历史内容；不能通过别名执行脚本、构建或清理。SHA256SUMS列出全部最终普通文件（不含清单自身），原绝对路径保留采集当时含义。
