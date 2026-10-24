# Film ABBA 40074197486：采集完整，immediate 未形成固定源码分组

本轮取得完整 A1→B1→B2→A2，共12个case、72个末态AXImage frame。**wait/direct四组的完整六图几何逐值相同；immediate同源码重复自身变化，不能把此前565/677差异指定为固定产品源码效应。** 不作像素等同或具体根因结论，也不由这一轮断言源码对结果分布绝对没有影响。

## 来源与采集合同

- A=f9e08b1d55bed4b9d880b19934abe48281057bb3 / existing build39991406873 / build harnessc1900f58bca6fd283bce2d4cf9769f1e6029ebb0。
- B=e48fff46b3a92a28465ad74295bd273a9d69af7d / existing build40070407306 / build harness25e18cbc7cd760c1c399042f1d7364c3d755a9dc。
- 本轮collection harness为 `e44cec24fcc54030d52e2e671aec2dd62c13b7c1`，原observerSHA `6c4d5c93c9331ba4dd6427aa18799b6a1e720b6e2e006e036fb908ced4f9e635`，driverSHA `f882d4ef6a2fa389f1ec58bb1eeff87302b70038dc7e6364a40ad6e1ba49de12`。
- 相对失败run的79da observer，仅稳定PNG后的唯一末态AX walk预算从0.12秒改为2秒。初始1秒sample、startup和所有交互/PNG顺序不改；无产品修改、应用重建或native logger。本轮与失败run分别保留，不拼接成配对。

07:29:13Z第一次查询仍in_progress，07:30:35Z第二次查询completed/success（相隔82秒，job120813964478）。按授权仅下载一次2,824,734字节artifact到raw，未重复下载app/原build、joblog或触发CI。

## 原始几何结果

以下均为 `runtime/result.json` 中稳定Film PNG之后的 settled AXImage，减去对应PNG的CGWindow屏幕原点后，转换为窗口内点。不是与PNG同一瞬间的原子测量；原始屏幕frame、时间戳与PNG全部保留。

| 组 | 源码 | immediate Glen中心x / 宽度 | wait Glen中心x / 宽度 | direct Glen中心x / 宽度 |
|---|---|---|---|---|
| A1 | f9 | 677 / 256.1530059814 | 601 / 267.5347869873 | 601 / 267.5347869873 |
| B1 | e48 | 565 / 268.7997528076 | 601 / 267.5347869873 | 601 / 267.5347869873 |
| B2 | e48 | 677 / 256.1530059814 | 601 / 267.5347869873 | 601 / 267.5347869873 |
| A2 | f9 | 662 / 259.1457641602 | 601 / 267.5347869873 | 601 / 267.5347869873 |

- wait/direct：四组所有六张图片的x/y/width/height全相同，最大绝对差0；不是只比较Glen身份或中心。
- immediate：A2−A1六图中心x均−15点；由于缩放，frame四属性最大绝对差16.4963790894点。B2−B1六图中心x均+112点，frame四属性最大绝对差118.3233734131点。
- 跨源码A1与B2的immediate六图frame也逐值相同（最大差0）。本轮不支持“f9固定565、e48固定677”的映射。
- 全部逐图、逐属性B−A差值及两对同源码差值保存在 `analysis/analysis.json`，不平均掉原始落点，也不选择更接近参考的一次代替。

## 启动/恢复历史仍是实测条件

每组有一个新bundleID，组内仍依次使用该身份启动immediate/wait/direct三个fresh进程，以保留原场景恢复顺序。新身份在启动前通过无有效defaults/savedState检查；没有预写窗口尺寸或为等待恢复增加动作。

| 组 | immediate ready宽×高 | wait ready宽×高 | direct ready宽×高 |
|---|---|---|---|
| A1 | 900×600 | 920×616 | 920×616 |
| B1 | 900×600 | 920×668 | 920×616 |
| B2 | 900×652 | 920×616 | 920×616 |
| A2 | 900×600 | 920×616 | 920×616 |

900/920/920宽度合同均成立；所有实际Film捕获均为920×668。**ready高度不恒定**，不能改写成四组相同初始窗口。仅就记录，ready高度600已对应677、565和662三种immediate中心，652也对应677；这不是对高度作用的完整排除，单一ready样本并未覆盖整个首次恢复与Inspector退出过程。

## 采集、隔离与清理核验

- 四个不同新bundleID，12个全局不同PID、12个不同session；实际ID/PID/session及所有startup样本见 `facts.json` 与各原report。
- 每组normal三标志false，AX/Screen Recording预检true，原active捕获检查通过，activation后的前台PID均为该ownPID。12个末态AX walk均未截断且六图齐全；耗时约46.5–74.2毫秒。初始1秒样本仍是其原来的有界观测，不用它代替末态。
- 36张原始PNG均有4次相同raw buffer比较；只核验稳定/完整性，**未执行跨组逐像素或ICC比较**。
- A/B原GUI/CLI、manifest/min13/ARM64/SDK26.2与包SHA按driver锁定核验。每组复制品全regular成员与原件相同；重签后实际只有Info.plist与主GUI文件改变，CodeResources未变，变化仍在允许集合内。全部Mach-O section record/hash与归一签名存储payload一致。原exact两侧全成员在末尾复验true；这些是CI记录及其数据一致性复核，不是在本机重新验证已清除的二进制签名。
- 四组observer耗时24.656/22.217/22.762/22.006秒；A1开始到cleanup结束92.534秒。各exit0、下一组前无遗留ownGUI/CLI。cleanup.errors为空，清理前后own进程均为空。远端scratch74,186,966字节和两份下载2,122,058/2,131,265字节已删除。没有TCC修改；正常退出与原observer fallback不能仅凭空进程列表进一步区分。

## 文件完整性与复核入口

raw完全保留下载内容，495个SHA条目全匹配、无漏列/缺失/多余文件；包含ledger自身共496文件。原 `raw/SHA256SUMS` SHA256为 `84d8fb444a9a698bbb7e9e1320f35c68619bd41dc149125812cab827f6930c5a`。

- `raw/{A1,B1,B2,A2}/runtime/result.json`：原始时序、AX、startup、控制器/窗口记录及PNG。
- `raw/summary.json`：采集完成、source/harness、四身份、签名及cleanup结果。
- `analysis/analysis.json`：原report重算的各case/各pair数据，分析器SHA `f3d48a5ea81d215f2c35bc159f6e048436c300efc83435e7552b7d1fbcb92d64`。
- `facts.json`：小型核验表，包含全部36次稳定捕获与12个PID/session。
- `OFFLINE-SHA256SUMS`：包含原raw和衍生分析/本文的独立总清单。

本次仅执行受限GitHub只读查询/一次下载与纯Python离线运算；没有本机应用/UI、产品/harness修改、编译或额外dispatch。现有证据仍不能解释native clip/inset/TargetContext变化，因为本轮没有新增原生日志；下一步由父任务决定，不自动扩大采集。
