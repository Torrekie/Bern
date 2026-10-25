# 单次 observer13：预声明离线验证

只准备源码；尚未读取新采集、执行此脚本或产生 native 结果。固定 source e48、新 observer GUI e2fb（成功40176620054，manifest fdb3）与原 CLI31a。原13基线是 canonical `macOS13-film-first-last-e48-20261025/raw/report.json`（e471），两PNG为38133/e31e；不用14或repeat Last替代。

## 端点控制

仅 initial/首次 Last，每状态六个完整唯一AXImage。保留原row、screen xywh、capture-origin-relative xywh和observer−原13逐字段原浮点差；相对框逐值精确相等，没有epsilon、归零、拟合、预定成功位置或14.5补偿。完整controls与commands/日志身份、时序、原capture/cleanup真假一并输出。原PNG先于AX，不是同时采样，也没有可补造的PNG绝对时间。原8秒stable/2秒AX是collector循环预算；记录真实完成耗时，不额外强加包含最后AX调用/PNG编码的墙钟上限。

PNG仅使用完整owned-window画面，记录原文件hash、mode、尺寸、scale、ICC原profile长度/hash和原metadata。Pillow以原mode解码后逐字节比较完整raster；不convert/resize/profile transform/ROI/隐藏sidebar。可比性要求mode/尺寸/scale/ICC一致；端点exact要求两状态全部相对xywh、controls和完整raster精确相同。文件编码hash另报，不用它代替像素相等。sidebar/chrome等任何差异也保留并使strict控制不通过，不能因此唯一归因observer；不自动改crop或阈值挽回结果。

## 诊断独立门槛

Core b9仅macOS13+显式env启用。请求是原target赋值之后读取的wanted/position/target；要求三者实际均为Swift.Int64(6)是校验门槛，未预先保证。本次可能合法地没有凑齐五槽，这应报diagnostic不完整，不改写原capture/cleanup真假。

校验原schema、5个固定slot、实际序列化每槽≤2048B/文件≤16384B、计数UInt64、request_count1、invalid_fields空、diagnostic_complete真；要求数值finite、字段形状准确。owner在request/terminal相同，surface身份在settle/terminal一致，并绑定wrapper强kernel握手所记录的同一ownedPID。该身份是source-backed packet assertion，不是分析器独立访问native对象。

c4原顺序为targetlookup inspect→Last activate→稳定PNG→终端AX→checkedFilmControls inspect→windowlist；collector仅env隔离派生版锁8bdf与source packet8b6a；三处env替换逆还原c4，UI/queries/采样/cleanup原字节保持，不能声称与c4同源/同binary。请求时间必须在Last activate开始至其后首次inspect开始之间；terminal落AX结束之后且在该inspect命令start/end内。不能要求请求早于CLI返回。first schedule/settle/writer不是同一work；writer token可大于1，保留writer自己的native_inputs，不借首settle数值，也不声称动画完成。

只读传入的锁定绝对诊断file一次逻辑快照；缺失、提前导出、错误、无效计数/身份/字段/时序均停止解释。应用原log若有export错误marker也拒绝。不搜latest、不fallback、不重试、不要求产品加inspect。原单次导出机会在IO前消耗。分析器最终复核已读文件hash；export结果不能替代cleanup。只有绑定、capture/cleanup、strict端点控制和诊断均通过，`diagnostic_interpretation_allowed`才真；这也不是14.5根因或整个移植验收。

## CLI（root稍后审核并执行）

在workspace运行：

```sh
python3 work/film-observer13-analysis-preparation/analyze.py \
  --report ACTUAL/report.json --watchdog WATCHDOG/watchdog.json \
  --diagnostic ACTUAL/diagnostic/film-last-observation.json \
  --locks PRIVATE/locks.json --build-manifest SUCCESS/observer-build.json \
  --output FRESH_ANALYSIS_DIRECTORY
```

`--baseline-report`可显式传canonical原13报告，但hash固定e471。输入目录与输出目录双向隔离，输出必须不存在。读取/门槛失败保存errors与可得原真假，退出1；全部门槛通过才退出0。wrapper仍负责实际source/build、私有签名归一与安全前置；分析器只核收据绑定，不执行driver、App、CLI或原生getter。历史defaults5秒false不变。本分析源码冻结后仍需root审核绑定才执行；无测试、矩阵、UI/CI/Git/编译调用。
