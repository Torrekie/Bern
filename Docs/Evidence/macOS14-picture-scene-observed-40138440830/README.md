# 完整 Picture Scene：macOS 14 只读观察

[CI40138440830](https://github.com/Torrekie/Bern/actions/runs/40138440830) 的构建与运行均成功。固定9dd完整应用保留原Scene、路由、Form及Grid，只在生成的Layout组件加入21个透明背景探针和187行公开API观察helper；未改变产品布局。与[无插桩control](../macOS14-picture-scene-control-40135147500/README.md)的13张选定原PNG全部逐文件逐字相同，首卡125pt、HDR卡147pt保持。这里13是文件数量，系统为14.8.9；Layout仍为原0.8秒等待，不是五帧稳定采集。

| 身份 | 实测值 |
| --- | --- |
| 源码 / harness | `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0` / `c9867c223b2efaf53a82214edd352b988c2952c9` |
| 工具链 / 最低版本 | Swift6.2.4、SDK26.2；GUI/CLI arm64、min13.0，实际严格签名检查通过 |
| 编译输入 BernGenerated.swift | 106494B，`f4cac6965e72f454c257a30420ca5966d2b9afc012d1e9e264c20ed947b706d2` |
| 原GUI / CLI | `c1d27a0435bd145f08a098adaaf22c6718c1192da15367456afb7ff151c4c12c` / `963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170` |
| Layout原PNG | `dfe053e307e033d0a4e583a88d34a4b60f428318f63e1954a500f14bb2016780` |
| 实际环境 | 14.8.9(23J631)、normal三项false、en/en_US、920×668外框、1×、活动自有窗口 |

[运行原始记录](run/raw/result.json)含80条CLI命令：两个独立浅/深色进程各首次sessions/status3在ready前恢复，其余78条为0，18个checks全通过。独立[几何复核](geometry-review/README.md)重核原ICC、固定ROI与完整可见边缘；[来源复核](native-review/README.md)重构精确编译输入、55个Git输入、tar16成员，并实际执行codesign/lipo/vtool。build/capture完整job日志在run/；outer ZIP的CI摘要与本机inner tar摘要分开记录，没有把两种容器混为同一个文件。

[原始观察包](run/raw/observer/picture-observer-1926.json)为286397B、49条事件，覆盖21标签，PID1926/window28绑定Layout记录。[事件复核](event-review/README.md)保留全部first/last与边界：Images Grid先记录719×105，末次resolved为719×109而同条原生探针仍高105；最近graphics祖先高125。HDR Grid高127、祖先147；末期SwiftUI global y加4时，原生坐标尚未同步。所有10个公开环境字段在各探针间相同。

这些都是callback记录，`end_state=not_observed`始终有效；不能把最后一条当稳定终态、同步呈现、proposed size或根因。字体inherited-nil描述探针环境，不能替代Text实际字体测量。截图一致只证明本次选定画面保持，不扩充为所有交互和时序无观察影响。

同一个SDK26.2/min13观察产物随后在[本机13完整A2/B3对照](../macOS13-picture-scene-observed-9dd/README.md)成功运行，9张PNG等于原版；13首卡仍129、HDR147。未加负padding、固定高度或配色补偿，整阶段仍未通过。

13张重复PNG已核哈希后改为指向control原件的相对别名，[归档布局](archive-layout.json)保留映射。CI tar、提取App/CLI和私有签名副本在两轮独立实际来源检查及13运行完成后清除；[清理收据](../macOS13-picture-scene-observed-9dd/cleanup/retired-artifacts.json)保留文件摘要和逻辑字节计数。原交付App/CLI保留；未声称APFS物理回收量。
