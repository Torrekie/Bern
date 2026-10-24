# ABBA 的首个完整几何：补上外部时间界，未补原生视口轨迹

仅从已冻结的 run40074197486 原始 JSON 重建。没有UI、CI、编译、网络或产品/harness修改；未改已有archive、总清单或 `film-native-observation-plan/PLAN.md`。生成前再次核495个原ledger条目全部匹配；原ledger SHA为 `84d8fb444a9a698bbb7e9e1320f35c68619bd41dc149125812cab827f6930c5a`。

## 四次 immediate 的时间表

令观察器记录的select CLI调用起点 `commands.select.start_uptime` 为0（它位于启动子进程之前，不是应用收到动作的时间）。下表单位毫秒，负值在该起点之前。只接受**未截断、六个名字各一次、完整有限正尺寸frame**的walk；没有拼接早期truncated样本。

| 组 | resize CLI起止 | Inspector-close CLI起止 | 首完整六图walk区间 | Glen中心x / 宽度 |
|---|---|---|---|---|
| A1 / f9 | −4695.876…−4486.649 | −107.587…−1.137 | +910.425…+989.943 | 677 / 256.153006 |
| B1 / e48 | −4248.389…−4181.619 | −108.255…−0.733 | +704.249…+753.912 | 565 / 268.799753 |
| B2 / e48 | −3992.138…−3924.310 | −107.114…−1.160 | +700.953…+745.725 | 677 / 256.153006 |
| A2 / f9 | −4238.544…−4192.036 | −107.349…−1.873 | +715.996…+794.658 | 662 / 259.145764 |

中心x减去最终Film PNG窗口X510作为参考；原AX屏幕frame和最终CGWindow bounds均保留。这不是首完整walk时同步取得的窗口坐标。每walk也是顺序查询区间，没有逐元素读取时间戳，不能把区间起点当成所有frame同一瞬间生效。

四次首完整walk的全部六图x/y/width/height均与各自末态完全相同（最大差0）。其前分别有3/3/2/2个truncated walk；**没有用它们推定挂载时间或补frame**。同样方法检查全部12case，首完整walk与各自末态最大差也均0，详细时间见timeline.json。

resize响应四次均记录主窗口920×668、`changed_by=Command`，但只证明返回的窗口事实，不证明scroll布局已稳定。select的command.end为+1088.065/+1086.074/+1041.548/+1036.402毫秒，包含观察器至少1秒的AX循环，**不是应用执行select或IPC回复的准确完成时刻**。close CLI结束也不是Inspector动画结束；四次结束到select启动仅0.733–1.873毫秒。

## ABBA 额外填补与仍缺失的部分

新增确定信息是：四种immediate落点在各自第一个完整早期walk中就已被读到，此后已保存的完整walk及末态没有六图差值。它把“只有最终PNG/末态几何”推进为select后约0.70–0.99秒内的完整外部观测区间；没有给出落点首次形成时刻，也没有证明其前后全程不动。

以下缺口仍在，不能由本轮填补或归因：

- 关闭前的四个 `inspector_ax` walk全部truncated（约−336…−109、−277…−110、−232…−108、−231…−109毫秒）；本分析不使用其中局部frame重建完整Inspector结构。稳定Inspector PNG仍是独立原证据。
- 从close命令开始，经select、早期截断walk，至首完整walk结束（约+746…+990毫秒），没有连续完整几何。未记录native `clip.bounds`、contentInsets、document.frame，亦未记录SwiftUI viewport/margin或TargetContext；这些原生/语义字段在整个ABBA都缺失，并非只有前0.7秒缺失。
- 首完整walk中四次AX容器box相同：window split920×616、detail split709×616、sidebar scroll210×580、Film AXScrollArea240×207。这些是可访问性区域；240不是已证明的原生clip宽，也不能以相同709 detail box推定有效content margin/clip origin相同。
- startup样本只补了own CG窗口与CLI窗口事实。resize响应距select仍有3.924–4.487秒；这段及Inspector退出时没有native viewport/inset时序，不能把先前窗口高度/首完整AX某个值指定为原因。

原观测方案的线程、scope、clip/insets/TargetContext及退出保留需求没有被ABBA替代，本次不修改或扩大该方案。

## 文件

`timeline.json` 是12case的小型派生时间表，保留原时间/command stdout引用、startup窗口事实、所有早期walk的完整性元数据，以及首完整六图/AX容器原屏幕frame。`timeline.py` 只读重建，不执行应用或采集脚本。`SHA256SUMS` 仅属于本新work目录，不改任何已有清单。
