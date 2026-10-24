# 正常AppKit循环：两端可见中间位移，颜色及完整动画未验收

[CI40110795231](https://github.com/Torrekie/Bern/actions/runs/40110795231)构建/14采集成功。源码`ace6e1ee4acda71e26616ef0a21a3fc94d085829`，harness `be6eb08a91e74d900cdaccc6d8730c81aefb96bc`。SDK26.2/Swift6.2.4仅构建一次arm64/min13；原签名binary `a98bd3d415e98fbd84daa3d9c4bdbe21f2d731b3858b82fa66b20b59255e8d0d`在14/13各运行一次。13运行前核验包、18成员/10-input source map、架构/min13/SDK与严格签名，未重签或本机编译。CI最终状态、包/构建及原收据保留。

本轮只替换observer执行模型：唯一NSApplication.run、launch delegate中的一次异步preload、default-mode selector Timer执行原采样body。没有手动RunLoop.run或finishLaunching，没有逐sample Task。原Hero/clock/draw/scene/key/asset/action、capture/save helpers及全部原生门槛保留。首个band只arm，下一相邻observer sample才拍唯一mid；policy字符串为schema连续性仍保留旧名称，由execution_model明确新语义。夹具仍是孤立NSHostingView场景，并非完整生成应用。

[源码独立审查](code-review/README.md)确认helpers逐字相同、sampling body仅搬运continue→return并增加terminal保护。终止先invalidate sampler、stop，再投递一次own applicationDefined wake，run实际返回后才原defer清理/write。[Apple stop文档](https://developer.apple.com/documentation/appkit/nsapplication/stop%28_%3A%29?language=objc)说明timer单独stop不足以退出；该terminal事件用于退出，不是物理输入、额外样本或显示同步fence。sampler invalidation字段是源路径flag，不是独立Timer.isValid观察。

| 宿主 | arm→capture index/p | 样本间隔 | sampler callbacks | 窗口秒 |
| --- | --- | --- | --- | --- |
| 13 | 8→9 / .237940663→.362234254 | 15.422417ms | 57 | 1.295496 |
| 14 | 7→8 / .646607109→.693877248 | 8.734208ms | 49 | 1.617048 |

[独立原生复核](native-analysis/README.md)提取锁定workflow完整native+execution gate，仅四处路径/OS适配，两边PASS。31输入hash匹配；launch/entry/实际return/terminal/stop/wake各1，default-mode、名义1/60、depth1/reentry0/terminal后callback0；callback计数含preload。loop持续1.520211/1.816907秒，terminal→return约.301/.218ms。原single flight identity、timer/frame/progress变化、finish后flight/timer/临时view归零、normal三项false/cache/前台保持（9292/314）、own-window/nonkey/inactive/noMTK/端点五stable全部通过。两边本例weak source均为nil；该值不是硬门槛，未推广为通用内存验收。

root已目检两张原mid，均有位移，14本次已离开source。[限定像素检查](pixel-analysis/RESULTS.md)的固定root12pt全opaque inset非白内容bounds为13 [96,76.5,416,256.5]、14 [233,166,554,347]。它们不是精确flight配准；实际capture sample逻辑原点为(137.710709,103.691536)/(249.142755,176.652994)，arm、capture和CG前后native bracket各自保留，不将画面等同任一状态。该运行模型下已有本例可见中间位移证据，但不唯一归因某个内部提交步骤或宣称零observer effect。

四项同宿主旧delay→新app before/source、settled/destination ROI的原RGB及perceptual intent0归一sRGB全部exact。新before→settled仍为13 sRGB MAE0.294106/255、max5；14为0.271169、max2，均非exact。六原PNG/ICC与14输入hash保留。端点内容保持和一张可见中图不通过跨宿主颜色、完整轨迹/时序、retarget/reversal/alpha/fit/corner或物理HDR；本次capture p也未实测超过.8分支。

下一[同snapshot原生显示对照](next-native-view-plan/README.md)尚未实现/运行。旧NSImageView13与body exact使用的是原CGImage，真实Flight输入却是ImageRenderer后的NSImage；且14 Hero本来就不等于14 body，不能直接拿body作新目标。只考虑保持同一实际snapshot NSImage和原默认Flight控制，单独比较NSImageView显示；默认须先复现旧13静态ROI。先报告完整signed H−B/D13−D14与灰阶的改善/恶化，再决定是否有价值；不绕过snapshot、RGB补偿、图像白名单、层setter或自创tonemap，也不需要为这个未知再开14 CI。

本轮原binary/tar与逐字核验work重复副本已清理，见`cleanup.json`；未创建本机编译缓存。原包清单含历史已删文件，现存清单以`SHA256SUMS.final`为准。保留源码、原PNG/ICC、报告、静态审查/API记录。原7.2s入口deadline、7.9s硬watchdog minimal-report/_exit边界保持。Film/chrome/Picture/Frame/交互/HDR等未通过项及完整macOS13阶段仍未验收，goal active，不进入11/Swift5.3/Objective-C/iOS。
