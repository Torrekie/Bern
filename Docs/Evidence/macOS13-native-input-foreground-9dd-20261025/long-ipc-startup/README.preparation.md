# 一次真正前台 Name 输入：准备包

仅准备原交付 Showcase9dd 的私有副本与专用 Showcase Guard。没有执行 watch、启动 App/Guard、获取 desktop、发送输入或修改权限、安装的后端、产品源码及原交付。`preparation/isolation.json`、成员与 Mach-O 比较、签名/编译命令记录绑定实际产品；`preparation/sources.json` 绑定运行源码。

目录分离：`products/` 是私有 App，`tools/` 是专用 Guard，`preparation/` 是准备记录；未来 watch 独占新建 `run/`，外部 MCP JSON/PNG 可写到另建的 `responses/`。不要把响应写进 `run/ready.json`、`run/own.json` 或清理收据。

根代理在 Gallery 桌面检查结束、桌面空闲后，从本目录执行一次：

```sh
python3 session.py watch
```

该进程先用 Guard 保存原前台 PID/path/kernel-start，再启动本次私有 App。直接子进程立即记录公开 kernel 身份，随后要求 NSRunningApplication 身份与单一 IPC session 一致。watch 不主动激活、导航或输入；`run/ready.json` **只表示 IPC 就绪，不能表示实际原生窗口或 Name 已就绪**。活动运行期从保存前台前开始计，最多240秒；结束后另有有界清理。根代理持有统一 exec 的 session_id 轮询这个进程，不重复启动它。

先获取实际 App 状态，确认窗口有内容；随后可显式用原 CLI 准备 Inputs 页面：

```sh
python3 control.py baseline state
python3 control.py setup-inputs inputs
python3 control.py before-edit inspect
```

每个标签只用一次。control 先核对同一 PID/bundle/path/kernel-start；CLI 调用最多8秒，并受 watch 剩余期限限制。它仅允许 state、ui inspect 与选择 Inputs，完全不提供编辑 Name 或提交的替代入口。实际原生页面/字段必须由新的 AX/截图确认后才能输入。

未来桌面操作只做一次清晰路径：在取得 lease **之前**已有 `run/original-front.json`；`acquire_desktop` 的 app 参数选 `run/ready.json` 的私有 PID，因该接口会先激活再采集 lease 基线。核验当前前台确为该 PID、截图 isActive 为 true、Name 草稿为空，然后由新快照的真实 Name 编辑区域得到全局点坐标，单次 coordinate click（不传 element_index），再次核实 Name 焦点。只有焦点明确时才使用 `type_text(strategy=unicodeEvent, delivery=direct, restore_focus=false)` 输入 `Bern13Input`。读回草稿与 Hello 预览且 activations 仍为 N 后，再发送一次 `press_key(Return, delivery=direct, restore_focus=false)`，最后要求 activations=N+1、last_action=Submit。

```sh
python3 control.py after-edit inspect
python3 control.py before-return state
python3 control.py after-return state
touch run/finish
```

若窗口、焦点或事件交付未确认，就记录未验证并创建 finish，不重试 AXValue/AXConfirm/Search/Tab 或坐标参数矩阵。工具成功摘要不等于原生编辑/提交通过。该路径仅针对合成键盘事件，不承诺物理键盘、IME 或 VoiceOver。

finish、240秒截止或子进程退出后，Guard 仅对本次强身份执行“必要时恢复原前台，再停止自有实例”；原前台已变则保留用户当前选择。正常 terminate 未退出时可能对核验相同的自有实例 SIGKILL，不能称正常退出。仅当子进程未注册为 NSRunningApplication 时，驱动允许核验 path/parent/kernel-start 且明确非前台后的直接子进程停止分支；实际是否使用由 cleanup.json 记录。

确认自有实例消失后，只清本次新身份的 preferences/savedState 与独占 IPC，并核对原四个二进制哈希。准备使用的专有 module cache 在 prepare 的 finally 中立即删除；一次运行完成后也删除不再使用的私有 App/Guard 二进制，保留源码与小型记录。若身份或恢复条件不满足，保留相应产物并如实记录清理失败，不扩大清理范围。

`preparation-attempt1/` 是准备阶段的元数据超时原件：swiftc --version 的8秒期限触发，尚未开始编译/运行。后续只把该元数据期限改为45秒，编译仍有90秒期限。最初相对 argv0 的准备调用断言在产生准备输出前已修正；这两项均为驱动准备问题，不是 Bern 产品结果。

`preparation-attempt2/` 保留随后已成功编译/签名的准备记录；其后的私有域缺席检查因遗漏 Path 导入失败，finally 删除了未完成的 App、Guard 与缓存。修正该导入后，最终准备使用相同命令完成。两次编译均只针对本包小型 Guard；失败尝试没有执行 Guard/App/watch，缓存均已移除。`preparation/kernel-reader-self-check.json` 仅验证 Python 对自身进程的公开 kernel 读取，不触及桌面。
