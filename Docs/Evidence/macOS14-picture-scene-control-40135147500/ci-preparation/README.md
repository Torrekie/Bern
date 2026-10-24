# Picture 完整 Scene control：只读准备

结论：优先复用 **9dd 的完整 Showcase CI 成品**，在14只跑一次原完整采集器；本轮未触发。
它是当前可获得、无需重编的候选 control，**尚未证明**在14重现首卡124/125pt与HDR147pt。
先记录实际首卡与HDR高度；重现后才允许在同一 exactsource 上加布局观察器。
如果得到129pt或其它结果，应保留该结果并停止进入插桩，不把历史125pt当当前事实。

## 当前可用性（唯一一次只读 API）

- `GET repos/Torrekie/Bern/actions/runs/40066468884/artifacts`：成功，原响应见 `artifacts-api.json`；未下载。
- artifact `12549219297` / `macos13-showcase` / 2,426,606B / `expired=false`。
- 到期 `2026-10-27T05:33:15Z`（上海10月27日13:33:15）；这是本次查询状态，不保证未来仍可下载。
- GitHub artifact ZIP digest：`sha256:3d2ac931aa00ccf328fc574a2008eadb5b35078e82fdb5c4f5d20b8c0de39dc3`。
- 内层 `showcase.tar.gz`：`fb5fd66e8247d1adada07411cb8368de716cc8e251f6ecf70968678b3d74662b`；两种digest不混用。

## 交付来源与源码差

- 完整产品源码 `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`；build run `40066468884`。
- build harness/head `1c4ef533cc62bb57ef73cfd98df13434bd40b304`，不能冒充产品源码。
- 原记录：macOS15.7.9 / Xcode26.3 / Swift6.2.4 / SDK26.2 / Rust1.99 / arm64 / min13。
- 9dd交付README及delivery.json记录：CI原件移动至 `outputs/macOS13/Showcase.app`、`bin/showcase`；16个archive成员哈希及签名核验保留，原压缩包删除。本轮未重验本地bundle。
- 9dd→当前 `80ff1a365cf05cb44fa3d8517f2da6942ff1a75c`，排除Docs/.github/work后，仅 `BernStyle.swift` 有119增/10删：legacy初始scroll ownership/anchor/snap generation修正。
- 这不是产品字节完全一致；但Showcase `layout_page`、Scene/Window生成、Form/Grid生成与资源均无此区间修改；Picture路径未使用新增scroll-position逻辑。
- 因此可用9dd建立**9dd完整Scene control**；不可将它标成80ff exactsource运行。
- 旧完整14 A=upstream `ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee`、B=`fa820f706e5faf1bae8b8f07e23545842a1648b7`。124/125是旧A/B事实；9dd/min13/SDK26.2不是原A build。

## 最小复用路径（下一次获准执行时）

1. 直接复用 `.github/workflows/macos13-compare.yml` 的 capture job，`build_run=40066468884`、`app=showcase`；该job不构建产品。
2. 下载既有artifact后，核内层SHA、environment的产品源码9dd、min13及strict签名；不重签、不改app。
3. 在14/arm64、normal（reduceMotion=false/reduceTransparency=false）运行原 `.github/scripts/macos14-reference.swift APP CLI OUTPUT`，`BERN_SOURCE_SHA=9dd…`。
4. 保留原collector及其到Layout前的页面/CLI顺序、en/en_US、920×668外框、前台窗口和WindowServer PNG路径。完整collector一次含13PNG；这是一份完整应用control，非采集矩阵。
5. 对唯一 `images-layout-light.png` 核真正Layout、首卡实际高度、HDR147、图像/文字边界；不因像素接近宣称Scene差已定位。无内部布局/环境/geometry观察器。
6. 若原collector启动/窗口/权限/采集失败，保留原partial及非零退出，不加自动retry、offscreen或缩小版fixture回退。

原 `macos14-reference.yml` 固定upstream A且空build_run会重编，不选作9dd复用入口。
原 `macos13-port.yml` 是产品构建入口，也不必重跑。现有compare已满足复用，当前不新增wrapper或workflow草稿。
“无observer”指无产品内插桩；外部CLI与WindowServer采集本就是原control路径。
外框归一化不等于内容rect相同；历史收敛129的isolated不补足真实Scene证明。
此建议只选一条baseline；不跑旧isolated，不改ForEach/static children/负padding，不推进Hero采样分支。

## 边界与冻结

本轮只读取必要源码/小元数据、做一次artifact状态API并写本私有目录；无下载、编译、UI、CI dispatch、产品/仓库/index/旧档案修改。
本次root已要求停止草稿扩展；运行准备状态为 **未执行、control待重现**。输入哈希与API次数见 `provenance.json`。
