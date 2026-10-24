# Picture 首卡：下一步回真实 Form row 入口

**只选一步：在完整 Showcase 的 Page::Layout 原位记录 Form→首个 Grid row 的公开 environment／resolved bounds；先在14重现124/125pt，再观察。**
不再增加 isolated 组合或先改布局。此处是下一检查点，不是根因或修复结论。

## 已知与停止的方向

- Acceptance:77 保留完整 A14/B14/C13 首卡124/125/129pt，图片/caption边界接近，HDR卡均147pt。
- macOS14-image-layout/validation.json：同一SDK26.2/min13 binary的9配置/27位置在13/14均首卡129、HDR147；row/grid/column第一行109、image90pt，仍有其它坐标最高2.5pt差。
- static-children/README.md：只将ForEach换四literal children后，两端首卡仍129；不是可继续的单变量。
- 不重复ForEach/static children，不用负padding、固定行高或改font抵消5pt，也不把probe129相同当整应用通过。
- A14/B14与13全应用是不同source版本的历史cohort；不能从它们加上另一同binary探针直接推出纯OS因果。

## 最小仍缺的真实边界

真实链来自源码：SwiftUI.Window → BernWindowRoot → BernSearchPaletteHost → NavigationSplitView.detail的Group/页面switch → layout_page的grouped Form →首Section/Grid。
`app.rs:220–259`产生真正Scene Window；`windows.rs:104–111`包WindowRoot/SearchPaletteHost；`navigation.rs:135–155`保留detail Group、navigationTitle及toolbar/inspector作用域。
`BernRuntime.swift:2195–2199`还注入window context和明确的界面locale；这不是手建NSWindow的默认environment。
旧fixture `image-layout-probe.swift:404–408`直接NSHostingView(LayoutForm)，没有这条真实detail入口。
它的EnvironmentProbe在159–176定义，却由297–307的Form外层background读取；尚未提供完整应用首row内部实际继承值。
因此“Scene/detail→Form row继承／尺寸约束入口”仍未对齐，而不是已证明某个environment key错误。

已有isolated inherited环境：13/14均regular control、dynamicType/sizeCategory=large、minRow24、font=inherited nil，Grid width均719；locale分别zh_CN/en_US、scale2/1，但卡高均129。
这些差别本身不能解释完整14首卡变矮；Form外nil font也不证明row实际字体相同。

## 唯一下一检查点的执行合同（本轮未实施）

1. 选择一个精确绑定source/binary的**完整14 Showcase**，走原sidebar选Layout、原语言/浅色/normal/窗口resize路径。
   先用无观察器控制重现其首卡124或125、HDR147；不能把当前main默认当作旧A/B同版本。
   若不能重现，停止该差异结论，保留实际值；不另包Scene来“追到”目标高度。
2. 仅在该完整生成树的Form根、首Grid row入口放同一套公开background/anchor读取；HDR原row作同Form内现成对照。
   复用旧EnvironmentProbe字段：font、controlSize、defaultMinListRowHeight、dynamicType/sizeCategory、locale、direction、scale、scheme/contrast。
   同次记录Form/首row/Grid/image/caption的resolved frames、实际content/detail/scroll viewport bounds；沿用原卡片边界测量/点单位。
   不插入新的布局容器、不替换BernImage/Grid/Column/FormRows，不添加fixed109控制row或改ancestor modifiers。
3. 无观察器→观察器的首卡/HDR几何须保持原值；记录source/asset/窗口/语言/normal及原PNG哈希。
   观察器若将124/125变成129或其它值，即observer影响，不能当作修复或有效环境证据。
   公开frame/Color.clear读取不等于记录SwiftUI的原始proposed size；对该未知保持诚实。
4. 先定位完整14的首row/image/caption是否仍109/90等同probe，而原生card额外空间改变；或实际row/frame/environment已经不同。
   只有实际记录的差异才支持后续单变量；全部相同只留下Form/native cell边界未知，不追加environment排列实验。
   HDR147作为局部对照，不能用整图缩放、色差或跨2×/1×像素相等代替布局证据。

本轮只读必要小JSON与源码，未读/复制大PNG、运行UI、编译、CI、像素算法或修改产品/旧档案。
没有新增Scene实现或产品补偿；目标是先让真实UI中的缺口可测，再决定局部修复。

## 本次读取的最小引用与SHA256

- `outputs/Bern/Docs/Implementation/macOS13-Acceptance.md` — `6fd6fcb6f34238cf25adc9bc4c42f148c64737227754bf5b11edacdfbc023cc4`
- `outputs/Bern/Docs/Evidence/macOS14-image-layout/validation.json` — `95207a55e9aab666d4152da8e8673a6c6ab8d7fe4a7e2fa6d13c9bc6febc33c3`
- `outputs/Bern/Docs/Evidence/macOS13-image-layout/static-children/README.md` — `fd7deddd30b597a9784159e4db638e34b5324949ba24c1d2ba6ffee3d9a63b7e`
- `outputs/Bern/Docs/Evidence/macOS14-port-comparison/comparison.json` — `3ef4356a585960edb43c0c2b4b3291e888ca12998cf3efb40691c9fa5ca682e3`
- `outputs/Bern/Docs/Evidence/macOS13-image-layout/sdk26/image-layout-probe.swift` — `daa7e0e16bf374b35ef9e431d65cb22eaff3b251dfe6c7336c4bac16bacec6e1`
- `outputs/Bern/crates/bern-backend-swiftui/src/swift/navigation.rs` — `e9dff9982696510c8d65aa24408e95c481fe5010c14d02aa924506b169b4357b`
- `outputs/Bern/crates/bern-backend-swiftui/templates/BernRuntime.swift` — `255bacb40db71fa17a8bd9ecaefc1b72c187864295221727c28653a09839e16e`
