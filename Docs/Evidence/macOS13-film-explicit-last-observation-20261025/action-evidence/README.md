# Last 命令：现有证据只到哪里

固定e48源码和canonical13 report e471…/watchdog fdd…、14reference892165…/rawresult54b06…为依据。只读源码和现存小响应；无新原生动作或产品改动。

13命令025、14首次Last命令017均为同session的`ui activate --target film.to_last`，status0、stdout/stderr均0B。两端terminal inspect中的Last都enabled=true、window=main#1、value=null。它们证明实际注册action被唯一解析、调用并正常返回；不证明物理点击。stage action_start还包住target解析，不能当App callback或到达时间。

固定源码链：`gallery-ui/src/lib.rs:332`声明draft.centered.set(6)；generator expr.rs:303–315发出session赋值，controls.rs:263注册同一action。真实e48生成源BernGenerated.swift:1159为`session_GalleryDraft.centered = Int64(6)`，并在1055绑定ScrollPosition。**setter580只有window?.set(...field8...)返回true才更新本地@Published缓存，否则静默return。**Runtime.swift:1334–1346只检查Rust bern_session_set的首字节；Rust runtime:385–411校验window generation/type并写draft/revision。Runtime.swift:1540–1544无论setter是否静默拒绝，activate闭包返回后都发空Unit成功；CLI收到ok=true/null即exit0。精确路径/固定commit行号和SHA见evidence.json。

因此现有日志可证明“action送达并返回、按源码尝试set6”，没有直接读回Rust draft或本地centered=6。唯一`state`在Last之前，读的是engine值，不含GalleryDraft.centered；ui.inspect的按钮value=null也不提供它。

更后段仍有边界：position的onChange可能因followed/target/nearest guard返回；14用native scrollPosition，13用ScrollViewReader/scrollTo。显式scroll会退役legacy initial owner。nearest来自已报告frames与viewport的计算；coming/150ms quiet wait再更新stops/arrived/arrivals，不是native completion回调。AX放大卡片、stable PNG和“Last”标签都不能替代这些私有字段或实际clip/content offset，也不能把本次14.5pt差归为某一源条件。

唯一下一观察契约（仅文档）：在BernScrollPosition.scroll(to:)既有go闭包**原target赋值之后**，一次记录首个typed6请求的uptime、wanted/position/target、nearest、coming/nudges、arrived/arrivals/stops、已有viewport/anchor/frame6，以及13已有legacyMargin/initial owner状态。用plain非Published内存slot；原分支/赋值/动画/时钟顺序不变，不增Task/timer/await/RunLoop/flush/layout/原生getter，采集完成后才一次序列化。内存复制仍有开销，不能声称零时序影响或等同旧collector。

这一个点只证明请求go实际到达及当时已有状态；native clip/content offset和后续arrival仍未知。缺record、多次候选、无效字段或IO错误应单独diagnostic_complete=false，不覆盖旧slot、不重试、不修改原action/native/cleanup成功值或旧cohort、不降低门槛。不会将“记录到target6”写成“布局修复/已到位”；不实现或启动该观察，也不展开记录矩阵。
