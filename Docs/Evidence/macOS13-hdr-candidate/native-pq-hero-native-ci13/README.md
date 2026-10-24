# native Core Image 固定输入阴性实验归档

本实验已经由root在macOS13完成编译、default控制和单独nativeCI采集；结果为阴性，未改产品。当前结论、实际构建入口和边界以 [RESULTS.md](RESULTS.md) 为准。

`fixture/`是work夹具、原report/PNG/收据的有界逐字副本；`analysis/`是冻结离线算法及完整结果。未归档HeroNativeCIProbe、modules或编译缓存；work原件暂留给root按所有权清理。

**历史措辞提醒：** `fixture/README.md`、`fixture/static-validation.json`、`fixture/source-provenance.json`及`fixture/SHA256SUMS`保留准备阶段的原字节和哈希，里面“未编译/未运行/等待14”不代表最终状态。准备README的“eager-profile-observer disturbance”只是当时的描述，**原因仍未知，没有证据证明eager observer造成差异，不应作为因果结论引用**。本归档不作该归因。

实际执行的是`fixture/root-build.sh`，复用既有sibling module cache；准备的`fixture/build.sh`没有执行。二者的来源和实际编译/运行收据均保留，不能将fingerprint中存在build.sh误写成它被执行。

顶层`SHA256SUMS`是最终现存文件合同；两个子目录清单分别属于原准备/原分析历史。`archive-provenance.json`列copy来源/排除项，`archive-validation.json`记录源、fingerprint、原PNG、独立ROI复算与运行门槛核查。没有修改Acceptance、索引、产品、harness或发布。
