private final class CustomCounter {var calls=0}
@MainActor private final class FixtureModel:ObservableObject {
    @Published var look="icon"
    @Published var enabled=true
    @Published var onBar=false
    @Published var hasIcon=true
    @Published var requestNative=true
    @Published var group:CGFloat?=nil
    var opens=0;var closes=0
    let counter=CustomCounter()
}
private struct FixtureCustomStyle:ButtonStyle {
    let counter:CustomCounter
    func makeBody(configuration:Configuration)->some View {
        let _ = {counter.calls += 1}()
        return configuration.label.padding(9).background(Color.orange,in:RoundedRectangle(cornerRadius:3))
    }
}
private struct FixtureView:View {
    @ObservedObject var model:FixtureModel
    let context:BernWindowContext
    private var button:some View {
        BernPopoverButton(label:"Volume",systemImage:model.hasIcon ? "speaker.wave.3.fill":nil,presented:nil,target:"fixture.volume",nativeCircular:model.requestNative,shortcut:KeyboardShortcut("v",modifiers:.command)) {
            Text("Volume popup").font(.headline)
            Slider(value:.constant(0.5),in:0...1).accessibilityLabel("Volume level")
            Text("Popover content").onAppear{model.opens += 1}.onDisappear{model.closes += 1}
        }.keyboardShortcut("v",modifiers:.command).disabled(!model.enabled)
    }
    @ViewBuilder private var styled:some View {
        switch model.look {
        case "icon":button.bernButtonLook(.icon)
        case "flat":button.bernButtonLook(.flat)
        case "secondary":button.bernButtonLook(.secondary)
        case "prominent":button.bernButtonLook(.prominent)
        case "custom":button.buttonStyle(FixtureCustomStyle(counter:model.counter))
        case "custom-inner":button.buttonStyle(FixtureCustomStyle(counter:model.counter)).bernButtonLook(.icon)
        case "plain-inner":button.buttonStyle(.plain).bernButtonLook(.icon)
        default:button
        }
    }
    var body:some View {
        VStack(spacing:16) {
            Text("Bern volume popover probe").font(.headline)
            styled
            Text(model.enabled ? "Enabled • ⌘V":"Disabled • ⌘V").font(.caption)
        }.frame(width:420,height:180).environmentObject(context)
        .environment(\.bernOnBar,model.onBar).environment(\.bernControlGroupHeight,model.group).bernItemKey(7)
    }
}
@MainActor private func views(_ root:NSView)->[String]{[String(describing:type(of:root))]+root.subviews.flatMap(views)}
@MainActor private func native(_ root:NSView)->BernCircularIconControl.Button? {
    if let b=root as? BernCircularIconControl.Button{return b}
    return root.subviews.lazy.compactMap{native($0)}.first
}
private struct ProbeFailure:Error {let reason:String}
@main @MainActor private enum Main {
    static func main(){exit(run())}
    static func run()->Int32 {
        let directory=URL(fileURLWithPath:CommandLine.arguments[1],isDirectory:true)
        try!FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)
        let baseline=CommandLine.arguments.contains("--baseline")
        let before=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0,started=Date()
        let app=NSApplication.shared;app.setActivationPolicy(.accessory);app.appearance=NSAppearance(named:.aqua);app.finishLaunching()
        let model=FixtureModel(),context=BernWindowContext()
        let host=NSHostingView(rootView:FixtureView(model:model,context:context))
        let w=NSWindow(contentRect:CGRect(x:240,y:300,width:420,height:180),styleMask:[.titled,.closable],backing:.buffered,defer:false)
        w.title="Bern volume popover probe 7E82";w.isReleasedWhenClosed=false;w.isRestorable=false;w.contentView=host;w.orderBack(nil)
        var report:[String:Any]=["success":false,"pid":getpid(),"os":ProcessInfo.processInfo.operatingSystemVersionString,"method":"Real ordered NSWindow; public NSButton.performClick and NSWindow.performKeyEquivalent. No physical mouse/keyboard delivery or activation."]
        var gates:[[String:Any]]=[],events:[[String:Any]]=[],activeSamples:[Bool]=[]
        func pump(_ t:Double=0.12){
            let until=Date(timeIntervalSinceNow:t);host.layoutSubtreeIfNeeded()
            while Date()<until {
                while let e=app.nextEvent(matching:.any,until:Date(),inMode:.default,dequeue:true){app.sendEvent(e)}
                RunLoop.main.run(until:min(until,Date(timeIntervalSinceNow:0.01)));app.updateWindows()
            }
            host.layoutSubtreeIfNeeded();activeSamples.append(NSWorkspace.shared.frontmostApplication?.processIdentifier==getpid())
        }
        func check(_ okay:Bool,_ message:String)throws {if !okay{throw ProbeFailure(reason:message)}}
        func value()->String{BernHost.shared.controls.all.first?.actions.value?() ?? "missing"}
        func popupWindows()->[[String:Any]] {app.windows.filter{$0 !== w}.map { win in
            let info=(CGWindowListCopyWindowInfo(.optionIncludingWindow,CGWindowID(win.windowNumber)) as? [[String:Any]])?.first ?? [:]
            return ["number":win.windowNumber,"class":String(describing:type(of:win)),"visible":win.isVisible,"alpha":win.alphaValue,"cg_onscreen":info[kCGWindowIsOnscreen as String] as? Bool ?? false,"cg_alpha":info[kCGWindowAlpha as String] as? Double ?? -1]
        }}
        func paintedPopup()->Bool {popupWindows().contains{($0["cg_onscreen"] as? Bool ?? false) && ($0["cg_alpha"] as? Double ?? 0)>0.001}}
        func event(_ name:String){events.append(["event":name,"value":value(),"opens":model.opens,"closes":model.closes,"enabled":model.enabled,"active":app.isActive,"popup_windows":popupWindows()])}
        func screenshot(_ name:String,_ window:NSWindow)throws {
            guard let image=CGWindowListCreateImage(.null,.optionIncludingWindow,CGWindowID(window.windowNumber),.boundsIgnoreFraming),let out=CGImageDestinationCreateWithURL(directory.appendingPathComponent(name) as CFURL,"public.png" as CFString,1,nil)else{throw ProbeFailure(reason:"WindowServer capture unavailable")}
            CGImageDestinationAddImage(out,image,nil);try check(CGImageDestinationFinalize(out),"PNG write failed")
        }
        defer {
            w.orderOut(nil);w.contentView=nil;w.close()
            if NSWorkspace.shared.frontmostApplication?.processIdentifier==getpid(){_ = NSRunningApplication(processIdentifier:before)?.activate(options:[])}
            report["view_classes"]=views(host);report["gates"]=gates;report["events"]=events;report["frontmost_pid_before"]=before;report["frontmost_pid_after"]=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
            report["self_frontmost_samples"]=activeSamples.filter{$0}.count;report["elapsed_seconds"]=Date().timeIntervalSince(started)
            try?JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:directory.appendingPathComponent("report.json"),options:.atomic)
        }
        do {
            pump(0.4)
            for mode in ["icon","flat","secondary","prominent","none","custom","custom-inner","plain-inner","handwritten-icon","bar","group","no-icon"] {
                model.look=["bar","group","no-icon","handwritten-icon"].contains(mode) ? "icon":mode;model.onBar=mode=="bar";model.group=mode=="group" ? 40:nil;model.hasIcon=mode != "no-icon";model.requestNative=["icon","bar","group","no-icon"].contains(mode);pump()
                let b=native(host),expected=mode=="icon"
                try check((b != nil)==expected,"look gate wrong: \(mode)")
                gates.append(["mode":mode,"native_circular":b != nil,"custom_calls":model.counter.calls])
            }
            try check(model.counter.calls>0,"Custom style was not used")
            model.look="icon";model.onBar=false;model.group=nil;model.hasIcon=true;model.requestNative=true;pump()
            if baseline {
                model.requestNative=false;pump()
                let key=NSEvent.keyEvent(with:.keyDown,location:.zero,modifierFlags:.command,timestamp:ProcessInfo.processInfo.systemUptime,windowNumber:w.windowNumber,context:nil,characters:"v",charactersIgnoringModifiers:"v",isARepeat:false,keyCode:9)!
                let opened=w.performKeyEquivalent(with:key);pump(0.25);event("baseline-window-shortcut-open")
                try check(opened && value()=="open","Baseline shortcut failed to open")
                let closed=w.performKeyEquivalent(with:key);pump(0.4);event("baseline-window-shortcut-dismiss")
                try check(closed && value()=="closed","Baseline shortcut failed to close binding")
                if let pop=app.windows.first(where:{$0 !== w && $0.isVisible}){try screenshot("after-dismiss-popover.png",pop)}
                report["inactive_dismiss_visual_confirmed"] = !paintedPopup();report["baseline"]=true;report["success"]=true;return 0
            }
            guard let button=native(host)else{throw ProbeFailure(reason:"native button absent")}
            try check(button.bezelStyle == .circular,"Wrong native bezel")
            try check(button.accessibilityIdentifier()=="fixture.volume[7]","Repeated AX target lost")
            try check(button.keyEquivalent=="v" && button.keyEquivalentModifierMask.contains(.command),"Shortcut environment lost")
            report["native"]=["class":String(describing:type(of:button)),"bezel_circular":true,"accessibility_id":button.accessibilityIdentifier(),"label":button.accessibilityLabel()!,"intrinsic":["width":button.intrinsicContentSize.width,"height":button.intrinsicContentSize.height],"shortcut":"cmd+v","effective_appearance":button.effectiveAppearance.name.rawValue]
            try screenshot("closed.png",w);event("ready")
            button.performClick(nil);pump(0.25);event("native-click")
            try check(value()=="open" && model.opens==1,"Click did not open exactly once")
            guard let pop=app.windows.first(where:{$0 !== w && $0.isVisible})else{throw ProbeFailure(reason:"No native popover window")}
            try screenshot("popover.png",pop)
            button.performClick(nil);pump(0.4);event("native-click-dismiss")
            try check(value()=="closed" && model.opens==1,"Second click did not dismiss")
            report["inactive_dismiss_visual_confirmed"] = !paintedPopup()
            if let pop=app.windows.first(where:{$0 !== w && $0.isVisible}){try screenshot("after-dismiss-popover.png",pop)}
            let key=NSEvent.keyEvent(with:.keyDown,location:.zero,modifierFlags:.command,timestamp:ProcessInfo.processInfo.systemUptime,windowNumber:w.windowNumber,context:nil,characters:"v",charactersIgnoringModifiers:"v",isARepeat:false,keyCode:9)!
            let handled=w.performKeyEquivalent(with:key);pump(0.08);event("window-shortcut")
            try check(handled && value()=="open" && model.opens==2,"Window shortcut did not activate exactly once")
            button.performClick(nil);pump(0.4);try check(value()=="closed","Shortcut popover dismiss failed")
            report["shortcut_dismiss_visual_confirmed"] = !paintedPopup()
            model.enabled=false;pump(0.08)
            guard let disabled=native(host)else{throw ProbeFailure(reason:"Disabled native view absent")}
            try check(!disabled.isEnabled,"Disabled environment lost")
            disabled.performClick(nil);let disabledHandled=w.performKeyEquivalent(with:key);pump(0.08);event("disabled-native-click-and-window-shortcut")
            try check(!disabledHandled && value()=="closed" && model.opens==2,"Disabled input dispatched")
            model.enabled=true;pump(0.08)
            BernHost.shared.controls.all.first?.actions.activate?();pump(0.08);event("external-activate")
            try check(value()=="open" && model.opens==3,"External activate did not open")
            BernHost.shared.controls.all.first?.actions.activate?();pump(0.03);try check(value()=="open" && model.opens==3,"External open toggled or duplicated popup")
            native(host)?.performClick(nil);pump(0.4);event("final-dismiss");try check(value()=="closed","Final popover dismiss failed")
            report["external_dismiss_visual_confirmed"] = !paintedPopup()
            report["disabled_shortcut_handled"]=disabledHandled;report["shortcut_handled"]=handled;report["success"]=true;return 0
        }catch{report["error"]=String(describing:error);fputs("\(error)\n",stderr);return 1}
    }
}
