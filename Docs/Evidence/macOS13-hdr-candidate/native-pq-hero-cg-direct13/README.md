# 同一实际快照的 CG direct 对照：阴性

本机 macOS 13 的 default/direct 两模式使用同一原签名二进制。default 先精确复现[旧 float-on](../../macOS14-hero-cgsemantics-40119614788/same-binary-13-14/runtime13/on/)的全部 12 个图像 ROI；direct 随后与 default 的全部 12 ROI 在原 RGB、各图自身 ICC→sRGB 下也逐像素相同。两模式四份原 raw 均与旧同 key 的数据直接逐字相同。

**绕过 NSImage.draw、直接绘制原 CGImage 没有改变本例结果，也没有改善主色差。** 该限定路线停止，不合入产品，不追加显示控件变体或远程 CI。它不证明其它对象状态、目标 context、合成或捕获路径相同，也不指定唯一原因。

## 实现与实际运行

只在原静态 fixture 中增加同一 held 容器内的 weak NSImage 身份关联和同步 CGImage 借用；没有另一份长期 CGImage 容器。default/direct 都建立相同关联，default 仍执行原两行 NSImage.draw。只有 named Flight 的候选分支在原 clip、当前 CGContext 中局部 save/defer-restore，按原 flipped view 推导一次 y 反转，再以 normal/source-over、alpha1 和 clamp(progress) 绘制原图两次。custom 原绘制保留；没有新 context、snapshot、图像复制、provider 访问、recache、layer setter 或每帧转换。

缺绑定、context、有效端点或原生门槛即 sticky failure，不回退默认再标成功。原 float 的 freeze/export/finish/release 代码逐字保持；新增关联随原 held 清空。原普通 catch、最终报告 `try?` 写失败、hard watchdog 绕过 defer 的限制保留；本轮没有故障注入或普遍释放/系统对象 deallocation 证明。完整代码与补丁见[source-preparation](source-preparation/README.md)，[独立源码审查](code-review/README.md)说明实际 closure 没有保存 CGImage；nonescaping closure 本身不是静态禁止所有引用逃逸的保证。

实际构建是 Xcode 15.2 / Swift 5.9.2 / SDK14.2、语言模式5、`-O -j2`、arm64/min13，首次构建成功；严格签名通过，linker ad-hoc，未重签。继承已有不可达 macOS15 gain-map 分支的编译条件与静态 fixture 的 unused-clock guard，不冒充真实 coordinator 或完整产品构建。24 输入和四段拼接核验见[provenance](fixture/source-provenance.json)、[build](fixture/build-fingerprint.json)。二进制 SHA：`be263dfbd54a965003c8adc82c2294475963cb9463fc86c6daedcc89a09d8fd0`。

| 运行 | PID | wrapper 秒 | 原窗口秒 | 前台 PID 首尾 |
| --- | ---: | ---: | ---: | --- |
| default | 41469 | 2.095345750 | 1.717992902 | 9292→9292 |
| direct | 41501 | 1.885338000 | 1.657393098 | 9292→9292 |

两次完整原 native/ICC/float/semantics gate 和附加 adapter gate 均通过：normal 三项首尾 false、cache 保持、owned fixed/nonkey/inactive window、各 phase 五个报告相等 buffer、no MTK、manager flight0/timer nil、两原 image held peak2→0/provider-copy2。named effective p0/p1 的 callback 数为2/1，报告同一原 CGImage/NSImage/Flight 身份及两次绘制状态。它们只覆盖同图 opaque/up/same-aspect/corner0 静态端点；CG 绘制 void 调用记录不等于像素成功，报告 buffer 一致性也不是独立重采。

## 几何与完整颜色结果

[几何计划](geometry-plan/README.md)在采集前冻结。root 分别查看两张原始 direct PNG，固定 named320×180pt/640×360px、上两行离散色块及底部横向 ramp 方向正确，内容非空，未见平移、裁切、空带或越界；结合 source review 的完整 bounds、opaque 原 atlas 和原 alpha 顺序，判为完整**可见** extent 通过。见[逐 phase 记录](fixture/root-geometry.json)。这是 visual-only，未运行 tuple 算法；白色区域与白背景不可分，不能证明每像素覆盖或亚像素边缘，alpha255/frame 也不单独证明无泄漏。基础 ROI 相等比较早于这次目检；完整 D13−D14 算法在绑定几何门槛后才运行。

[完整分析](pixel-analysis/RESULTS.md)使用三份原算法/spec，不改像素、ROI 或阈值。一次 runner 和五个子命令全0；保留的14参考重算在版本、analyzer/spec、68个完整 comparisons、16个 primary、全部 ROI 和 ramp gzip SHA 均与原冻结结果相同。这是本轮本机新 binary 与保留14结果的对照，不是本轮新的跨 host 同 binary 采集。

每个 phase/source 的十色块30通道均为改善0、恶化0、不变30，全部 signed/absolute 变化0；named/custom 的 ramp aggregate RGB 残差变化也均为 `[0,0,0]`。named 的 mean absolute(D13−D14) 仍为 p0 `5.210863095`、p1 `5.224399038`，最大残差仍为 `112.616328984` / `113.048334478`。这是编码 sRGB 码值的 patch-mean 指标，不是物理亮度或全图 MAE；未将 Hero13=body13 当目标。所有通道和 native ramp 列数据均保留。

## 独立复核与清理

[独立 native review](native-review/README.md)核验实际 exe、构建/拼接和报告。其首次复核误以为 exe 已删，在内存中用先前实际 SHA 替代一次 rehash 表达式；当时实际上只删了 modules。[addendum](native-review/README.addendum.md)保留该更正，并对两模式直接执行原字节附加 validator（分别原字节调用完整 base/on13），均退出0，actual exe 前后 SHA 相同。原三文件及首份 manifest 未改；补充另有 manifest。没有重跑 UI、构建或像素。

原 exe614208B 与本轮 module cache56885800B，共57500008逻辑字节已清理。七个 work 树逐字核验后替换为本归档 symlink，删除重复逻辑文件13585553B；归档内部16个同字别名硬链接去重名义5716684B，未链接至 work/其它归档。见[收据](cleanup.json)。这些数字不是 APFS 实际回收或磁盘净变化。原图/raw/源码/失败边界/复核均保留；历史 build 与复核中 exe 身份属于清理前记录，当前现存清单为 `SHA256SUMS.final`。

归档与旧 work symlink 只读。复现时将必要脚本复制到 work 下 fresh scratch，输出另用 fresh 目录；完整附加 validator 还需要恢复同 SHA 的原 exe，不能拿不存在的 exe 重验签名或用重编产物替换历史身份。未下载/安装工具链或模拟器，也未新增远程 CI。

[下一唯一候选](next-sdr-plan/README.md)尚未实施：对实际 renderer-return snapshot 使用系统 Core Image 的固定 RGBA8/sRGB 派生显示表示，再沿原 NSImage 双绘制。它不同于旧 cached-PQ→RGBAh 实验；`.toneMapHDRtoSDR=true` 对 extendedSRGB 是否实际生效没有合同保证，不预言改善或重标记成 PQ。完整 macOS13 颜色/动画及其它 UI 项仍未通过，goal active，不进入 macOS11/Swift5.3/Objective-C/iOS。
