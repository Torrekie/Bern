# Film initial / 首次 Last：冻结方案离线结果

冻结 analyze.py 唯一执行 exit 0（0.2566187909687869 秒），stdout/stderr 空。未改脚本或方案；execution.json 的逐项 before/after 哈希全部相同。仅离线读取原 JSON/PNG 元数据；没有像素解码、缩放、颜色转换、ROI、容差或位置验收判定。命令日志另保留实际原始路径/大小/SHA，未倒填其 before/after。

输入：13 report `e47168e331b8c231755d18add58aaaf56541e59090f29e75d60e6d4486fc5c98`；watchdog `fdd2e7776729971bb3d0ba67a094a02e3cb98a1cc9a645cb733bdcc74d350116`。14 固定 canonical reference `8921655d…e8f50` 的 initial_setup 与首次 Last；没有读取 repeat Last 的几何来替代首次 Last。

## 采集与真值

- 13 collector success=true，elapsed=8.599077939987183 秒；外层 native invocation exit0。27条 CLI，仅首两条 sessions 为 status3，其余25条0；完整命令/controls/时钟和原日志身份保留在 analysis.json。14完整33条原命令亦保留，其中含后续阶段，仅两状态几何进入比较。
- 13正常配置的三个辅助显示开关均false，Light/Film；Row ledger和scroll trace均false。两终态 AX walk 各有六个唯一、有finite frame的 AXImage，均未truncated。
- 13 collector强kernel receipt记录原前台1390在stop前已恢复；owned Gallery25080已结束、termination0，外层own=null。collector与watchdog success均true，defaults delete status0、private preferences absent、exact-child/IPC cleanup true、originals unchanged。完整原值在collector report、watchdog及额外JSON中；不将14旧cleanup当成本机安全证明，也不改历史5秒timeout的false。

## 元数据

| 状态 | 13 stable samples / elapsed | 14 stable samples / elapsed | 13 PNG SHA | 14 PNG SHA |
|---|---|---|---|---|
| initial | 6 / 0.7693675833870657 | 5 / 0.6381279999999947 | `38133c7326467de07e8981affb5b516e782c6c511b4a0a83fe35205e06350879` | `46ae79801159c1a9b26e6a86225e51bcfc34a667bf215ec94a611c6cfe8b00d8` |
| last | 14 / 1.8508213749737479 | 11 / 2.0844297500000266 | `e31e7385a300e3f686b2a434a627e0a1ad49a0214a16e92ad8188b783393cb69` | `13788694f15e1d1c87111de35daac508c6fa65e7f725ae4639136504013e6522` |

两端 capture bounds 均920×668pt，四次连续相等；13 origin=(270,80)、PNG1840×1336、scale ratios=(2,2)；14 origin=(510,158)、PNG920×668、scale=(1,1)。均RGBA。13原ICC profile4032B/SHA `e2473ef48182e793b50bd21dd4d1d9b37d26b02b5a38508ded86d836ef9b64d4`；14为3300B/SHA `3d40c076ef474f107eb2c08fa5cebe2546e836500f4029ded5db7de763eb5f55`。完整PNG/EXIF/ICC元数据见analysis.json；scale与ICC原样报告，未归一化或据此比较像素。

## 每张图的点差

下表是原声明的 `(13−14)` capture-origin-relative `(x,y,width,height)` 点差；screen原始xywh、relative原始xywh、screen点差和每图原AX row均完整保存在analysis.json。origin自身差为(−240,−78)，没有把窗口位置差当成内容偏移。全部数值按原浮点表示保留，不按阈值归零。

| 状态 | AXImage | Δ(x,y,width,height) pt |
|---|---|---|
| initial | Gingham | `(0, 0, 0, 0)` |
| initial | Tartan | `(0, 0, 0, 0)` |
| initial | Madras | `(-4.884147301709163e-06, -3.235747612961859e-06, 9.768294489731488e-06, 5.494665600735971e-06)` |
| initial | Glen | `(3.076170855820237e-06, 2.037963326984027e-06, -6.152341825327312e-06, -3.46069231227375e-06)` |
| initial | Houndstooth | `(0, 0, 0, 0)` |
| initial | Windowpane | `(0, 0, 0, 0)` |
| last | Gingham | `(-14.5, 0, 0, 0)` |
| last | Tartan | `(-14.5, 0, 0, 0)` |
| last | Madras | `(-14.5, 0, 0, 0)` |
| last | Glen | `(-14.5, 0, 0, 0)` |
| last | Houndstooth | `(-14.5, 0, 0, 0)` |
| last | Windowpane | `(-14.504430837515656, -0.0029354298540056334, 0.008861675031312188, 0.0049846922050562625)` |

首次Last前五张image的relative x差均−14.5pt；Windowpane为−14.504430837515656pt，宽/高差非零原值如上。初始四张image差向量为零，Madras/Glen保留非零原浮点差。以上只描述本次实际观测；不设“可接受”门槛，不据此推根因、完整移植或视觉等效。

PNG在AX walk之前，二者不同时；两端collector/startup/heartbeat/采样时序不同。本轮仅initial与首次Last，不重开wait/direct旧验收，也不外推到repeat/history/wide、物理输入或完整动画。下一判断由root查看原PNG及独立安全/数据复核；此导出没有产品修改或新采样。
