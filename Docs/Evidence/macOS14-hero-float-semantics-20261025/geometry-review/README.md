# PRIVATE：retained raw 几何独立复核

**PASS：四个实际raw在固定top-down/bottom-up两候选中均唯一top-down。** 独立`verify.py`只使用stdlib的Fraction坐标与`struct.iter_unpack("<4H")`完整四word tuple矩阵；没有import/执行root pipeline，没有half数值/RGB颜色解释、方向拟合、图像构造或raw复制。一次执行exit0，具体每patch/每band/每bin计数、坐标、真假及原hash保留于`review.json`。

核对的root结果为`work/hero-snapshot-float-geometry-compact/result/geometry.json`：57139 bytes，SHA256=`215ccb6ecc2ab77e6039cbc07c08f09f83358fd84747c9228f6aa90881a1ddf2`。四raw字节数/完整SHA均与各自原on报告和root结果输入库存一致。

|实际文件（归档same-binary-13-14下）|原SHA256|top-down|bottom-up|
|---|---|---|---|
|runtime13/on/snapshot-named.bin|`edc1c9380bbf86e35c9830359428b715953cccd0f5952b10ade269923a6a2469`|true|false|
|runtime13/on/snapshot-custom.bin|`314b9001c1c47eea9f39a23fd6c697d1bcb66cfcda83dbc01153149c2d36e67c`|true|false|
|runtime14/on/snapshot-named.bin|`807393b1503ad04a08e2dc09cac516e9d2abfcd86c9db3b15ec2761230201962`|true|false|
|runtime14/on/snapshot-custom.bin|`807393b1503ad04a08e2dc09cac516e9d2abfcd86c9db3b15ec2761230201962`|true|false|

13每文件1843200 bytes/640×360/stride5120；14每文件460800 bytes/320×180/stride2560，均tight8-byte pixels。两方向均按冻结atlas精确整数坐标计算，无resize/平移/阈值调整：

- 四个top-down：十个flat内区的完整tuple distinct count全部为1；三固定band的ramp marker依次**false/false/true**，所以通过。
- 13 named bottom-up：前五flat counts为**112,112,112,112,101**，后五全部1；custom为**112,112,112,112,108**，后五全部1。
- 14两个bottom-up：前五均为**56,56,56,56,56**，后五全部1。四个reverse三band marker均为**true/false/false**，所以失败。

marker严格保留原条件：固定band内所有行完整bits相同，且五个预声明x-bin的首行各至少两种完整pixel tuple；必须只有第三band具有marker。独立结果逐项匹配root的十flat、三band、bin counts、whole-band counts、row-count/row-equality及坐标，不通过颜色值或13/14接近程度选方向。tuple解释对任何固定通道置换保持相同相等关系；lane语义由前一独立lane合同审查另行支持。

compact与png版`structure.py`完整源码只存在一次`json.dumps`由indent转为compact separators的替换；保留sort_keys、allow_nan=False、全部字段和128KiB guard。两版policy、atlas spec、冻结analyzer及parser API notes逐字相同，policy SHA=`e89de719d300dc83faa46e186abd71ae4b5d19315351df87340133e3f64d48b7`。源码SHA：png版`9d98d461274444e284e3890be49ab35d6e2e19b1e74e6956ae08a75c01658e7f`；compact版`46e7eb7d0c096eed43d7f50924a955597bee96d2c315f1b73add335238c6b112`。此前parser失败和pretty体积失败不作为成功证据，也未被覆盖或删除。

本次范围是上述四文件、固定两方向和主要raw结构门槛；没有重跑源PNG decoder、完整native/receipt门槛或root整个pipeline。原source-atlas解码/身份前提由root保存的独立流程承担，本review未重新证明PNG parser。该结果支持当前retained raw的行序证据，不证明所有CGImage恒top-down、具体颜色因果、显示等效或产品修复。未重编、UI、CI、新采样、half语义提取或大raw复制；仅本目录的verify.py、review.json、README及SHA256SUMS，完成后冻结只读。
