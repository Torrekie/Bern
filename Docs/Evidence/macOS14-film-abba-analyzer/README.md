# Film ABBA 离线分析器（独立归档副本）

`analyze.py` 与实际分析run40073935416、40074197486所用文件逐字节相同，SHA256为 `f3d48a5ea81d215f2c35bc159f6e048436c300efc83435e7552b7d1fbcb92d64`。只依赖Python标准库，不联网，不导入/执行artifact中的任何脚本或应用，不读取或改写原PNG像素。

用法：

```sh
python3 analyze.py RAW NEW_OUTPUT EXPECTED_HARNESS EXPECTED_OBSERVER_SHA EXPECTED_DRIVER_SHA
```

NEW_OUTPUT必须不存在且位于RAW之外。先核完整SHA256SUMS覆盖、两份锁定采集源码、source/隔离成员/Mach-O记录，再从每leg原result重算startup与六图frame。输出analysis.json和它的SHA256SUMS。缺组或截断末态AX保持缺失，不以较早样本填补。

成功run40074197486的三个锁值依次为：

```text
e44cec24fcc54030d52e2e671aec2dd62c13b7c1
6c4d5c93c9331ba4dd6427aa18799b6a1e720b6e2e006e036fb908ced4f9e635
f882d4ef6a2fa389f1ec58bb1eeff87302b70038dc7e6364a40ad6e1ba49de12
```

分别报告acquisition、startup高度、同源码重复和跨源码几何；不自动判像素、视觉等同或具体因果。签名/清理记录的一致性复核不是重新验证已清理的二进制。输入RAW保留不动；本文件夹的SHA256SUMS只覆盖本独立工具副本。
