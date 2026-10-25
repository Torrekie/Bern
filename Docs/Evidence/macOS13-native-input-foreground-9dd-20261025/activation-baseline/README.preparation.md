# 前台 Name 输入：短 IPC 根的定点修正

新 regular 目录，仅准备，不执行 App、Guard、watch、desktop 或输入。旧 `native-logic-input-foreground13-20261025` 全部源码与 sources receipt 保持原样；旧失败是驱动完整 Unix socket 路径超过产品100字节上限，不能归为 Bern 输入功能失败。

本包复制同源驱动，仅在 common/prepare 中改为唯一短 `/tmp/bern-input13-<uuid12>`，并在 prepare 与 load_lock 都断言完整预计 `bern-<16hex>/<14hex>.sock` 小于100字节。独立短IPC自检在72字节路径成功bind，随后立即close/unlink/rmdir；未来运行的IPC根尚未创建。原始自检见 preparation/short-ipc-bind-self-check.json。它仅证明本机AF_UNIX bind，不证明Bern已启动或Name输入通过。

session.py、control.py、FocusGuard.swift 与旧包逐字相同。Guard编译参数在仅替换任务文件路径后完全相同；原小型二进制因上一轮watch按约删除而重建一次，编译/签名成功。编译器版本元数据复用旧事实，未再次执行版本查询。专有module cache已在finally立即删除；receipt记录逻辑字节，不声称APFS物理节省。完整source/flags比较见 driver-delta.json 和 driver.patch。

根代理在桌面空闲时，从本目录启动一次：

```sh
python3 session.py watch
```

驱动先保存原前台强身份，再启动私有Showcase9dd；活动期最多240秒，清理另有有界期限。run/ready.json仍只代表单一IPC会话就绪，不能替代真实原生窗口/Name的AX和截图检查。不得并行启动另一个watch。

```sh
python3 control.py baseline state
python3 control.py setup-inputs inputs
python3 control.py before-edit inspect
```

每个control标签只用一次；仅允许state、ui inspect、选择Inputs，绝不提供Name编辑/提交。先确认实际窗口，再显式选择Inputs并确认新快照唯一Name字段。之后完全沿用根代理已审查的严格前台方法：以私有PID获取exclusive lease，确认isActive/前台PID，单次坐标点击真实编辑区域，确认Name焦点，再unicodeEvent/direct/restore_focus=false输入，草稿/Hello预览同步且计数不变后，才一次Return/direct/restore_focus=false；最后要求计数+1和Submit。

```sh
python3 control.py after-edit inspect
python3 control.py after-return state
touch run/finish
```

事件或焦点不明确即记录未验证并finish，不执行AXValue/AXConfirm/Search/Tab/坐标矩阵。MCP响应另放responses/，不覆盖run中的身份与控制记录。finish/截止后仍使用原Guard的恢复前台→停止自有实例顺序，只清本次私有偏好/savedState及短IPC根。原四二进制哈希复核通过；一次运行结束后不再使用的私有App/Guard按原驱动清理，保留源码和记录。
