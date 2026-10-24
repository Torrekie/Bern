# PRIVATE：retained snapshot raw 的下一最小语义边界

**可先走一条纯离线几何结构验证路线；当前尚未证明row方向，不能直接输出已命名的跨host十色块结论。** 不再提出display widget或event-loop变体。本轮仅读小metadata、原采集/decoder源码、atlas规范及本机CGImage公开header；未读/复制raw大缓冲、执行新分析或写算法。

输入锁为`outputs/Bern/Docs/Evidence/macOS14-hero-float-40091326190`：`package/ProductHero.swift:85–102`在实际`renderer.cgImage`返回处观察同一个CGImage，`FloatCapture.swift.inc:29–105`保留该对象、在原teardown后直接导出provider，无转码/备用图。on报告为13的640×360/stride5120和14的320×180/stride2560，均16bpc/64bpp float、bitmap4353、alpha1、byteorder4096、packed0，长度恰为stride×height且无padding。两端ExtendedSRGB ICC SHA相同；这不证明payload或空间语义相同。原报告仍是`row_direction=unverified`，旧分析仍是unknown且没有semantic patch值。

唯一下一步按以下顺序，任一不成立即停止语义比较：

1. **先固定格式→lane证据。** 对照原descriptor、导出guard与现有`analysis/analyze_float.py`：decoder以每像素4个uint16LE拆分，再以IEEE binary16解释；原独立`struct<4e`全buffer复核只支持相同数值解码结果。公开CGImage header将4096定义为16Little、4353另含float与premultipliedLast，pixel-format0为packed；现有RGB color-space metadata和该格式合同须共同支持明确的byte/lane→RGBA表。已有lane3全为0x3c00/1是alpha的交叉检查，**单凭恒1不能证明其余三lane的RGB排列**。不能通过哪种置换更像某色、13↔14更接近或更接近PNG来选择通道；证据链若不足，保持lane0..3，不标RGBA语义，不做channel permutation search。
2. **方向先用空间结构，不用预期色值。** 冻结`analysis/atlas-rois.json`（SHA`39ca622a45c0120d08e90daa7a17a0145be1b79485decb4619a0e5a3f23cadaf`）及独立源`color-probe13/report.json`定义：640×360的上两排各5个128×120平坦patch；底120行是唯一全宽横向ramp，输入仅随x变化。先核锁定源atlas本身符合这项结构，再预先固定验证标准：以完整pixel-bit tuple的空间恒定/变化结构分别检查raw的top-down、bottom-up两候选，要求两排5块内区与唯一ramp带共同成立，方向必须唯一。不得用PQ理论值、RGB大小关系、已见主色差或跨host接近程度来打分；不搜位移/比例/任意裁剪，不事后放宽阈值挑方向。13/14、named/custom各自记录证据，不预设所有文件同向。若结构被采样/抖动/退化破坏或两向都成立/都失败，保持unknown；当前缺失的正是这一独立几何方向证据，metadata/whole分布本身无法补足。
3. **唯一且复核后才命名/比较。** 保存小型方向证据：输入SHA、format/lane依据、每个结构检查与两候选的通过/失败、唯一选择或明确歧义；由独立review确认，不只给方向字符串。旧冻结analyzer的`--orientation-evidence`只记录文件/hash，不能自行证明证据真实；须先审查证据再使用其现有known-direction入口。复用原十patch内区：13为112×104，14为56×52；ramp分别632×80和316×40，按实际size精确整数映射，不resize、配准或拟合。比较对应命名内区的原half bits/finite数值摘要与13−14差，保留样本数、alpha/NaN/Inf/负数/>1，不clamp/unpremultiply、应用ICC/transfer或换算nits，不与WindowServer编码RGB直接相减。14 named/custom raw相同仅是该case事实，不当作独立重复证明。

这条路线不需要新采样；但它的成功仍是待执行条件，不是本提案已经完成的结果。如果无法取得唯一结构映射或格式合同不能确定RGB lanes，则保留旧unknown whole-buffer结论并明确缺少actual raw坐标/分量对应证据，不能用新dump或颜色“看起来合理”冒充已补证。即使十patch语义成立，差异也仅定位到实际snapshot raw边界；1×/2×采样、边界与宿主context仍在，不等于可见主差的原因、修复或颜色等效验收。

下轮仅执行上述一条有失败出口的离线证据路线。本轮未写算法/Driver/产品、编译、UI、CI或大复制；只交付此README与SHA256SUMS并冻结只读。记录时间2026-10-24T17:07:39Z。
