# Generic SplitButton selected-label color：离线规格（冻结）

只有原参考规格绑定；未读取任何candidate、未填假source/binary SHA、未运行App/helper/编译/UI/CI。未来结果是独立 label-color 验收，绝不调用/修改旧Row-observer PixelGate或翻转失败cohort。

原13来自已归档macOS13-frame-control-e48-20261025，report60d716…5ac480，PNG ece61b2d…aff37f3，ICC e2473ef4…ef9b64d4，1840×1336/2×。原14为40158031681真实成功control/a，reportcc3ce7…be59d1，PNG ef6951d5…eccfb6b，ICC3d40c076…eb5f55，920×668/1×。全SHA/路径在spec.json，actualPNG/embeddedICC/原输入未变均已核。

| 固定半开crop（相对outer的point） | `[x0,y0,x1,y1)` |
|---|---|
| 完整Frame | `[211,52,920,668)` |
| Caption body含menu/bezel和margin | `[250,532,360,555)` |
| 可变label：icon+Caption，不含menu/bezel | `[255,535,329,551)` |
| glyph-free背景条 | `[273,535,276,551)` |

这些都在candidate出现前取自原图，绝不移动/扩大/拟合。13乘2成整数pixel，14原1×。13同host要求Frame减label矩形的原RGBA **exact零容差**、Frame alpha和背景条原RGBA exact，保留body/label及整窗全部差异；整窗单列不混为全UI gate。14candidate对白要求 **完整Frame原RGBA+embeddedICC exact**，整窗差异另报。

一次reference绑定：分别按各自embedded RGB ICC→固定保存sRGB ICC（74507e…d90b84）、Pillow12.3.0/LCMS2.19、intent0/flags0/无BPC，alpha不变。foreground在native scale，从原label相对该row背景条RGB median的L∞差≥32且alpha255的像素取；阈值32预先固定，空mask/ICC异常就停，不换阈值。原13 mask957像素、原14 mask333；坐标runs和maskSHA已存reference-binding.json。未来只复用原13 mask，不能从candidate重新选。

原14固定rendered foreground目标均值RGB=`[158.570571,197.579580,239.447447]`；原13 mask均值`[84.009404,147.430512,226.273772]`，toward14平均绝对误差`[74.561166,50.149068,13.173675]`。包含AA的rendered pixels不是NSColor/系统style的内在值，两个native scale的mask/AA分布也不相同。

未来颜色判据：对原13 mask每一固定像素，分别统计R/G/B对同一14目标的绝对误差；各通道mean均不退步，且至少一项严格改善（epsilon0）。全部通道mean/max/signed delta、每像素改善/退步/相同数都保留，禁止挑通道、最佳crop或只报总均值。comparison-rules.py已固定纯函数，未执行candidate比较。

完整Frame的跨host外观诊断继续用同一固定sRGB ICC：13在转换后做整数2×2 Pillow RGBA BOX到709×616，14不缩放；encoded-sRGB8 premultiplied RGBa，不是linear-light。完整RGBA/all4channels及所有正负误差保留，不设跨scale rawexact gate。此次明确load序列化ICC，processed hash独立记录，不冒称上一版in-memory sRGB object的hash。ICC不匹配/不可正确转换即停止颜色阶段，不换profile/intent/filter。

Native/context/time前置：同一base e48、实际单一generic色改source证明与真实新binary/manifest由root后供；13/14候选必须同一实际产品binary（私有CFID签名差异走sections/归一证明）。每host clip/volume对各自原框 exact：13 clip(251,167,629,354)/volume(620.5,533,20,20)，14 clip同/volume(619,536,22,15)。原目标关系是CLI label+role/action+shared owned AXGroup；main_window.find只是继承ID，不冒充Caption/Size Layout或Cocoa类测量。

保留920×668、各自2×/1×和原ICC、en/normal三false、Light/captiontrue/closed、真实source-bound Ready→Paused0和媒体SHA、原ownPID/awake/stable4≥5samples、75秒内部/95秒outer等待及原成功cleanup/cursor收据。只核每run内有限且有序capture/sample时间，不拿跨run uptime相等当门槛；不放宽原链、不retry、不fallback。候选报告ledger=false、无arm/packet；此色改不产生Row记录。

当前交付spec/reference binder/纯比较函数与计划，尚无candidate IO adapter或acceptance结果。root提供真实candidate路径及source/binary/report/PNG/cleanup bindings并通知后，才能按本规格接入；不得看到candidate后改ROI/threshold/判据。源真实性、原图目检、布局/native语义仍是独立门槛，不因颜色数字改善自动采用。
