import AppKit
import MetalKit
import CoreImage
import ImageIO
import UniformTypeIdentifiers

@main @MainActor struct ProofMain {
static func main() {
let resource=URL(fileURLWithPath:CommandLine.arguments[1])
let output=URL(fileURLWithPath:CommandLine.arguments[2],isDirectory:true)
let decodedAt = CFAbsoluteTimeGetCurrent()
let fixture=PQFixture(resource)
let decodeMilliseconds = (CFAbsoluteTimeGetCurrent() - decodedAt) * 1000
let vectorHeadrooms: [Double] = [1,1.5,2,3,4,5]
let vectors=vectorHeadrooms.map { hd in ["headroom":hd,"left":annex5EDR(pqSignal(203),headroom:hd),"right":annex5EDR(pqSignal(812),headroom:hd)] }
for hd in [1.0,2.0,1.0,2.0] {autoreleasepool {_ = fixture.image(headroom:hd)}}
let device=MTLCreateSystemDefaultDevice()!
let app=NSApplication.shared
let originalFront=NSWorkspace.shared.frontmostApplication
app.setActivationPolicy(.regular)
let window=NSWindow(contentRect:NSRect(x:160,y:160,width:480,height:180),styleMask:[.titled,.closable],backing:.buffered,defer:false)
window.title="Bern Annex5 linear EDR proof 8C42"
window.isReleasedWhenClosed=false
let root=ProofRoot(frame:NSRect(x:0,y:0,width:480,height:180))
window.contentView=root
let standard=ToneView(fixture:fixture,name:"Standard",frame:NSRect(x:24,y:20,width:192,height:108),device:device)
let adaptive=ToneView(fixture:fixture,name:"High candidate",frame:NSRect(x:264,y:20,width:192,height:108),device:device)
for (view,label) in [(standard,"Standard / Hd=1"),(adaptive,"High / current Hd")] {
    root.addSubview(view)
    let text=NSTextField(labelWithString:label)
    text.alignment = .center;text.font = .systemFont(ofSize:12);text.textColor = .black
    text.frame=NSRect(x:view.frame.minX,y:140,width:192,height:20)
    root.addSubview(text)
}
let runStarted=Date()
var restored=false
var restoreSeconds:Double?
window.makeKeyAndOrderFront(nil);app.activate(ignoringOtherApps:true)
DispatchQueue.main.asyncAfter(deadline:.now()+0.35) {
    if let originalFront {restored=originalFront.activate(options:[.activateIgnoringOtherApps])}
    restoreSeconds=Date().timeIntervalSince(runStarted)
}
var stage=0,ticks=0,staticCount=0
var lastData:Data?
var captures:[[String:Any]]=[]
let stages=["standard-initial","high-request","back-to-standard","high-again"]
func rect(_ r:CGRect)->[String:Double] {["x":r.minX,"y":r.minY,"width":r.width,"height":r.height]}
@MainActor func finish(_ failure:String?=nil) {
    standard.stop();adaptive.stop()
    var report:[String:Any]=[
        "os":ProcessInfo.processInfo.operatingSystemVersionString,"source_sha256":fixture.sourceSHA256,
        "source_nits":fixture.sourceNits,"decode_validate_milliseconds":decodeMilliseconds,"source_raw":"640x360 opaque neutral PNG RGBA16 BE, ImageIO decoded explicit byte order handled; CICP9/16/0/1; copy(namedPQ) retains identical provider bytes; original file/ICC unmodified","decoded_byte_order":fixture.bigEndian ? "Big":"Little",
        "candidate":"BT2408-6 Annex5 LB0 LW1000 Lmin0 Lmax203*Hd; LW1000 is candidate preset, not PNG metadata; ISO default diffuse white203 is not read from ICC lumi100",
        "output":"Float32 RGBA CGImage linear BT2020 Lout/203 -> CoreImage -> rgba16Float CAMetalLayer extendedLinearITUR2020 -> system screen conversion; no PQ output layer",
        "vectors":vectors,"timings":fixture.timings,"captures":captures,"real_os_notifications":osEvents,"submitted_texture_pixels":textureSamples,
        "original_frontmost_pid":originalFront?.processIdentifier ?? -1,"restore_requested":restored,"restore_after_seconds":restoreSeconds ?? -1,"frontmost_at_finish":NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1,
        "duration_seconds":Date().timeIntervalSince(runStarted),"resident_at_finish":residentBytes(),
        "limitations":"Known neutral input only. No physical nit measurement, color/gamut or metadata rule proof. Hd>1 is an unverified extension of a scalar candidate, not Apple14 equivalence. WindowServer SDR PNG may clip >1 even when distinct linear EDR pixels are submitted. No manually posted screen notifications."
    ]
    if let failure {report["failure"]=failure}
    try! JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("report.json"))
    if !restored,let originalFront {_ = originalFront.activate(options:[.activateIgnoringOtherApps])}
    window.close();exit(failure == nil ? 0:1)
}
_ = Timer.scheduledTimer(withTimeInterval:0.15,repeats:true) {_ in
    Task { @MainActor in
    guard Date().timeIntervalSince(runStarted)<25 else {finish("bounded timeout at stage \(stage)");return}
    ticks += 1
    guard ticks>=3,let screen=window.screen else{return}
    let current=Double(screen.maximumExtendedDynamicRangeColorComponentValue)
    let potential=Double(screen.maximumPotentialExtendedDynamicRangeColorComponentValue)
    if stage==0 || stage==2 {guard current<=1.001 else{return}}
    else {guard potential>1 && current>=potential*0.995 else{return}}
    guard let cg=CGWindowListCreateImage(.null,.optionIncludingWindow,CGWindowID(window.windowNumber),.boundsIgnoreFraming),let data=cg.dataProvider?.data else{return}
    if (data as Data)==lastData {staticCount += 1}else{staticCount=0;lastData=data as Data}
    guard staticCount>=4 else{return}
    let dest=CGImageDestinationCreateWithURL(output.appendingPathComponent(stages[stage]+".png") as CFURL,UTType.png.identifier as CFString,1,nil)!
    CGImageDestinationAddImage(dest,cg,nil);precondition(CGImageDestinationFinalize(dest))
    captures.append(["stage":stages[stage],"current":current,"potential":potential,"image_width":cg.width,"image_height":cg.height,"content_width":480,"content_height":180,"scale":window.backingScaleFactor,"active":app.isActive,"key":window.isKeyWindow,"frames":["Standard":rect(standard.frame),"High candidate":rect(adaptive.frame)],"draws":[standard.draws,adaptive.draws],"requests_edr":[standard.requested,adaptive.requested]])
    stage += 1;ticks=0;staticCount=0;lastData=nil
    if stage==stages.count {finish();return}
    prototypeStage=stages[stage]
    adaptive.high = stage==1 || stage==3
    adaptive.refresh()
}
}
app.run()

}

}
