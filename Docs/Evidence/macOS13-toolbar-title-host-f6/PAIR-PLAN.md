# Showcase toolbar A→B：仅准备，须显式 --run

本次仅在work编写/静态解析wrapper与JSON示例。未执行wrapper（连plan模式也未执行），未复制app/CLI、签名、编译、启动UI或联网。父任务已确认B原件核验通过：GUI `7a1a1f6a51645087b35c60994a331fb8be2ac792aaeec76270363ce353e0c775`、CLI与A同值；observer source为 `2e713cd3513eea2723eaf27af86871749c92302b67c6605649623b441628145e`。父任务将把这些值和唯一编译后的binary SHA填入实际locks；示例的null使实际run在任何app操作前失败。

## 文件与输入

- `run-pair.py`：任务局部wrapper，不改产品/collector。Mach-O函数逐字复用已审查ABBA helper；regular-member和signature-storage规范化检查保持同一方法。
- `run-locks.example.json`：A硬锁为原交付9dd，GUI cc267abc…、CLI963eb1f1…。B只允许f6be9bd…与本任务exact路径（并非build/exact），GUI/CLI SHA由父任务从核验结果填入。observer锁住父任务唯一编译的binary及source SHA；不执行artifact内脚本。
- 父任务另写 `run-locks.json`；不要原地改示例。observer binary应为本任务专属 `observer-work/ToolbarProbe`；该专属目录及module cache属于本次清理范围，不放其它工作。

只有父任务审查后明确执行下列形式才有动作：

```text
python3 /absolute/work/toolbar-title-host-f6/run-pair.py --run --locks /absolute/work/toolbar-title-host-f6/run-locks.json
```

省略--run仅打印计划，不读app、不创建结果/复制品、不执行子进程。该行为本轮只做静态审查，没有实际调用。

## 将执行的有限合同

1. A/B原件先全部full hash/strict签名核验，保存完整regular-member与全部ARM64 Mach-O section记录。原交付A、B exact和B tar不删除、不改签名；B tar是否保留由父任务单独决定。
2. 依次A→B，各一个新 `dev.bern.toolbar13.a.<uuid>` / `.b.<uuid>`。与collector一致的明确owned前缀；新ID的plist/savedState及有效defaults域均须不存在。只改复制品Info的CFBundleIdentifier，合法ad-hoc重签；全部member只准Info.plist、主GUI签名、CodeResources集合变化；sections和规范化payload完全相同。记录所有前后hash。
3. CLI也复制为本组scratch下的相同字节文件并strict verify，使timeout清理不会误杀同时使用原交付CLI的进程。原CLI仍末尾核hash，永不进入删除范围。
4. 调用父任务提供的同一observer：APP CLI OUTPUT，环境仅指定source与variant=A/B，并清除本任务不使用的trace/snapshot/IPC遗留环境。observer负责原样Buttons→Text→Controls→Buttons、启动门槛、activate/条件恢复。wrapper不加入UI动作、不改global normal或TCC；light只是collector请求，不声称配色验收。
5. 每个observer外层最多等120秒；整体work预算330秒，启动下一组前必须还剩完整120秒加15秒清理余量。超时只kill该observer process group及完整路径复核为本任务副本的进程，不retry。A任一失败停止B，原日志/result/PNG完整保留为partial。
6. 前台PID/bundle与normal有效值直接取collector的original_front、front_restore.after、normal_profile_start/end；省lsappinfo，不另读其它应用元数据。wrapper要求normal首尾三项全部false、成功四页/完整AX及每PNG至少4次raw相等比较。不把requested light当颜色一致。
7. 原exact全members与CLI在末尾再次核对。清理用ps -ww列PID、proc_pidpath复核完整可执行路径，只匹配本任务GUI/CLI副本和专属observer；前后复查。新域plist先存档，再仅删本次UUID域/savedState（symlink只unlink本链接）；删除runtime-work和专属observer-work/modulecache。绝不删A交付、B exact、B tar或其它app/domain。

## 输出与边界

结果固定 `capture-pair/`，scratch固定 `runtime-work/`，已有目录使run拒绝启动。每组保存isolation、full member/Mach-O、签名日志、原collector输出与source；summary明确phase、source、前后台、normal和cleanup。异常保存traceback，尾部SHA清单覆盖保留证据。

若observer外层超时被强制杀死，wrapper只按owned process group/完整可执行路径清理；可能没有完整front_restore或normal_end字段，将其保留为缺失/失败，绝不宣称restore成功。正常条件恢复由collector负责；若用户已切换前台，wrapper不激活别的应用或覆盖用户更改。该情况不能作为UI或布局验收通过。所有签名/UI/复制等内容在本文件中均为待执行计划，不是本次已验证结果。
