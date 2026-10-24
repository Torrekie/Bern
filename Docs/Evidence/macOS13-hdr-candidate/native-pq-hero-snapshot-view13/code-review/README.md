# PRIVATE：original-snapshot NSImageView 源码审查

**PASS — 有界源码结论，未编译/运行。** 审读`work/hero-snapshot-native-view-preparation`的NativeDisplay、Driver、adapted Hero、两个patch、README/provenance；对照archived static-route13 fixture。未发现新增明显Swift类型/访问控制、同输入选择或清理控制流阻断。输入hash、检查及有限结论见`review.json`。

- Helper SHA256=`7f48e05a391ad8ba4a8babfffcc6895f6f489f103e103def4591bc8c0758f2b3`。mount只在image-view且index0继续；`image=picture.image`，要求`f.from===f.to===image`，再直接赋给stock NSImageView的image，无原/derived CGImage替换、readback、重缓存或snapshot变更。image.size只读；opaque/up/aspect/corner0/固定320×180前提来自已生成ledger和已验证atlas，未把alphaInfo当opacity证明。
- control的mount/check/cleanup在读取新image/view属性前返回；finish仅置scalar success。call-site有新的现有ledger字典查找和参数传递，draw也有新增false Bool分支，因此不能声称零observer effect。custom/index1在读取picture.image前返回。false flag之外，原Hero绘制路径及snapshot逐字不变。
- helper的child/flight/expectedImage全弱；真实Flight的from/to和stock child自然拥有原NSImage。Driver在调用mount前已将overlay flight放入外层owned数组，故普通throw展开后，defer仍有强owner可供child清理。records只留scalar/class/id/geometry/configuration。orderOut后先child.image=nil、detach，之后才移除原fixture flights并关闭window；没有全NSImage释放的虚假断言。missing child/不完整清理会置finalizationFailed、native success=false、整体report失败并影响exit。
- 两patch均逐字等于实际base→prepared diff；main前Driver prefix逐字相同；删去Hero的新false flag与draw开头return后逐字回到base。provenance的10项base及6项generated字节数/hash均匹配。新增helper无显式layer/display/layout/RunLoop、provider读或图像转换；原Driver的两处RunLoop、一处layout/display、needsDisplay、CG capture及float finish调用点计数均未增加。旧静态progress0/1、五stable、默认observer/float off、actual overlay和原native/cache门槛保留。
- 普通catch记录helper失败、保留已完成records/captures；PNG保存及hash后才执行post-PNG检查，之后才推进phase。helper仅在原final gates完成后置success；cleanup再检查并可推翻success。helper成功标志只是子门槛，不能取代整体report/receipt或像素验收。

两项继承报告边界应限定README/操作口径：原Driver最终report使用`try?`，写失败未变成非零exit；源本身也没有已有report/PNG拒绝覆盖，fresh输出需调用方保障。硬watchdog只写`hard-deadline.txt`并`_exit`，不执行defer，不能保证完整partial report。因此“失败保留partial且非零”只适用于普通catch并成功写report的路径；不是本patch新增回归，本次未扩修。legacy顶层scope仍描述actual Flight.draw，候选named已skip，必须合并`native_display`解读，不能单引旧scope。

该source允许继承的expected13/14，当前授权的候选运行应由wrapper限定本机13。stock NSImageView的实际可见内容、方向、raster/colors/ICC、control复现及相对14的H−B残差均未由source证明；缺图/错图不能写成颜色结论。仅限opaque/up、同aspect、corner0、from==to固定端点，不能外推custom/alpha/其他方向/fit/corner、真实flight/crossfade、High/HLG或产品修复。没有改输入source/产品、编译/typecheck、测试、UI、CI或新像素算法。记录2026-10-24T17:00:11Z；本目录仅README/review.json/SHA256SUMS，manifest后冻结只读，无source/大图副本。
