# CG direct 运行后最小几何门槛（PRIVATE，未运行）

先做几何，再读颜色结果。root 对 named 的 p0、p1 **分别**保存原PNG/report/hash并填四项记录：`metadata / upright-nonempty / visible-extent / evidence-limit`；不得以另一 phase 通过代替。此处不创建脚本、裁剪图、UI 或CI；old-on→default及全部 D13−D14 由root另行负责。

1. **固定坐标。** 原 report 的 flight-named 必须为320×180pt，完整落在原PNG中，root与screenshot坐标映射、实际像素尺寸与default一致；沿用旧 analyzer 的整数映射，不找图像边缘重定位、不resize。以下均相对该pane左上角，先声明后查看：十flat为 `(4+64c,4+60r,56,52)`pt（c=0…4，r=0,1）；三band为 `(2,10,316,40)`、`(2,70,316,40)`、`(2,130,316,40)`pt；它们来自冻结640×360 atlas的精确1/2映射。
2. **upright与非空。** root在原PNG的同一固定pane目检：上两行是离散flat块，底部第三行是横向连续变化的ramp，且左右、上下位置与原atlas空间布局一致；三行完整、无整pane空白或背景替代。只看结构位置，不用RGB接近原图、14或body来选择flip。source review另须确认x轴没有镜像、唯一y补偿来自原flipped view，图像完整画入同bounds；本atlas的“ramp在底部”只能独立区分上下，不能仅凭该标记证明左右不镜像。
3. **完整可见extent。** root同时查看pane四边与其相邻背景：顶/底两行在预定y=0/60/120/180pt结束，块列位于预定64pt网格，ramp贯穿第三行；检查四角与四边无可见平移、裁切、空带、背景缝或越界绘制。固定查看内侧1pt四条边带，及可见时的紧邻外侧1pt边带，不按颜色自动移动ROI。结合 source review 的opaque原图、corner0/full-bounds clip、两次sourceOver及p0/p1 alpha设置，才记录 `visible-extent: pass`。某些块合并同色时不要求每条内部边界都可见，不得为此改阈值。

若root复用已有tuple结构检查，可把各固定ROI的完整像素tuple相等关系作为**额外强证据**：十flat各一tuple；三band所有行相同且各五个固定x-bin均有≥2种tuple的marker依次F/F/T。x-bin源坐标为[8,120)、[136,248)、[264,376)、[392,504)、[520,632)。它只用相等关系，颜色整体改变仍可成立。旧raw在两方向的唯一结果不能当作新PNG已验证；PNG若有抖动/空间色彩处理使精确条件失败，记录 `tuple gate unavailable/failed`，不放宽计数、不平滑、不搜索flip/平移/通道或相似色，不能伪称精确结构PASS。本轮允许只交付root上述固定位置目检，明确标为 `visual-only`。

**限制与停止条件：** 旧NSImageView分析的alpha255、RGB范围及ROI尺寸只证明合成PNG有不透明内容和已记录pane，不单独证明upright或原图覆盖。上述目检/source/metadata组合支持本opaque夹具无**可见**背景泄漏；背景与图像恰同色时，不能从此PNG证明每像素覆盖或全部边界精确，必须保留这个限制。任一phase倒图、空图、明显错位/裁切/泄漏、坐标不符或无法判断则该phase几何incomplete，颜色即使更接近14也不能标为有效改善；禁止改flip后挑较好色差。全部通过也只验此静态named/up/same-aspect/corner0端点。

引用：`work/hero-cgsemantics-next-direct-plan/README.md` SHA256 `6a4cc1152251e0c5c50083e68a99d32d57feb9be5230ca3ffcf1f0699fa87199`；`outputs/Bern/Docs/Evidence/macOS14-hero-float-semantics-20261025/analysis/atlas-rois.json` `39ca622a45c0120d08e90daa7a17a0145be1b79485decb4619a0e5a3f23cadaf`，同目录`policy.json`为既有三band/五bin定义；`outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/native-pq-hero-snapshot-view13/pixel-analysis/analyze.py:40–53,178–198` `98243090f0b45fe18baed3d89d4e382c7d8f7c02662a930cfda8c87c3b0f39d4`。本轮只读小源/元数据，未读raw/PNG像素、运行分析、构建或新采样。
