# 原始PNG的限定像素检查

输入为40103369574同一个原签名binary在13/14的三张原始WindowServer PNG及各report。原图和嵌入ICC保持，Pillow按各ICC、perceptual intent0转sRGB。只在同一宿主比较before source与settled destination的同尺寸、完全opaque ROI；没有跨宿主拟合、重采样或配准。

13的640×360端点ROI在sRGB中MAE0.2941059/255、max5；14的320×180端点ROI为MAE0.2711690、max2，均非逐像素相同。两端目的图内容可见；root已目检两宿主原始before/settled图。它们支持本例终点恢复，不通过颜色完全相同、alpha/方向变体或全动画门槛。

root目检原始mid：13已有位移，14仍位于source位置。`mid-opaque-bounds.py/json`仅取固定root四边12pt内、alpha全255区域的sRGB非白像素bounds，排除圆角/透明窗口边缘：13为root点[80.5,66,400.5,246]，14为[16,24,336,204]。它不是完整image/flight边界配准，白色图块可能不计入；原图也未修改。

同次逻辑trigger分别p0.2872209362/root origin(112.5062,87.1886)与p0.6920757961/(248.5375,176.2567)，前后native bracket未变。截图可见位置与逻辑状态没有建立同步，因此本批不通过中间帧或动画视觉验收；不能据此唯一归因RunLoop、WindowServer、CA或系统版本。13/14采样时刻和进度不同，未作mid跨宿主相等比较。

`analyze.py/summary.json`为先完成的v1，不回写。其whole-root非白bounds包含底部圆角/透明角：不作为flight位置结论。保留该已知限制，后续固定12pt inset结果只解决这个统计污染，不改变任何原始采样。v1逻辑flight的8pt inset非白比例是内容描述，不是可见性或运动pass。

两个脚本只读取已保留PNG/report并写小JSON；无编译、UI、CI、产品或截图修改。若重算，使用新的输出目录；脚本拒绝覆盖既有summary。
