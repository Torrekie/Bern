# Toolbar title-host 候选：本机 A/B 阴性

本次四组对应PNG整文件与解码RGBA逐字相同，所有选定header/title/Toggle/sidebar几何最大差0。单文件navigation.rs候选f6未在这次active macOS13四页序列中改变结果。按父任务决定不合入产品，也不追加14CI；不外推所有页面/平台永远无效。

## 来源与范围

A为原交付source `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`，B为仅navigation.rs诊断source `f6be9bd95253970ad82429f8b6df107d4447e647`。实际observer source SHA为 `bcc2d36a35aad9aa79f3bd1a398600735837025fb9ec2e51657c8aa98ab382ee`，wrapper为 `2155609f04678ac13249125995831ebf26c8331cd00960e1f643517111d150c1`。

输入为v2唯一A→B运行的capture-pair，134项原SHA全部匹配；原清单自身SHA `cfa7992edd0470d64cae8b32b694daaa001e575c6a5caa6512ff23f270012a61`。旧attempt-1独立保留，未与新运行拼接。分析只读raw，不依赖已清理的B exact/tar，不执行app、collector、UI或CI。

## AX祖先与窗口内点

均由AX屏幕frame减主AXWindow原点(260,112)得到，采用顶左坐标。它们是AX可访问性范围，**不是**直接读到的NSView/NSToolbarItem实例frame、标题文字墨迹或实际私有canvas类型。

八个stage在breadth-first树中最早匹配动态标题的节点均为index9 `AXStaticText`，其AXValue等于主窗口标题。祖先为 `AXApplication → AXWindow → AXStaticText`；它是Toolbar的兄弟，不是Toolbar后代。

| 阶段 | AXWindow/CGWindow标题 | titleheader local(x,y,w,h) |
|---|---|---|
| Buttons | Buttons | (197,0,575,52) |
| Text | Text | (197,0,715,52) |
| Controls | Switches & Sliders | (197,0,236.5,52) |
| Buttons重访 | Buttons | (197,0,575,52) |

上述标题及frame，A/B逐项一致。宽度是AX标题可用区域，不是标题字符串的字形宽度。

共同几何与祖先：

- 主AXWindow：(0,0,920,668)；Toolbar为它的直接子节点，local(0,0,920,52)。
- Toggle：`AXWindow → AXToolbar → outer AXButton → inner AXButton`，两层AXDescription均为Toggle Sidebar。outer为(149,0,48,52)，inner为(158.5,14,29.5,18.5)。不能把两者混为一个button边界；inner仅按AX层级记录，不给它杜撰native类名。
- sidebar scroll及其AXOutline均为(0,52,140,616)，outline id为`main_window.sidebar_search`；detail scroll为(141,52,779,616)。两者位于主AXSplitGroup的不同分支。A/B全部阶段一致，没有sidebar宽度或分隔起点改变。

完整节点索引、Window/Toolbar祖先链、局部frame与四对B−A差值在ax-analysis.json。只报告此处保存的末态，未测物理按键、折叠侧栏、窗口resize或编辑过程。

## 完整树与可选属性错误分开

A/B对应visited/discovered分别210/213/241/208；八次均 `tree_complete=true`、`structural_query_failed=false`、`truncated=false`，必需窗口/toolbar/Toggle/sidebar frame均可读。与此同时，八次均 `complete=false`、`query_failed=true`，不能称所有AX属性完整。

保留的可选错误包括outer Toggle/按钮AXSubrole=-25200、Controls的AXRadioGroup/部分AXCheckBox AXDescription=-25200。**A首Buttons还有AXMenu node97的AXSubrole=-25204；B对应记录为-25205。** 两者父链位于MenuBar下，不属于主Window Toolbar；该差异照实保留，不归因为产品变动，也不以像素相同抹掉。所有-25205/-25212及其它代码计数均在JSON，原节点仍在raw。

## PNG配对

四对00-buttons/01-text/02-controls/03-buttons均1840×1336 RGBA（920×668点、2×），每对文件字节及全部2,458,240像素完全相同：变化像素0、差异bbox为空、MAE0、最大通道差0。无需移位、裁剪、重采样、合成或色彩变换。

八张PNG的4032-byte Display ICC相同，SHA `e2473ef48182e793b50bd21dd4d1d9b37d26b02b5a38508ded86d836ef9b64d4`；原collector的color_space_name=unnamed也原样保留。详见pixels/metrics.json及其复算脚本。

Light仅由collector请求，未断言effective appearance；这些是本机13同次A/B结果，不是13/14色彩验收或一般视觉等同结论。

## 运行记录与封存

原collector A/B分别约6.55/6.07秒，normal首尾全false，前台1390→1390；四页程序化选择均成功，每捕获四次raw相等。wrapper cleanup.errors为空、ownPID空、两侧原件全members复验true。磁盘偏好清理不宣称清除cfprefsd内存域。

本目录仅有离线脚本、小JSON/说明和清单，没有复制原PNG或binary。复算应在副本/新输出路径中进行，避免覆盖冻结派生文件；原capture-pair始终保持不变。
