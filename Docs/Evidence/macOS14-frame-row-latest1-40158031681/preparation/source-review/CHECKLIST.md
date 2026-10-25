# Latest1 独立源码审查要点（首版前）

状态：已按 review.json 三核心 SHA 完成并 freeze 源码审查；无剩余阻断发现。绑定已读三核心及作者最终整包 manifest，不替代运行验收。范围为 work/frame-row-latest1-preparation；不执行 patch/helper、编译、UI、CI 或改仓库。

1. **新合同**：新 schema 明示 latest1、保留容量1及总文件≤65,536B；不让旧 prefix reader 默认为成功。明确 total/replaced 与 latest.sequence 的定义和0/1起点，成功路径必须可复算，retained count只能1。无样本、溢出或计数不一致均失败，不称完整历史或 settled。
2. **原子提交**：仅完整 candidate record+计数+identity 一起编码/提交；检查总 packet 大小而非只查 record。首次先检查无旧文件，再同后续一样 atomic 替换；此为自有单 writer 前提，不提供外部并发排他；内存 committed slot/计数只在成功写出后更新，或明确区分 observed/committed。不得混合新计数与旧 slot。
3. **失败锁存**：单条超限、不完整、编码/IO/计数错误之后锁存失败；旧成功 slot即使仍合法 JSON也不可被 consumer接收。保留明确 stderr错误标记及 consumer完成前/cleanup后检查，失败不得静默回旧 slot或改写为正常结束。
4. **原测量与完整 record**：Row EDITS、三次sizeThatFits/一次dimensions/一次place及原分支/数学/推进顺序不变；不增加查询/UI/layout操作。全部原 raw/normalized/offer/extent/top/guide/point/proposal/ordinal/count/bounds/row_size/gaps/finalX/thread/uptime字段保留，不以缩减字段或挑ordinal塞入文件。post-place才做arm/encode/IO的边界不变。
5. **Consumer**：保留 fresh目录、PID/stage/token、arm前后单调时钟与 latest.complete≤stable sample begin 的原条件；保留same real e48/normal/closed/Ready→Paused0/awake/ownPID/stable4/ICC及cleanup/exit失败规则。PNG实际SHA及decoded ICC绑定、固定ROI与整窗差异分列不变。不得放宽时间/原图/IO门槛或把latest叫呈现fence。
6. **失败 cohort与停止条件**：40155522534继续原 observer failure、truncated invalid、非PixelGatePASS。新cohort需独立先过14控制；若latest1仍单条超限、IO/完整性/原时间关系失败，就停并报告缺口，不升cap、节流、重试或扩采样矩阵。

已只审实质阻断，最终绑定当前三核心 SHA和精确源差异；作者若改核心须重新绑定。后续本机13草稿尚未检查，不修改、不提前运行。
