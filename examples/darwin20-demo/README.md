# Darwin 20 Demo

这个独立应用工作区由本分支的 `bern new` 创建，业务协议、引擎与 UI 声明完全共用。
默认有 macOS / iOS 的 SwiftUI 与纯 Objective-C 两种构建入口；最低目标为 macOS 11 / iOS 14。

在本目录运行（先从仓库安装或构建 `bern`）：

```sh
bern run --target macos
bern run --target macos_objc
bern build --target ios
bern build --target ios_objc
```

界面由 `darwin20-demo-ui/src/lib.rs` 唯一定义。两种入口都显示问候、计数、加一和重置；按钮触发同一个 Rust 命令。比较两入口时，使用相同系统、语言、窗口内容尺寸、外观与字体设置。

`bern build --target ios_device` 与 `bern build --target ios_swiftui_device` 分别构建两种入口的 arm64 iOS 应用包。构建不会安装到设备，也不会申请签名或描述文件。框架实现与验证边界见仓库 `Docs/Implementation/Darwin20.md`。
