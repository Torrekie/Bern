# Actual payload and retained source/runtime review

原生`!`→首次Library链没有到达，三次driver.success全部保留false。
本审查没有启动App/helper、执行CLI交互、编译、UI、网络或Git操作。

实际读取了retired-attempt1/Showcase.app、build/Showcase.app和Keyboard.app，
并分别绑定attempt1/prepare.json、prepare.json、keyboard-prepare.json。
三份均strict codesign通过：15文件、1个Mach-O、40个sections。
全部sections和签名存储大小归一后字节与原交付GUI `cc267abc…a1c1b`
及对应prepare一致；归一哈希均为`7b85edf1…6bb56`。
实际GUI均min13 / SDK26.2；Info.plist的private UUID与各prepare一致。
变更仅Info.plist和GUI签名相关字节，没有产品代码或资源变化。
原CLI `963eb1f1…e3170`直接bytes一致且strict codesign通过。
FocusGuard `e843bcc9…68ddae`和Profile `88f0b7d5…26839`实际读完，
均strict codesign通过且与三份prepare锁定值一致。payload.json保留完整哈希。
已通知root可退役三App与两helper；本审查不执行删除。

- Case1 / PID81490：108次sessions全部status3，18s未ready，未投递UI。
  实际IPC base113字节已超过完整Unix socket路径100字节上限；当前transport
  :251–263的字节哈希与保留failure-analysis一致。exact9dd关系沿用该记录，
  本次没有Git重查。此为采集器路径错误，不是产品修复；旧执行前review未覆盖
  transport长度边界，不能沿用其“无阻塞”结论把本次失败标通过。
- Case2 / PID81989：短/tmp IPC，joint ready1.237606s；target acquire是自有PID。
  click前后MCP文本均为`The focused UI element is 12 outline.`，search是index15，
  没有确认search焦点。无Unicode事件或Libraryselect；180s守护等待结束时
  finish.json缺失，driver保持false；之后late capture的appNotFound原错误保留。
- Case3 / PID82774：独立freshID，joint ready1.347112s；一次Shift-Tab后未确认
  search焦点，finish明确false，无文字事件或Libraryselect。正常在期限内结束，
  留有1840×1336原PNG收据；本审查不作视觉验收。

两次ready均证明唯一own-PID/layer0/onscreen窗口，初始Text、query空且Library
未挂载。源码的control白名单没有search写入；短IPC runner保留18s/180s期限，
180s finish断言已加入。keyboard runner仅切换私有输出及prepare路径。
Profile.swift只读三项系统flag，没有写用户设置。

三次cleanup均绑定原PID/bundle/path/kernel start；own_instance_still_running=false，
App exit0，front在stop前恢复/保留原PID9292。start/end三项normal flags均false，
desktop均released、cursor distance0。短IPC两次在精确stop后删除自有/tmp目录；
首次长IPC的单独清理收据也保留。完整绑定在source-runtime.json，raw未修改。

这里证明实际交付代码来源及上述失败/cleanup边界，不证明键盘、IME、文本绑定、
首次invalid_search或整体原生UI通过；不从未确认焦点推断产品输入缺陷。
