# 本机13：同一静态Flight挂载root与真实existing overlay

单个进程缓存 `BERN_HERO_STATIC_ROUTE=root|overlay`、默认root；两组均强制backing observation和float capture off。仅使用已存在的manager overlay和公开坐标转换，原p.image/from/to/corner、真实Flight.draw、固定p0/p1、source anchors、stable5、缓存/normal/front/window时限均保留。没有调用enter/leave/finish、改变manager映射/clock/visibility/ID/绑定、设置layer或重画取图。

SDK14.2 / Swift5.9.2 / arm64 target13，沿用已明示的unused-clock/gainmap诊断编译保护；严格签名binary `8fb1b7f57b60de0948866bb950be07696b15196d9f89e2fda994fac1a22d3fac`。只复用本轮已有module cache，未建立第二份；完成后两个local cache引用及binary均清理。`fixture/`保留实际assembled源码、编译fingerprint/log、四原PNG/ICC、receipt和控制JSON；`source-preparation/`与`route-plan/`为运行前历史准备记录。

原backing-off→新route-root、新root→overlay两组各12ROI原始RGB及ICC→sRGB均exact。原desired root位置y244通过overlay.convert变成overlay y272，再转换回y244，两个flight在mount及postPNG时的最大误差都为0pt。每个sample直接检查retained两flight的真实parent/window/320×180/回转位置及其整个子树noMTK，避免旧root-descendants漏查overlay siblings。屏幕ROI未手动翻y或扣标题栏。

root/overlay窗口1.681115/1.613716秒，前台1390保持，normal三项false、原缓存不变、noMTK/noManagerFlight/noTimer/非key/非active/五stable全部通过。overlay分支在原orderOut之后只移除夹具自建的两view，再执行原contentnil/close；未用manager.finish处理未注册view。

该容器切换在本机没有改变所测静态输出，主色差未改善；不表示另一宿主也相同，也不等于真实飞行、插值、retarget、隐藏恢复、High/HLG/alpha/方向或整应用通过。下一步先对14的真实overlay静态路径建立同binary控制，再决定单一existing-layer格式请求是否值得测试；不预设AutomaticAppKit/RGBA8就是实际存储或根因。

冻结的历史build.sh指向原自有cache路径；如需重建，先恢复为新的work副本并指定自有cache，不在本归档运行。原prebuild manifest和build fingerprint保持，已清理binary另有[收据](../hero-backing-route-cleanup-20261024.json)，现存完整文件见 `SHA256SUMS.final`。
