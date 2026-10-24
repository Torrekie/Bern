# Named PQ十个平坦快照内区的RGBA16F位模式两端相同

这次纯离线分析复用CI40091326190同一签名binary在实际macOS13/14导出的四份原snapshot provider数据，没有新构建、UI、采集、CI或产品修改。没有复制原raw/PNG。先建立格式lane合同与唯一行序，再运行冻结analyzer的known-direction入口；结果不能当作整个snapshot、显示链或macOS13阶段等效。

Apple公开SDK的vImage_CGImageFormat合同直接对应实际CGImage getters：16bpc/64bpp、float、premultiplied-last、16Little、RGB3/packed。lane0…3固定为R/G/B/A，每个为LE binary16；不是从alpha恒1或颜色接近推断。独立lane审查保留header精确路径/行数/hash和公开API引用。原采集保留的是实际renderer.cgImage返回对象，provider导出无转换；不是NSImage再缓存或替代图。

在读取snapshot raw前，预先锁定了十个flat内区、三条固定横带和每带五个固定tile-x内区。结构gate只比较完整8-byte tuple：flat各有且只有1个tuple，ramp所有行相同而每个tile-x内区均变化；三带只有底带可作ramp。仅评估top-down/bottom-up，禁止颜色/跨host接近打分、平移/比例/裁剪搜索或阈值放宽。两源PNG的无色管RGBA16BE解码active SHA均为29339554132137a1db6e48a560ae53d1727e13d59b12656d97824acea02b221f，与既有验证一致，top-down唯一通过。

四份raw均唯一top-down：10flat distinct counts都1，三个ramp marker为false/false/true；bottom-up首5内区不恒定，markers为true/false/false。独立Fraction坐标与struct tuple实现逐项复核两方向坐标/counts/row-equality/bin-counts/marker及原hash，不执行root pipeline。成功结构JSON57,139B，SHA215ccb6ecc2ab77e6039cbc07c08f09f83358fd84747c9228f6aa90881a1ddf2。13每flat11648pixels，14每flat2912pixels；只是独立区域统计，不resize或逐像素注册。

独立几何/lane审查被冻结并由semantic-binding绑定后，原analyze_float.py（SHAb616c42b192c13b7fee3d903d90e9553f389c6ac4b6f7da8cc96996877fcca2a）才对两host运行known top-down。它保留每region的bits/min/mean/max、finite/NaN/Inf、负值/>1/alpha计数，没有ICC/transfer处理、clamp/unpremultiply或nits换算。新增compare-patches只比较已经证明恒定的对应命名内区；ramp仅保留各native-resolution aggregate，没有配对跨host列。

| 输入 | 十flat的RGBA位模式相同数 | RGB最大绝对数值差 | 30个RGB分量绝对差平均 |
| --- | ---: | ---: | ---: |
| named PQ | 10/10 | 0 | 0 |
| custom ICC/cICP | 5/10 | 0.001953125 | 0.000244140625 |

named每个flat原half bits完全相同，包括主差涉及的cool812。其原存储R/G/B分别为0.65966796875、1.8779296875、2.53515625，alpha=1；这些是premultiplied extended-sRGB存储值，不是显示编码RGB或nit。custom改变的只有white812/red812/green812/blue812/pastel812，其余五块相同；完整20patch的RGBA bits、数值与13−14差在constant-patch-comparison.json。独立numeric reviewer直接用struct<4H/<4e读取四个raw，验证40flat整区恒定/alpha1、20patch/80delta、4whole与44region统计及完整histogram hashes。

**named十个平坦内区的主显示差，不能由这些内区snapshot原数值不同来解释。** 原cohort的WindowServer颜色差仍存在，且既有off/on每12ROI控制exact；本轮没有重新采集窗口或重算其PNG。这个结果不等于整个CGImage绘制语义相同：未采集的decode/renderingIntent等属性、1×/2×边缘/采样、原NSImage及graphics context/显示环境仍未分离。不能指定唯一OS、ImageRenderer、AppKit、HDR余量或其它根因，也不把custom的小数值差换算成可见差或修复。整图/灰阶的不同采样和原whole分布差保持原结论。

两次先前程序失败完整保留：首轮source parser只支持filter0，在实际source使用Sub/Up时停止，未读取snapshot raw；随后仅依[W3C PNG过滤规范](https://www.w3.org/TR/PNG-Filters.html)补标准0…4无损byte解码，几何条件不变。第二轮在最终pretty JSON的128KiB限额处失败，未写结果；第三轮仅压缩JSON空白，保留全部字段/相同上限，实际57,139B并exit0。compact差异由独立review确认。失败不是几何反证，更不是颜色通过；没有读取失败进程的未保存数值来选方向。

下一步需先补齐实际CGImage的剩余绘制语义或相应最小显示边界，见归档next-display-plan。没有把未知CGImage字段或当前source计划当作完成的证据。完整颜色/UI、动画/中断/其它输入、High/HLG/物理HDR及其它macOS13 gate仍未通过，goal active，不进入macOS11/Swift5.3/Objective-C/iOS。
