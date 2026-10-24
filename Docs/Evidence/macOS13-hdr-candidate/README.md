# macOS13 HDR：公开算法候选证据（未产品化）

这组证据补充已提交的系统SDR/路由修复；**没有把Annex5候选接入Bern产品**，不代表整个High、彩色、元数据或物理HDR已经等同macOS14。

- [数值推导](numeric/REPORT.md)：原始PQ资源和14真实窗口的完整中性ramp，无相位/曲线拟合，BT.2408-6 Annex5的0/1000/0/203预设在188列×3通道MAE约0.098/255。
- [13独立窗口原型](prototype/README.md)：CPU raw-PQ→nit→Annex5→linear BT2020相对UI白输出；真实Hd1/2/1/2、GPU读回与系统通知，Hd1对14实图MAE0.104109/255、max0.456522。
- [研究说明](../../Implementation/macOS13-HDR-Tone-Mapping.md)：默认203、ICC lumi、峰值和算法身份的证据边界。
- [产品化前的策略与待验证项](production-strategy.md)：先确认色彩/元数据规则；生命周期、通知去重、后台latest-only和有界缓存可独立准备。
- [SHA清单及范围](reference.json)：原始输入、参考图片、原型源码与全部归档文件。

1000是该样本受14ramp支持的候选预设，不是PNG读取的母版峰值；203来自适用ISO默认，不来自ICC lumi100。Hd2输出纹理为1/1.996094 linear EDR，SDR截图却接近255/255，两者单位不可混用。没有14同headroomHigh或物理亮度对照，不能升级为High等同通过。

归档保留原始PNG/JSON、源代码、分析脚本与环境；不保留可执行文件或module cache。原work目录为指向此处的symlink，复跑请按子目录README写入独立scratch，避免覆盖证据。

## 13公开Core Image接口的边界

已验证的 `CIImageOption.toneMapHDRtoSDR` 是Bool；SDK14.2的`CIImage.h:101–110`仅承诺YES映射到working SDR、NO保留未裁线性范围，没有目标headroom参数。公开[CIExposureAdjust](https://developer.apple.com/library/archive/documentation/GraphicsImaging/Reference/CoreImageFilterReference/#//apple_ref/doc/filter/ci/CIExposureAdjust)只乘`2^EV`，没有把SDR mapper转为可调余量mapper的契约。

即便假设已知Annex5的SDR函数`T1`，理想203/812nit在Hd2时，后乘2得到`1.566915/1.998871`，先除2再映射并乘2得到`0.992081/1.911780`，均不等于直接目标406nit的`1/1.996624`。这是已有候选函数的数学反例，**不是额外执行的系统CI组合实验**；不能将前后曝光包装成已等同的High。

另有[13原生彩色probe](color-probe13/validation.json)，仅记录13的已知输入/输出和稳定截图，不是Annex5产品实现或14彩色等同证明；对应14采集尚待完成。

## 当前产品与原生组件的彩色补证

- [e06 Standard实际helper](standard-color-e06/validation.json)：相同atlas的自定义ICC经cICP规范化后，与命名PQ在产品路径中输出完全相同；对13原生SwiftUI的10色块通道均值MAE约1.087/255，最大约4.759/255。灰阶接近不能替代彩色验收。
- [系统NSImageView候选](native-sdr-components13/validation.json)：正确设置图像逻辑尺寸后，真实Hd1下与13原生SwiftUI整幅图逐像素相同；CGContext8位sRGB路径仍有约5级色块均值差。这是可复用组件候选，未修改产品。
- [余量切换的有限尝试](native-sdr-headroom13/validation.json)：7.5秒采集上限内仅取得初始Hd1两张相同buffer，其它阶段未完成，不推断失败原因或动态Standard恒定性。

以上补证均为本机13独立窗口，非激活状态，不是14彩色采集或一般High等同证明。原exe/cache已清。

- [同一Hero snapshot的系统NSImageView显示对照](native-pq-hero-snapshot-view13/README.md)：先复现12ROI默认控制，候选只改变named Hero且max1/255，其余10ROI exact；完整14残差有改善亦有恶化，主要色差未解决，未换入产品。原PNG/ICC、同对象身份/清理、完整色块/灰阶与构建证据保留，binary/cache已清。
