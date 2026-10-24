# 完整Scene Grid宽度回调：运行前准备

仅准备下一最小单变量诊断，不是产品布局修复，也没有在这里运行Swift6产品或采集UI。前置真实结果为[14原观察版](../macOS14-picture-scene-observed-40138440830/README.md)的125/147、13张PNG保持，以及[13 A2/B3](../macOS13-picture-scene-observed-9dd/README.md)的129/147、9张PNG逐字相同。

原9dd生成Style的现有BernAdaptiveGrid宽度action加入入口旧值/时钟捕获及defer日志；guard、Transaction、State赋值仍为连续原字节。Style205764B/e1cad857…变209558B/09d8f99a…，移除插入和helper可恢复全部原字节；原21点Generated仍106494B/f4cac696…不变。三处配置120/16/16、192/16/16、140/12/12均如实记录，配置不是实例身份。

[源码准备](source-preparation/README.md)及[独立审查](source-review/README.md)保留精确diff、负例、来源与限制；Foundation helper已用本机Swift5.9/SDK14.2/target13通过小型typecheck。defer的锁、JSON和同步I/O发生在原动作之后但callback返回之前，会影响时序；记录时间不代表I/O完成或稳定状态。

[CI准备](ci-preparation/README.md)与[独立CI审查](ci-review/README.md)核对固定9dd、55个Git输入、唯一CLI hook、原target.plan/退出码、两种生成源SHA、9段shell语法和artifact路径。本地fixture只验证CLI/纯文本补丁链，Git边界为明确的数据替身，未运行cargo或产品Swift编译。只有四个active候选文件及说明进入.github；旧observer包不变。

下一次实际运行需先核新14产物的原13PNG/125+147和21标签保持，再解释独立width packet；之后以同binary在13采集。目标两配置需实际有限、主线程事件，PID/route绑定，日志未触上限。缺数据或相同宽度历史均不能推因果、settled、proposed size或完整UI等效。原0.8秒等待不冒称五帧稳定。

workflow沿用同run命名artifact→build/→内部tar SHA核验；outer ZIP/API digest与内部tar摘要分别核对。root下载工具已准备在提取/删除前记录实际ZIP SHA并与API digest绑定，但本归档不代表该网络路径已执行，也不倒填旧cohort的outer验证。原collector SHA和CLI实际min13仍由root的harness/产物检查完成，未把记录字段说成workflow中的额外硬断言。
