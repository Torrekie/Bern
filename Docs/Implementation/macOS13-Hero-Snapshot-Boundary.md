# Hero 下一边界：读取原 snapshot 的 float 样本

**现有证据尚不能区分 snapshot 内容差异与后续绘制差异。唯一建议的下一步：在原PNG采集及原teardown之后，读取实际 `renderer.cgImage` 返回对象的 provider 原字节。** 本段保存制定时的只读设计；该诊断后来已执行，结果与后续范围见末节。

## 已知边界及公开接口

- `BernAppKit.swift:1848–1864` 是原 ImageRenderer→`pixels`→`NSImage(cgImage:pixels,size:)` 链；`1922–1939` 的实际 Flight.draw 是圆角clip后，from以sourceOver/fraction1绘制，再以clamped progress绘制to。同图、opaque、固定尺寸端点只测试这条链，不测试协调飞行动画。
- [metadata证据](../Evidence/macOS14-hero-cgmetadata-40086541042/RESULTS.md)记录13/14同为16bpc浮点/64bpp、extendedSRGB、完整ICC3144bytes/SHA相同；它没有读取snapshot像素。相同描述不等于相同样本。[colorMode](../Evidence/macOS13-hdr-candidate/native-pq-hero-colormode13/RESULTS.md)和[nativeCI](../Evidence/macOS13-hdr-candidate/native-pq-hero-native-ci13/RESULTS.md)的阴性结果也未比较实际ImageRenderer输出与新CGImage的raw payload，因此不能排除任何一侧边界。
- 本机SDK14.2 `NSImage.h:190–218` 的公开契约是：从CGImage初始化的NSImage，其绘制等价于绘制该CGImage；这不是跨OS、跨目标context的结果相同保证。`CGImageForProposedRect` 则可能选择已有表示或重新生成绘制快照，受context/hints/caching影响，不能拿它当原`pixels`读回。
- `CIImage.h:101–110` 的 `toneMapHDRtoSDR` 是Bool、macOS11起，未指定为false，仅当输入有HDR色彩空间才生效；它不提供数值target-headroom。SDK14.2当前NSImage init/draw、CGContext及CIContext声明未见给这条绘制链设数值target-headroom的参数，这不是对全部系统接口的穷尽证明。[WWDC23 10181](https://developer.apple.com/videos/play/wwdc2023/10181/)区分HDR安全存储、SDR目标转换与显示tone mapping；[WWDC24 10177](https://developer.apple.com/videos/play/wwdc2024/10177/)区分content/display headroom，并另介绍当年的headroom控制API。不能将这些新接口或旧Bool当作已验证的13修复。

## 单一最小诊断，不增加绘制分支或pane

1. 继续原default fixture、同一新binary的13/14、同一两key/窗口/两phase/五buffer及全部normal/front/cache/noMetal/noTimer门槛。snapshot只将**那一次已经返回的原CGImage**连同实际key加入有界强引用列表；原NSImage构造/返回/draw保持不变，不复制、relabel、再次renderer取图或创建CI/CGContext。主采集前清理边界冻结列表，cleanup期间的snapshot不再保留图；不按前两条/预期key悄悄截断，主条数与key必须实际为2。
2. 所有原PNG落盘、原窗口teardown完成后，才对这两对象各取一次 `dataProvider` / `CGDataProviderCopyData`（公开API，macOS10.3起）。它复制provider提供的数据，没有目标色彩空间或tone-map参数；可能触发lazy数据准备/同步，不能承诺零内部工作。保存原 `.bin`、完整长度/SHA和已有尺寸、rowbytes、bitmap/alpha/byte-order/pixel-format、ICC。先检查确为本轮已记录的16float/RGBA64/16Little/premultipliedLast布局，且长度**恰为**rowbytes×height；nil、未知布局或长度不符就明确停止raw解释，不用重绘/NSImage.cgImage/TIFF/CI转换补救。
3. 导出后明确释放图引用；记录retain开始（原snapshot）、终止（导出结束）、primary/cleanup边界及导出耗时。13两图的已知rowbytes×height合计3,686,400bytes，14为921,600bytes，可设有界内存/文件额度。原窗口7.9秒界限不延长；post-teardown导出另记时间并受原外层进程界限约束，不把导出冒充原采集时间。
4. **保留本身是新观察变量。** 同一probe只设retain/dump off/on开关，不添UI；off应复现既有v2，on应复现off的原PNG、12ROI及既有色块/几何检查。先做13控制；任一控制失败便保留失败资料，停止跨OS归因，不宣称延后读取已经消除观察效应。14仍须对自身既有基线核对，不能用metadata相同代替控制。具体执行由root决定，本方案不自动运行。
5. 离线先按已确认的布局读取原binary16 bits，保留raw bits；解释half→数值仅作标量解码，不执行色彩转换、clamp、unpremultiply、曲线或nits推算。对已有10个平坦色块内区记录RGBA min/mean/max、唯一bits/NaN/Inf及<0/>1数；先验证opaque内区alpha为1。按真实640×360/320×180及既定atlas坐标做整数映射，不硬resize到同尺寸，不根据颜色自动flip/平移以凑匹配。若raw行方向或采样位置无法确认，先保留数据而不比较。ramp的1×/2×采样差不能当成像素处理差。

## 能回答什么

- 若相同ICC、对应平坦内区的原float样本已不同，差异**到该snapshot边界已经存在**；仍不唯一归因ImageRenderer，也不排除后续绘制继续改变结果。
- 若这些内区样本相同而受控截图仍不同，差异在其后续原生绘制/目标context/窗口合成或捕获路径中；不能只点名NSImage.draw。不同scale意味着局部匹配不证明整幅payload相同。
- 元数据或API文字本身不能替代上述样本；不新增tone-map组合、跨平台API矩阵或手拟颜色修复。

本机依据：SDK14.2 `CoreGraphics/Headers/CGDataProvider.h:182–188`、`CGImage.h:22–64,219–289`；`AppKit/Headers/NSImage.h:190–218`；`CoreImage/Headers/CIImage.h:101–110`。`CGDataProviderCopyData`保证复制provider数据，不保证任意provider都是可直接按bitmap描述解释的raster，因此保留格式/长度失败门槛。所列头文件位于 `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk/System/Library/Frameworks/`；本次只读声明，没有做Swift类型检查。


## 执行状态（2026-10-24）

已完成[本机SDK14.2 off/on控制](../Evidence/macOS13-hdr-candidate/native-pq-hero-float13/RESULTS.md)以及[新SDK同binary13/14控制与raw导出](../Evidence/macOS14-hero-float-40091326190/RESULTS.md)。所有配对各12个raw/ICC归一区域精确复现，未据此宣称普遍零观察效应。保留完整原provider数据，原始行方向仍未证实；未执行语义色块值的跨宿主比较。

13旧/新SDK的raw各自逐字相同，14的named/custom raw彼此逐字相同。13/14的RGB范围接近而全buffer均值/部分计数有差，实际采样尺寸2×/1×不同；这不足以定位可见主差的原因。原snapshot后的native draw/context/compositor路径仍待分离。[下一观察](macOS13-Hero-Backing-Observation.md)先记录现有flight/root与真正overlay的图层/祖先事实，不假定已有图层或RGBA8，也不将简化父容器中的静态差异冒充完整应用flight缺陷。
