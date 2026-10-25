# 原 e48 controls：13/14 离线复核（冻结）

本轮仅是未插桩 plain13 与成功14 control 的事实对照，非 PixelGate、跨OS原像素等效、布局验收或原因判断。两报告均 success、ledger=false、normal三项false、closed/Light/captiontrue/Paused0。未读或解释 Row ledger。

13 原PNG ece61b2d…aff37f3，1840×1336/2×；14原PNG ef6951d5…eccfb6b，920×668/1×。actual PNG及embedded ICC SHA均与报告对应。ICC分别e2473ef4…ef9b64d4（4032B）和3d40c076…eb5f55（3300B），不同；不做跨scale raw exact 判定。原报告/PNG未改，完整绑定在spec.json/result.json。

| 相对 main outer 的点坐标 `(x,y,w,h)` | 13 | 14 | 13−14 |
|---|---|---|---|
| frame.clip / AXUnknown | (251,167,629,354) | (251,167,629,354) | (0,0,0,0) |
| frame.volume / AXButton | (620.5,533,20,20) | (619,536,22,15) | (+1.5,−3,−2,+5) |
| 共同 content AXGroup | (211,52,709,616) | (211,52,709,616) | (0,0,0,0) |

Volume中心差为(+0.5,−0.5)pt。已核screen减main outer等于报告relative值；各自全部已有native_geometry阶段框一致（13八阶段、14五阶段），不据此证明永久settled。定位来自原CLI标签/role/action和同一owned AXGroup关系；两边actual_ax_identifier都继承main_window.find，不能冒充直接target ID匹配。这不是Caption/Size的Layout宽度、Cocoa类或bezel/ink测量。

固定历史Frame ROI `[211,52,920,668)` points 在本次记录中恰等于该parent范围；仍使用事先固定ROI，没有按当前图拟合。13原ROI像素为`[422,104,1840,1336)`，14为`[211,52,920,668)`。原ROI有透明/半透明边缘：13共118 native pixels、14共33。

外观诊断算法在spec.json预声明后只执行一次：Pillow12.3.0/LittleCMS2.19，分别用各自embedded RGB ICC→同一保存的sRGB profile，intent0(perceptual)、flags0、无BPC，保留alpha；13固定整数2×2 BOX到709×616、14保持1×。Pillow RGBA BOX采用encoded-sRGB8 premultiplied RGBa再反预乘，**不是linear-light/物理亮度误差**。两profile均可识别且支持该转换，执行无错误；若不支持本来会停止raster阶段。实际target-sRGB.icc仅588B，已保留哈希。

完整固定ROI共436,744点，处理后RGBA不同219,513点（50.2613%）；平均绝对差RGBA=`[4.210645,1.406955,2.683171,0.000151]`（0…255），max=`[191,131,131,7]`；alpha不同21点。各通道差异数全部保留于result.json，不挑通道或取最佳结果。

另列双方归一后alpha都255的436,709点，RGB平均绝对差`[4.210568,1.406758,2.683034]`、max`[191,131,131]`。这是明确alpha语义的固定ROI诊断，不把透明RGB当可见色差；全ROI RGBA结果仍完整保留。processed hash不等于原PNG/raw hash，不设通过阈值。

没有自适应ROI、拟合、新region matrix、输出图或算法选择。私有CFID/签名、OS、display/ICC/scale及CI/本机cleanup差异仍在；这里不归因、不解除旧observer或全UI门槛。Root另做原图目检，本review未替代。

仅运行私有离线Python分析；未运行App/CLI/helper、编译、UI、CI或网络。execution.json保存exit0/空stderr与输入未变收据；所有原图留在原路径，没有复制或修改。
