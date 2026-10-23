# 产品化建议（仅方案，未接入产品）

当前CPU证明锁定单张中性图片，不能把图片SHA或近中性检查带入通用功能分派。SHA可用于内容版本/缓存身份；渲染路径应依据真实编码、有效元数据及动态范围意图。

## 色彩规则需要先取得14证据

| 问题 | 已知边界 / 下一证据 |
|---|---|
| 颜色应用空间 | 中性轴不能区分逐RGB、maxRGB保色相、luminance/ICtCp等。新14彩色probe的非等通道、在输出色域内的warm/cool块，以及饱和BT2020块，应与完整系统色彩管理输出比较，再选择实现；不能只将三个通道各自套当前曲线 |
| ICC与CICP | 新probe比较同码值named-PQ与ffb自定义ICC，可判断当前条件的等价性；真实产品还须验证保存PNG后ImageIO重解码。新probe直接展示in-memory CGImage，不自动证明文件加载链路或所有ICC冲突/TRC优先级 |
| 内容白与峰值 | 203只作为适用ISO无有效覆盖时的内容白；不能用ICC lumi100替代。1000只是此无峰值元数据样本的候选，不能硬编码成所有来源的已知峰值，也不能改用实测asset最大812（已与14 ramp不符）。有效diffuse-white、CLLI/MDCV/CCV的读取、优先级和缺省须用合法元数据变体逐一验证 |
| 黑位/越域/不压缩 | 现有ramp无法区分绝对黑位，且全部低于LW1000。负值、源超过母版峰值、目标高于内容峰值等边界不能从这张图推断Apple规则 |
| HLG、alpha、EXIF | 新彩色probe不覆盖这些。HLG的display/scene与OOTF不能套PQ EOTF；alpha的非预乘/预乘及线性合成顺序、旋转和其它ImageIO位图格式须分别验证/用系统格式归一化，不从当前RGBA16不透明图猜 |
| 实际Hd>1 | 本机13已证明linear输出单位和动态更新；新14虚拟SDRprobe仍不能给出同Hd2的native14目标。需同headroom14参考，或明确把BT.2408候选作为有范围的算法交付，不能称High已等同 |

这些前提确认后，通用入口才可按完整CICP/CGColorSpace、位图格式和元数据选择PQ/HLG处理；SDR继续原SwiftUI路线。不要把错误/不支持格式变成fatalError或宣称成功，也不应悄悄把High全部强制Standard。

## 可不依赖最终色彩算法而先改进的所有权和调度

- 解码结果与解析出的元数据不可变、按源revision共享。CICP只解析一次；渲染导数独立缓存，key包含源版本/ICC/意图、mapper及参数版本、方向、尺寸/backing scale和输出空间。不要只按URL或图像张数缓存。
- **Standard缓存独立于当前显示headroom**：这个实验在1→2→1→2时Standard原始RGBA完全不变。当前产品的NSWindow screen通知不应仅凭通知名就丢弃全部SDR结果；区分真实screen/profile/scale变化与同一屏幕的headroom更新。
- 用有界串行后台worker拥有CPU转换和工作buffer；每consumer最多一个在途作业和一个可覆盖的latest请求。去重有效显示参数，合并重复NSApp/NSWindow通知；不在MainActor draw里执行18–88ms的CPU块。
- 完成结果必须核对源revision、intent、screen/输出参数与generation；过时结果不能挂回新图片或已关闭视图。主线程只采屏幕状态、申请EDR、更新图层并提交已完成结果；不要用当前值1取消潜在HDR请求。
- 在目标不断变化时保留最后有效frame，但不能假定高于当前headroom的旧结果仍安全。向下变化需有明确的显示/裁剪策略，且与14时序另行比较；不要未经误差界证明就任意量化headroom或人为延迟收敛。
- `stop/dismantle`失效generation、清未启动job/observer/derivative cache、releaseDrawables。工作buffer必须活到GPU command完成，不能因取消CPU任务而提前复用；所有临时拷贝有明确边界/释放点。
- 缓存按bytes限额并响应内存压力，先避免同源多view重复转换。640×360一张Float32RGBA约3.52MiB；4K同格式一张约126.56MiB，另有raw、LUT、Data和GPU在途所有权。当前60.1MB只是进程resident采样，不是可据以给任意分辨率承诺的内存上限。

这些是可独立准备的资源生命周期切片；并不要求现在固化逐通道曲线、metadata默认或shader。CPU原型首几次约7ms、动态median18.64ms/max88.08ms，足以说明它不应原样在主线程产品化。先确认颜色/参数，再选择后台CPU+缓存或GPU/LUT实现；优化不能先替尚未确定的语义作决定。

## 公开Core Image的既有SDR路线

本机SDK14.2 `CIImage.h:101–110`的toneMapHDRtoSDR为Bool（macOS11+），没有targetHeadroom。`CIExposureAdjust`的公开定义只是工作空间RGB乘2^EV，并没有组合后等同High的保证。[Apple filter reference](https://developer.apple.com/library/archive/documentation/GraphicsImaging/Reference/CoreImageFilterReference/#//apple_ref/doc/filter/ci/CIExposureAdjust)

在已有Annex5标量候选中，Hd2的直接目标映射与简单前后曝光不相同，反例见[候选说明](README.md)。因此保留已验证Standard系统转换；不能据这些公开接口宣称已获得14的通用可变余量mapper。没有开展新CI组合或UI实验，也不推断未公开filter不存在。
