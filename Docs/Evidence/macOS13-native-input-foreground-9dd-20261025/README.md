# macOS13 真正前台键盘输入验收

最终通过的是source-bound9dd Showcase的Tab键盘路径，未修改Bern产品或重编App，不是程序化赋值。完整原件见`keyboard-and-focus/run`、`keyboard-and-focus/responses`和`keyboard-and-focus/runtime-report.json`。

真实窗口与Inputs页面确认后请求激活，观察实际active，再取得不重复激活的新baseline；一次Tab将焦点从outline12移到Name53（截图有插入光标）。unicodeEvent输入Bern13Input后，真实窗口显示Hello, Bern13Input，CLI注册草稿同值；此时activations仍0。一次Return后revision1、activations1、last_action Submit，文本保留。所有检查在同一PID11709内完成。

保留两次未通过的鼠标聚焦尝试：AX范围中央和可见placeholder都仍focus outline12，均未发文字/Return；不改写为鼠标通过或已定因的产品故障。placeholder读回后的控制脚本text变量TypeError也保留。此前IPC长路径与早取foreground baseline是准备/控制失败原件，分别在long-ipc-startup和activation-baseline，未计为键盘成功。

此证据仅支持本机13.7.8下受控合成键盘事件的常规编辑、绑定/预览与单次提交，不声称硬件键盘、IME、VoiceOver、自动化鼠标或全控件矩阵已通过。源码复用证明限定在9dd到当前的输入路径。各目录是历史归档，路径不可直接执行。

每次自有进程已按PID/path/bundle/kernel-start保护停止，偏好、normal/TMP savedState和IPC均清理。中间保留App/Guard以避免无谓重编；最终统一删除，记录见final-owned-cleanup.json。各prepare专有module cache均已删除；四原交付二进制保持不变。
