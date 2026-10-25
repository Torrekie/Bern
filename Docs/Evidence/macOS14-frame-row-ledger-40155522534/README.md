# e48 Frame Row：真实14采集与记录截断

[CI40155522534](https://github.com/Torrekie/Bern/actions/runs/40155522534)在实际macOS14.8.9/arm64取得原e48与观测版关闭状态Frame原图。构建job成功，capture job在观测组完成截图后因`Missing/truncated row placements`失败；PixelGate步骤未运行，不将该CI或记录宣称验收通过。

产品源码固定`e48fff46b3a92a28465ad74295bd273a9d69af7d`，harness固定`7987f3527dc4461957eb17b718c58aac11759ab0`。构建沿原产品plan，以Xcode26.3/Swift6.2.4/SDK26.2、arm64/min13构建观测应用和两只外部helper；远端最低版本与严格签名检查通过。原control直接复用CI40070407306的e48原件，未重编。观测GUI为`eabdde25…e5b06f0`，CLI仍为原`31a75c0a…f379f5`；两只helper的原SHA与min13/SDK26.2回读在采集产物中保留。本机未下载这些临时二进制，也未替换交付App。

| 本次原报告 | 结果 |
| --- | --- |
| control A | success=true；真实Ready→Paused0、超过3.2秒awake、关闭状态stable4原图、原窗口ID/ownPID/ICC门槛通过；清理后stopped、termination0 |
| observer B | 同样取得稳定原图和最终关闭/Paused0上下文；记录器随后因byte_limit使报告success=false；清理后stopped、termination0 |

原packet最多64KiB/64条完整置放，实际在0.1721741667秒内保留序列0–34共35条、63828B后触及字节上限，明确`truncated=true`。这是前期布局产生大量置放而触发的**采集保留上限**，不能由这个有限前缀解释Caption/Size差异。未读这些宽度值作根因判断，也未上调上限、忽略截断或再次触发CI。

root目检两张原PNG，并用PIL/numpy离线比较原存储RGBA；独立复核以PIL/逐pixel bytes重算。两图均为920×668、原PNG SHA与capture报告一致、ICC相同。预先固定的Frame detail `[211,52,920,668]`原像素完全相同；整个窗口仍有5284像素差异，边界`[10,118,200,146]`位于侧栏选中行。没有采集firstResponder，不指定侧栏差异原因。这只补充失败cohort的图像事实，**不是PixelGate PASS、完整记录或13/14视觉等效**。

原图：[control](runtime/a/frame-closed-light.png)、[observer](runtime/b/frame-closed-light.png)。原报告、失败packet和所有CLI收据均原样保留。下载artifact12584493248共151597B，实际ZIP SHA256 `5845fce6497e2ee7a43b5ee303e4e51692f71965457f71a5eb462cd47200a058`在删除前匹配API digest，170个成员提取后保留；独立复核仅核已删除ZIP的收据，没有声称二次重算。

下一步只修正[保留合同](result-review/LATEST1.md)：使用新的schema保留**最新一条完整置放**，显式记录总完成数/已替换数，仍限制单packet64KiB；不改原查询、数学、place顺序、UI或采样节流。单条超限/不完整/编码或I/O失败仍拒绝，保留原时间关联与像素门槛，latest不称settled。方案尚未实现或运行；若新时间关联不成立，不放宽门槛或扩矩阵。

本机13尚未运行。Gallery专用kernel guard与仅cleanup变体的collector草稿仍有未完成检查，冻结为禁止执行的待续输入；它不冒称已接管旧defer，也不会把不同helper binary说成跨系统同binary。后续主观测产品仍须使用同一原件，13的A/B须使用同一经核验的采集适配。

[独立失败复核](result-review/README.md)、[离线原像素结果](offline-analysis/offline-result.json)、[下载收据](download.json)和[清理/原交付核验](root-review/result-and-cleanup.json)随同保留。所有已用work结果树移入这一归档后以相对别名引用，没有保留重复payload；未执行的13草稿仅保留在work，不作为交付或通过证据。

准备包的三项本机SDK14.2/min13类型检查均通过；临时模块缓存49,800,734B在无编译器/打开文件后清理，数字为逻辑文件量，不是APFS实测回收。本轮没有本机App副本、运行进程或UI操作。此次已实际使用远程14，不满足“连续数小时无法采集14”的暂停条件。整个macOS13阶段仍未验收、goal active，后续11/Swift5.3、Objective-C与iOS仍推迟。
