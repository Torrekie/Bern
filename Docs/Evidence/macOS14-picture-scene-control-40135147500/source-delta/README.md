# Picture真实路径源码差分索引：fa820f7→9dd99b7

范围只读，精确比较 `fa820f706e5faf1bae8b8f07e23545842a1648b7` → `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`；下列行号属于各自commit，不能拿当前HEAD偏移替代。未生成/复制完整树、编译、UI或CI，未改仓库或旧work。目的仅列来源，不指定首卡高度根因。

## 未变的真实入口/直接布局

| 来源 | 结果/范围 |
|---|---|
| examples/showcase/showcase-ui/src/pages.rs | 整文件相同；layout_page:146，首120/gap16 Grid、四gap6 Column、120×90三图片及caption、宽64标志；HDR192×108两图片，均未改。 |
| examples/showcase/showcase-ui/src/lib.rs + Bern.toml | 整文件相同；Navigation/Search/Page::Layout入口及配置未改。examples/showcase全部路径均无diff（含资源）。 |
| src/swift/app.rs / windows.rs | 整文件相同；Scene.Window、component与WindowRoot/SearchPaletteHost生成未改。 |
| src/swift/content.rs | 整文件相同；Image与caption/Text生成未改，首卡Image没有新增dynamicRange显式参数，仍用默认值。 |
| src/swift/layout.rs | 仅旧594附近→新597附近：Scroll组件末尾增加mac bernScrollScope。Form/Section/BernFormRows/Grid/Column生成无修改；layout_page的grouped Form不是此Scroll组件。 |
| Runtime BernWindowRoot | 旧2114→新2123整声明相同，context/locale/environment注入未改；BernCompatibility.swift整文件也相同。 |
| Style BernAdaptiveGrid | 旧2959→新3053整声明相同；列宽/测宽/子内容布局没有源码改动。 |
| Style Forms完整区段 | 从“Forms on their page”至LegacyScrollProbe之前逐字相同，含Form layout/insets/environment defaults及BernFormRows（旧4699→新4822）；不能把后面的Probe diff误读成FormRows改动。 |
| Style BernPictureHero | 行1631整声明相同；首卡没有hero key，不经过真实coordinator。 |

## 有diff但不应混成14首卡直接变化

- navigation.rs（46a2862）：旧19→新19检测Sidebar后代Search；新72附近仅给**无Search**侧栏用bernSidebarColumnWidth。Showcase lib.rs:144–148有Search，所以仍走原min180/ideal210/max320 modifier；detail Group/title/toolbar/inspector段没有diff。
- AppKit新增BernSidebarWidthStartup.capture（新105）及宽度helper（新669–734）；capture是全Mac启动的defaults读取，helper的13 priming并未由此Showcase分支调用，14 helper本身也走原native modifier。没有已知首卡环境setter来自此改动。
- Style Scroll相关（46a2862）为13 padding/scope/viewport替代，Form不调用新增Scroll生成modifier；14 snap路径保留native。Pinch（5226454）、圆形button/popover（0f5226d/f9e08b1）无首Grid/image/caption挂点，且14保留SwiftUI fallback。
- RuntimeUnavailable（0f5226d，旧2020→新2021）只改13回退；此Picture首两Section不实例化Unavailable。

## 仍需绑定实际14树的具体Image源码候选

1. **e06e080**：新增BernImageDynamicRange/default .high（新2223、2513），bernImageDynamicRange从无参改带intent（旧2323→新2483）；14默认仍请求.allowedDynamicRange(.high)。新增13HDR/SDR分支、intent/headroom与cache实现，改变BernImage.body的ViewBuilder备用分支构型；不是首卡常量/显式padding修改。
2. **9dd99b7本身**：standardImage从旧2403无displayImage参数，变为新2624 `displayImage: CGImage? = nil`，构造Image输入变为 `displayImage ?? picture.image`；新2642–2644增加explicitStandard的13 PQ分支。14当前实际选择仍为2640–2641的standardImage(picture)，用同一原图/fit；但“相同active表达式”不能代替生成/编译后的真实树证据，也不能排除opaque/ViewBuilder结构差异。
3. decode旧2397→新2576加legacyHDRColorSpace/legacyStandardPQImage存储；新2594在14对非原生HDR标志直接nil，ColorSync CICP fallback只13；新2614在14直接nil，不创建derived PQ copy。14普通JPEG/PNG不会改走13native SDR/Metal表面。原orientation/ratio算法及后面的固定frame/aspect/clip/task/hero位置没有改动。

因此若9dd完整14首卡不再125，源变化候选集中在上面**共享BernImage声明/包装构型及decode附加字段**，而不是已证实改过FormRows/Grid/Scene。这里只是候选边界：没有证据把高度变化归因于其中任何项；当前source diff也不能证明SDK、编译器、原生environment、窗口/语言/恢复或采集状态相同。不同source历史B/9dd不能直接作纯OS因果比较；先保留9dd control实际值，再取真实generated Form/row环境和resolved bounds。

## 逐字未变区段指纹（SHA256）

- BernAdaptiveGrid声明：`c544144ef070c4385f23dc9688c58808ae95380b7c7a6407591c06b6d8193b88`
- BernFormRows声明：`ec9de982f958e5d06805505e904193cfad0ccbdeefdaa6bdb8685517bb855e43`
- Forms完整区段：`8ea002b3d149f3154d46e553a66b678f4042b4b91fd679046a52611e2e17e593`
- BernWindowRoot声明：`6b6d59ba13eb3dbb77df3f0794e1e3d84945094b6f1bca58c1941072733a2e7a`
- BernPictureHero声明：`0e1ef978955207f468e2c6be6f510d08e17da11a2f4bb8e3d33597aee1c83cb8`

来源方法：git对象级diff/name-status、目标commit git show与Image局部blame；声明/Forms区段两端逐字比较并哈希。未保存整源或大diff，也未运行像素/布局实验。
