# 完整 Picture Scene：macOS 13 原版／观察版

真正9dd完整Showcase在本机13.7.8(22H730)完成A2原版与B3日志开启版对照，使用相同Collector/FocusGuard、原完整页面顺序、normal/en/en_US及920×668外框。9张原始2×PNG全部逐文件逐字相同，包含ICC；首卡129pt、HDR147pt保持。与[同一观察产物的14运行](../macOS14-picture-scene-observed-40138440830/README.md)的125/147相比，首卡仍多4pt，下一HDR卡下移4pt。没有加入产品布局或配色补偿，整阶段未通过。

| 运行 | 结果与范围 |
| --- | --- |
| [首次A](first-A-and-B-isolation/capture-A/result.json) | 9PNG及14个capture checks可用；清理因直接启动进程launchDate为null而失败，overall仍false。另存精确自有进程的手动恢复/退出收据，原失败未重写。 |
| [A2原版](A2-control-and-B-log-off/capture-A2/result.json) | 新身份；60命令、首sessions/status3随后恢复，其余59条0；14checks、normal开始/结束、自动清理均通过。 |
| [B日志关闭](A2-control-and-B-log-off/capture-B/result.json) | 21背景modifier存在，输出目录缺失使日志关闭；59命令、首sessions/status3，其余58条0，自动清理通过。不能当作日志开启门槛。 |
| [B3日志开启](B3-IO-on/capture-B3/result.json) | 新身份及预建外置输出目录；与A2同一采集器，60命令/14checks/normal开始结束/自动清理通过，21标签真实packet存在。 |

四组9PNG均逐字等于A2，A2为唯一原图存储，其余重复文件为[已核哈希相对别名](archive-layout.json)。Layout原PNG SHA256为`ce10e8d2b029e48e53edbe6746dfc2aeb019d6f96e08457eb3cd8bcec1e2f98f`。原页面从Controls提交到Text/Buttons/Inputs/Query/Layout的操作保持，Layout仍只等0.8秒；没有五帧稳定门槛，也没有强制调整侧栏。两宿主侧栏分界均在140–141pt，卡片横向均x161–900。首Grid为5columns/4children，HDR为3columns/2children。

[独立几何与事件复核](geometry-review/README.md)从完整原图确认13首卡[161,98,900,227)、HDR[161,325,900,472)，14分别为[161,98,900,223)、[161,321,900,468)。固定ROI、ICC转换和扫描算法未改；没有将x800扫描线冒充通用卡片检测。

[B3原始packet](B3-IO-on/events-B3/picture-observer-69534.json)为124058B、21事件/21标签，均为viewDidMoveToWindow、PID69534/window10731，1203个rect有限，全部探针bounds size与resolved相同。Images Grid为719×109、最近graphics祖先739×129；HDR为719×127、祖先739×147。十个公开环境字段与14仅display scale为2/1不同；caption等子节点的半点取整差异另存原记录。

14记录过Images Grid的105→109 resolved变化，而其native探针仍105；HDR末条global y虽与13同335，实际native/PNG仍差4pt。两包均为`end_state=not_observed`，不得把最后记录当稳定终态或同步呈现，也未得到proposed size或唯一根因。字体inherited-nil是探针环境。颜色/HDR、完整交互和动画仍未验收。

[来源与运行独立复核](native-review/README.md)保存实际App/CLI/tar/helper检查：四份私有签名副本只变测试bundle ID与签名成员，所有40个Mach-O section及签名存储尺寸归一后的非签名字节均与各自原GUI一致。私有GUI整文件字节因签名不同，不能称整文件相同。GUI/CLI为arm64/min13/SDK26.2，helper为本机Swift5.9.2/SDK14.2/min13；原交付App/CLI保留。

[采集器v2](collector-v2/README.md)用PID、私有bundle ID、可执行路径和Darwin内核启动时间绑定身份，launchDate只保留可空诊断值。原1574B提交前缀和至Layout动作字节保留；独立[源码审查](collector-v2-review/README.md)通过。观察器要求目录预先存在：早期v1 README的“产品会创建目录”说明错误，v2已纠正，首次B无日志不被重标为通过。A2/B3在停止自有实例前均恢复原Simulator PID9292，最终[桌面收据](B3-IO-on/desktop-final-released.json)为idle、同前台且光标未变；没有停止Simulator或修改TCC/系统外观设置。

[产物退休清单](cleanup/retired-artifacts.json)与[缓存清理](cleanup/module-cache-cleanup.json)记录25,876,991及49,553,800逻辑字节的删除。清理只涉及本轮私有App、临时CI tar/提取副本、helper和自有cache，另核27张重复PNG再以链接替代；未声称APFS物理回收量。所有实际签名与section检查发生在删除前。历史失败、缺日志、原始轮询与更正均保留。

下一最小诊断候选只记录原BernAdaptiveGrid宽度回调；本归档没有执行该候选，也不因width值相同便认定原因。macOS11/Swift5.3、Objective-C和iOS仍推迟。
