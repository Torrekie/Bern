# macOS 13 Volume Popover 系统按钮验证

产品提交：`f9e08b1d55bed4b9d880b19934abe48281057bb3`。本证据只验证独立组件，不代表整个 Gallery / Showcase 构建或 macOS 14 视觉比较已通过。

生成器仅在 Mac、带图标、非 toolbar、无显式宽高、无自定义绘制外观时传入 `nativeCircular: true` 与快捷键。`BernPopoverButton` 默认请求为 false；13 的明确请求直接复用已有圆形 NSButton bridge，14 保留 SwiftUI Button。通用 circle、Menu 和 toolbar 实现未修改。

## 已执行

- Swift 5.9.2 / SDK 14.2，`arm64-apple-macos13.0`，局部抽取组件 typecheck 及链接通过，无诊断。完整 fixture 保存在 `VolumePopoverProbe.swift`，抽取来源与适配边界见 `extraction.json`、工具链及源码 SHA 见 `validation.json`。
- 独立、真实、有序 NSWindow 中确认系统圆形 NSButton，intrinsic 20×20 pt、label `Volume`、重复项 AX target `fixture.volume[7]`、Command-V 转发。
- 自有进程内 `NSButton.performClick`、`NSWindow.performKeyEquivalent` 均只打开一次；禁用后两者均不触发；外部 activate 打开且重复调用不切换关闭。未发送真实鼠标或物理键盘输入。
- 12 项 runtime gate：明确请求的 icon 使用 bridge；其余 false 请求、非图标、bar、ControlGroup 均保留原触发器。plain/custom 等负例按生成器排除后的 false 请求模拟；这不是独立执行 Rust 生成器条件矩阵的测试。
- native 与 `nativeCircular=false` 的 SwiftUI 原触发器只做一轮 inactive 对照。均为 open → closed；关闭后 WindowServer `CGWindowAlpha=0`，随后窗口移出 onscreen 列表。没有激活测试应用，两个进程前后前台 PID 一致，self-frontmost 样本均为 0。

`report.json` 保存 native 输入、三个关闭路径和所有 gate；`baseline/report.json` 保存 SwiftUI 触发器对照。两张代表 PNG 是关闭时的组件窗口 `closed.png`、打开时的系统 popover `popover.png`，保留原 ICC；截图属性另列于 `png-metadata.json`。

最初尝试的全局 Primitive/metadata 路线被 inner `.bordered` 覆盖，已经完全撤回，最终产品没有该路线的修改。最初以 `NSWindow.isVisible` / `onDisappear` 判定关闭也不准确：两条路径都会暂存窗口对象，报告中对象仍 visible、onDisappear=0，但 WindowServer alpha 已为 0；因此使用绑定与实际合成透明度判断，不把缓存对象误报为仍在绘制。

## 复现

从仓库根目录执行；生成和编译产物放在 work，不会改写本证据。`prepare.py` 从当前源码重新抽取，若源码 SHA 改变，应作为新的验证批次。

```sh
python3 Docs/Evidence/macOS13-popover/component/prepare.py work/volume-popover-reproduction
xcrun swiftc -swift-version 5 -parse-as-library -target arm64-apple-macos13.0 \
  -typecheck -module-cache-path work/volume-popover-reproduction/module-cache \
  work/volume-popover-reproduction/VolumePopoverProbe.swift
xcrun swiftc -swift-version 5 -parse-as-library -target arm64-apple-macos13.0 \
  -module-cache-path work/volume-popover-reproduction/module-cache \
  -framework AppKit -framework SwiftUI -framework ImageIO \
  work/volume-popover-reproduction/VolumePopoverProbe.swift \
  -o work/volume-popover-reproduction/VolumePopoverProbe
work/volume-popover-reproduction/VolumePopoverProbe "$PWD/work/volume-popover-reproduction"
work/volume-popover-reproduction/VolumePopoverProbe "$PWD/work/volume-popover-reproduction/baseline" --baseline
```

局部 fixture 将未执行的 SDK 26 glass 类型名替换为旧 SDK 可识别的对应类型；13 实际运行的 trigger、原生 bridge、popover 与 control registry 代码原样抽取，theme / host 为最小边界适配。该检查不能替代新 SDK 对完整生成应用的编译。测试用可执行程序、旧失败产物与 module cache 均已清理。
