# 下一门槛：一次真实 Standard named coordinator transition

**选择真实 flight gate；不先扩 custom，不据静态均值采用 recipe。** 当前 named p0/p1 平均绝对残差5.21086→1.52520、5.2244→1.56788，但分别5改善/7恶化、3改善/9恶化，最大残差仍25.754/26.186；其它10ROI exact、原raw不变。实际报告确认一次转换0.2589792917秒。这不是视觉等效，也未验证进入真实动画前的同步成本；custom静态扩展不能回答该风险。

**源码可行性与最小派生。** 复用 `Docs/Evidence/macOS14-hero-coordinator-app-40110795231/same-binary-13-14/probe/ProductHero.swift`：FixtureScene的同URL、同非空key、显式`.standard`的BernImage以`.id("source")/.id("destination")`替换（行363–383），正常NSApplication.run/default-mode sampler与实际Hero原块，不手动snapshot/enter/leave/tick/visibility。产品AppKit:1992–2014在enter获取previous/departed的from与新anchor的to，2033–2044的leave可先生成Departure；真实成功单次替换的目标是两个实际snapshot记录，而非让fixture自己制造两张。Flight.started在1967/1969初始化，120Hz原timer在2018–2024建立，均在同步snapshot之后：须单独报告触发→两snapshot→Flight.started/首次live延迟，不能只看动画内progress。

只在原renderer.cgImage返回后、原NSImage构造前，插入同一固定CIImage(true、原空间)→RGBA8/sRGB、deferred:false recipe；两条原NSImage.draw、实际clock/visibility/finish均不改。default不创建context/派生，candidate一个context、两个实际source/destination派生（不预热）；同key不可合并成静态单图缓存，也不可只凭可能复用的CGImage scalar地址缓存。按snapshot序号+anchor scalar identity/rect记录归属；弱NSImage身份与manager实际Flight.from/to对应，保留各原尺寸与corner0。两个结果各一次，重复/漏失/额外primary快照明确incomplete，不能去重以凑数；原teardown前freeze，cleanup仅原路径、转换0。helper缓存/context仅在PNG及原窗口teardown后清理；不额外retain原CG/provider、不称对象全部dealloc。

**构建与一次配对。** 本机Swift5.9.2/SDK14.2的静态clock guard在mac13会preconditionFailure，不能搬到真实flight。沿已验证SDK26.2/Swift6.2.4→arm64/min13同binary分发（旧cohort a98bd3…），保留原timer/MainActor实现，不用假clock、Unsafe或shim。本机13先default：原生/execution/缓存/normal/front/3PNG全部通过，并复现旧同host的两个endpoint控制（旧source→dest本有小原生差，不要求二者彼此exact）；失败停止。再fresh-process candidate，仅一次真实替换；如需14参考，使用同新binary的default，不在14应用候选。不延长原3s preload/1.5s readiness/7.2s collection/7.9s watchdog/15s外界限或512采样上限。

**最小报告/拒绝口。** 两次snapshot分别记录序号/anchor与from-to归属、开始/renderer返回/转换开始结束/包装返回uptime、原/派生scalar IDs/布局/extent、上下文创建数1、转换数2、请求true而实际tone-map执行未知；并记录transition触发、实际Flight.started与首次live时间。原single-flight identity、真实frame/progress改变、timer存在、overlay归属、source正常detach、native finish后timer nil/临时view0/destination唯一attached，以及normal/front/cache/noMTK原门槛全保留。before/settled五稳定buffer；mid仍首次band arm后下一原自然sample一次capture，完整before/after state/uptime，最多3PNG，不冻结/补帧/重试。仅靠metadata不能证明实际隐藏/显示：原图需确认中间确有飞行内容、未双重绘制，最终destination非blank；不同progress的13/14 mid不作像素相等。保留所有转换成本和同步阻塞区间，不因native成功即接受0.259秒冷停顿；本gate只检验可运行性/生命周期/实际延迟，混合色差仍未解决。

**生产意图仍是独立阻塞。** Runtime:2513保存dynamicRange，2642按Standard选择显示，2680传BernPictureHero时未传intent；Style:1631–1651→AppKit Probe:1771及Anchor.snapshot:1848–1864也没有intent字段，snapshot仍用picture.image。此private Scene显式Standard足以限定实验，不能冒充产品正确路由。产品采用前至少须显式传递并更新intent到Probe/Anchor，并只在mac13/Standard正确门控，不能靠key/图像profile/像素猜意图；High、默认High、其它输入/尺寸/retarget均未验。本步不实现该产品改动，不继续toneflag/格式矩阵，也不声称全动画/视觉等效。

本轮仅源码与已有小报告只读审查；无实现、编译、UI或CI。
