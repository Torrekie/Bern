# 同binary13/14：root与真实existing-overlay静态端点

[CI40097558084](https://github.com/Torrekie/Bern/actions/runs/40097558084)的build/measure均成功（原状态另存ci-jobs.json）。源码提交 `c34866855288b215f41cb9f058748225857f1b62`，harness `313c9cdfc1df5c36e1e2dffa45c4491c775c8e39`。SDK26.2/Swift6.2.4仅构建一次arm64/min13，原签名binary `cb4bd5d007048cfc0bcbda4ecc66df4ffd79053df27edbb7590563ba5022f8d1`在14与13分别运行root/overlay；13不重签、14不重编。归档hash、26包成员/source map、架构/min13/SDK/严格签名在13执行前已独立校验。

独立的hero-route-probe源目录避免破坏此前float/backing工作流。产品Image/Hero base与旧newSDK夹具逐字相同，不带本机SDK14 unused-clock/gainmap编译保护。只是手动静态Flight的parent切换到已存在的实际manager overlay，保持相同opaque/up图、snapshot、NSImage、Flight.draw和屏幕ROI。公开坐标convert实现root y244→overlay y272→root y244；采集不硬编码该偏移。保留原所有root检查，并直接检查两retained flight子树，避免overlay sibling逃过noMTK门槛。

父任务实算：13旧backing-off→新root、13root→overlay、14旧backing-off→新root、14root→overlay，四组各12ROI原始RGB及ICC→sRGB均exact，四控制JSON与八PNG/ICC/报告在same-binary-13-14。CI不把图像相等当采集success门槛；[独立离线摘要](analysis/README.md)校验既有控制记录、53输入hash及四份原报告，不声称又重算像素。该parent切换没有改善已存主差，未重算跨宿主残差。

| 宿主 | root / overlay窗口秒 | 原前台保持 | 坐标往返最大误差 |
| --- | --- | --- | --- |
| 13.7.8 | 1.852830 / 1.818322 | 1390 | 0pt |
| 14.8.9 | 2.166785 / 1.928855 | 335 | 0pt |

四进程normal false、缓存深比较不变、非key/非active、own PID/window、两phase五stable、noMTK/managerFlight0/timernil及7.9秒窗口门槛通过。float与backing观察始终off：原snapshot provider export、强留峰值/raw bytes为0，backing root/overlay为null。每次mount/postPNG的两records与对应ROI、parent/window/320×180/子树一致；真实bounds由Swift内部guard核查，JSON没有独立bounds字段。

两系统原日志均包含prepareOverlay添加NSThemeFrame subview的warning，完整保留，不把它称作13特有或新根因。这里仍是手动静态同图p0/p1：没有调用真正enter/leave/finish，不能替代实际计时、插值、visibility恢复、retarget或完整应用验收；本轮没有读取图层hint，也没有格式setter。

随后[本机existing-layer RGBA8探针](../macOS13-hdr-candidate/native-pq-hero-existing-rgba8-13/README.md)在早期mount时因layer=nil停止，setter0、PNG0，不能算视觉阴性。下一门槛转为[一次真实coordinator条件替换](next-coordinator-plan/README.md)及[中途原窗口图](next-coordinator-plan/Supplement.md)。这是未执行方案，不能当动画已通过。

原binary、tar、已用完cache与逐字归档work副本已清理，见[收据](../macOS13-hdr-candidate/hero-route-format-cleanup-20261024.json)。原CI包清单保留已删binary/tar的hash，最终现存文件以SHA256SUMS.final为准；不要向冻结归档写模块cache。ci-preparation为执行前草稿，actual execution以原receipts/构建元数据和ci-jobs为据。
