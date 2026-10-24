# PRIVATE actual-snapshot SDR candidate pixel runner — prepared only

`analyze.py`、`compare.py`、`atlas-rois.json` 与上一轮CG direct及原NSImageView分析逐字节相同。wrapper只改固定runtime路径、mode/record gate与候选标签；不新增像素/方向算法，不预设改善、恶化或阴性，不改产品或旧归档。归一化仍用每张PNG自身ICC→sRGB、intent0、flags0、8bit RGB；保留raw编码RGB。

输入固定为 `work/hero-snapshot-sdr13/runtime13-default`、`runtime13-baked-named`；14固定为 `outputs/Bern/Docs/Evidence/macOS14-hero-cgsemantics-40119614788/same-binary-13-14/runtime14/on`。环境mode为 `BERN_HERO_SNAPSHOT_SDR=default|baked-named`，实际report key按root转达作者合同使用 **snapshot_sdr_display**，不是snapshot_sdr。读取PNG/PIL之前，wrapper要求13两报告的 requested/selected 精确等于对应mode、success=true、error=null，并原样携带完整记录；primary_frozen、计数、IDs/layout/extent、phase_checks、引用清理等内部native绑定由root native/additive gate承担。helper的 requested_tone_map_hdr_to_sdr=true 与 actual_tone_mapping_applied='unknown' 必须保持各自含义，离线分析不宣称系统确已执行tone mapping。准备阶段未读未冻结source，字段依据root已转达的作者合同；不是helper source review。

须等待root明确通知runtime/native gates、default→旧on全部12ROI raw+sRGB exact，以及candidate p0/p1原PNG几何目检通过，再填写新的root-gates.json。示例故意保持false/placeholder，不可无证据改true。gate绑定三份report及六PNG SHA；几何沿用 `work/hero-cg-direct-geometry-plan/README.md` SHA `aef01e69917f0d6f64c0d9f0f4f2d434511978624d052e432a6cdd800eecc0b3`，此版schema用candidate_geometry。前置check_gates完成前不importPIL/读PNG，全部分析后再次核对report/hash及snapshot_sdr_display完整记录。

获root通知后，用旧冻结环境（Python3.14.6、Pillow12.3.0、LittleCMS2.19）执行一次：

```sh
python3 -B work/hero-snapshot-sdr-pixel-analysis/run-analysis.py --gates work/hero-snapshot-sdr-pixel-analysis/root-gates.json
```

仅写新result/，已有目录拒绝覆盖；失败保留summary.complete=false/error、子结果、logs/execution。不得边看候选边改阈值、flip、ROI或拟合。准备阶段只做AST静态解析和原文件byte/SHA检查，未importPIL、未执行wrapper/子算法、未读raw/PNG像素。PREPARED-SHA256SUMS固定此准备版本；本目录保持可新增未来输出。

14先重算，严格匹配旧冻结14全部68comparisons、16primary、逐phase完整六ROI和ramp gzip SHA，并核同版本/analyzer/spec；不因压缩差异静默降级。候选对default完整12ROI比较保留；其它10ROI raw/sRGB任一不exact即incomplete，不形成候选颜色结论。named自身允许变化，其uniform/extrema辅助检查仍与原wrapper相同，不能代替root的upright/可见extent目检；白色与背景同色不可分，alpha255/frame不证明每像素覆盖的限制不变。不运行tuple/方向新算法。

完整报告named/custom、p0/p1、十patch、所有RGB通道的 D13_default−D14_default、D13_baked−D14_default、signed change、绝对残差变化和改善/恶化/不变；分类仅按正负/零，不加感知阈值。保留全部native raw/sRGB ramp列、每来源/phase RGB aggregate及mean/min/max；不跨host配对不同列数、不resize、不挑通道/均值，不把bodyexact当目标。退出0仅表示有界描述性分析完成，不表示产品、实际协调动画、High/HLG、通用alpha/orientation或物理HDR验收。
