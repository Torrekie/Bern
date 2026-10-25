# 原生搜索焦点门槛：未通过

本轮没有完成原生搜索输入链，**没有发送`!`，没有选择Library或执行Query验收**。坐标点击后的公开AX焦点仍是侧栏outline；另一个干净实例的一次Shift-Tab之后，快照未返回focused节点。后者不等于事件没有发生。停止这组输入尝试，不用CLI edit/focus/submit、AX赋值或粘贴补成成功，也不把当前结果指定为Bern缺陷或macOS14差异。

## 三次记录及边界

| 记录 | 实际结果 | 采集状态 |
|---|---|---|
| [首次启动](attempt1/driver.json)，PID81490 | IPC根路径113字节；108次sessions均3，无可用会话。源码固定拒绝超过100字节的完整socket路径 | UI投递前停止，driver false |
| [坐标点击](coordinate/driver.json)，PID81989/window10762 | 短IPC的会话/唯一可见窗口联合就绪1.237606秒；全局坐标330,178位于search的公开AX框内。点击前后仍focused12 outline，cursor距离0 | 焦点门槛未过；root整理现场超过180秒，缺finish.json的原Errno2及迟到capture的appNotFound保留，driver false |
| [键盘焦点](keyboard/driver.json)，PID82774/window10767 | 新私有身份，联合就绪1.347112秒。只请求一次shift+Tab、direct、restore_focus=false；之后无可确认的search焦点 | 保存[1840×1336原PNG](keyboard/window.png)，及时finish=false，driver false |

[独立runtime审查](runtime-review/README.md)核对原MCP请求/回复、PID/窗口、正常效果设置及恢复记录。三组App退出码都是0，只证明自有进程正常退出，不代表输入链验收通过。坐标组只有两张逐字相同的920×668 **MCP预览图**，并非原始2×WindowServer缓冲；不将其升级为raw截图或完整视觉对照。键盘组只有一次原PNG，没有5帧稳定链。

首次IPC错误来自采集脚本选择了过长路径。[分析](attempt1/failure-analysis.json)确认运输层源码与精确9dd相同，根目录本身113字节已超过完整socket路径上限；改用旧collector同类的短/tmp根后，同产品在1.24秒内就绪。仅修正本轮驱动，没有改产品或重新编译产品。

## 来源、输入方法与恢复

使用已交付9dd完整Showcase；GUI原件SHA`cc267abcafeec30112c2796b3c0ea7699a6836a0f09a1caa73f66ea48bfa1c1b`，CLI原件SHA`963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170`。三个私有bundle仅隔离身份/签名，[actual payload审查](source-review/payload.json)核验每份15成员、1Mach-O、40sections及归一化非签名字节与原件相同；actual strict签名通过，min13/SDK26.2。没有新增产品UI或自定义原生控件。

[输入后端源码审查](delivery-audit/README.md)区分坐标CG事件与可能走AXPress的element-index动作；显式unicodeEvent无源码AXValue/粘贴回退。但本轮并未调用type_text，不能声称Unicode投递实际通过。该源码审查也不是已安装后端与当前源的重建证明。AXFocused节点不是App内部firstResponder对象，未取得后者不构成其不存在的证明。

启动前先保留原前台Simulator9292；实际目标前台确认后重新建立MCP exclusive基线，再发单次动作。各组正常效果三项开始/结束均false。精确PID/bundle/path/kernel-start匹配后，先保留或恢复原前台，再停止自有进程；最终desktop released、cursor距离0。恢复导致的中间interrupted=true与最终release状态均保留。

未修改TCC或系统辅助功能设置。采集工具的虚拟光标临时关闭后恢复原配置并清除本轮标记；immediate-off收据曾报告overlay visible，而随后实际MCP快照为off/hidden，原数据未改。最终配置和隐藏状态见两组desktop/virtual-restored收据。

## 清理与下一项

[实际payload读完后](source-review/README.md)，已[退休3份App及2个helper](cleanup/payload-cleanup.json)，合计12,853,477逻辑字节；[71个模块缓存文件](build/cache-cleanup.json)删除49,553,800字节，合计约62.4MB。三个新私有ID的偏好及本轮IPC目录也已清理；[偏好收据](cleanup/private-preferences.json)明确首个42字节空plist删除前hash未保留，不回填该值。两个相同预览合并83,878字节。以上不是APFS物理回收量。

[交付GUI/CLI哈希及strict签名](cleanup/delivered-preserved.json)保持。源码、原日志/失败状态、截图及审查移入本归档，旧work目录为[相对别名](archive-move.json)；不在归档路径运行历史脚本或创建缓存。

下一项回到[Frame Caption/Size源级边界](next-frame-plan/README.md)：历史实际对照为f9，不能冒称当前e48的新Frame运行；两按钮的2pt宽度变化相互补偿，不支持分别加padding/改字号。先补精确e48 Gallery Frame生成片段，再确定同一真实行需要的单一布局事实。现有picture-source-export脚本固定9dd/Showcase/layout_page，不能直接改标签当作Gallery结果；后续须准备固定e48的source-only导出，不重编产品、不扩控件矩阵。

整个macOS13移植仍未通过、goal active。macOS11/Swift5.3、Objective-C及iOS阶段继续推迟；本轮未触发远程CI或新定时任务。
