# Scene showsTitle：macOS 13 原生对照

**停止此候选，不合入产品。** 冻结源码的真实 SwiftUI `App` / `Window` Scene 中，`unifiedCompact(showsTitle: true/false)` 两侧均为38pt顶部区域；false隐藏实际标题，并将plus工具栏项左移691pt。它不满足已有整应用52pt顶部区域及可见标题的目标。本次没有追加14 CI，也没有创建自定义原生控件。

## 实际结果

只改变一个不可变Boolean；NavigationSplitView、detail toolbar、Buttons内容、sidebar/search、同一次外框归一化与激活均相同。使用本机Swift5.9.2、SDK14.2、arm64/min13，在macOS13.7.8运行。每侧3次原生getter样本、一次外部原PNG和AX快照；记录为key/main/visible/frontmost。最终来源与窗口身份已由[独立审查](review/README.md)核对。

| 窗口点位 | true | false |
|---|---|---|
| 外框 | 920×668 | 920×668 |
| contentLayoutRect | 920×630 | 920×630 |
| content safe-area top / AX toolbar高度 | 38 / 38 | 38 / 38 |
| 原生sidebar toggle item-view | x149，top8，34×22 | 相同 |
| 原生标题field | x189，top11，55×16，可见 | hidden，0×0 |
| logical NSWindow.title | Buttons | Buttons |
| 原生plus item-view | x882.5，top8，29.5×22 | x191.5，top8，29.5×22 |

原图：[true](runtime/true/window.png)、[false](runtime/false/window.png)。原生item-view边界、AX外层点击框、可见字形和logical title彼此区分。false的logical title仍是Buttons，不能据此称屏幕标题仍存在。截图为深色；未记录normal三设置或effective appearance门槛，不作配色等效结论。

这是独立Scene机制检查，不是完整Showcase/Gallery或14运行。既有52pt参考来自[真实应用](../macOS13-toolbar-title-host-f6/RESULTS.md)及先前Scene记录，源码范围不同；不作跨范围逐像素比较。没有5帧稳定链、物理交互、焦点导航或动画验收，也不据此断言所有公开AppKit路径均不可行。

## 来源与首轮边界

[冻结源码](source/ToolbarShowsTitle.swift)SHA`e590fec503cfbd63830f911b1e78acb1d3df551deb04a7210cba5c4a008abb0a`；冻结确认后编译产物SHA`5db7396a34c05f2cd45cc4a35c2631bbd88ee1bbf20b1527fec68a682fee0ed0`。[编译收据](build/build-input.json)、[打包清单](build/prepare.json)和[实际payload审查](review/final-payload-review.json)保留全部26sections、签名storage归一化比较与actual strict codesign结果。两个私有bundle从同一次编译复制，仅Info.plist/签名身份不同；不把整文件签名差异解释成程序逻辑差异。

首编启动时源码准备仍在修订时段，编译前输入hash没有锁定。后续冻结源重编与首编字节不同，因此首轮来源归属被拒绝，记录保留在[preliminary](preliminary/true/driver.json)及[首轮payload审查](review/preliminary-payload-review.json)。它不用于冻结源码验收，也不将编译差异指定为某一修订的已证明结果。[修链说明](preliminary-build/rebuild-proof.json)保留失败比较；最终重新采的是同一个Boolean问题，没有扩大style/页面矩阵。两轮截图逐字相同，仅支持原PNG去重，不回填首轮源码归属。

## 清理与后续范围

两次桌面session均已释放；最终pair的两个进程都先恢复原Simulator9292，再退出精确匹配的PID/bundle/path/kernel-start实例。[清理及桌面审查](review/final-runtime-review.json)保留中间AX将自有激活标为interrupted的状态，未把最终released/false回填为全过程无中断。光标距离为0，未改TCC或用户设置。

清理前已独立读取实际payload。随后[退休4个App、3份裸程序、2个guard及pycache](cleanup/payload-cleanup.json)，合计2,011,883逻辑字节；[73个缓存文件](preliminary-build/module-cache-cleanup.json)经无打开文件检查后删除，合计49,621,131字节。另将224,235字节的[两张逐字重复PNG](cleanup/duplicate-png.json)改为相对别名。原交付Showcase的GUI/CLI哈希及strict签名[保持](cleanup/delivered-preserved.json)。这些是逻辑大小，不是APFS物理回收量。

源码、日志与证据均在本归档，旧work路径为[相对别名](archive-move.json)，没有重复保留试验App或编译缓存。历史构建/驱动脚本原样保留，使用时须复制到新的自有work目录并配置原工作区路径；不在归档内执行。

[远程产物查询](preliminary-build/remote-availability.json)仍返回两项未过期产物，没有重复dispatch/download。本轮未达到用户要求的远程长时间不可用暂停条件。整个macOS13移植仍未验收；macOS11/Swift5.3、Objective-C与iOS阶段继续推迟。

[后续小步审查](next-plan/README.md)建议停止无新证据支持的toolbar参数排列，转向既有完整9dd应用的一次sidebar search原生ASCII输入链。该动作尚未执行，只补13输入链证据，不预告IME、人手或14等效通过。无需新产品probe、产品构建或CI；现有FocusGuard裸程序已退休，如后续确需恢复/退出保护，可只从已核源码重建小helper，并继续清理其自有缓存。
