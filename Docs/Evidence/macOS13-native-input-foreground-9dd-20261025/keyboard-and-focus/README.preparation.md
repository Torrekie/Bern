# Name 前台输入：实际窗口与前台就绪

仅准备，不启动 App、Guard、watch、desktop 或输入。复制自已实际通过短 IPC ready 的 native-logic-input-foreground-short13-20261025；旧源码与 sources receipt 保持原样。本轮 common.py、prepare.py、control.py、Guard 源码逐字不变，编译参数仅替换任务文件路径；新的私有 identity/短 IPC nonce 仍由同一准备器生成。

唯一源码改动是 session.py 的结束策略：仍按强身份恢复原前台、停止 own，确认消失后清本次 preferences/savedState/IPC，并复核四原交付；保留 private App 与 Guard，在 cleanup.json 记录它们仍用于未完成的 Name 验收，由 root 最后统一清理，避免再为同一个 Guard 重复编译。编译 module cache 仍立即删除。

从本目录启动一次：

```sh
python3 session.py watch
```

240秒活动期限、finish、原前台 PID/path/kernel-start 收据与有界清理不变。run/ready.json只代表IPC会话就绪，不能证明实际窗口、Name或前台就绪。

```sh
python3 control.py baseline state
python3 control.py setup-inputs inputs
python3 control.py before-edit inspect
```

根代理先获取实际原生窗口，再选择Inputs并核实Name。acquire_desktop(app=ownPID)只视为激活请求；该后端在activate后仅短暂等待，第一份lease可能仍记录旧前台。root须确认actual native active/前台确为ownPID；若不能确认即停止。确认后释放早期lease，不带app重新acquire，让基线绑定已经实际前台的own，再核验Name。

随后保持唯一输入路径：单次Name编辑区域坐标点击，确认focus hint对应唯一Name AXindex；Unicode/direct/restore_focus=false输入后要求草稿/Hello预览同步且activations不变；再一次Return/direct/restore_focus=false，要求activations+1和Submit。不得用AXValue、AXConfirm、Search、Tab或参数矩阵代替。

```sh
python3 control.py after-edit inspect
python3 control.py after-return state
touch run/finish
```

每个control标签只用一次；MCP响应放独立responses/。finish后轮询同一watch session并核查cleanup.json。App/Guard留在products/与tools/，属于仍需要的验收产物；root完成或放弃检查后按归属统一删除。身份或恢复条件失败时，不扩大清理范围。

preparation/保留源码、签名、成员/Mach-O等价证明、编译命令和缓存清理收据。完整预计socket路径72字节小于100；独立socket bind自检后立即删除，不运行Bern。没有修改权限、已安装后端、产品源码或原交付。
