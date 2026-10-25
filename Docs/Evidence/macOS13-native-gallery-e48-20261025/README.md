# macOS13 原生 Gallery 功能补验

复用交付 e48 Gallery（GUI `d44f051c…` / CLI `31a75c0a…`），本机13.7.8 arm64。没有重建或改动产品，没有像素/颜色数值对比，也没有新增CI。四次独占身份进程均使用同一来源明确的私有签名副本、清洁偏好与独占IPC；下列各次运行范围分别保留，不能混写成一次全通过。

## 新实测满足的范围

- **合理窄窗及退出 Inspector。** `narrow-attempt/` 的真实外框从900×652调整到720×600。详情、关闭按钮与主图案可见。对当前可见 Close 发一次原生AXPress，工具返回 `-25204`；随后草稿Details读回false，Close退注册，原生截图显示面板消失、网格扩展。效果有独立读回，不能把工具返回写成干净成功；也没有做物理点击、divider拖动或极限宽度矩阵。
- **原生浅/深色可读。** 上述正常系统深色截图中控件和图案可辨。`clean-appearance-attempt/` 独立干净启动，只调用现有Light菜单绑定，engine从System到Light，随后真实窗口为浅色、AX完整68项；未在这次动作前请求AX树或关闭Inspector。它证明这一条干净启动外观路径，不证明下述超时已经修复。
- **e48的First。** `film-first-attempt/` 通过现有Film页及First真实Bern控件绑定，原生图显示Gingham首卡可见且放大；First/Last均enabled，AX72项。没有把始终存在的六个AX名称当成滚动位置证明，也不要求精确居中坐标。没有宣称这次完成Last→First运动轨迹。
- **真实播放进度与暂停。** 根目录 `media-progress-report.json` 的AVFoundation状态为Playing 0→501ms，然后Paused 848→848ms；sourceVersion1、views1、无error，7项检查均true。原生Frame图有实际视频内容。控制经已有CLI执行，Gallery本来声明`controls:none`；ACK本身未计通过。只静音本次独占播放器，未证明可听响度或手动播放按钮行为。
- **Volume复用已有充分证据。** `volume-source-reuse/` 独立核对f9/e48/b72的11处相关源码区域字节相同，因此复用f9的原生popup开/关与内容注册/卸载，以及另一次草稿0.7→0.55读回。这是两份旧实测加来源未变证明，不是e48新测试，也不证明物理拖动或实际音量变化；示例Slider仅绑定draft，未接Video音量。

## 如实保留的失败与限制

`narrow-attempt/` 在原生Close后切Light，engine已Light、窗口仍为旧深色，AX0；下一Dark UI请求超时10秒，后续读回仍Light。后台窗口、AX读取与UI响应之间的原因尚未确定，不能预先归因为13外观适配缺失。第一次准备采样时进程已由600秒watch结束，身份保护拒绝操作；没有拿到栈。干净启动Light随后真实成功，不能据此消去这次未解释现象。

干净外观诊断中的只读`sample`又触及8秒上限，未产出栈；这是诊断采集失败，非产品崩溃证据。首次Frame读取没有先等待挂载与Ready，返回`player_not_found`，尚未播放；同一代未继续观察，不能确认其原因，该原件保存在 `film-first-attempt/`。独立补查增加最多8秒的挂载/Ready/views等待，得到上述实际进度，不改产品和测试数值；它不补成前一代Film→Frame挂载已完成的证据。

普通Name焦点/键盘编辑/提交仍沿用前一输入补查的“未验证”，未在本目录重试。没有全量键盘、IME、VoiceOver、手势或显示器矩阵。当前goal未完成；下一步只需针对未解释的Close/外观响应和真正原生输入缺口处理，不重开像素或已满足的媒体/Volume路线。

## 来源及清理

`session.py`、`control.py`及两个限定脚本是当时采集源码；各次isolation记录实际期限（600/120/300/300秒）、PID/kernel身份、CFID、完整成员与签名变化。只改变私有CFID和签名，Mach-O section及排除签名尺寸后的其余字节核对相同。辅助Guard冷编译90秒超时、同缓存一次增量编译成功的原件保留；它不是产品构建证明。

四个自有PID72260/76112/77738/78500均由绑定kernel身份的Guard停止，并清掉偏好、IPC及普通/临时savedState。Guard在terminate后仍存活的同一自有实例使用了SIGKILL，不写成正常退出。最后前台成为Simulator，Guard保持该前台，没有为恢复旧1390而打断它。无其他进程被停止；光标位移0、配置未变、lease均释放、最终overlay不可见。

`owned-artifacts-cleanup.json` 记录移除53,434,798逻辑字节的私有App和已无用module cache，不能当APFS实际回收量。只保留一个158,832B、签名及源码哈希明确的活动Gallery清理Guard，位于 `work/native-logic-gallery13-tools/`，供尚未结束的Close/外观诊断复用，避免反复生成约50MB编译缓存；完成该范围后删除。历史目录及work别名不可直接执行、构建或清理。
