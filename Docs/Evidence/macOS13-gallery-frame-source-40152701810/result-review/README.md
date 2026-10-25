# Actual Gallery source-export result review

结论：PASS，仅限真实源生成证据；没有产品二进制、UI或Frame布局验收。
本审查未执行helper、CI/API、构建、UI或Git写操作；输入及旧审查目录未改。

10个产物文件中，SHA256SUMS覆盖其余9个，实际字节全部匹配。
before631项与固定e48 Git blob逐项size/SHA256一致；after630项保持原字节，
仅CLI为精确env gated early-return hook。原63af68fa…fa64→0510fef5…ef3636，
保存的unified diff逐字匹配独立重构，原needle唯一且位于917行。

source=e48fff46…69af7d，harness=84f1f07b…9f33a，环境与下载收据相符。
从实际harness对象读取的helper仍为冻结5b4a2545…a2b017；workflow真实名字是
`.github/workflows/macos13-gallery-source.yml`，实际运行source job为macOS15。
环境记录Xcode26.3、SDK26.2、Rust1.99。完整2360B日志rc0、marker恰好1，
检查Gallery6components/2windows并新写20files/20changed。

实际BernGenerated.swift为81110B / f72cb1c6…ef1653，与cache中旧Showcase
95129B / 1d1da316…c52083不同。实际Frame切片9021B / 9e67b689…6d4a67，
为原源1248–1353行、bytes[65675,74696)，独立逐字重切完全相同。
真实main Scene/Frame route及Caption、caption_size、caption_sizes tokens存在；
本审查没有预分析控件宽度或推断布局原因。

独立读取的build.json与after内metadata一致：Gallery.app、gallery协议、arm64、
swiftui-modern-macos、release、minimum_macos13.0。exact hook、日志和收据均支持
在产品target.plan前返回；报告Gallery executable目录、dSYM、bin均不存在。
min13是源构建元数据，不冒充实际产品Mach-O或原生行为验证。

外ZIP已在本审查前删除。download.json中的API digest和先前实算digest一致，
与run/harness/10成员收据相符；本审查未重新计算已删除ZIP或调用API。
完整哈希与有限结论见review.json；首轮review仅在workflow文件名猜测处失败，
该reviewer错误收据单独保留，未作为产物失败或放宽任何源验证门槛。
