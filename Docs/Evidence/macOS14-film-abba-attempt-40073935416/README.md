# ABBA 40073935416：首组末态 AX 预算耗尽，未取得配对结论

本次为失败的采集器运行，**不是产品失败，也不是完整 ABBA 结果**。harness `2c186620c10c98656d1bd530c531c765574249dd`，固定 observer `79da4a84909a07a6d975cf7606a0cae6d4c22c1c1979a3fdbb0ce0e29aeb0755`，driver `f724bcf84f7d962c51f0e6f0c23ec1861942adcb3b476413c9372b9c8abcb07e`。

2026-10-24T07:24:31Z 仅查询一次状态，job120813156384 已 completed/failure。随后通过既有受限 helper **只下载一次** 740,321 字节的 `macos14-film-abba-evidence` 到 raw。artifact 已足够定位，未另下载 joblog、应用或制品，未触发任何重跑/产品修改/UI。

## 原始失败点

`raw/summary.json`：`phase=observe-A1`，`failure="AssertionError: "`。A1 observer exit0，26.350秒，原 observer 的全部 immediate/wait/direct 已执行。外层验证在 `gallery-film-abba.py:193` 的 `assert c['first_second_ax'] and not c['settled_ax']['truncated']` 失败；traceback 原样保留于 raw。

| A1 / f9 场景 | startup-ready尺寸（点） | 最终PNG | 末态AX耗时 / visited / 截断 | 完整AXImage |
|---|---|---|---|---|
| immediate | 900×600 | 920×668，4次相等比较 | 0.1217967秒 / 113 / true | 0/6 |
| wait | 920×668 | 920×668，4次相等比较 | 0.0810540秒 / 172 / false | 6/6 |
| direct | 920×668 | 920×668，4次相等比较 | 0.0892088秒 / 174 / false | 6/6 |

原末态walk的默认预算是0.12秒，故此处的直接证据是 immediate walk 未遍历到图片即达到时间上限。不是缺少 `first_second_ax`（实际有3次）；也不能以稳定PNG补造缺失AX几何。wait/direct 的六图均完整，Glen窗口内中心601、宽267.5347869873。immediate 的末态几何没有值，保持未知。

只有一组新身份实际启动：`dev.bern.film.abba.40073935416.a1.2224040c2e0e4b7ab5b874c9c0dbf74e`，三个不同PID/session。B1/B2/A2均未启动，所以没有A1/A2或B1/B2重复性、跨源码差值或根因结论。该组全部normal标志false，AX/Screen Recording预检true，原active捕获门槛通过。

## 来源、完整性与清理

raw保留原始JSON、全部PNG/CLI/AX/startup、隔离签名/成员记录、原源码及日志，没有后补或改写。独立核验166个ledger条目全部匹配，无漏列、缺失或多余文件。原 `SHA256SUMS` 自身SHA256：`8ddd7c4eac97d339960232b0c3362c3286b7392a79be784dc0bc1b8c4c44ea3a`。包括ledger自身，raw共167个文件。

CI记录两侧原exact所有regular member在退出前均复验相同；A1复制/重签只改变允许的三个成员，Mach-O section与归一签名存储payload一致。cleanup.errors为空，清理前后own进程均为空；scratch62,575,244字节、两份下载目录2,122,058和2,131,265字节已移除。记录证明最终未遗留own进程，不证明每个应用一定通过正常退出（原observer仍有有界SIGKILL fallback）。

`integrity.json` 为下载后的独立SHA核验；`analysis/analysis.json` 从原report重算每case startup与六图，不信任summary内派生geometry。分析器来自工作区 `work/film-abba-analysis/analyze.py`，没有网络/应用执行功能。它区分采集门槛、启动高度、同源码重复性和跨源码几何，不自动判像素或因果。

## 单行采集器修正的审查边界

父任务拟将唯一 `entry["settled_ax"] = axSample(root)` 改为 `axSample(root, timeBudget: 2)`，复用已有followup预算；仍是同一轮末态walk，不增加retry/输入动作，首次1秒采样、startup、Inspector/Film动作和稳定PNG顺序不变。若仍截断/不足六图继续fail。这是稳定PNG之后的元数据完整性修正，不是产品fix。

这一walk可能实际增加耗时，使其后的ui.inspect与下一fresh场景起点变晚；新observer/harness必须分别记录，不能称与79da逐点同序同耗时。新运行不得拼入本失败run组成ABBA；各次原始证据独立保存。
