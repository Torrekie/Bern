# macOS13 连续响应与页面挂载补查

按目标系统的原生逻辑验收，不做像素复刻；沿用source-bound e48交付，无产品修改、App重编译或远程CI。

- `close-appearance-functional`：同一PID99916在720×600关闭详情后，草稿false、Close卸载、实际网格展开；随后Light和Dark的模型及真实窗口均更新，控件树75项。两次切换继续响应。本次通过真实Bern注册回调执行，原生Close按钮证据复用前次独立原件。
- `native-ready-frame`：先确认PID1812实际前台窗口，再走Film→First→Frame。真实播放器读回Ready、6000ms、views1、sourceVersion1、无error；原生截图可见视频，离页后可见Patterns。通过时为独立进程，不解释前次进程最终结果。
- `interrupted-before-close`：前台从ChatGPT变为Simulator，desktop会话在Close前拒绝投递，0 action。Details仍true符合预期；不计作产品失败或通过。
- `close-appearance-functional`中的Frame在约8秒的37次读取内仍Loading。栈包含解码器初始化、ready通知和AVKit内容更新，未证明永久Loading或死锁；最终状态未知。大JSON读取的截断/SyntaxError另记为控制脚本错误。
- `early-ipc-startup`：仅IPC出现后立刻选择Film，5秒超时且原生AX0，尚未建立窗口就绪前提即停止；最终重检先验证实际原生窗口。保留这次未通过的采集，不改写成成功或已定因。

各目录保留原始控制脚本、命令、读回、截图、进程身份及清理记录，仅供历史审计，路径已归档；不要直接执行历史驱动。原交付与accepted templates没有修改。全部私有进程/偏好/状态/IPC已清理，共用私有App在最终身份复核后删除（3,876,102 logical bytes，不声称等量APFS回收）。辅助Gallery Guard二进制已删除（158,832 logical bytes），源码与来源记录保留在gallery-guard-retired。

这组证据补足连续Close/外观响应和独立Film→Frame实际挂载；旧短观察未知项如实保留，不再为其扩展外观或延迟矩阵。仍须单独完成真正聚焦的文本输入/提交。
