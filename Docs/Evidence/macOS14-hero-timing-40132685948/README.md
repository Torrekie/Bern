# 真实 Hero 时序：13/14 原门槛通过，观察空档范围缩小

[CI40132685948](https://github.com/Torrekie/Bern/actions/runs/40132685948) build和measure14均成功。源码`cc96030b22c74010df79423979aee1abf83b7cb5`，harness`d72cb5f9bcec8a90fa394bca1060ed0f392ba8f3`。Xcode26.3/Swift6.2.4/SDK26.2一次构建arm64/min13，compile.log为空；同一原签名binary`723896fc46a2a5e29a1c02293ebc138948f5bffdff10cbe0eec2cf0cdb1108b6`（661776B）在本机13.7.8/远程14.8.9各运行一次default。没有本机编译、重签、SDK/模拟器安装或额外CI重试。

## 变动与验证

仅在既有诊断夹具增加固定3个native事件、前2个实际live采样和1个pending callback的内存标量时间记录。复用原tick的now/p、callback计数、scalars和弱匹配；没有额外window/image query、timer、dispatch、layout/flush、图像holder或动画赋值。计时器、原guard/弹簧/draw、arm区间(.2,.8)、下一采样拍mid与全部期限保持。仓库仅新增5-file overlay；其它输入来自已提交的`4fc027626aa33b5140a4881708a100fc4d2a7c7d:.github/scripts/hero-coordinator-sdr-probe`。本轮没有运行SDR候选，也无产品/UI控件改动。

完整旧native/execution/SDR gate前缀19155B在仅换binary名后逐字相同。新增strict timing检查实际最早两条live sample的index/uptime/identity/start/progress及固定slots；trace-only仅报告coverage，不能把partial变成功。独立复核实际读取binary前后字节，检查arm64/min13/SDK26.2/strict signature、20包成员/12源输入、tar/assembly及5overlay+git base；两端原gate、strict timing均exit0。完整原报告、6原PNG/ICC、收据和源/包清单保留。

13旧SDR default→本次两个对应端点、14旧正常app-loop参考40110795231→本次两个对应端点，原RGB及ICC intent0 sRGB均exact。14来自不同VM，此结果不是同一物理宿主声明；也不要求source与destination彼此exact。Root目检两原mid和14settled，均有可见非白内容位移、目标非空；白格与背景不能区分，视觉检查不证明完整像素覆盖/所有overdraw。mid进度13约.339、14约.733，未配准或计算跨宿主mid色差。

## 这次实际测量

|边界，毫秒|13|14|
|---|---:|---:|
|Flight.started→原timer注册后|0.129|0.435|
|首次callback入口→原first-live stamp|0.429|0.642|
|首次callback入口→scalars结束|0.448|0.666|
|其中原WindowInfo整调用|0.388|0.572|
|其中弱匹配入口→原first stamp|0.019|0.028|
|Flight.started→first tick既有now|9.159|159.427|
|首次scalars结束→first tick|3.033|140.835|

两端first_applied复用同一次first_tick的now；首个写入p分别.006709853/.674501439。它不是赋值完成或呈现时间。首次callback可能在native创建前后，不强加callback入口与timer注册先后的假设；第二row沿用全局旧firststamp，不能把它当第二次matching结束。原绝对uptime、精确值与局限见`observation.json`及报告。

本次14的native构造/挂载/注册段和首个callback前缀均很短，较大未标记区间落在首个scalars结束到first tick之间。但没有callback退出或draw边界，不能拆成采样尾部、自动绘制或事件分派，更不能定位到某个API。不同进程/VM、观测开销和缓存状态不允许据此解释上一轮215ms空档、宣称零observer effect或通用性能结论。

## 对移植阶段的含义

本次补齐了这个限定真实条件替换的14正常效果参考，且原native生命周期、端点稳定和可见mid证据齐全。上一[40129608288失败](../macOS14-hero-coordinator-sdr-40129608288/README.md)仍为失败，原deadline/缺样记录未改；这次成功不是时间标记修复动画的证明。远程14已实际可用，没有达到用户设定的“数小时无远程环境”暂停条件。

已有参考足以让工作回到实际UI颜色/布局未通过项；不因尚未定位全部空档继续盲CI，也不据此修改产品clock，见[收尾说明](closure/README.md)。原静态SDR方案仍有改善/退步并存，产品intent链未接，未采用候选。[下一步](picture-scene-next-step/README.md)回完整Showcase原位的Form→首Grid row环境/实际布局框，先重现14首卡124/125及HDR147，再观察且保持原卡高；此前isolated双方129不能代替它。完整动画/High/HLG/其它输入/retarget/物理HDR及Film/chrome/Picture/Frame/输入等整UI门槛保留；goal active，不提前进入mac11/Swift5.3/ObjC/iOS。

## 清理与重现边界

独立实际字节复核后，binary/tar和重建的source副本已清理（35文件、1331112逻辑字节），见`artifact-cleanup.json`。完整源可从上述两个git提交的5overlay与base重建，编译指令/环境、原SHA清单、实际校验收据及原PNG/report保留。历史包清单包含已删除payload，不能作为仍存binary或当前可重跑的证明。其余工作副本清理见`cleanup.json`；现存文件以`SHA256SUMS.final`为准，逻辑字节不等于APFS实际释放量。
