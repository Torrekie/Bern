# 下一条最小边界：先补原 CGImage 绘制语义

**本轮只提四个 deferred getter，不先做 direct CGContext 绘制。** root当前报告named十patch的RGBA原half bits13/14全exact（独立数值复核仍在进行）；这只排除了这些对应平坦内区的payload差异。1×/2×的整图/ramp/边界不等于全payload相同，而相同bits+ICC也不等于完整CGImage绘制语义相同。custom五块的微小差不能未经量化解释主要WindowServer差异。

实际源码 `BernAppKit.swift:1862–1864` 是一次renderer.cgImage→NSImage(cgImage:size:)；1933–1936是圆角clip后两次NSImage.draw。container/colorMode/源canonicalPQ→CI.RGBAh以及同actualsnapshot的stockNSImageView阴性结果，分别否定了那些单变量作为充分修复，未唯一定位NSImage、context、compositor或headroom。SDK14.2 NSImage.h:190以后称CGImage初始化的绘制等价，故directCG是将来可证伪adapter边界，不是已知修复。

唯一建议：在现有float-capture持有的**原renderer-return CGImage**上，全部原PNG和原teardown之后、原释放之前，一次记录 `renderingIntent.rawValue`、`isMask`、`shouldInterpolate`、`decode`。这些公开getter在本机CGImage.h:219/263–276均自macOS10.0可用。不要读NSImage.cgImage/TIFF、再取renderer、重读provider、重新缓存/构造/转换CGImage或创建绘制context；不改现有图像、ICC、draw、目标context和屏幕条件。

[Apple decode说明](https://developer.apple.com/documentation/coregraphics/cgimage/decode)定义每个色彩分量一对数值；已有非mask/RGB3分量格式合同成立时，非nil只立即复制6个CGFloat（不含alpha）。nil单独记录，不能替换成猜测默认数组；保存原数值及其有限Double bits，不规范化±0。未知色彩模型/分量、mask或无法安全有界记录时明确incomplete，不扫指针找终止、不构造替代图。只保留标量/数组，不延长decode指针寿命。

沿用原off/on对象保留生命周期及12ROI/cache/normal/front/native控制，off无新getter；新观察不得增加一次snapshot/provider读取。查询发生在原PNG后，但保留本身仍是观察变量，不能称普遍零观察效应。逐host/key比较四项：若不同，只能否定“这几项对象语义相同”，不能立即判根因或复制属性修产品；若全同，也只排除这些公开状态，后续adapter/context/合成/捕获仍待分离。缺字段或控制失败即停止，不加缓存/图层/曲线矩阵。

本轮没有实施getter、算法、产品/CI修改、构建或新UI。只交付此短计划；不把已有named平坦样本相同扩写为整个snapshot显示语义或物理HDR相同。
