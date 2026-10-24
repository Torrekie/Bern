# Picture Scene observer: source boundary retained for continuation

本轮只读定位完成；**尚未形成可apply补丁或Swift observer源码**。未取得保留的完整generated Showcase Swift，不能诚实声称已验证generated Form/row表达式的唯一匹配。Root确认没有generate-only CLI；获取真实生成源需后续受控远程构建/诊断停点，本轮未执行。未改repo/index/旧档案，未构建、UI或CI。

已确认源码定位：`examples/showcase/showcase-ui/src/pages.rs:146`的layout_page只有一个Form。首Section内Grid min_width120/gap16，四Column gap6/center：landscape120×90的contain/cover/fill及bern.png宽64，各后接caption/secondary。下一HDR Section为Grid min_width192/gap16，gainmap.jpg与hdr-pq.png各192×108及caption。层叠等后续Section不应匹配为首卡。

生成器证据：`src/swift/windows.rs:25–68`为component生成唯一`/// Generated from the ... component.`标签；`layout.rs:399`输出SwiftUI.Form与.formStyle(.grouped)，`454–482`输出Section与原BernFormRows；`233–270`输出BernAdaptiveGrid和原fill-width modifier；`70–113`输出原VStack；`content.rs:141–181`输出BernImage单行调用。真实生成版本仍须独立确认这些形状，不能把当前generator推测当已保留的9dd生成源。

下轮唯一可接受的补丁入口：调用者提供真实generated文件SHA和layout_page的唯一component范围；逐项验证Form、首120Grid、HDR192Grid、Column/image/caption的唯一小needle、完整表达式范围及片段SHA后，仅追加background/anchor modifiers。Form根解析public anchors，首Grid入口读取同一套public环境（font/controlSize/defaultMinListRowHeight/dynamicType/sizeCategory/locale/direction/displayScale/scheme/contrast）；不换children、BernImage、BernFormRows，不加Scene/容器、行高或负padding。原始Geometry/anchor bounds不是原始proposed size，Section语义anchor也不能冒充原生card边缘；真实window/detail/clip几何继续来自外部采集。

先让选定完整14无observer control重现其124/125pt首卡和147pt HDR，再插桩；若observer将首卡变成129或其它高度，立即停止此证据解释，不称修复。export时机/具体modifier挂点必须在取得真实表达式后review；本轮不凭空选择或生成布局替身。现有冻结picture-scene-next-step计划不变。

只读时repository HEAD：80ff1a365cf05cb44fa3d8517f2da6942ff1a75c
