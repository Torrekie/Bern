# Name 输入：9dd → 当前源码复用证明

交付源 `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0` 与当前 `13354f94bfee6e71d152b3c3ec1005cbc2044e7a` 的下列15处相关区域逐字相同；未做源码归一化。所查当前工作树源码也逐字等于固定提交，当前文档修改没有改变这些源。完整哈希/精确区域边界见 comparison.json。

| 区域 | 当前文件与起始行 | SHA256 前16位 |
|---|---|---|
| Rust window-owned MainDraft including name | examples/showcase/showcase-ui/src/lib.rs:73 | `5d8420bc5afd5ef8` |
| Rust Inputs Name action and Hello preview | examples/showcase/showcase-ui/src/pages.rs:123 | `039f232f2e8465e0` |
| Rust record command: last_action and exactly one activation | examples/showcase/showcase-core/src/lib.rs:90 | `ca389d59cc7058b9` |
| Rust Action enum including Submit | examples/showcase/showcase-protocol/src/lib.rs:9 | `8aeb209b501dd2c8` |
| Rust State and record protocol declaration | examples/showcase/showcase-protocol/src/lib.rs:66 | `f970d4c2aaa11d5d` |
| SwiftUI TextField, binding, onSubmit and control registration generator | crates/bern-backend-swiftui/src/swift/controls.rs:362 | `2965a38065712f4b` |
| Swift Binding get/set expression generator | crates/bern-backend-swiftui/src/swift/expr.rs:241 | `afc10b25884b71ab` |
| Generated window draft @Published storage and validated setter | crates/bern-backend-swiftui/src/swift/values.rs:400 | `23d710568238c932` |
| Runtime window-owned session state and set entry | crates/bern-backend-swiftui/templates/BernRuntime.swift:497 | `17bf9f87130d2bc8` |
| Runtime BernHost.sessionSet validation bridge | crates/bern-backend-swiftui/templates/BernRuntime.swift:1334 | `c9aceaad587e554e` |
| Runtime mounted control registration, removal and readback API | crates/bern-backend-swiftui/templates/BernRuntime.swift:665 | `f79997e93eaa878e` |
| Sidebar focus and arrow-key modifier | crates/bern-backend-swiftui/templates/BernStyle.swift:1272 | `6c88052b2ee509c1` |
| macOS13 sidebar arrow-key monitor | crates/bern-backend-swiftui/templates/BernStyle.swift:5272 | `891b7b89094b60dd` |
| macOS13 scrubber arrow-key monitor | crates/bern-backend-swiftui/templates/BernAppKit.swift:1294 | `4e65029678bdab82` |
| Window input idle monitor returns original event | crates/bern-backend-swiftui/templates/BernAppKit.swift:1552 | `00a9878c17c3af92` |

Name 仍是原生 SwiftUI.TextField，直接绑定窗口 MainDraft.name；预览同读该草稿。onSubmit 调用同一 record(Submit)，只增加一次计数并设置last_action，不清空Name。生成的setter仍通过Rust会话校验，再发布新值，没有为此新增自定义控件。

相关键盘monitor未变：sidebar仅消费符合焦点/窗口条件的上下箭头；scrubber仅消费箭头并排除NSTextView；窗口idle monitor返回原event。这些被比较的monitor不会消费Tab/Return。并不据此泛化整个后端。所查文件中，唯一9dd→当前差异是Style的legacy滚动实现，完整Style文件没有被误称为相同。

root报告的最终通过路径是前台Tab→唯一Name53焦点与caret→Unicode输入→Hello/草稿同步→一次Return，计数0→1、revision0→1、last_action=Submit（own11709）。本目录只证明该实际9dd路径对应的当前实现未变；运行原件由root独立保存，没有在这里新造或重写。

两次coordinate鼠标仍focus12的记录、控制器text变量TypeError均保留，不能写成鼠标通过。最终PASS只覆盖受控合成键盘事件，不声称物理硬件键盘、IME、VoiceOver、整个应用或像素级一致。

此次只读Git与当前源码；仅写本子目录，不改run/responses、产品、工具或源文件，不执行UI/编译/CI。
