# macOS 13 title-host 候选：阴性结果与清理

仅把动态 navigationTitle 从 detail 移到整个 NavigationSplitView，没有改善本轮完整 Showcase 的工具栏。四个阶段的 A/B 原始 PNG 文件逐字相同，解码 RGBA 的全部像素差为0；选定标题、工具栏、两层侧栏按钮与 sidebar/detail 几何也相同。因此停止此候选，不合入产品，不为此追加 macOS 14 CI。不能外推为所有标题 composition 都无效。

## 精确来源

A 是交付的9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0；B 是独立诊断分支 ci/toolbar-title-host-candidate 的f6be9bd95253970ad82429f8b6df107d4447e647。B仅修改navigation.rs，显式Detail(titled:false)保留原路径；本候选也会改变14+的标题宿主，未达到产品14保持门槛。补丁、完整文件与来源保存在diagnostic-source/，原只读责任边界审查在source-review/。

[CI40075331576](https://github.com/Torrekie/Bern/actions/runs/40075331576)成功。f6与9dd的环境逐行相同（扣除source/harness行）：macOS15.7.9、Xcode26.3、SDK26.2、Swift6.2.4、Rust1.99，target13。构建manifest相同，原包16个regular文件只有GUI不同，其余15个含CLI/资源/CodeResources相同。GUI SHA7a1a1f6a51645087b35c60994a331fb8be2ac792aaeec76270363ce353e0c775；CLI仍963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170。静态签名、min13、arm64与SDK26.2已核验。

本机collector用Swift5.9.2/SDK14.2构建，min13，运行macOS13.7.8。A/B各用独立新身份，重签只改变允许的Info/GUI/signature成员；所有Mach-O section及归一签名存储payload保持。未修改或启动交付原件。

## 本机运行与几何

capture-pair/为唯一完整v2 A→B记录，134项原始hash由父任务及离线分析独立复核。两组均Buttons→Text→Controls→Buttons，8张稳定原图，每张4次相同raw buffer比较；前台1390→1390，A/B约6.55/6.07秒。normal三项首尾false；Light仅为环境请求，effective appearance未断言，本轮是同宿主几何比较，不是13/14颜色验收。

| 项目 | A/B共同窗口内点 |
|---|---|
| Window / Toolbar | (0,0,920,668) / (0,0,920,52) |
| 最外层Toggle Sidebar / 子按钮AX框 | (149,0,48,52) / (158.5,14,29.5,18.5) |
| 标题header | x197/y0/h52；Buttons宽575、Text715、Switches & Sliders236.5 |
| sidebar scroll/outline / detail scroll | (0,52,140,616) / (141,52,779,616) |

标题header是Window直接子AXStaticText，与Toolbar为兄弟；这不是直接读取NSView/NSToolbarItem实例或字形墨迹。动态窗口标题均正确。完整frame/祖先、原PNG、ICC与像素计算见[离线分析](offline-analysis/README.md)。全部4对PNG连文件字节都相同，1840×1336、2×，无移位/裁剪/重采样/颜色转换。

八次均tree_complete=true、structural_query_failed=false、truncated=false；同时complete=false/query_failed=true，因可选Subrole/Description等仍有原生错误。其中A首Buttons与B的一个隐藏菜单属性错误不同，不宣称全AX属性逐值相同。Role/Children异常、截断、必需标题/toolbar/Toggle正有限frame缺失仍失败。未测物理输入、sidebar折叠、编辑或更多尺寸。

## 失败尝试、版本与封存

capture-pair-attempt-1/原样保留首轮partial及68项原清单：A仅到Buttons，B未启动。210/210树已遍历，初版collector把可选属性错误一并判失败。v2新增结构完整性字段，保留旧query_failed/complete原义与所有错误，并要求实际标题/toolbar/Toggle几何；动作、2秒AX预算与稳定截图顺序不变。两次运行不拼接。

实际v2 observer源SHA为bcc2d36a35aad9aa79f3bd1a398600735837025fb9ec2e51657c8aa98ab382ee，wrapper为2155609f04678ac13249125995831ebf26c8331cd00960e1f643517111d150c1；每次运行目录都包含当时完整源文件和locks。attempt-1-build/保留旧编译/准备元数据。PAIR-PLAN、PAIR-v1清单与原准备provenance属于初版历史，当前以每run的实际source/locks和attempt-2-harness.json为准。原静态README只记录UI运行前的取得状态，本页记录后续结果。

## 清理与清单边界

原件A/B在运行结束全成员复验相同，进程退出且自有路径查无进程。测试副本、observer/module cache由两次wrapper合计移除114986073逻辑字节；下载ZIP验证后已移除2426368字节。阴性结论后再次核验B原件全成员与无writer，清除unused exact与tar合计7526851字节。它们是累计逻辑文件量，不是APFS物理回收测量。

首轮defaults delete自有新UUID超时，留下279字节文件；其后已保存并移除，仅检查自有UUID磁盘路径。v2仅保存并删除各自新UUID磁盘文件，既有全局/原bundle域不动，不操作cfprefsd，不宣称清空内存域或不会再次落盘。收据见post-attempt-1-cleanup.json、post-negative-cleanup.json及各run summary。

STATIC-ACQUISITION-SHA256SUMS是清理前44项历史清单，曾全部核验；其中17个artifact成员现按post-negative-cleanup.json有意删除。其它保留项仍匹配，不将历史清单冒充现存文件合同。两个run内部原SHA256SUMS仍有效；最终本目录SHA256SUMS覆盖所有现存证据。原始PNG/JSON/日志没有改写，未保留不再使用的应用副本。

交付Showcase仍为9dd，Gallery仍为e48，GUI精确hash和严格签名复核通过。本候选没有推进macOS11/Swift5.3、Objective-C或iOS阶段；13的chrome等效仍未通过。
