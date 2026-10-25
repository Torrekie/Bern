# 完整Scene宽度回调：同一可执行代码在13／14

[CI40144017622](https://github.com/Torrekie/Bern/actions/runs/40144017622)的Swift6完整构建与macOS14运行成功；同一产物的私有签名副本在本机13也成功采集。14的13张原PNG逐字等于control，卡高125/147保持；13的9张原PNG逐字等于A2原版，仍129/147。宽度回调的有限记录在两侧相同，**尚未解释4点差异，因此停止本组width诊断**，不继续增加探针、重跑CI或据此补padding。

| 身份 | 值 |
| --- | --- |
| source / harness | `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0` / `7dddc256ccdc006d746766af6ef3d7f68d887547` |
| 工具链 / 最低版本 | Swift6.2.4、SDK26.2；GUI/CLI arm64、min13.0，实际严格签名通过 |
| 原21点Generated | 106494B / `f4cac6965e72f454c257a30420ca5966d2b9afc012d1e9e264c20ed947b706d2`，逐字保持 |
| 新Style | 209558B / `09d8f99a26a73498e7ef4d7d597eca646be751f32b4fe99f63482b944a81987f` |
| CI GUI / CLI | `5e9790ef812c424f27bb91e3248c73ea451069d92d7d627d57428f8390a96765` / `963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170` |

[准备与边界](../macOS14-picture-grid-width-preparation/README.md)保留原guard、Transaction和赋值，只在原action入口捕获旧值/时钟、defer中写独立有界packet。原Scene、窗口路由、21背景测量源码未改。它是诊断产物，未替换交付App或采用产品布局补偿。

14 [原记录](run/raw/result.json)为14.8.9、normal三项false、英文、920×668@1，80条命令仅两个进程首sessions/status3，其余78条0，18checks通过。13 [原记录](local13/capture/result.json)为13.7.8、normal开始/结束三项false、同动作顺序与920×668@2；60命令首sessions/status3恢复、其余59条0，14checks通过。原Layout0.8秒等待保持，没有五帧稳定门槛。13 helper重新编译后整文件SHA与A2/B3 helper相同；B4私有GUI因测试ID/签名整文件不同，40个section及归一化非签名字节与CI原GUI一致。

[14 width packet](run/raw/observer/picture-grid-width-1532.json)为1364B，[13 width packet](local13/events-13/picture-grid-width-74700.json)为1365B；各3条，配置顺序均140/12/12→192/16/16→120/16/16。每条old width为正零、measured719、body-captured columns1、主线程、有限、原guard通过，无写出cap。去掉两个uptime字段后全部记录逐字段相同，canonical SHA256为`3cae04b3a75b497a4ef6213c960460e84180f80542d90fdae6c76c7e4486e5a3`。捕获的列数不是依据measured重算的最终列数；配置也不是实例ID。

[14几何独立复核](geometry14-review/README.md)核13PNG/125+147、49事件/21标签；按label/callback配对，全部几何与旧观察版一致，但末期Gainmap/PQ六条记录全局顺序交换，不能称完整回调顺序相同。[跨系统复核](cross-review/README.md)核13的21事件逐标签等旧B3，原生祖先129/147、14仍125/147，caption37.5vs38等完整字段及环境scale2/1差异保留。最后width记录到首geometry callback分别约24.926/44.050ms，是各自callback边界，不能当呈现耗时、纯I/O成本或原因。

所有packet均为`end_state=not_observed`。width包只有PID，没有window或实例身份；窗口关系来自同进程的geometry/capture记录，未冒称直接记录窗口。同步锁/JSON/I/O在原动作后、callback返回前，post-action时钟在I/O前；截图保持只证明这些选定画面未变。匹配的有限prefix没有解释Form行尺寸、proposed size、稳定终态或全UI等效，不能据此硬调4pt。

[来源/native独立复核](native-review/README.md)核55Git输入、两份生成源的独立重构、实际tar16成员、签名/架构/min13/SDK26.2、B4 code sections与进程身份。两份outer ZIP本轮由root在提取/删除前实算SHA并匹配API digest，[build](run/build.download.json)及[capture](run/raw.download.json)收据分别保留；再与runner上传日志交叉，和内部tar SHA `d7db5e239e86ccae5c2cdda6c6ad151bd3b06080a00299336c4d2a82aac86b0d`分开记录。独立review未重读已删ZIP，未倒填旧cohort验证。

13先恢复原Simulator PID9292再停止自有PID74700，最终[桌面释放](local13/desktop-release.json)为active=false、前台与光标保持。只读核验结束后，清除本轮[12,291,616B临时产物](cleanup/retired-artifacts.json)及[49,559,240B编译cache](local-build/module-cache-cleanup.json)；原交付App/CLI保留。22张重复PNG先核哈希再换[相对别名](archive-layout.json)，逻辑内容不变；未声称APFS物理回收量。

整阶段、HDR/颜色/交互/动画其它未通过项仍见[验收记录](../../Implementation/macOS13-Acceptance.md)。goal active；macOS11/Swift5.3、Objective-C和iOS仍推迟。
