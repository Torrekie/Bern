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
- 若这些内区样本相同而受控截图仍不同，还需区分CGImage的其它绘制语义、后续原生绘制/目标context/窗口合成或捕获路径；不能只点名NSImage.draw。不同scale意味着局部匹配不证明整幅payload相同，相同bits/ICC也不等于整个图像对象语义相同。
- 元数据或API文字本身不能替代上述样本；不新增tone-map组合、跨平台API矩阵或手拟颜色修复。

本机依据：SDK14.2 `CoreGraphics/Headers/CGDataProvider.h:182–188`、`CGImage.h:22–64,219–289`；`AppKit/Headers/NSImage.h:190–218`；`CoreImage/Headers/CIImage.h:101–110`。`CGDataProviderCopyData`保证复制provider数据，不保证任意provider都是可直接按bitmap描述解释的raster，因此保留格式/长度失败门槛。所列头文件位于 `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk/System/Library/Frameworks/`；本次只读声明，没有做Swift类型检查。


## 执行状态（2026-10-24）

已完成[本机SDK14.2 off/on控制](../Evidence/macOS13-hdr-candidate/native-pq-hero-float13/RESULTS.md)以及[新SDK同binary13/14控制与raw导出](../Evidence/macOS14-hero-float-40091326190/RESULTS.md)。所有配对各12个raw/ICC归一区域精确复现，未据此宣称普遍零观察效应。保留完整原provider数据，原始行方向仍未证实；未执行语义色块值的跨宿主比较。

13旧/新SDK的raw各自逐字相同，14的named/custom raw彼此逐字相同。13/14的RGB范围接近而全buffer均值/部分计数有差，实际采样尺寸2×/1×不同；这不足以定位可见主差的原因。原snapshot后的native draw/context/compositor路径仍待分离。[下一观察](macOS13-Hero-Backing-Observation.md)先记录现有flight/root与真正overlay的图层/祖先事实，不假定已有图层或RGBA8，也不将简化父容器中的静态差异冒充完整应用flight缺陷。

## 独立行序与平坦内区语义（2026-10-25）

[纯离线语义归档](../Evidence/macOS14-hero-float-semantics-20261025/README.md)现已补足上述unknown：Apple SDK直接格式合同确定RGBA16F LE lanes；预声明十flat/三band/五x-bin tuple结构只测试两个y方向，四raw都唯一top-down，独立Fraction/struct实现逐项复核。没有以颜色或跨host接近选择方向。两源PNG无损解码active SHA复现旧值，未复制raw/PNG或触发新构建/UI/CI。

冻结原analyzer在独立review绑定之后才运行known方向，另一独立struct<4H/<4e reader确认40flat全区恒定/alpha1、20patch/80delta及4whole/44region统计。named十patch RGBA原half bits13/14全同；custom五patch不同，RGB最大原数值差0.001953125、30项绝对差平均0.000244140625。原负值/>1/NaN/Inf/alpha计数完整保留，不做ICC/transfer/clamp/unpremultiply/nits转换；ramp各自632×80/316×40，仅记native aggregate，不注册跨host列。

named主显示差不能用这些对应平坦内区的raw数值差解释，但仍未证明整幅图或CGImage全部绘制语义相同。下一[唯一检查点](../Evidence/macOS14-hero-float-semantics-20261025/next-display-plan/README.md)是PNG及原teardown后的deferred renderingIntent/isMask/shouldInterpolate/decode getter；RGB非mask decode只可有界读六值，nil单列。它尚未实现/运行，不先加入directCG/cache/图层等变量。任一对象字段差异也只是新的边界证据，不直接指定根因或修产品。

filter0 source parser拒绝及pretty JSON体积失败分开保留；成功版本只补标准PNG无损过滤解码并压缩JSON排版，几何判据与128KiB上限未放宽。这些程序失败不算颜色证据。完整颜色/动画/UI、其它macOS13门槛继续未通过，goal active，11/Swift5.3/Objective-C/iOS仍延期。

## 延后读取四项显式绘制语义（2026-10-25）

