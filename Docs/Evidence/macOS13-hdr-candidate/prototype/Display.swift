import AppKit
import MetalKit
import CoreImage

@MainActor var prototypeStage = "standard-initial"
@MainActor var osEvents: [[String:Any]] = []
@MainActor var textureSamples: [[String:Any]] = []

@MainActor final class ToneView: MTKView {
    let fixture: PQFixture
    let commands: MTLCommandQueue
    let imageContext: CIContext
    let name: String
    var high = false
    private var pixels: CGImage?
    private var mappedHeadroom = -1.0
    var draws = 0

    init(fixture: PQFixture, name: String, frame: NSRect, device: MTLDevice) {
        self.fixture = fixture; self.name = name
        commands = device.makeCommandQueue()!
        imageContext = CIContext(mtlDevice:device, options:[.cacheIntermediates:false,.workingColorSpace:fixture.linearSpace])
        super.init(frame:frame,device:device)
        colorPixelFormat = .rgba16Float
        framebufferOnly = false
        isPaused = true; enableSetNeedsDisplay = true
        clearColor = MTLClearColorMake(0,0,0,1)
        let surface = layer as! CAMetalLayer
        surface.colorspace = fixture.linearSpace
        surface.isOpaque = true
    }
    required init(coder:NSCoder) {fatalError()}
    deinit {NotificationCenter.default.removeObserver(self)}
    override func hitTest(_ point:NSPoint)->NSView? {nil}
    var headroom:Double {Double(window?.screen?.maximumExtendedDynamicRangeColorComponentValue ?? 1)}
    var potential:Double {Double(window?.screen?.maximumPotentialExtendedDynamicRangeColorComponentValue ?? 1)}
    var requested:Bool {(layer as! CAMetalLayer).wantsExtendedDynamicRangeContent}

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        NotificationCenter.default.removeObserver(self)
        if let window {
            NotificationCenter.default.addObserver(self,selector:#selector(screenChanged(_:)),name:NSApplication.didChangeScreenParametersNotification,object:nil)
            NotificationCenter.default.addObserver(self,selector:#selector(screenChanged(_:)),name:NSWindow.didChangeScreenNotification,object:window)
        }
        refresh()
    }
    @objc func screenChanged(_ note:Notification) {
        osEvents.append(["stage":prototypeStage,"view":name,"name":note.name.rawValue,"current":headroom,"potential":potential,"intent":high ? "High":"Standard","manual":false])
        refresh()
    }
    func refresh() {
        (layer as! CAMetalLayer).wantsExtendedDynamicRangeContent = high && potential > 1
        needsDisplay = true
    }
    override func layout() {super.layout();needsDisplay=true}
    override func viewDidChangeBackingProperties() {super.viewDidChangeBackingProperties();refresh()}
    override func draw(_ dirty:NSRect) {
        draws += 1
        let effective = high ? max(1,headroom) : 1
        if pixels == nil || effective != mappedHeadroom {
            pixels = fixture.image(headroom:effective)
            mappedHeadroom = effective
        }
        guard let pixels,let drawable=currentDrawable,let command=commands.makeCommandBuffer() else{return}
        let input = CIImage(cgImage:pixels)
        let scale = CGAffineTransform(scaleX:CGFloat(drawable.texture.width)/CGFloat(fixture.width),y:CGFloat(drawable.texture.height)/CGFloat(fixture.height))
        let image = input.transformed(by:scale)
        let target = CIRenderDestination(mtlTexture:drawable.texture,commandBuffer:command)
        target.colorSpace=fixture.linearSpace;target.isFlipped=true
        do {_ = try imageContext.startTask(toRender:image,to:target)} catch {fatalError("CI render: \(error)")}
        if let readback=device?.makeBuffer(length:512,options:.storageModeShared),let blit=command.makeBlitCommandEncoder() {
            for (index,x) in [drawable.texture.width/4,drawable.texture.width*3/4].enumerated() {
                blit.copy(from:drawable.texture,sourceSlice:0,sourceLevel:0,sourceOrigin:MTLOrigin(x:x,y:drawable.texture.height/4,z:0),sourceSize:MTLSize(width:1,height:1,depth:1),to:readback,destinationOffset:index*256,destinationBytesPerRow:256,destinationBytesPerImage:256)
            }
            blit.endEncoding()
            let sample:[String:Any]=["stage":prototypeStage,"view":name,"intent":high ? "High":"Standard","current":headroom,"effective":effective,"requests_edr":requested,"unit":"linear BT.2020 relative to UI white=1 (ISO default Wc=203)"]
            command.addCompletedHandler {_ in
                let words=readback.contents().assumingMemoryBound(to:UInt16.self)
                let left=Float(Float16(bitPattern:UInt16(littleEndian:words[0])))
                let right=Float(Float16(bitPattern:UInt16(littleEndian:words[128])))
                DispatchQueue.main.async {var s=sample;s["left"]=left;s["right"]=right;textureSamples.append(s)}
            }
        }
        command.present(drawable);command.commit()
    }
    func stop() {NotificationCenter.default.removeObserver(self);(layer as! CAMetalLayer).wantsExtendedDynamicRangeContent=false;pixels=nil;releaseDrawables()}
}

@MainActor final class ProofRoot:NSView {
    override var isFlipped:Bool {true}
    override func draw(_ rect:NSRect) {NSColor.white.setFill();bounds.fill()}
}
