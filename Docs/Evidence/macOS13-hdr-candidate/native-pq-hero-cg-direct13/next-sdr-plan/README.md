# 单一下一候选：actual snapshot 的固定 SDR 烘焙

**可作一条尚未测过的显示边界 recipe，不能称为已知修复或已知 tone mapper。** root刚报告 direct/default 全12ROI raw+sRGB exact、原raw不变、完整十块/ramp残差零变化；这表明仅替换 NSImage→当前 CGContext 原语在该case不足以解决主差，没有唯一定位OS、context、headroom或显示合成。

已核旧 `native-pq-hero-native-ci13/fixture/NativeCI.swift.inc:55–99`：输入是 cached canonicalPQ／原Picture CGImage，输出RGBAh/extendedSRGB。已核原 `ProductImage.swift:36–64`：RGBA8/sRGB也只用于原Picture/PQ Standard。已审相关hero归档源码中未发现“同一次 renderer-return float snapshot→RGBA8/sRGB→原NSImage.draw”的等价实验；新候选不重复旧 nativeCI。

SDK14.2 `CIImage.h:101–110` 明定 toneMapHDRtoSDR只在输入CGColorSpace为HDR时生效，默认false。当前snapshot的extendedSRGB与大于1样本**不单独证明**CoreImage将其分类为此合同中的HDR。故保留实际snapshot ICC，不重标PQ、不伪造HDR空间；报告只能写 requested=true、tone-map执行未知。固定sRGB/RGBA8输出本身是新的、公开定义的SDR目标转换边界，值得以一次recipe实测，但其结果不能归功于Bool。

唯一配对为13 default／baked-named：继续取得并保留同一次原renderer.cgImage，原FloatCapture观察/export/release不变。只对Standard、named、已知opaque/up/same-aspect/corner0固定端点，将**这个snapshot**交给CIImage（toneMapHDRtoSDR:true，沿用图像自身空间），用一个普通CIContext从精确原extent创建RGBA8/sRGB CGImage，deferred:false。CIContext.h:318–352明确格式/目标空间及deferred:false在调用时渲染一次，10.12起可用。按原snapshot身份/尺寸缓存一次named派生显示图，再用原NSImage尺寸构造显示包装、沿原两条NSImage.draw与p0/p1路径；不resize、旋转、滤镜、曲线或directCG分支。custom/body/oracle不变；这不是High或产品缓存合入方案。

缓存只持有新的SDR显示派生，原snapshot仍由原Held所有；不能覆盖原图/profile/Picture缓存，不能让旧CGdirect弱关联宣称派生NSImage由原CGImage直接构造。记录实际原/派生身份、原extent、请求true、输出尺寸/8bpc格式/实际sRGB ICC、一次生成计数及失败，无provider重读或伪fallback。空/未知格式、尺寸改变、CI失败或原7.2/7.9/外15秒门槛不满足即incomplete，不为CI预热延长期限。

default先复现既有12ROI、原raw/semantics与native/cache/normal/front控制；candidate原raw保持，另外10ROI须exact。named两phase先验非空、完整extent、上下不对称atlas/三band/ramp方位与无背景泄漏（alpha255不充分），再以冻结14默认Hero为目标，完整比较十块/ramp的(D13_baked−D14_default)与(D13_default−D14_default)，保留各通道signed差及全部变坏项。不能用Hero13=body13或单块改善替代目标。即使变好，也只证明固定SDR烘焙recipe敏感；不能分辨Bool与输出目标各自贡献。阴性则记录并停止此recipe，不继续颜色/缓存/图层矩阵。

本轮仅源码/本机公开头文件核查和短计划；未实施、构建、运行UI/CI、读新raw、写产品/算法或修改旧档案。合同本地已足够，无新增联网研究。
