# Film 初始卡片：已知事实与最小区分采样

本项尚未等同。固定上游 A14 与此前移植 B14 的首次 Film 都显示 Glen；本机 C13 显示 Madras。Rust 声明的 `GalleryDraft.centered` 初始值为3，但现有采集没有实际读到这个 draft、SwiftUI target 或 nearest 的逐帧轨迹，因此不能把“3写回成4”当作已证事实。

## 已排除与尚未排除

- A14、B14 的 Patterns、Inspector、Film、Last 最终外框均为920×668点，window version保持4；C13同样920×668点。最终外框差异不能解释卡片身份。
- A14/C13 detail 都从x211起。Inspector稳定显示时，分隔线约x695，右侧实际约224点加分隔线；关闭后detail约709点。不能把实现中的默认300或理想280直接当作实际宽度。
- 初始放大卡本身的四边差值与Last一样在约1点内，且Last双方均为Windowpane。身份差异与最终卡片大小应分开判断。
- A14/B14首次Film的深色PNG相同，浅色仅少数像素相差1级；身份差异不是Combine移植独有。
- 原采集在`show_details=false`后紧接着选择Film，仅在Film出现后等待静态缓冲。C13对应两条命令间隔约0.068–0.303秒，也没有等关闭稳定。
- Inspector修饰器位于Detail的page match外，可与新Film的首次挂载同时经历退出布局。现有GIF只记录Inspector打开和Film→Last，没有关闭→首次Film，最终静态截图不能排除首次布局时序。

以上来自[A14原始记录](../Evidence/macOS14-gallery-normal/reference.json)、[C13比较](../Evidence/macOS13-candidate/gallery-comparison.json)及`navigation.rs`的Inspector生成位置；它们不足以归因某个原生动画或contentMargins算法。

## 下一项最小采样

同一个锁定A14应用，每组新进程、同一light外观、920×668点外框和侧栏：

| 组别 | 输入序列 |
|---|---|
| immediate | Inspector打开并稳定，关闭后立即进入Film |
| wait | Inspector打开并稳定，关闭且窗口缓冲稳定后进入Film |
| direct | 从未打开Inspector，直接进入Film |

记录Film选择命令开始至首秒的实际时间戳、AX scroll area与可见卡片标签几何，以及最终连续相同缓冲的PNG。AX只能提供公开可访问性几何，不能替代内部target/nearest状态；未获AX或没有可匹配节点必须明确记录缺失。

若只有immediate显示Glen，才支持继续调查Inspector关闭/首次挂载时序。若wait/direct仍显示Glen，应优先调查初始contentMargins与原生scrollPosition。现阶段不硬编码4、不添加卡片位移补偿，也不先模拟未经确认的14动画。
