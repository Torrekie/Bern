# macOS 13 系统音量弹出按钮

产品源码为 `f9e08b1d55bed4b9d880b19934abe48281057bb3`。复用已有圆形 NSButton，没有增加自画按钮或修改通用 Menu、toolbar、圆形样式。

- [独立组件](component/README.md)：实际 NSWindow 中验证系统20pt按钮、单次 native action、快捷键、禁用、外部打开与关闭；原 SwiftUI 触发器同条件对照通过。绑定关闭后 WindowServer alpha为0，窗口对象暂存不代表仍绘制。
- [Showcase完整构建](https://github.com/Torrekie/Bern/actions/runs/39991409277)、[Gallery完整构建](https://github.com/Torrekie/Bern/actions/runs/39991406873)：Swift6.2.4、SDK26.2、Rust1.99，真正的swiftui-modern、ARM64、target13.0。两应用签名和最低版本复核通过。
- [Showcase本机启动](full-app/showcase/report.json)、[Gallery本机运行](full-app/gallery/report.json)：13.7.8建立会话并inspect成功；Gallery通过CLI原绑定选择Frame、打开volume弹出层，注册volume_level初始0.7并编辑为0.55。它不是物理鼠标、AX几何、整应用关闭或14视觉比较。

两应用已移至本项目旁的macOS13候选应用目录，移后签名复核通过；不保留重复tar或临时IPC。完整构建来源和可执行文件SHA位于各 `provenance.json`。检查进程均已停止，前后台应用一致。

本机检查脚本初次把成功CLI动作的空stdout按JSON解析、随后把popover_button误筛为button，均已按源码的实际命令与role修正；这些是验证脚本错误。最终记录是修正后同一二进制的新进程检查，不把这些脚本错误归为产品失败。

整应用14/13 Frame实图和物理鼠标仍待验证。其余阶段状态以[验收记录](../../Implementation/macOS13-Acceptance.md)为准。
