# PRIVATE CG-direct pixel runner — prepared, not executed

`analyze.py`、`compare.py`、`atlas-rois.json` 原字节复制自 `outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/native-pq-hero-snapshot-view13/pixel-analysis`；没有新像素或方向算法。`run-analysis.py` 只改固定输入、root门槛、完整控制/结果汇总与失败留存。ICC仍为各PNG自身profile→sRGB，perceptual intent0、flags0、8bit RGB；raw编码RGB另行保留。不修改输入、产品或归档，不生成派生图片。

固定输入为 `work/hero-cg-direct13/runtime13-default`、`runtime13-direct`；14 reference 为 `outputs/Bern/Docs/Evidence/macOS14-hero-cgsemantics-40119614788/same-binary-13-14/runtime14/on`。必须等待root明确通知runtime/native、default全部12ROI控制与两个phase原PNG几何目检通过。届时根据原report/PNG的实际SHA填写一份新的 `root-gates.json`，不要将示例的false直接改成无证据的true；示例当前故意不能运行。全部三report/六PNG hash、p0/p1几何及其visual-only限制必须绑定。wrapper在PIL import和任何PNG读取前验证门槛，结束前再核一次report绑定。

获root通知后，用与旧冻结结果一致的Python/Pillow/LittleCMS环境执行（旧环境Python3.14.6、Pillow12.3.0、LittleCMS2.19）：

```sh
python3 -B work/hero-cg-direct-pixel-analysis/run-analysis.py --gates work/hero-cg-direct-pixel-analysis/root-gates.json
```

输出仅在新建的`result/`；已有目录一律拒绝。失败保留summary.complete=false/error、已生成子结果及logs/execution，不覆盖重跑；如确需再次执行，先保留失败，再指定新的`--output work/hero-cg-direct-pixel-analysis/<fresh-name>`。准备时只做静态AST解析与字节/hash检查，未调用此命令、PIL、analyzer或compare，未读取raw/PNG像素。

14先用同一原analyzer重算，并与旧冻结 `macOS14-hero-snapshot-40080838898/analysis/host-analyzer/sdk26-14-analysis/analysis.json` 严格比较版本、analyzer/spec SHA、68个完整comparisons、16个primary、逐phase完整六ROI记录及ramp gzip SHA。路径、runtime PID和时间不是像素合同；输入完整性另由hash绑定。gzip编码版本差异也不静默降级为通过。

随后完整保存default→direct的12ROI raw/sRGB比较；其它10pane有一个不exact即incomplete，不形成候选颜色结论。named两个phase沿用旧wrapper的固定320×180pt位置与非uniform/extrema检查，作为root方向/可见extent目检之外的辅助，不能以alpha/extrema证明upright、每像素覆盖或无背景泄漏。几何策略固定为 `work/hero-cg-direct-geometry-plan/README.md` SHA `aef01e69917f0d6f64c0d9f0f4f2d434511978624d052e432a6cdd800eecc0b3`；不尝试反转、自动找ROI或放宽tuple门槛。

每个phase、named/custom、十patch、全部RGB通道都记录 `D13_default−D14_default`、`D13_direct−D14_default`、有符号变化、绝对残差变化及逐通道改善/恶化/不变，分类只按计算值正负/零，不加感知阈值。保留全部每host/每pane raw+sRGB ramp native columns、全ramp mean/min/max和两来源RGB aggregate残差；不对13/14不同列数做配对、拟合或重采样。所有退步项同样保留，不以bodyexact或单均值代替目标。退出0只表示此有界描述性分析完成，不表示视觉验收、物理HDR、产品修复或唯一根因。
