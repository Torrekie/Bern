# Actual-snapshot system-SDR candidate：混合改善，仍非等效

冻结runner单次运行完成，三个host分析和两个crosshost比较均exit0；Python3.14.6、Pillow12.3.0、LittleCMS2.19。14/on重算严格匹配旧冻结14的版本/analyzer/spec SHA、68个完整comparisons、16个primary、全部逐phase ROI及ramp gzip SHA。三份原算法/spec不变，未跑新方向/tuple算法、UI、CI、构建或新采样。准备态README/provenance/PREPARED-SHA256SUMS保留原字节；本文件及result/为获root通知后的执行结果。

**named的总体残差下降，但不是单调改善，不能据此采用。** candidate相对default只改变named两个phase；其余10ROI raw+sRGB均exact。13两mode的同一localSDK14.2 binary为 `e555781e4f3c647243017e33a6ea64f0393e667a8e71e9ce29998dc2365d15dc`；14为保留的cgsemantics/on参考，不是本轮新跑14。default旧on12ROI与原raw不变、原native/additive gates由root-validation承担，离线分析不重新证明运行时对象。

目标始终为 `D13−D14`，Dh=Hero_h−body_h，不是bodyexact。下表使用全部十patch×RGB通道，单位为8bit编码sRGB码值；mean/max都是patch-mean残差统计，不是整图像素MAE、线性光或nits。分类逐通道精确按计算值正负/零，未设感知阈值。

|phase|source|mean absolute residual：default→baked|max absolute residual：default→baked|改善 / 恶化 / 不变|
|---|---|---|---|---|
|progress-0|named|5.210863095 → 1.525197459|112.616328984 → 25.754035027|5 / 7 / 18|
|progress-0|custom|5.223883929 → 5.223883929|112.618732830 → 112.618732830|0 / 0 / 30|
|progress-1|named|5.224399038 → 1.567882898|113.048334478 → 26.186040522|3 / 9 / 18|
|progress-1|custom|5.236956273 → 5.236956273|113.048334478 → 113.048334478|0 / 0 / 30|

cool812 R两phase均减少86.862293956码值，但仍留p0约25.754035、p1约26.186041的残差。red812 B与warm406 B改善明显；同时green、yellow、blue、red和cool的其它通道出现新退步。以下列出**全部16个恶化patch/channel项**，不是抽选（显示9位小数；完整精度见CSV/JSON）：

|phase|patch|channel|default D13−D14|baked D13−D14|绝对残差增加|
|---|---|---|---|---|---|
|progress-0|blue812|B|0.116758242|-0.204069368|+0.087311126|
|progress-0|cool812|G|0.000686813|-0.222699176|+0.222012363|
|progress-0|cool812|B|0.003949176|-0.123368819|+0.119419643|
|progress-0|green812|R|-0.137362637|2.298076923|+2.160714286|
|progress-0|green812|B|-0.118818681|1.367874313|+1.249055632|
|progress-0|red812|G|-0.133585165|0.600961538|+0.467376374|
|progress-0|yellow812|B|-0.119505495|2.036143544|+1.916638049|
|progress-1|blue812|B|0.000000000|-0.320827610|+0.320827610|
|progress-1|cool812|G|-0.100961538|-0.324347527|+0.223385989|
|progress-1|cool812|B|-0.112122253|-0.239440247|+0.127317995|
|progress-1|green812|R|0.000000000|2.435439560|+2.435439560|
|progress-1|green812|G|0.000000000|-0.018458104|+0.018458104|
|progress-1|green812|B|0.000000000|1.486692995|+1.486692995|
|progress-1|red812|R|0.000000000|-0.177111951|+0.177111951|
|progress-1|red812|G|0.000000000|0.734546703|+0.734546703|
|progress-1|yellow812|B|0.000000000|2.155649038|+2.155649038|

`patch-channel-changes.csv`完整包含named/custom、p0/p1、十patch及全部RGB的120行有符号残差、signed change、绝对变化、分类，含所有改善与不变；同值保留，不归零或隐藏。result/summary.json和两套crosshost/comparison.json保留完整host内均值与向量统计，全部host analyzer比较亦保留。

**ramp也非单调改善。** named aggregate的绝对残差变化p0为[-0.001424051,-0.000494462,-0.002511867]，p1为同量正值：p0三通道变小、p1三通道变大。custom两phase三通道全不变。ramp-channel-changes.csv保存全部12项完整精度；每host/每pane raw+sRGB native列、mean/min/max在各child analysis的ramp-column-means.json.gz和summary中，无13/14不同列数的配对、拟合、resize或曲线调整。

完整snapshot_sdr_display记录已原样保留。candidate记载conversion/context各1、用时0.2589792917133309秒、输出640×360/RGBA8/sRGB/extended=false、引用清理通过；default conversion/context为0。requested_tone_map_hdr_to_sdr=true，但 actual_tone_mapping_applied='unknown'；本报告不把请求或输出格式当作系统已执行tone mapping的证明，不归因为唯一根因。

root在读完整颜色结论之前，按冻结几何计划逐p0/p1查看原PNG，upright/非空/三行ramp/完整可见extent通过。该门槛为visual-only，未跑tuple检查；白色可与白背景合并，alpha255/frame不证明每像素覆盖或亚像素边缘。root-gates绑定三report/六PNG，运行前后均核对，source/runtime支持与这些可见性限制保留在root-geometry/root-validation；INPUT-SHA256SUMS记录其context哈希。

本步只说明actual-snapshot的这个系统SDR候选在本机13 opaque/up/same-aspect/corner0静态p0/p1中改变了显示，有大残差降低，也有全部保留的通道退步和未消除残差。它不足以成为产品采用/13与14等效结论；未验证一般方向、alpha、fit、圆角、实际协调动画、High/HLG或物理HDR。不调阈值或图像来掩盖退步，不从单色块或均值推出修复。
