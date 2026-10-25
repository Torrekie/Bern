# 下一有界单元：clean e48 首次 Last，先补事实

建议仅处理 **e48/macOS13 fresh direct Film 后第一次 Last 的真实终态**，不改产品，不重开已停止的 wait/direct 初始几何、Row/配色/搜索/Scene 路线，不做 immediate/history/First/Last-again/wide 矩阵。

现状与来源：

- [Acceptance](../outputs/Bern/Docs/Implementation/macOS13-Acceptance.md:153)仍将首次Last/resize列为未验收；[Film事实](../outputs/Bern/Docs/Implementation/macOS13-Film-Initial-Position.md)记载immediate在同源14重复也变化，当前没有单一确定落点可作下一修复目标。
- [clean e48/13](../outputs/Bern/Docs/Evidence/macOS13-film-clean-e48fff46/README.md)是交付原件d44…/CLI31a…，三场景仅followup=none；wait/direct初始六图几何已等效，不需再做该验收。**clean e48首次Last数据缺失**。
- [已有14 followup](../outputs/Bern/Docs/Evidence/macOS14-film-followup-40067683100/README.md)是f9、active/1x：首次Last Windowpane中心573，Last-again565，wide599。旧13/f9与d146诊断的差值不能套给clean e48；也没有找到同e48的14首次Last参考。因此新13结果即使接近573，也不能据此宣布等效或定因。

源级已确定：Gallery DSL [film/to_last](../outputs/Bern/examples/gallery/gallery-ui/src/lib.rs:280)把centered置6；实际e48生成源[film.to_last](../outputs/Bern/Docs/Evidence/macOS13-gallery-frame-source-40152701810/ci/BernGenerated.swift:1139)的registry动作同样赋Int64(6)。[BernScrollPosition.scroll](../outputs/Bern/crates/bern-backend-swiftui/templates/BernStyle.swift:2588)先结束13 initial ownership，再expect/更新target；没有证据支持把初始anchor公式或补偿常数套到Last。

最小未来动作：复用原e48交付及CLI，在一个fresh私有身份、normal/light/en、920×668的direct Film进程中，初始Glen/完整六图只作为setup precondition；通过现有session/inspect解析唯一启用target后，仅一次`gallery --session SESSION ui activate --target film.to_last`，保留命令起止、稳定原PNG/ICC、完整六图AX frame及窗口/来源/前台身份，然后结束。不要继续First/Last-again/resize，不插日志、不改变默认值、不新建CI或重编产品。

本小单元验收是**可归属的clean e48首次Last记录**：源码/原件及私有副本身份成立，命令成功，六图AX完整，Windowpane成为最大卡，原PNG有四次稳定buffer比较且尺寸/ICC/own窗口一致，强kernel恢复与精确IPC/private-prefs清理成功。按原坐标体系保留全部六图frame并单列与已有f9/14参考的差值；这是描述性结果，不是clean e48跨系统视觉通过，不解读私有Binding setter或动画根因。

执行入口仍有明确缺口：[旧Film probe](../outputs/Bern/Docs/Evidence/macOS13-film-clean-e48fff46/runtime/gallery-film-probe.swift:337)已有FirstLast动作与stable/AX采样，但现成followup会执行完整五步，且其[旧defer](../outputs/Bern/Docs/Evidence/macOS13-film-clean-e48fff46/runtime/gallery-film-probe.swift:245)先stop后restore，不能原样运行或通过证据alias执行。目前资料未证明已有带现行kernel-guard安全包络、仅FirstLast的可调用入口。root若不能直接复用已经验证的安全采集入口，应保持该单元未决，只先解决这一接线缺口；不要为建议重建旧probe、临时放宽门槛或补一轮远程矩阵。

本次只读文档、既有源码及证据说明；未执行App/CLI、原图分析、编译、原生动作、CI或Git，也未写实现。
