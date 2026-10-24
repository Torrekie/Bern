# 本机13：PNG之后的容器与图层标量观察

Xcode15.2 / Swift5.9.2 / SDK14.2 / arm64 target13，仅隔离夹具。实际 snapshot、NSImage、Flight.draw 不变；旧gainmap编译条件和未使用clock保护继续保留。binary `b57b0d9303ba39ff60740c52a84cc34ab212694dff99692d69bb636b6c7c57a4` 已严格验签，完成后清理。源码、原编译记录、两个进程和四PNG、控制报告均在 `fixture/`。

`BERN_HERO_LAYER_OBSERVE=off|on`进程缓存、默认off；本轮强制float capture off。唯一新增读取在全部PNG与原cache/normal/front最终检查之后、原teardown之前。off不访问新增view/layer/ancestor属性。on读取两root-mounted真实FlightView、root和已prepare的真实manager overlay及祖先的公开标量；不读contents/presentation/provider、不set/强制绘制/创建layer，也不留图像或图层引用。每次node调用读取一次layer，祖先可能重复读取；不保证getter无内部工作。

原float-off→新backing-off、新off→on各两phase×六ROI在原始RGB及ICC→sRGB均exact。窗口off/on 1.699726/1.694244秒，前台9292保持；首尾三项normal false、原缓存不变、无MTKView/manager flight/timer、五stable与时限均通过。开启后观察到flight/root已有 `_NSViewBackingLayer`，wantsLayer=false、contentsFormat=`AutomaticAppKit`；已存在overlay和NSThemeFrame的format=`RGBA8`。各层scale2、delegate为对应view；没有祖先flatten开关。

这些是保存PNG后的属性，不能证明绘制时实际像素存储、前PNG持久状态、色差原因或真实coordinated flight通过。新SDK同binary13/14证据见[完整队列](../../macOS14-hero-backing-40095339192/README.md)。原prebuild `fixture/SHA256SUMS`和build fingerprint保持；最终现存文件见外层 `SHA256SUMS.final`。不要在冻结归档中直接重建；恢复自有work副本并使用独立cache。
