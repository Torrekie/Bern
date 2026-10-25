# Caption 选中态前景：最小源码审查与下一候选（未实现）

固定 e48 的 Caption 走系统 `ControlGroup → Toggle(.button) → Label(titleAndIcon)`。这条直接路径在13与14相同，没有14专属API分支；本机SDK将 ControlGroup / ButtonToggleStyle 均标为macOS12起可用。源码没有给该Label设置选中前景、字体或disabled。根代理目检原图所述“13灰、14白”尚未由本审查做像素复核，也不能据此认定Bern或SwiftUI某个内部根因。

准确入口：Gallery DSL389；真实Generated1275、Frame末尾1342–1344；controls.rs324–345；固定e48 BernStyle72–79、1062–1156。`capsule=false`，所以胶囊分支的13pt/medium字体完全未进入。Popover里的headline/Slider和后面的secondary Rest文字也不是Caption标签。直接前景保持隐式；`bernAccentTint`仅在有accent时调用tint，不给文字/图标指定颜色。

Frame源码明确强制dark scheme，窗口本身Light。既有13/14状态收据均是Crimson、Light、caption=true，normal三项false且无ledger。13注册行enabled=true只能证明注册状态，不能当作NSControl.isEnabled或解析后的foreground。`BernAppearanceRegion`只供菜单跟踪选择appearance，不给Caption控件设颜色。BERN_RENDER可控制根的controlActiveState；现有记录未直接给出SwiftUI实际环境值。ThemeChoice上游含13 onChange兼容器，但direct accent环境两边都赋值；源码不足以指认此处有传播缺陷。

现有边界：13.7.8与14的popover material均进入13.3+原分支，且目标是closed状态；extraLarge14适配与自绘capsule也未被这个Caption选中。没有找到需要将14专用的Caption前景API移植到13的证据。更可能涉及系统运行时如何解析原生selected-label，但这是待验证的范围，不是已证原因。NSColor SDK头明确语义色是动态命名颜色，可随OS/appearance改变；不能从颜色名推出一定为白。

唯一可选的下一最小诊断：只在macOS13、`target == frame.caption`、非capsule、selected、enabled、key、dark这组状态下，给原有toggle Label的文字和symbol用动态 `Color(nsColor: NSColor.selectedControlTextColor)`。该语义在本机SDK写明为selected controls的文字色；不抽取RGB、不强制appearance、不改tint/bezel、不造新控件。其它状态返回原Label，不加primary等替代。14+保留原Label分支；新增View泛型结构仍需14实际无影响对照，不能只凭availability宣称视觉不变。本轮没有写这个修改。

若root选择实现，验收仅围绕这一个颜色变量：用现有同源/资源/en/920×668/normal/Paused0/own-active/stable4原始图与ICC、实际scale，核Caption标题及captions.bubble的实际前景；同时确认13原bezel、几何、邻接控件及视频未改，14实际画面未改，原binding/popover动作保留。不以截图推Caption/Size宽度，不复用失败ledger解释颜色。若系统语义色仍灰、被原生style忽略或产生副作用，保留阴性并回root决策；本方案不顺势再试第二颜色或固定白色。未实际检查的off/disabled/inactive不宣布运行等效。

`review.json`保留精确Git blob、实际报告/PNG与SDK输入SHA和完整未知项。未实现、编译、运行UI/CI、提取像素或修改旧证据。
