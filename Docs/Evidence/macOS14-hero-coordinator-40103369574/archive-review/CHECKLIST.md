# 本批 checkpoint / archive 只读核对清单

状态：已完成本批有界只读 archive review，结果见 archive-review.json。整归档最终manifest及Git检查/提交/推送由root完成。本文件未修改验收文档或archive；准备时与复核时的输入快照分开记录。

## Checkpoint 应保留

- 准备时验收文档第202行“此方案尚未实现或运行”是上一检查点状态；现新增段已明确由 CI40103369574 和同 binary13 运行落实，历史文字已被当前检查点取代。
- 新 SDK26.2/min13/arm64 一次构建，原签名 binary `5739a0405bf78c04e71a46116c99fd48a7fa7b0b659bf8e97744ee3982ecea36`；harness commit `2e43bfb86126c8a03d85e0af45a0451ed3c5ed17`。真实同非空 key 的 SwiftUI 条件替换触发原 coordinator/clock，区别于上一批 manual 静态端点。
- 两端 native schema 通过：各一次 transition、单一 observed flight view identity、实际 timer/live frame/progress 变化、source 不再 attached、temporary view 移除、最终 flight/timer/temp count0。source_weak_deallocated 两边均 false，不能写成 source 已释放。
- normal false、cache unchanged、own-window/PID、non-key/inactive/no-MTK；前台13=9292、14=309保持；window1.546953/2.044402秒。before/settled五 stable 与场景 root ROI (16,24)/(352,244)、320×180通过。六张原 PNG 及原 report/receipt保留。
- 中图仅 trigger p 在 (.2,.8)，不要求五 stable。原 trigger / capture-before / capture-after 逻辑记录与时间完整保留：13 p=.2872209362/root(112.506235,87.188606)，14 p=.6920757961/root(248.537468,176.256675)。这些不是像素位置或 presentation timestamp。
- 原 native `pixel_acceptance` 明确 Not performed；随后冻结的独立像素报告须单列。该报告同宿主opaque端点为13 sRGB MAE0.294106/max5、14 MAE0.271169/max2，均nonexact，root目检支持本例目的图可见。固定12pt opaque inset非白bounds为13[80.5,66,400.5,246]、14[16,24,336,204]，不叫精确flight配准或同步帧；跨宿主颜色、中图和完整动画仍未验收。
- 无产品修复合入、无格式 setter/新层/强制 flush 来凑图。原 Hero exact字节身份与新 SDK 构建来源须保留；不能将其扩为整个应用/阶段已等效。其它 Film/chrome/layout/Frame/交互/HDR未通过项及11/Swift5.3/ObjC/iOS延期保持。

## 明确禁止的过度结论

- “CI绿/exit0/native通过，所以动画或颜色已通过”“源/终点五 stable，所以中图也同步”“两端不同进度可直接逐像素匹配”。
- “source weak deallocated=false 就是生命周期失败”或“source已经dealloc”；实际门槛是 source 不再 attached 与原 coordinator finish/临时视图/timer退出。
- 把逻辑 rect 叫作截图测得的位置，把 capture调用区间叫作 WindowServer presentation 时间，或把一次中图滞后归于某个 renderer/layer/系统版本的已证实根因。
- 把旧静态同图端点色差、backing hint 或早期 RGBA8 nil getter，直接套成本轮真实 flight 的同一缺陷/修复。
- 普遍零 observer effect、完整 enter/leave/隐藏恢复/中断/交互生命周期验收、物理HDR或整应用视觉等效。
- 把历史签名/整包指纹收据写成删掉 binary 后重新验证了现存 binary；把逻辑清理字节数写成 APFS 实际回收或磁盘净变化。

## 最终 archive 到达后核对

1. 路径与来源映射清楚，逐文件核对原 report/receipt/六 PNG/日志、source/provenance/构建收据、native分析、冻结后的像素分析（若有）及各自manifest；不重新执行采集或像素算法。
2. 18成员原包清单、10项source map、tar/binary原SHA与 root package验证收据保持；若排除 executable/tar/cache，须有明确历史排除库存，当前 archive 最终manifest只核现存文件。
3. 复制源与 archive 文件字节/SHA一致；本批 source Hero exact仍8e1e90a0…ed186c、Driver仍d8ed3e8d…a739b。分析来源与 native/pixel验收状态不混写。
4. 原始3阶段截图保持本机2×与远端1×、ICC、窗口/frame/ROI与真实mid状态；不把重采样或派生图当原图。允许归档内部完全相同文件去重，但不能链接活跃 work/其它归档作为唯一原件。
5. README/RESULTS/checkpoint 对 native通过、像素未通过/未知、产品未修、后续范围一致；新增像素事实只引用最终冻结证据。最后生成本次只读 archive-review 结果；没有最终 archive 前不标记哈希验收完成。

## 归档复核结果

四个子manifest共18项现存文件均匹配；native旧清单35输入中的33项仍匹配，binary/tar两项与明确删除库存和历史收据一致，没有假称重验已删本体。10项source map及provenance/workflow共12组，与当前repo工作区和HEAD逐字相同；生成Hero精确等于imports+原Hero exact+冻结Driver。六原PNG与两个像素结果的report/PNG引用匹配；未重跑像素算法。

两个文字问题已由root修正并复核：Acceptance binary后缀应82ecea36；两像素脚本intent0是perceptual而非relative-colorimetric，当前pixel子manifest为b3a2ca6b…12776c。没有更改算法或数值。v1全root bbox圆角污染、8pt非白比例仅描述、12pt非白bounds非配准等限制均被保留。

Remaining只含root负责的最终整归档manifest/Git whitespace/提交/推送。本review没有重新跑已交付app签名或像素算法；现存retention收据与本review边界分开。

## 最短 checkpoint 核心

实际 coordinator 采集现已完成，40103369574 与同原签名 binary13 均通过一次同key替换、单一 flight/timer运动及自动退出的原生门槛；before/settled 五stable、normal/cache/front/own-window等合同保持。有限像素报告支持本例终点可见但端点nonexact；中图实际显示和逻辑记录未建立同步、跨宿主颜色及完整动画视觉仍未验收。不指定根因、不合未证实修复、不推进11/Swift5.3/ObjC/iOS阶段。下一自然采样迭代仅为尚未实现的observer候选，不承诺同步或产品修复。
