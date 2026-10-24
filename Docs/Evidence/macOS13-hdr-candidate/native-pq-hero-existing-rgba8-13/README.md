# 本机13：早期existing-layer RGBA8前提未成立

这是停止的限定实验，**没有格式视觉结果**。固定真实existing-overlay静态路径，process-cached BERN_HERO_FORMAT_REQUEST=control|rgba8，默认control；backing/float均off。源图、原snapshot/NSImage/Flight.draw、原route/stable5/时限不变。control在任何新view/layer getter前返回；request只允许挂载后读取已有flight.layer，并单次请求RGBA8；nil/已RGBA8/覆盖/换层则停，不创建layer、不设wantsLayer/新delegate/重试或额外display。

Xcode15.2/Swift5.9.2/SDK14.2/min13，已明示的unused-clock/gainmap诊断编译保护与旧本机夹具相同。binary `bd65ca534e9db9f169e08cef9ff23aac165b468cb675d550f98dc8f7276b8b31`严格验签、两receipt同hash。源码、编译日志/指纹、实际combined文件、原日志和部分失败报告在fixture；source-preparation/source-plan为准备阶段原件。

control成功：1.665022秒、两phase/两PNG，旧同binary13 overlay→control的12ROI raw及ICC归一全部exact；normal/cache/front1390保持/noMTK/managerFlight0/timernil/五stable均通过。[独立小摘要](analysis/README.md)核控制记录和27输入hash，不声称重复算像素。

rgba8在0.209013秒窗口内exit1：实际first snapshot已完成→创建第一flight→原mount到existing overlay→下一次原display loop之前读取layer，返回nil。此处先于contentsFormat读取/写入，也先于第二flight及任何窗口截图；唯一record为flight-named/layer_present=false/set_count0/checks[]，sample0/PNG0，无持久性检查。原snapshot primary1、cleanup2，raw export/copies/retention为0；这不表示程序从未解码或生成图像。

失败分支只有首尾normal false和前台1390保持等部分观测，没有到after-cache ledger及最终guards，不能说全门槛通过。没有setter，所以不能说RGBA8没有视觉影响。它只表明所选早期插入点没有可用的已有层；以前PNG后的layer存在观测在不同阶段，不与此矛盾。不通过强设wantsLayer、等待重试或隐藏失败来继续这个候选。

13control/candidate及14route root/overlay日志均有相同unknown-subview warning和prepareOverlay栈，完整日志保留，不指定其为色差原因。产品没有加入此探针或格式补偿。真实flight、计时、移动像素、自动结束和目的内容可见性仍需单独验证。

完成后清理本机binary和唯一module cache；原build fingerprint保留binary hash，prebuild source manifest保持，现存文件见外层SHA256SUMS.final。冻结build.sh只可恢复至新的自有work副本后使用，不能在此创建cache。
