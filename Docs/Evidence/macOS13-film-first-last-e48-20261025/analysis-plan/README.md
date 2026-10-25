# 单次 Film13 initial / first Last 离线比较计划

此包先于本机数据冻结，只准备一次实际采集后的离线导出。没有运行分析入口、helper、driver、App、CLI、UI、编译、CI 或 Git，也没有生成本机观测值。collector 固定 c4a1bd81e61079a75047e9cfc1f1407b2f12de1ccad7744878ff98975839ee9b；canonical reference.json 固定 8921655dea0938f76e49cfc808414d3278fce1deabeca1b98f5fd1d5bdfe8f50（真实 e48 / 40165343690），路径可在只读归档后变化，字节 hash 不变。

只导出 `initial`、`last` 两个 Film 状态，各取 Gingham/Tartan/Madras/Glen/Houndstooth/Windowpane 唯一 AXImage。保存原始 screen x/y/width/height、capture bounds X/Y，并仅计算 `x−originX`、`y−originY`；width/height 不变。再逐字段列出 13−14 的 screen 和 origin-relative 点差，不四舍五入，不配准，不设容差、成功位置或“更接近”判定。initial 是同进程前置上下文，不重新开启已停止的 wait/direct 几何验收。

每状态保存原 capture/stable 记录（四次相等、samples、elapsed）、完整 controls、AX 时间/visited/truncated 等原元数据；PNG 只读原始文件 SHA/字节数、Pillow format/size/mode/info、解压后的原 ICC profile 字节数/SHA，以及像素尺寸÷capture点尺寸的 x/y 比率。不存在 PNG resize、load/convert、像素哈希拟合、颜色转换、ROI、阈值或像素比较；原 WindowServer raw buffer 未留存，不把 PNG 文件 SHA 称为该 raw buffer SHA。不同 scale 原样报告，不重采样。

原始完整 commands 表保留 startup 非零 status/原时钟；其 stdout/stderr 保留原路径、大小和 SHA，不复制或修改原日志。14 完整 commands 含后续四步，仅作为原报告真值；几何仍仅 initial/首次 Last。两状态完整 controls、各自实际 timing、collector success/cleanup fields 全部直出。强制读完整外层 watchdog JSON；可追加真实 kernel/ownership/post-run/prefs/helper-build/locks 等 JSON，每份带原始字节身份，保持所有 false、错误和独立后续 cleanup 的区别。脚本不做安全验收或重写结果。

PNG 先于 AX walk，二者不是同时观测。13 c4a1 collector 的 startup、own-PID heartbeat、select 后采样、75 秒 deadline 和强 cleanup 与14 6c4d不同；不以同产品二进制称“同 collector”。14 旧 stop-before-restore 无强恢复/终止收据，只作几何来源，不能满足13的 cleanup gate。物理输入、完整动画、视觉一致、原因或完整移植均不由此导出证明。历史 defaults delete 5秒 timeout 的 wrapper false 不改；单独后续清理成功不能倒填它。

未来 root 实际运行完，使用同一冻结脚本（路径示意，当前没有运行）：

```sh
python3 analyze.py --reference CANONICAL/reference.json --collector-source FROZEN/FilmFirstLast.swift --local-report CAPTURE/report.json --watchdog CAPTURE.watchdog/watchdog.json --truth-json post_run POST_RUN.json --truth-json build HELPER_BUILD.json --output FRESH_PARENT/analysis.json
```

脚本只读输入，输出父目录须已存在，目标 JSON 必须 fresh，排除与直接输入同路径并用 exclusive create。实际缺少状态、六图、finite frame、正确 reference/source hash 或原 PNG 时停止，不造 fallback；原始数据保留。输出是数据导出，无 parity/pass 字段。后续判断需独立读取完整安全收据与差异，不因脚本返回0推断验收通过。冻结后不临时加 tolerance/ROI/位置规则；确需改变方案时另行记录新版本。
