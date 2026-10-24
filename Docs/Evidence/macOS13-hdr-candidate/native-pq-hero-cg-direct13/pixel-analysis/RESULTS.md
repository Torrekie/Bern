# CG direct：有界阴性结果

冻结runner单次执行完成，三个host分析和两个crosshost比较全部exit0。三份原算法/spec字节未改；Python3.14.6、Pillow12.3.0、LittleCMS2.19。未运行新UI、CI、构建、方向/tuple算法或新采样。准备态README/provenance/PREPARED-SHA256SUMS保留原字节，属于执行前检查点；本文件及result/是获root授权后的结果。

**default→direct的全部12ROI在raw编码RGB及ICC→sRGB均exact。** named候选两个端点没有任何像素变化，其它10pane全部exact。13两模式使用root已验证的同一localSDK14.2二进制 `be263dfbd54a965003c8adc82c2294475963cb9463fc86c6daedcc89a09d8fd0`。14使用已有cgsemantics cohort/on；对它的重算严格匹配旧冻结14的版本、analyzer/spec SHA、68个comparisons、16个primary、两个phase全部ROI记录及ramp gzip SHA。这不是本轮新跑14或新的跨host同binary主张。

全部十patch、全部RGB通道的 D13−D14 均保持原值。下表default与direct数值相同，单位为8bit编码sRGB码值；分类为每组30个patch/channel的改善/恶化/不变，不用感知阈值或均值掩盖退步。

|phase|source|mean absolute residual|max absolute residual|改善 / 恶化 / 不变|
|---|---|---|---|---|
|progress-0|named|5.2108630952380945|112.61632898351648|0 / 0 / 30|
|progress-0|custom|5.223883928571423|112.61873282967032|0 / 0 / 30|
|progress-1|named|5.224399038461538|113.04833447802197|0 / 0 / 30|
|progress-1|custom|5.236956272893773|113.04833447802197|0 / 0 / 30|

named/custom、p0/p1的gray-ramp aggregate RGB残差变化均为[0,0,0]，全部native列数据仍在各host分析的ramp-column-means.json.gz，包含raw及sRGB域；无跨host列配对、resize或拟合。完整逐patch/通道signed值、绝对残差变化、分类与全ramp统计在 `result/summary.json`；原host内全部比较和两组crosshost结果亦保留，未挑色块或通道。

几何门槛先于算法：root绑定原PNG逐p0/p1目检upright、非空、三行/ramp及完整可见extent通过；这是visual-only，没有运行tuple门槛。白色与背景同色处不可分，alpha255/frame不单独证明每像素覆盖或亚像素边缘；仍保留这些限制。原native、default旧on12ROI控制及raw一致由root-validation记录，离线脚本不重新证明运行时对象。root-gates绑定三报告/六PNG，运行前后均复核；前置context见INPUT-SHA256SUMS。

结论仅为本机13 opaque/up/same-aspect/corner0、同原renderer-return snapshot的静态p0/p1中，绕开NSImage适配直接CG绘制没有改变结果，也未改善对14的原残差。它否定该单变量在此夹具中作为充分修复；不定位context/合成/捕获/OS为唯一原因，不外推其它方向、alpha、fit、圆角、实际协调动画、High/HLG、物理HDR或产品验收。不继续display-widget变体。
