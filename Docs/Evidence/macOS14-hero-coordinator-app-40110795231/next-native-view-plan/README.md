# PRIVATE：下一最小原生颜色对照

建议先补一个本机13的**同snapshot、仅换显示组件**静态对照；暂不把Flight改成直接显示原图的NSImageView产品方案。现有数据已否定“匹配13 body就等于匹配14 Hero”的依据，但尚不足以否决NSImageView显示实际snapshot NSImage的路径。本轮app-loop的native/execution与位移结果由root提供；此处不再提出事件循环变体，也不重新做像素分析。

已有离线证据可直接缩小取舍：

- `outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/native-sdr-components13/validation.json`：13、current/potential headroom1/2、正确320×180pt下，原named-PQ CGImage→NSImageView与直接SwiftUI图像在640×360 raw/ICC→sRGB RGB逐像素exact。该组件沿用`imageScaling=.scaleAxesIndependently`、`imageFrameStyle=.none`，NSImage logical size也是320×180；旧错误逻辑尺寸已被排除。这个输入没有经过Hero的ImageRenderer。
- 实际`ProductHero.exact.swift:82–98`先以原Picture/方向/fit构造SwiftUI Image，再由默认ImageRenderer生成CGImage并包成NSImage；`:155–170`的Flight只接收from/to NSImage，使用两次sourceOver绘制和corner clip。因此只换Flight显示器时应给NSImageView原`p.image`，不能偷偷改成原/derived CGImage、再次取CGImage/TIFF或绕过snapshot。旧原生组件exact不能预测这一输入的输出。
- 冻结的14真实静态参考`macOS14-hero-snapshot-40080838898`证明Hero14也不等于body14。现成`default-vs14/comparison.json`的p0/named指标为：`D=mean(hero)−mean(body)`，当前`|D13−D14|`十色块RGB均值绝对平均5.210863；若假设新H13=B13，则同指标必变成现成`|D14|`平均14.951694。这是既有统计的代数推论，不是NSImageView新输出预测。14的warm812蓝通道D约96.10、white203红通道约25.97；把D13一律压成0会破坏已有接近项。故不能用body exact或单个cool812改善当14等效目标。

下轮只需补的具体控制：在已有静态snapshot夹具中，保留原默认`BernHeroFlightView.draw`控制；一个候选只用已有NSImageView显示**同一实际snapshot路径产生的NSImage**，不改snapshot、源/cache/ICC、fit、几何、parent route、observer入口或默认渲染设置。锁定`from==to`、p0/p1、corner0、320×180pt且与atlas同aspect，先做现有opaque、EXIF-up的named PQ atlas；custom-cICP亦不可从named结果自动推出。默认控制须先复现冻结的同host raw/sRGB ROI；否则停止解释候选。原actual-overlay parent、坐标回转/no-MTK（含sibling subtree）、五稳定buffer、normal/cache/front/nonkey/inactive及窗口限期照旧。只用原NSImage对象赋给image属性，保留logical size，清理时置nil；不加layer setter。

先用冻结的十色块/灰阶ROI和现成14参考比较候选的signed H−B及D13−D14；不得跨13的2×与14的1×硬resize或要求raw全图相等，也不能从异步运动mid图反推静态颜色ROI。若同snapshot NSImageView输出与默认Flight exact，则这个display-only方向可在该范围内关闭；若有变化，先报告所有色块/灰阶的改善和恶化，再决定是否值得进入真实flight，不能只挑最大残差或平均值宣称通过。当前没有该同输入显示对照，无法离线预言结果；新增一轮14或真实动画不是这个最小未知所必需。

这只是可逆私有static candidate的取舍提案。广泛方向、alpha、其他fit/aspect、corner、不同from/to的crossfade、缩放移动、High/HLG、动态intent及完整产品仍未验收；opaque/up/aspect限制只约束夹具，不做文件SHA产品白名单、RGB补偿、自创tonemap或图像特判。未写Driver/产品、编译、运行UI/CI或新像素算法，未复制大图。仅读取冻结小报告/源码并写此README及SHA256SUMS；下轮再实现。记录时间2026-10-24T16:27:13Z。
