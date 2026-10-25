# macOS13 现有 Name 输入的有界补查

按用户“符合目标平台逻辑，允许细微版本差异”的新合同，复用已交付 Showcase9dd，没有修改产品源码、创建 UI 控件、运行像素对比或触发 CI。

结果仍为**未验证**。Text Fields 窗口、普通 Name/Password/Notes 与预览均正常绘制；系统当前深色外观直接保留。工具 AXValue 将 Name 显示改成 `Bern13Input`，但 `ui inspect` 的草稿仍为空，预览仍为 `No name entered yet`。这没有证明原生编辑事件已交付给 SwiftUI binding。后续 AXConfirm 在后端解析失败，AX 树随后只返回9项标题栏/toolbar；同时截图仍有完整输入内容，因此不能把 AX 缺项归为界面空白。没有再发送坐标点击、键盘、CLI edit 或 submit。

补查的写值前后窗口均为 `isActive:false`，前台保持 ChatGPT1390，快照焦点是侧栏 outline12，未确认 Name 的 first responder。这是后台 AXValue 操作，不能当成前台键盘编辑失效。一次独立只读复核已核对截图、AX、草稿、计数及清理结论，没有发现可据此断言的13独有产品缺陷。

`report.json` 汇总实际范围；`supplement-after-edit.png`、`supplement-partial-AX-before-click.png` 与相应原始 MCP JSON 保留显示/AX/模型的差别。截图含工具虚拟键盘标记，不能当 Bern 控件。

首次短会话保存在 `attempt1/`：侧栏文字不支持 AXPress，CLI 只用来准备页面；外层300秒期限在编辑前结束。window activate 的8秒 IPC响应超时和最初 defaults 的15秒清理超时如实保留。后者通过一次明确的 defaults 删除得到0、核对仅剩空字典后删除本次独占 plist，连同独占 IPC/临时 savedState 清完。`session-after-cleanup-correction.py` 是修正后保存的源快照，不能标成首次超时路径逐字执行源码。辅助工具首次编译的15秒超时也在 `attempt1/preparation-timeout.json` 保留；只调整了辅助编译期限，未重建应用。

补查以600秒为总上限，主动结束；kernel PID/path/start 绑定的 Guard 确认本次65454结束，原前台1390保持同一 kernel 身份。首次63373在停止前恢复原前台。独占身份两次均已清除偏好、保存状态及 IPC，没有停止其他进程。lease已释放、物理光标位移0，虚拟光标配置未变，最终 overlay不可见。两个有界检查的终止中，Guard 在正常 terminate 后仍运行的同一自有实例使用 SIGKILL；不能写成两次正常退出。

私有副本只改变 CFBundleIdentifier 与签名，Mach-O sections 和排除签名尺寸的其余字节验证相同；原交付 GUI/CLI 哈希未变。所有不再使用的私有 App、辅助二进制和 module cache 已删除，详见 `owned-artifacts-cleanup.json`。本目录为历史诊断，不应直接重新执行；没有完整本机输入验收，也不证明新的macOS13独有产品缺陷。后续优先独立的布局/Inspector/媒体功能缺口，不继续这组 AX 参数尝试。
