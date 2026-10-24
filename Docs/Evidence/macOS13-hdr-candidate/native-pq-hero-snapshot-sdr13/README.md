# 实际快照的系统 SDR 表示：部分改善，仍非等效

对同一次 `renderer.cgImage` 快照执行固定的系统 Core Image RGBA8/sRGB 输出，再沿原 NSImage 双绘制，明显降低了 named 主残差，但同时引入若干通道退步。**本轮不合入产品，不宣称颜色或动画等效。** 原资源、cache、原始浮点导出保持；没有改图、重标 PQ、手写曲线或新增 UI 控件。

## 完整结果

目标为每 host 的 `D = Hero − body`，再比较 `D13 − D14`，不是让 Hero13 等于 body13。下表是十色块全部30个 RGB 通道的 patch-mean 残差，单位为8bit编码 sRGB 码值，不是全图 MAE、线性光或 nits。

| named phase | mean absolute：default→candidate | max absolute：default→candidate | 改善 / 恶化 / 不变 |
| --- | --- | --- | --- |
| p0 | 5.210863095→1.525197459 | 112.616328984→25.754035027 | 5 / 7 / 18 |
| p1 | 5.224399038→1.567882898 | 113.048334478→26.186040522 | 3 / 9 / 18 |

cool812 R两phase均减少86.862293956码值，仍有约25.754/26.186的残差。最大新增恶化为p1 green812 R的2.435439560码值，另有green B、yellow B、red G等退步；全部16项恶化见[完整结果](pixel-analysis/RESULTS.md)，[CSV](pixel-analysis/patch-channel-changes.csv)保留全部120项通道，不挑选均值或有利色块。

named ramp aggregate 的p0三通道改善、p1三通道小幅恶化，绝对变化量分别约0.001424/0.000494/0.002512码值。custom十块及ramp均不变。保留各自 native 分辨率的完整列数据，不跨host配对/resize/fitting。两张本机 candidate phase PNG本身逐字相同；上述分类是相对14各phase参考的结果，不能把它说成新出现的13逐phase转换分支。

[一次分析 runner](pixel-analysis/README.md)及五个子命令全部退出0。三份原算法/spec字节不变；保留14/on重算在版本、analyzer/spec、68个完整 comparisons、16个 primary、全部ROI及ramp gzip SHA均与冻结14结果相同。这是本轮本机新 binary 与保留14的比较，不是新的跨host同binary采集。

## 实现与运行

[最小源码](source-preparation/README.md)在原快照 observer之后、原NSImage构造之前，只对named主快照创建 `CIImage(cgImage:options:[.toneMapHDRtoSDR:true])`，沿用实际输入空间，单个CIContext按精确原extent输出RGBA8/sRGB、`deferred:false`；缓存这一个派生，再构造原320×180pt NSImage。default不创建CI对象，custom原样；原FloatCapture和完整Flight.draw两行逐字不变。没有新renderer、provider导出、NSImage recache、图层或direct-CG变量。

记录明确是 `requested_tone_map_hdr_to_sdr=true`，**实际 tone mapping 执行仍为 unknown**。公开合同只保证输入CGColorSpace被Core Image认作HDR时Bool生效，extendedSRGB及大于1样本不能单独证明它执行了tone-map。本轮只检验整个固定输出recipe，不能把改善归因于Bool。输出实际为640×360/8bpc32bpp、`kCGColorSpaceSRGB`、nonextended；其ICC3144B/SHA与原extended-sRGB快照相同，不能因此抹去两者的name/range/format差异。

Xcode15.2/Swift5.9.2/SDK14.2、语言模式5、O/j2、arm64/min13首次构建成功，严格验证linker ad-hoc签名，未重签。继承原不可达macOS15 gain-map条件和静态unused-clock guard；保留原switch的两条warning，没有编译错误。23输入及四段组装见[provenance](fixture/source-provenance.json)、[build](fixture/build-fingerprint.json)，原binary SHA为 `e555781e4f3c647243017e33a6ea64f0393e667a8e71e9ce29998dc2365d15dc`。

| 模式 | PID | wrapper 秒 | 原窗口秒 | context / conversion |
| --- | ---: | ---: | ---: | --- |
| default | 44718 | 2.141286583 | 1.729274988 | 0 / 0 |
| baked-named | 44746 | 2.084109416 | 1.868616939 | 1 / 1 |

候选一次转换用时0.258979292秒，17条phase检查保持同一派生CGImage/display NSImage，cleanup透传2次、没有新转换。该测量不证明全局冷/热缓存状态，也不是实际进入动画前的延迟验证。前台9292保持；normal首尾false、cache不变、自有固定nonkey/inactive window、各phase五个报告相等buffer、noMTK、manager flight0/timernil均通过。noMTK不代表CIContext内部不用GPU。

default先精确复现旧on全部12ROI的raw RGB/ICC→sRGB；candidate仅named两phase改变，其它10ROI均exact。四份原raw与旧同host/key直接逐字相同。原始比较器退出1仅表示named有差异，两wrapper和两native validator均退出0。原输出目录必须不存在的wrapper保持fresh/no-overwrite；独立[源码](code-review/README.md)及[native复核](native-review/README.md)均通过，native reviewer在exe仍存在时直接执行未改的附加validator及原base/on13，前后实际exe SHA相同。

## 证据边界与清理

[几何记录](fixture/root-geometry.json)在完整颜色算法前，按[既有冻结计划](../native-pq-hero-cg-direct13/geometry-plan/README.md)分别查看p0/p1原PNG：固定pane320×180pt/640×360px、上两行色块/底部横向ramp方向正确，非空，未见位移、裁切、空带或越界。它是visual-only；白色可能与背景合并，alpha255/frame不证明每像素覆盖或亚像素边缘，未运行tuple检查。native绘制/身份/清理记录不能替代该目检或完整颜色结果。

原float export/finish/release逐字保持，helper在PNG及原窗口teardown后记录派生ICC，再清除派生/context/weak display引用。只证明这些容器清空，不证明全部系统对象dealloc。继承的报告 `try?` 写失败、CLI自身无完整overwrite guard、hard watchdog绕defer等边界保留；本轮没有故障注入、真实flight、High/HLG、其它方向/alpha/fit/corner或物理HDR验收。

exe与本轮module cache共57485328逻辑字节已清理。六个work树逐字核验后变为本归档symlink，删除重复逻辑文件13677124B；内部13个同字别名硬链接去重名义5077367B，未链接至work/其它归档。见[收据](cleanup.json)。这些不是APFS实际回收或磁盘净变化。保留原图/raw/源码/完整数值和独立审查，当前现存清单为 `SHA256SUMS.final`；构建/原exe哈希与签名属于清理前证据。

归档和旧work symlink只读。复跑时复制必要脚本到work下fresh scratch并新设输出；完整native validator需要恢复同SHA原exe，不能拿重编产物替代历史身份。CSV保留原标准CRLF记录，不修改已冻结结果字节。未新增远程CI、工具链或模拟器。

[下一单一门槛](next-flight-plan/README.md)尚未实施：用新SDK/min13 binary验证一次真实Standard named coordinator transition，区分同key的两次快照，并记录两次转换和Flight.started之前的延迟；不能搬用会在13拒绝timer的静态clock guard。产品intent尚未从BernImage传至Hero modifier/probe/anchor，不能把本fixture的Standard限定冒充生产路由。完整目标仍未通过，goal active，不进入macOS11/Swift5.3/Objective-C/iOS。
