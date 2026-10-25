# 下一唯一候选：latest1 完整 placement（提案，未实施）

值得用一个完整 latest slot 替代历史 prefix：本轮已证明 prefix retention 在原 byte_limit 停止，尚未证明任何布局原因。保留原查询、算术、place、arm、clock、UI 及独立 control；仍为65,536B，不增加 cap，不节流、挑样本、合并 ordinal 或新增布局操作。

新 schema（例如 bern_frame_row_latest_v2）必须明确 retention=latest1、retained_limit=1、file_byte_limit=65536。只替换完整 record，保留全部真实 ordinal 与原字段；不缩减或拆分 placement 来塞入文件。complete/end_state 不能宣称 settled；end_state 仍 not_observed。

计数定义须唯一：N=有效 arm 后、完成全部原 place 和 memory 完整性检查的观测 placement 总数；latest.sequence=N−1（从0计），retained_complete_count=1，成功路径 replaced_complete_count=N−1。N=0无样本即失败。计数使用有界整数并检查溢出，溢出立即失败；删除旧 prefix 的64条 retention 上限，改为1条 retention，而不是增加历史容量。不存在一份文件内的连续轨迹证明。

每次把候选完整 record、N/replaced 元数据整体编码到≤64KiB后原子提交；只有成功提交才能替换已承诺 slot。计数和 slot 必须同一快照；失败后不得写出似乎与最新计数一致的旧 slot。单条放不下、memory 不完整、编码/IO/计数错误均锁存失败并保留明确 stderr marker，collector 继续前/后 cleanup 检查；旧有效文件不可作为 fallback。schema/计数/sequence/token/PID/时间关系或最终文件哈希不符即失败。

沿用原 collector 的时间关联和原图门槛：latest 的 entry 在 arm 后，complete不晚于实际 stable sample begin；读取后仍须绑定 packet SHA。latest 表示最后观测到的完整 placement，不证明没有后续调用或呈现已完成。如果持续后续 placement 使原时间关联失败，按失败停止；不放宽时间门槛、不添加强制 layout/flush/fence 或新的 UI 状态。缺样本、超限、IO或关联失败均不解释布局原因。

下一实际 cohort 先以同 collector 的真实 e48 control/observer 在14通过原固定 ROI/ICC gate，整窗差异仍单列；通过后才考虑同 binary13。不能回改本轮为通过。若 latest1 仍无法满足完整单条/时间关联/IO门槛，停止这条修正路线并报告缺口，不升 cap 或展开采样矩阵。
