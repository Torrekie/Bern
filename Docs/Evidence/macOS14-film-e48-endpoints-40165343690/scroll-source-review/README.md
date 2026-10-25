# ScrollPosition source-only review — no proven compatibility failure

固定e48源码链已核：Film position=draft.centered（初值3），所有adaptive First/Last都只赋1/6；真实Generated的原生action与bernControl activate同样赋值。layout.rs497–566生成keyed scroll items、center snap/anchor与horizontal scope。文件SHA均匹配既有e48的631输入记录；没有读取旧几何大档案或运行程序。

没有找到“明确Last/First后initial owner仍未退役”的源码缺口。Style2469/2492/2525/2590分别在用户滚动、消失、stops和scroll(to:)退役它；finish2222清key/applied并增generation。5112–5124的pending snap检查generation，因此未开始的旧work会失效。已开始的AppKit动画是否会被后续滚动自动替换不能从这一guard推出。

三个应区分的静态事实：

- 唯一scroll(to:)调用2537之前的guard2536要求wanted!=target，因此2599的target==wanted清空/重发分支在这条同步调用链不可达。这是13/14共用逻辑，不等于13缺陷；重复赋相同ID也不是独立操作事件。若item本来已对齐，没有用户可见错误。
- initial owner在同一个StateObject中是永久一次性的（2210–2229）；onDisappear会finish，而同对象再次onAppear不能begin。Gallery实际离页/返回是否保留该对象没有证据，不能宣布重现bug。
- resize在target仍非nil或初始owner仍owned时可能重发（2473–2488/2571）；stops后target=nil，不再持有程序化ID。后续AppKit bounds通知仍可能snap，14的原生resize行为也需实际证据。源码只证明分支条件，不能证明fallback center错了。

如果旧证据尚未覆盖且root选择一个下一序列，仅考虑：Film初值3→First1→停稳→现有窗口resize；实际state/nearest仍1时，再点First。先证明action送达、model值及真实viewport/item center，才判断重复同ID是否缺少必要重对齐。若resize改变nearest或画面本来正确，就停止该假设，不人为制造偏移。要认定13兼容缺口，还需同适用状态的14对照；现有静态几何差不能代替此链。内部owner/target身份不在普通registry中，未观察到就保持未知，不凭截图补结论。

本轮不提出修复，不修改anchor/padding/font/计时常数，不重开Row或颜色任务；未运行native、编译、CI、测试或新skill。完整源行与边界见review.json。
