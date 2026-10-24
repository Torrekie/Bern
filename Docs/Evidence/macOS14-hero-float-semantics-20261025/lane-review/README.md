# PRIVATE：retained float snapshot 的 memory-lane 合同审查

**可以固定导出接口的lane0..3=R、G、B、A；每lane为little-endian IEEE754 binary16，颜色分量为premultiplied。** 这是Apple公开格式合同与实际导出metadata/源的对应结论，不使用颜色“看起来像”、13↔14接近程度、通道排列搜索或alpha恒1补证。row方向仍unverified，本审查不解决几何命名。

决定性证据为本机Apple公开SDK13.3的`vImage_Utilities.h`（经MacOSX.sdk symlink解析，精确路径/完整SHA见review.json）：

- **55–60**说明`vImage_CGImageFormat`描述颜色channel顺序/数量/类型/alpha，并镜像CoreGraphics的CGImage/CGBitmapContext格式描述。
- **84–90**定义alpha-last包含`kCGImageAlphaPremultipliedLast`，并明确把16bpc/64bpp、alpha-last、floatComponents、byteOrder16Little这一组合列为`RGBA16F`。这是所需的直接格式对照，不仅是CGImage.h的RGBA示例。
- **452–455**说明当bpc>8时，端序单位按channel的大小解释；此处16Little因此作用于每个16bit分量。**677–679**规定16bit float为IEEE754-2008 binary16。
- **461–470**还明确：CGDataProviderCopyData返回格式由实际CGImageGetBitmapInfo/ColorSpace/BytesPerRow/BitsPerPixel/BitsPerComponent等getter描述，不能以创建请求替代实际导出格式，也不能声称这就是CGImage内部/GPU物理存储。

`CGImage.h:22–65`给出alpha1、float0x100、16Little0x1000、packed0；故4353=0x1101与这些位完全对应。`CGColorSpace.h:31–40`确定model1为RGB。两份actual on报告1974–2096的primary descriptors/导出records均记录RGB3分量、16bpc/64bpp、bitmap4353、alpha1、byteorder4096、pixel-format0；13 stride5120/640×360，14 stride2560/320×180，均为8 bytes/pixel无padding，带同一ExtendedSRGB ICC。这里只重读小report，没有重新读取raw字节或native对象。

|每8-byte pixel内偏移|格式语义|
|---|---|
|0–1|R，binary16 LE|
|2–3|G，binary16 LE|
|4–5|B，binary16 LE|
|6–7|A，binary16 LE|

实际导出源`FloatCapture.swift.inc:29–40,48–105`保留原CGImage；严格检查格式后，从该对象provider直接取得Data，要求长度恰为rowbytes×height，再写原bytes，无转换fallback。`ProductHero.swift:85–102`在renderer.cgImage返回后、NSImage包装前传入同一个对象。现有`analyze_float.py:24–28,106–122`以`<4H`顺序读四个16bit word，以`<e`解释half，并按RGBA命名；其读法与上表合同一致。现有alpha恒1只属于一致性观察，不是选择A或证明RGB排列的依据；本审查没有重算它。

Apple网页交叉核对：[CGBitmapInfo](https://developer.apple.com/documentation/coregraphics/cgbitmapinfo)、[premultipliedLast](https://developer.apple.com/documentation/coregraphics/cgimagealphainfo/premultipliedlast)、[byteOrder16Little](https://developer.apple.com/documentation/coregraphics/cgbitmapinfo/byteorder16little)支持相应枚举/端序说明；[vImage_CGImageFormat](https://developer.apple.com/documentation/accelerate/vimage_cgimageformat)的精确RGBA16F桥接证据以已读取的SDKheader为准。旧Quartz网页的supported-format表不足以单独证明本case的half-float组合。

适用范围只到保留provider导出接口的lane/数值表示合同。没有假设源PQ数值应直接保留，没有应用ICC/transfer、clamp、unpremultiply或换算nits；没有证明row序、十patch空间对应、颜色等效、唯一OS/系统原因或产品修复。root可在独立几何验证中固定此lane合同，不做RGB排列搜索；row歧义依然应fail-closed。本轮无源修改、新算法、raw大复制、UI、CI、新构建或运行decoder。记录2026-10-24T17:19:53Z；仅README/review.json/SHA256SUMS并冻结只读。
