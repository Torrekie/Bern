# Film 显式 Last：源码证据与有界观察准备

当前产品仍为原e48，未修复或采纳新滚动行为，完整macOS13验收未通过。本单元没有新原生运行、桌面操作、远程CI、产品编译或下载；它收窄[上一单次对照](../macOS13-film-first-last-e48-20261025/README.md)中约−14.5pt差异的证据边界，并实现下一次诊断的源码。

## 已确认与仍缺失

[源码审查](source-audit/review.json)证明兼容层可能介入程序化滚动：非live的bounds通知也会排队snap；initial owner首次退役后generation不再递增，后来的显式Last不因此自动使这波工作失效。源码允许这条路径，现有运行没有记录它是否实际执行，更不能由此解释−14.5pt或指定修复。

[已有AX复查](existing-ax/RESULTS.md)确认未截断的是筛选后的walk。持久化结果是flat role/frame/string行，没有父子ID、数值AXValue、实际NSClipView、document offset或完整原生树。13的AXScrollArea行宽709pt，14对应行宽240/254.4pt，这些公开AX矩形不能直接充当真实viewport。

[Last动作复查](action-evidence/README.md)确认成功Unit响应只证明唯一可用注册闭包被调用并返回；generated setter在window.set拒绝时可以静默返回，原activate仍complete成功。这是源码上的可能性，没有实际写入失败证据。原日志没有直接读回centered/target/nearest/arrival/native offset；放大卡片与稳定PNG也不能替代这些值。

Apple的[scrollPosition(id:anchor:)](https://developer.apple.com/documentation/swiftui/view/scrollposition(id:anchor:))说明identity绑定与anchor影响，且[scrollTo(_:anchor:)](https://developer.apple.com/documentation/swiftui/scrollviewproxy/scrollto(_:anchor:))描述对应点的对齐；均没有提供解释这次数字差异的native inset公式。[updateTarget(_:context:)](https://developer.apple.com/documentation/swiftui/scrolltargetbehavior/updatetarget(_:context:))列举两种主要触发情况，不是其他上下文的排除保证，不能据此宣布14绝不处理程序化请求。当前官方页面读取的URL/摘要hash与限定见[收据](api-reference.json)，未保存整页或把当前文档当14实现轨迹。

## 已实现的观察源码

[小型源码包](preparation/README.md)锁定Style3912ecd…与Runtime255bac…两个e48模板；patcher只输出统一diff，拒绝未知hash及生成后Runtime。原repo模板不变。外部core在Runtime尾部加入，inspect只有一个macOS条件hook。

- 只在macOS13且显式env启用；单请求、非Published内存，五个固定槽及有界计数。没有新增View、Task、timer、layout/flush或滚动操作。
- 请求槽在原target赋值之后读取已存在SwiftUI状态；weak owner关联同一BernScrollItems。首eligible schedule/settle与首writer分别记录，writer保留自己的token和native输入，不能混作同一工作。
- native运算只取原locals；唯一document.frame getter提为maximum前的local，次数仍一，差异明确写入patch。原条件、算式、队列、动画和150/160/180ms不变；内存复制/clock与getter位置变化仍有开销，不能声称零观察效应。
- 首post-request ui.inspect触发导出。当前固定collector是在Last PNG与terminalAX后才有这次inspect；core本身不识别PNG或Last action，未来必须核单请求、实际wanted/position/target6、owner及collector顺序，意外早请求不能拿后续记录补救。
- 所有JSON清理/编码发生在一次postcapture导出phase，每槽2KiB、总16KiB；缺槽、多请求、身份变化、非法字段、限额或IO失败独立成为diagnostic失败，不改原IPC响应、采集或清理真值。不记录被guard拒绝的路径或通知cause；writer表示已请求setter，不是动画完成。终态在PNG/AX之后读，非原子。

## 实际本机检查

[实际收据](checks/template-patch-and-parse.json)：冻结patcher执行一次；系统patch以fuzz0应用到两份私有源副本，得到Style `fb2adb07…cb771c`、Runtime模板 `1da1f603…8a2b77`。两完整模板在Swift5.9.2/请求SDK14.2/arm64-target13下parse0、log0；[独立core](checks/core-typecheck.json)真实AppKit/Foundation typecheck0、12.757726s、log0。parse不是模板类型检查，standalone typecheck不覆盖整个SwiftUI应用；没有Swift6产品链接或Mach-O内嵌SDK声明。

[独立源码复核](review/review.json)核过正逆10个Style改动、一个Runtime hook、core、实际源/补丁hash、weak身份及导出边界，无所查源码阻断。它没有运行诊断，也不证明视觉无影响、路径执行、到位、根因或产品通过。

临时module cache49,557,817B及三份编译/parse源副本359,166B在完成检查与peer读取、hash/lsof核验后清除，共49,916,983B逻辑文件，见[cache](checks/cache-cleanup.json)和[副本清理](checks/source-copy-cleanup.json)。core、两diff、小收据与原始上轮证据保留；不把逻辑大小当APFS实际回收。

## 下一门槛

下一只准备精确e48的最小observer构建：先核原631输入，再只改变这两个模板，让原generator和正常build plan生成/编译；实际生成Runtime需验证file-extension展开及可能SVG来源，不能把template-only patcher直接套到它或臆造已有SHA。不得修改Rust session语义、原CLI响应、几何/anchor/默认3/nearest或计时常数。

完整Swift6/新SDK/target13产品构建与实际来源、诊断关闭/开启的观察影响控制、远程14适用参考、独立strong kernel私有副本入口，都仍是运行前门槛；本单元不放宽原5秒偏好清理或95/75秒界限，也不重用旧cohort原始locks。已停止的Row、颜色、搜索和Scene路线不重开。完整13等效、macOS11/Swift5.3、Objective-C和iOS阶段均未因此通过，goal保持active。

本目录为canonical证据，work相对别名仅供读历史，不能执行、构建或清理。未来使用须复制已核hash的源码到fresh regular目录。顶层SHA256SUMS覆盖最终普通文件，不含清单自身。
