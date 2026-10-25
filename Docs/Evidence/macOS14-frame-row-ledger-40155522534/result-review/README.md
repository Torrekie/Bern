# Frame Row：失败 cohort 独立复核（冻结）

本轮保持失败：control success；observer 原 report.success=false，failure=Missing/truncated row placements。没有 PixelGate PASS，也没有可接受的 ledger。未修改任何原收据或产物。

- observer packet 是 byte_limit 截断：63,828B，35条完整 placements，sequence0…34，首 entry→末 complete 为0.1721741667秒；PID/stage/token 与 arm 对应。end_state=not_observed。只确认保留机制失败，不解释宽度值或指定 UI 原因。
- 两次报告均记录 termination0、app_still_running_after_cleanup=false、front327→327，并有恢复前台请求；无 cleanup failure 或 ledger I/O error。首次 sessions status3 保留为原允许的启动轮询。这里核的是 CI 收据，不是重新观察远程进程。
- 两原 PNG 均920×668/8bpc RGBA，SHA 与 capture 对应，ICC逐字相同（3d40c076…eb5f55）。独立 Pillow/四 byte tuple 离线计算没有色彩转换、重采样或 numpy。
- 预声明 Frame ROI `[211,52,920,668]` 的存储 RGBA exact（0差异）；整窗5,284差异像素，半开边界`[10,118,200,146]`。两个区域 raw SHA 均与 root offline-result 相符。这是失败 cohort 的离线图像事实，不能翻转其 success 或接受截断 ledger。
- ZIP 收据记151,597B，API/实算digest同为5845fce6…00a058，170 members；实际解压170普通文件、无 symlink。原 ZIP 已删除，本 reviewer 未能重算 ZIP，也未调用 API；独立确认的是收据一致性和现存解压文件数。

唯一下一方案见 LATEST1.md（≤1页）。它仅修 bounded retention 合同；本轮不实施、不重跑 CI，不改 queries/UI。详细输入哈希与有限结论在 review.json。

本 reviewer 只读收据、JSON/源码，并运行小型纯离线 PNG 比较；未运行 helper、产品、UI、构建、CI、网络或 Git mutation。
