# 既有 AX 能否解释首次 Last 的 14.5pt 差

不能从现有证据把该差绑定到实际 viewport、NSClipView bounds 或 document/content offset。本批记录确有公开 AXScrollArea frame 差异，但缺少祖先关系、scrollbar 数值及原生 clip 字段；不能把 AXScrollArea scope 直接当作真实 NSClipView。这里的“缺失”是采集未保存，不表示系统公开 AX API 本身无法提供。

固定 e48；只读 canonical13 `macOS13-film-first-last-e48-20261025/raw/report.json`（e47168e3…5c98）和 canonical14 `macOS14-film-e48-endpoints-40165343690/reference.json`（8921655d…8f50）绑定的 initial / 首次 Last。没有使用 repeat Last、其它 cohort、PNG 或像素处理。

## 实际留下了什么

四个 terminal sample 各保存22个 flat rows：2 AXSplitGroup、2 AXScrollArea、6 AXImage、12 AXStaticText。字段仅 frame/role/text/text_attribute。13两次visited204；14初始174、首次Last172；truncated均false。六图完整原row、screen/outer-origin-relative frame，以及每张image相对两条已存scrollarea origin的纯坐标差都在 excerpts.json。

两份 collector 的 `axSample` 函数字节相同：13源191–223行、14源180–212行。它遍历 AXChildren，但只保存 scrollarea/splitgroup/六个名字匹配的行；不保存 AX element身份、父/子ID或层级路径。读取 AXValue/Title/Description 只接受String，数字 AXValue 不落盘；没有读取 scrollbar min/max/orientation、AXSubrole、content offset或原生 clip getter。因此 flat row次序、frame包含关系与truncated=false均不能补出祖先链或完整原生AX树。

## 四次公开 frame

下表是已有 row index3 的 AXScrollArea `(x,y,width,height)`，先只减capture origin，不改变尺寸；index指过滤后保存的数组位置，不是层级或稳定元素ID。

| host / state | screen原frame | outer-origin-relative frame |
|---|---|---|
| 13 initial | (481,132,709,207) | (211,52,709,207) |
| 13 first Last | (481,132,709,207) | (211,52,709,207) |
| 14 initial | (955.5,210,240,207) | (445.5,52,240,207) |
| 14 first Last | (948.3,210,254.4000000000001,207) | (438.29999999999995,52,254.4000000000001,207) |

其余 row0/row2 AXSplitGroup 的outer-relative框分别为(0,52,920,616)/(211,52,709,616)，row1 AXScrollArea为(0,52,210,580)，两host/两state数值相同。仅据几何可列出这些关系；不能给row3赋予“Film实际viewport”或把row1/row3确认成六图的祖先。

row3 的13/14差已在initial存在，而initial四张image的outer-relative frame逐字段相同，Madras/Glen仅保留原非零浮点差。首次Last前五张image的outer-relative x差为−14.5pt，Windowpane为−14.504430837515656pt；row3公开frame的变化不能直接提供这个差的原生offset定义。没有从frame倒推hidden scroll offset，也没有将宽度变化拟合为原因。

## 结论边界

现有普通AX导出不足以完成“14.5pt＝实际viewport/offset差”的对应。缺的是已确认对应六图的真实层级/scroll owner、scrollbar原始数值或真实公开native clip/document geometry；这些字段没有在旧raw中，不能离线补造。PNG与AX又是前后两次观测，不能把它们当成同一时刻native状态。

本轮到此停止。原始5份JSON/Swift输入before/after哈希一致；只用临时stdlib读取/减原点，没有执行归档分析脚本、helper、UI、编译、CI或产品修改。excerpts.json保留原样AX样本、必要派生坐标及共同sampler源码，不作NSClipView识别、容差、像素或根因结论。
