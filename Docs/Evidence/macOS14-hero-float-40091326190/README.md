# Actual hero float：same-binary13/14归档

本cohort已完成CI40091326190的新SDK/min13构建、实际14 off/on以及同一分发binary的实际13 off/on；四次运行与离线控制完成。结论和完整边界见 [RESULTS.md](RESULTS.md)。没有证明UI/完整flight等效，也没有选择raw行方向或确认系统性/唯一OS原因。

- `same-binary-13-14/`：原CI/本机cohort、package源码/manifest、build/signature记录、四run receipts/report/PNG、四个raw payload、root独立whole-buffer复核。指定binary和tar未复制；原SHA与验证记录保留。
- `analysis/`：冻结half-float analyzer/spec、四份unknown-direction结果、全buffer比较及来源。
- `controls/`：root原PNG比较helper及全部原记录；其中包含较早local SDK13和smoke历史，不能全部当成本cohort新控制。当前四个控制在RESULTS列明。

`archive-validation.json`记录源package23项、tar/bin、四receipts、原PNG/raw、ICC、root独立解码和当前控制指纹核查；`archive-provenance.json`记录copy与排除项。顶层`SHA256SUMS`覆盖所有现存文件（除自身）。子目录原manifests保持原字节与历史范围，其中binary/tar相关引用有意缺少实物；不能把它们冒充最终现存文件合同。

所有work原件保留供root清理。只在本新归档内部对完整SHA且bytes相同的PNG/raw去重硬链接，没有链接work或旧archives。逻辑去重量不代表APFS物理回收量。