上节唯一检查点现由[CI40119614788](../Evidence/macOS14-hero-cgsemantics-40119614788/README.md)执行：SDK26.2/Swift6.2.4构建的同一原签名arm64/min13 binary在13/14各完成off/on，原PNG/teardown/raw导出之后、原primary释放之前读取那两个实际CGImage。每对象只读renderingIntent/isMask/shouldInterpolate/decode各一次；RGB3 guard沿用前两条primary descriptor已持有的space，没有新增image.colorSpace getter或provider访问。

两key/两host均为intent0、isMask=false、shouldInterpolate=true、decode=nil；nil独立列空值，非nil/±0/nonfinite分支未运行。完整native/ICC/16字段与时序gate通过，四组旧→off及off→on各12图像ROI原RGB/sRGB exact，四raw与旧同host/key长度/SHA全同。独立审查分别覆盖源码失败传播、原包身份与native记录；不重复采集或将报告buffer一致性当独立捕获。观察耗时与原导出timer边界均保留。

此结果排除了这四项已读属性不同的解释，没有消除可见色差或证明全部对象/绘制context状态相同。下一[唯一计划](../Evidence/macOS14-hero-cgsemantics-40119614788/next-direct-plan/README.md)是13本机相同retention/原snapshot的默认与CG direct配对，尚未实施：原context内只替换named两条sourceOver绘制原语，先验证方向/非空/完整extent，再完整比较D13−D14；不将NSImage边界预定为根因或预测修复。产品没有修改，真实flight/general HDR及完整UI门槛仍未通过，goal active，后续阶段保持延期。

## 原 context 内直接绘制原 CGImage：阴性（2026-10-25）

上述[default/direct 实测](../Evidence/macOS13-hdr-candidate/native-pq-hero-cg-direct13/README.md)已完成。同一SDK14.2/Swift5.9.2原签名arm64/min13 binary、本机13两mode保持同held/weak NSImage绑定与原post-teardown导出/释放；direct只替换named两条绘制原语，局部一次y反转、normal/sourceOver、alpha1/clamp(p)及成对save/defer-restore，custom原样。完整native/ICC/float/semantics及附加gate通过；default→旧on、direct→default各12ROI原RGB/sRGB exact，四raw与旧同key直接bytes相同。

两phase原PNG的固定三行/ramp方向、非空和完整可见extent经root目检通过，保留white/background不可分、无逐像素覆盖及非真实flight限制。绑定这些门槛后，单次原算法完整十patch/ramp比较确认D13−D14全部通道变化0，原14参考完整重算一致。绕过NSImage适配在本夹具中没有改变主差；这不是全部NSImage行为或目标context因果的证明，停止此变量，不加widget变体。

下一[单一原生SDR烘焙表示](../Evidence/macOS13-hdr-candidate/native-pq-hero-cg-direct13/next-sdr-plan/README.md)尚未实施：只对实际renderer-return snapshot做系统CoreImage RGBA8/sRGB显示派生，再原NSImage绘制。旧nativeCI处理的是cached原PQ并输出RGBAh，因此不是等价已测输入；但Bool合同仅保证HDR CGColorSpace时有效，不能从extendedSRGB/>1断言它实际执行tone-map或预测修复。原资源/cache/raw保留，不重标PQ/手写曲线，继续以完整D13−D14及所有控制判读。产品未改，完整目标未通过，goal active，后续平台阶段保持延期。

## 系统 SDR 输出改变显示，但仍有残差与退步（2026-10-25）

上述[actual-snapshot SDR recipe](../Evidence/macOS13-hdr-candidate/native-pq-hero-snapshot-sdr13/README.md)已在本机13完成：named实际renderer-return CGImage经CIImage(true、原空间)→单CIContext→精确extent RGBA8/sRGB/deferred:false，再沿原NSImage双draw；default/custom不转换，原FloatCapture逐字保持。两原native/additive gate、default12ROI复现、candidate其它10ROI控制及四raw逐字相同均通过，实际toneMap仍unknown。输出SRGB8/nonextended，原和派生ICC3144B/SHA相同不能抹去range/format差异。

