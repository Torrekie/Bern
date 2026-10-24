# 原 Hero CGImage 的四项绘制属性在 13/14 一致

[CI40119614788](https://github.com/Torrekie/Bern/actions/runs/40119614788) 的 build/measure 均成功。同一份新 SDK 构建、原签名 arm64/min13 binary 在 macOS 13.7.8 与 14.8.9 各运行 off/on；两 key 都观察到 `renderingIntent=0`、`isMask=false`、`shouldInterpolate=true`、`decode=nil`。四组控制各 12 个图像 ROI 的原 RGB 与 ICC intent0→sRGB 均逐像素相同；四份 raw 也分别与旧 cohort 同 host/key 的长度及 SHA 相同。

这些结果排除了本例四项已读取显式属性不同这一解释，**没有解决主显示色差，也不构成完整 UI/动画验收**。原样本、这四个属性相同不证明全部 CGImage 状态、目标 context、绘制或捕获结果相同；不指定 NSImage、系统或显示余量为唯一原因。产品实现未改变。

## 身份与运行

- source：`3c137f307576a44ffc58543def3cfec5b310c9d7`；harness：`9989b904fe3bd2018d53ce91eec08bc52573fcc6`。
- 原产品来源仍是 `b08db54e01ac2ec54fb84e6f2a70041f1f4c3604`；provenance 的 fixture base `5eca0e5904117d131e1129302d50d357e4234a15` 标识本次复制的 probe，不冒充产品来源。
- 构建：macOS 15.7.9 / Xcode 26.3 / Swift 6.2.4 / SDK 26.2，一次构建。binary SHA：`68974a3fe0ae28c23ef47de9657fbc6d34287bb36f50d12d6ac69d52b3eee334`；tar SHA：`2c1151e83775c0a214f3ff36e33f1160883175c8709a6a86456072c52053b014`。
- 本机执行前独立核对 29 个 package members、21 个 source inputs、原始拼接、arm64/min13 与严格签名；未本机重编、重签或创建 module cache。见[执行前验证](same-binary-13-14/package-verification-local.json)、[独立复核](native-analysis/README.md)。

| 运行 | 原窗口时长（秒） | 前台 PID 首尾 | 实际四属性 |
| --- | ---: | --- | --- |
| 13 off | 1.657092094 | 9292→9292 | 不读取 |
| 13 on | 1.612710953 | 9292→9292 | 两 key 均 0 / false / true / nil |
| 14 off | 2.352032900 | 316→316 | 不读取 |
| 14 on | 1.916947961 | 316→316 | 两 key 均 0 / false / true / nil |

四份完整 native/ICC/semantics gate 均通过：normal 三项 false、原 cache ledger 保持、自有固定 nonkey/inactive 窗口、每 phase 五个报告记录的相等 buffer、no MTK、manual static manager flight0/timer nil。它们是静态同图 p0/p1，不是实际 coordinator 或完整应用。retained peak/provider-copy on2、off0，export 后 helper 引用数0只证明该容器清空，不证明全部对象释放或普遍零观察效应。

## 唯一新增观察

只改 [FloatCapture helper](same-binary-13-14/probe/FloatCapture.swift.inc)。原 PNG 保存、原 window teardown、原 provider 导出及记录完成之后、原 primary 引用释放之前，对原持有的 `renderer.cgImage` 对象各读取四个 getter 一次。off 不调用 helper；没有新 snapshot、provider 访问、context、draw、图像复制、recache 或 layer 操作。RGB3 guard 复用前两条 primary descriptor 的既有 space 引用，没有第五个 CGImage getter。原 Driver、产品 Hero/Image/Style 与 finish 主体保持。源码边界及失败传播见[独立审查](code-review/README.md)。

decode nil 独立记录为 present=false/count0/空 values/bits。非 nil 路径在 nonmask/RGB3/64 位 CGFloat、Double guard 后最多读六项，保留有限值及精确 Double bits，遇非有限值保存 partial 后停止；本轮只观察到 nil，非 nil、±0、nonfinite 分支未运行验收。普通失败记录先 append 再走原 catch/release/nonzero 路径，仍受最终 report 写成功限制；原 `try?` 写失败和 hard watchdog 绕过 defer 的边界未扩修。

新观察耗时 13 named/custom 为 8.416711/7.624971μs，14 为 43.333333/15.000000μs。原 per-record 导出 timer 在 getter 前填入，不包含新观察；整个 finish 用时包含它。完整 16 字段 schema 与 provider-start→observation→release 时序由独立 gate 核验。

## 像素与 raw 控制

[四份控制](same-binary-13-14/controls/)分别是旧 float→新 off（13、14）及新 off→on（13、14）。每份 body/flight/oracle 两 phase 共 12 ROI 的 raw RGB 与 ICC intent0（perceptual）归一 sRGB 均 exact，同 host 嵌入 ICC 相同。只覆盖这些图像 ROI，不扩写成整个窗口 chrome exact；独立 native reviewer 检查其输入 hash，没有重复像素算法。

| 原 raw | 长度（B） | SHA256 |
| --- | ---: | --- |
| 13 named | 1,843,200 | `edc1c9380bbf86e35c9830359428b715953cccd0f5952b10ade269923a6a2469` |
| 13 custom | 1,843,200 | `314b9001c1c47eea9f39a23fd6c697d1bcb66cfcda83dbc01153149c2d36e67c` |
| 14 named/custom 各 | 460,800 | `807393b1503ad04a08e2dc09cac516e9d2abfcd86c9db3b15ec2761230201962` |

四份均逐字复现[旧 float cohort](../macOS14-hero-float-40091326190/README.md)同 host/key；因此先前[独立行序/平坦区语义结果](../macOS14-hero-float-semantics-20261025/README.md)仍适用于这些 raw，不需要再运行数值算法。named 十 flat 原 half bits 相同并不能证明整图或最终显示相同。

## 复核、清理与下一检查点

[native-analysis](native-analysis/README.md)独立复核 package/raw/metadata/全部 gate。root 从 workflow 提取的 gate 只将报告路径、mode、expected major 改为 argv；保存文件还多一个末尾 LF。独立 checker 首次在此字节比较停止、尚未运行 gate，之后显式重建该 LF 并通过四组；不是 runtime 失败，也未修改断言或报告。原始与适配 hash 保留于 [adaptation](tools/hero-cgsemantics-validation-adaptation.json)。报告中五 buffer 相等只做记录一致性核对，不声称独立重采。

本轮原 exe/tar 合计 844,797B 已清理；12 个 work 路径逐字验证后成为本归档 symlink，清理重复逻辑文件 8,742,890B。归档内部另将 22 个相同文件别名硬链接到同内容代表，名义重复量 2,765,989B，所有文件名保留且没有链接至 work/其它归档。见[完整收据](cleanup.json)。这些不是 APFS 实际回收或磁盘净变化数字。原图、raw、源、日志及审核仍保留；历史 package manifest 中有意清理的 binary/tar 由收据解释，当前现存清单为 `SHA256SUMS.final`。

归档及旧 work symlink 只读；复跑需复制必要脚本到 fresh scratch，输出另设 fresh 目录。`check-package.py` 需要已清理原 exe/tar，不能把当前缺失当损坏或用重编替换原身份。无新工具链、模拟器或本机编译缓存。

三份历史 package `SHA256SUMS` 均以 `same-binary-13-14/probe` 为成员基准；其它子 manifest 以各自目录为基准，均不包含自身。现存成员全部匹配，历史 package 各自只缺收据列明的原 exe；完整重放还需恢复同 SHA 的原 tar。native input 清单的 70 项中 68 项当前可核验，另两项为已清理 exe/tar 的清理前身份。

[下一单一计划](next-direct-plan/README.md)已冻结但未实施：本机13在相同 retention/原 snapshot 下比较原 NSImage.draw 与实际 CGImage 的 scoped direct draw；先过 default 复现、方向/非空/完整 extent 等门槛，再完整比较 `D13−D14`，不以 Hero13=body13 为目标，也不预测修复。其余颜色/布局/交互/动画验收项保持未通过；goal active，不进入 macOS11/Swift5.3/Objective-C/iOS。
