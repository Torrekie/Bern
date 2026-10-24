# Named PQ的十个平坦快照内区在13/14原位模式相同

这次纯离线分析完成了此前unknown的行序/色块对应证明：四份原raw均唯一top-down；Apple公开SDK格式合同独立确定RGBA16F的lane。先冻结并审查这些证据，再用原analyzer提取命名内区。没有新构建、UI/CI采集或产品修改；输入raw/PNG仍引用[CI40091326190 cohort](../macOS14-hero-float-40091326190/README.md)，未复制。

[完整结果](analysis/RESULTS.md)及[20patch数据](analysis/constant-patch-comparison.json)显示：named十区RGBA原half bits全部相同；custom有五区不同，RGB最大绝对存储数值差0.001953125、30项绝对差平均0.000244140625。alpha均为1。它们是premultiplied extended-sRGB数值，不能与8位WindowServer codes或nit相减。13/14各flat为11648/2912原pixels，不resize、配准或拟合；ramp仅保留各自native aggregate，不配对跨host列。

这排除了named这十个对应平坦内区的**原样本值不同**作为其显示主差的解释，不证明整个CGImage或最终显示相同。既有cohort的WindowServer主色差与off/on12ROI控制结果仍保留；未重跑截图。整图/ramp/边界采样、未读的CGImage对象语义、NSImage/context/显示环境尚未分离，不指定唯一OS、ImageRenderer、AppKit或HDR根因，也不宣称UI等效。

证据链如下：

- [预声明与成功几何结果](analysis/result/geometry.json)：只按完整tuple的恒定/横变结构检验top-down/bottom-up两候选，不按颜色接近评分；十flat及三band/五x-bin规则未放宽。源PNG无损active SHA与旧证据一致。
- [lane合同](lane-review/README.md)、[原结构源码审查](structure-review/README.md)、[PNG修订审查](png-review/README.md)：精确header/源/格式及小修订范围。
- [独立几何复核](geometry-review/README.md)：另用Fraction/struct读取原raw，两个方向的全部细项与root一致；compact变化仅JSON排版。
- [语义绑定](analysis/semantic-binding.json)、两份[原analyzer输出13](analysis/host13-known/analysis.json)/[14](analysis/host14-known/analysis.json)：绑定前置review/hash后才运行known-direction入口。
- [独立数值复核](numeric-review/README.md)：直接struct<4H/<4e确认40flat/20patch/80delta与4whole/44region统计。保存的时间/hash/源码顺序不是历史进程的独立attestation；原wrapper receipt未记wrapper自身SHA，此限制与当前hash均保留。

两次程序失败分开保留，均不是颜色/几何通过证据：[filter0解析前提失败](attempt-filter0/result/geometry.json)在读snapshot raw前停止；依[W3C PNG过滤规范](https://www.w3.org/TR/PNG-Filters.html)只补齐标准0…4无损恢复后，[pretty JSON体积失败](attempt-pretty-json/run.stderr.log)在末端写出前停止。成功版只压缩JSON空白，保留字段及128KiB上限，结果实际57139B；没有用未保存数值挑方向。

[下一唯一计划](next-display-plan/README.md)是deferred读取原CGImage尚缺的renderingIntent/isMask/shouldInterpolate/decode；尚未实现或运行。计划形成时数值复核仍在进行，当前已由上述独立报告完成。先补对象绘制语义，再决定是否做CG direct边界，不同时堆入缓存/图层/曲线变量。

本轮没有产生binary/module cache。九个work树经逐字核验归档后替换为symlink，清理673116B重复逻辑文件，见`cleanup.json`；不当作APFS实际回收或磁盘净变化。源码/日志/失败/数值/复核均保留，现存清单为`SHA256SUMS.final`。复跑应复制必要脚本到fresh scratch，归档只读。完整macOS13颜色/动画及其它门槛仍未通过，goal active，不进入macOS11/Swift5.3/Objective-C/iOS。

子目录复现命令保存的是归档前布局；归档后的work路径为symlink。将必要脚本/spec复制到工作区work下的fresh目录后再运行，输入可继续引用原归档，输出另用fresh路径。不要通过旧work symlink写结果。旧semantic-binding只绑定原分析，重新执行需保留新的review/hash绑定。
