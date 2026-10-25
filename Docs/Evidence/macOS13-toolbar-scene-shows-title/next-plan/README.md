# showsTitle后的最小检查点

**停止toolbar参数试验，当前chrome差异仍未解。** 在保52pt、真实可见title、不接管SwiftUI toolbar delegate/items、不加offset或自画title的条件下，现有证据不足以支持另一条小原生参数。不能宣称所有公开API已穷尽，也不应因此继续换style排列showsTitle。

依据很具体：[原window计划](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/work/toolbar-next-public-window-plan/README.md:34)已把38pt列为compact停止点；最新[真实Boolean pair复核](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/work/toolbar-shows-title-native-review/final-runtime-review.json)确认两侧都是38pt，false隐藏可见标题，toggle不动。editor与f6标题宿主已阴性。原生完整toolbar所有权在[旧原型](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/work/native-toolbar-owner-fixture/README.md:33)只使Showcase接近参考；Gallery toggle仍偏17.25pt且完整search/query未实现，它是较大导航边界而非本约束内的小修。显式titleBar或其它style没有新的改善证据，不为“尚未试”再开fixture。

下一项可转到**实际9dd完整Showcase的sidebar search原生输入链**，只验证一次ASCII `!`：用现有交付App的独立身份，在Text页以实际窗口点击聚焦search，再通过已知键盘事件路径输入U+0021；读取同一窗口公开AX焦点/字段文本及原registry确认query确为`!`，然后仅用已有页面选择进入Library，等待首次Query报告`invalid_search`并保留原图。页面选择是准备/观测，不把它算原生导航验收；不使用CLI edit/focus/submit替代这次输入。

[BernSearchable](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/crates/bern-backend-swiftui/templates/BernStyle.swift:1020)把原生searchable文本直接绑定MainDraft.query；该Showcase调用没有submit closure，故此动作**不以Return作为提交合同**。其command/shortcut焦点在15之前也未接入searchFocused，不能误称13特有退化。[真实Library生成源](/Users/torrekie/Documents/Codex/2026-10-23/https-github-com-aimessoft-bern-https/outputs/Bern/Docs/Evidence/macOS14-picture-source-40136458675/raw/BernGenerated.swift:1425)把同一query编码到BernQueryView；先输入再首开Library可避开“已有结果保留”的另一个变量。

先保证own front/window与search字段的公开焦点事实；否则停止，不投键。若工具只能读取AXFocused而不能取得App内firstResponder对象，就明确后者未读，不为此造probe，也不能将两者等同。工具若实际走AX setValue/粘贴，只记该输入路径，不能升级成键盘事件验收。输入后若field已是U+0021但binding/query不符，保留这一次原始输入与状态再查源，不先归因兼容层；若两者吻合，只补13这条输入链的有限证据，不冒充人手、IME、14对照或完整UI通过。全程沿用现有focus恢复/精确进程清理，不新写probe，不编译、不触发CI、不重启width或toolbar矩阵。

本目录仅为只读后续路线；本次未执行上述输入动作或改产品。
