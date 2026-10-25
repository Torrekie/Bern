# Reopened audit: final 631-input candidate

Root明确要求重开本目录；旧manifest `50141ae6…54e7b6`已取消冻结，原件保存在
SHA256SUMS.before-addendum。旧README的38项是旧picture selector替换Gallery的统计，
不作为这份broader631候选的门槛。完成本增补后重新冻结，不修改作者源码。

最终script：15448 B / `5b4a254565f437f819a308f8cf3c5b1990b937f76b9918ff5b935e91e1a2b017`。
作者manifest `695e86c6…7da93`全部成员独立复核通过。实际fixed e48 Git树给出631个唯一文件：
crates620、Gallery9、根Cargo2；全部100644/blob，无symlink会被regular-file门槛误拒绝。
INPUT-PATHS.txt与Git列表逐字相同，SHA `8bdc7bd9…78849d`，总输入7430108 B。
此范围覆盖本地compiler/generator/target-api/icon资源及Gallery；不声称外部依赖/工具链闭包。

最终tokens有固定e48源依据：names.rs输出AppView_{name}；windows.rs用真实component.name，
Gallery为frame/main_window；calls仅检查左括号，已不预设空initializer参数。
Mac普通caption_size value分支确输出SwiftUI.Slider(value:，Caption输出BernSplitButton，
Size Menu输出SwiftUI.Menu {，target为frame.caption/caption_size/caption_sizes。
未发现会确定拒绝真实生成的剩余token；实际生成尚未由本审查取得或执行。

首版尾部才复制raw的失败证据问题已修：最终版在身份/header/bounds门槛之后，先保留真实
BernGenerated.swift及build.json原字节，再判Scene/Frame/build语义；后续失败仍false/nonzero。
更早的identity/header失败不会达到raw复制阶段，不将其描述成“任何失败都保留完整raw”。
自定义FRAME marker使最终CLI patched SHA为0510fef5…ef3636；旧5a05是旧marker情形。

Frame行宽仅保留最小源事实：Row gap12/center、!window.idle条件，同Row有Caption split、
Size menu、Volume popover及条件帮助文本。DSL/生成器不能提供实际proposal、allocated width
或原生intrinsic width；没有预分析生成布局、修复或原生验收结论。

结论：该冻结候选在本次只读scope内无剩余blocking。未运行prepare/collect、生成fixture、
Cargo/Swift/UI/CI或Git写操作。完整独立证据见candidate-addendum.json。