完整十patch/ramp报告保留全部退步：named p0/p1 meanabs(D13−D14)降至1.525197459/1.567882898，max降至25.754035027/26.186040522，但7/9通道恶化、ramp p1小幅恶化，custom不变。candidate两phase原PNG逐字相同；这些是相对14各phase参考的分类，不证明新phase-dependent转换。方向与完整可见extent为两原PNGvisual-only检查，不能推成逐像素覆盖或全UI等效。此输出边界在本夹具中有作用，尚不能隔离Bool/输出目标各自贡献或确定唯一根因，未合入产品。

一次转换约259ms，且真实Flight.started在同步source/destination snapshot之后。下一[唯一真实flight门槛](../Evidence/macOS13-hdr-candidate/native-pq-hero-snapshot-sdr13/next-flight-plan/README.md)已冻结但未实现：沿新SDK/min13/原timer/正常AppKit loop做一次Standard named替换，按两实际snapshot而非key合并派生，保留原生命周期及触发前延迟。静态clock guard不能用于真实13timer，产品intent链仍需显式传递，不能靠profile/key猜Standard。其它颜色/动画/UI与后续阶段边界保持，goal active。

## 真实两snapshot已在13完成，14新参考未完成（2026-10-25）

上述下一门槛现已[实际执行](../Evidence/macOS14-hero-coordinator-sdr-40129608288/README.md)。同一SDK26.2/min13原签名binary在13的default/candidate均通过完整原native/execution及新增两snapshot gate，default先复现旧13两个端点，candidate两个端点也raw/ICC exact。候选单context对两实际source/destination snapshot独立转换，以实际Flight.from/to弱NSImage绑定，原timer/tick/draw/期限不改；cleanup原路径一次且转换0。两转换约47.474/2.598ms，触发→started58.058ms、default27.438ms；两轮准备/render成本不同，差值不隔离为纯CI成本，首次live观察也不是显示首帧。

14 default确实运行并记录两个原float snapshot，但firstlive进度0、下一个.845710569，未进入(.2,.8)arm区间，197样本后原collection deadline失败，仅before PNG。CI build成功/measure失败及原收据/日志保留；没有新14中间与settled对照，不扩充为全native通过，不放宽门槛或重跑。远程设备在本次可运行，尚非等待数小时仍无14环境的暂停条件。

13原mid有可见位移、候选settled非空；白格与背景不能区分，视觉检查不证明完整像素覆盖/全动画等效，也不按不同progress配准计算颜色。此前静态recipe仍有7/9恶化通道等残差，产品intent传递仍是独立门槛，候选不采用。下一小步只读界定默认路径首次tick/观察空档；High/其它输入与完整UI验收保留，goal active，不提前后续系统/语言阶段。

## 正常效果14参考已补齐，结束本轮追时序（2026-10-25）

[Timing CI40132685948](../Evidence/macOS14-hero-timing-40132685948/README.md)以同一SDK26.2/min13 binary在13/14完成default；原native/execution/SDR及新增strict timing均通过，各3PNG。13两个对应端点复现旧SDR default13，14两个端点复现旧正常app-loop14，raw/ICC exact。两mid目检有可见位移、14最终目标非空，非同步帧/完整颜色或动画验收。旧40129608288缺样仍为失败，没有改band/期限或重试该run。

新增固定3native slots和前2live callback的内存标量使本次14空档范围缩小：started→timer注册后0.435ms、首callback前缀0.666ms、started→first tick159.427ms；首scalars结束→tick140.835ms仍未区分采样尾部、自动绘制或分派。13相应注册0.129ms、first tick9.159ms。first_applied复用tick的now/p，不是赋值结束或呈现；不同VM/进程与observer开销不允许据此回推旧215ms的唯一解释。

本次参考合同已完整满足，现有证据不支持产品clock改动；未知细段不阻挡使用此有限14参考，也不要求继续盲CI。回到实际UI的颜色退化、生产intent及Picture Scene布局等未通过项；SDR候选仍未采用，其余High/输入/物理HDR/全动画及后续平台/语言阶段边界保持，goal active。原binary/tar和重建source副本在独立实际pre/posthash后已清，源仍由提交的5-file overlay+base保存；详见本轮清理收据。
