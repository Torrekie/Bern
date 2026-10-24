# 9dd Showcase 完整构建、启动及交付

源码 `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`，CI [40066468884](https://github.com/Torrekie/Bern/actions/runs/40066468884) 成功。Swift6.2.4 / SDK26.2 / arm64 / macOS13.0最低版本。构建、GitHub记录、原压缩包成员哈希、严格签名及Mach-O section比较均保留。`README-preparation.md`只描述执行前准备；后续运行以本文和原始report为准。

初次检查只等transport session，`windows=[]`就调用inspect，3秒超时；该partial原样保留于`launch-check/`，不能据此判断产品挂起。改为同一18秒绝对期限内同时等待CLI登记main及本PID可见CG窗口，约6.328秒就绪；随后window/control inspect成功（1窗、2控件），全程6.575秒。原始poll、窗口记录、stdout/stderr和成功report见`startup-window-gate/`。harness没有调用activate，前台PID1390→1390；这不是主动窗口外观或全界面视觉验收。

本机运行的是独立bundle ID签名副本；所有40个GUI/14个CLI Mach-O sections与CI原件相同，CLI字节相同，GUI整体因签名不同。未经修改的CI原件现已移动到`outputs/macOS13/Showcase.app`及`bin/showcase`，再次核验全部16个archive文件哈希及两份严格签名。Gallery仍为f9。交付替换及清理见`delivery.json`；旧Showcase、签名副本和重复CLI已在自有PID退出后删除，原包也已删除。没有清用户defaults/TCC/窗口历史。

实际BernImage Standard→High→Standard分支/像素验证另见HDR候选目录；本目录启动检查不替代它，也不覆盖hero、High色彩或全部控件。
