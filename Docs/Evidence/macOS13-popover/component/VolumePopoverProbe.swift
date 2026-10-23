import AppKit
import SwiftUI
import Combine
import CryptoKit
import ImageIO


enum BernButtonLook {
    case secondary, prominent, icon
    /// An icon with no background, in the secondary color.
    case flat
}

extension View {
func bernButtonLook(_ look: BernButtonLook) -> some View {
        modifier(BernSystemButtonLook(look: look))
    }
}


private struct BernControlGroupHeightKey: EnvironmentKey {
    static let defaultValue: CGFloat? = nil
}

private struct BernOnBarKey: EnvironmentKey {
    static let defaultValue = false
}

extension EnvironmentValues { var bernControlGroupHeight: CGFloat? { get {self[BernControlGroupHeightKey.self]} set {self[BernControlGroupHeightKey.self]=newValue} }; var bernOnBar: Bool {get {self[BernOnBarKey.self]} set {self[BernOnBarKey.self]=newValue}} }

@MainActor final class BernThemeState: ObservableObject { static let shared=BernThemeState() }; struct BernColor { var color: Color; static func role(_ name:String)->BernColor {BernColor(color:.white)} }

extension EnvironmentValues { var bernSceneScaled: Bool {false}; var bernAccent: Color? {nil} }; extension View {func bernPrimaryLabel()->some View {self};func bernAccentTint()->some View {self}}

private struct BernSystemButtonLook: ViewModifier {
    let look: BernButtonLook
    @Environment(\.bernControlGroupHeight) private var groupHeight
    @Environment(\.bernOnBar) private var onBar
    @Environment(\.bernSceneScaled) private var scaled
    @Environment(\.bernAccent) private var accent
    @Environment(\.controlSize) private var controlSize

    @ViewBuilder func body(content: Content) -> some View {
        #if os(tvOS)
        // tvOS's own buttons take a television's sizes, which a scene that
        // is scaled up as a whole would enlarge again: there a button keeps
        // the design's sizes for a television (46 points, 52 for a large
        // one, on 16 and 17-point type) and shows the focus as tvOS's own.
        if scaled && groupHeight == nil && !onBar {
            let large = controlSize == .large || controlSize == .extraLarge
            switch look {
            case .icon:
                content.buttonStyle(BernFocusShapeStyle(
                    prominent: false, accent: accent ?? .accentColor, circle: true, height: 46, padding: 0))
                    .font(.system(size: 20))
            case .prominent, .secondary:
                content.buttonStyle(BernFocusShapeStyle(
                    prominent: look == .prominent, accent: accent ?? .accentColor, circle: false,
                    height: large ? 52 : 46, padding: large ? 28 : 22))
                    .font(.system(size: large ? 17 : 16, weight: look == .prominent ? .semibold : .medium))
            case .flat:
                // A plain button is its label, as a link reads in the text.
                content.buttonStyle(BernFocusShapeStyle(
                    prominent: false, accent: accent ?? .accentColor, circle: false, height: 0, padding: 0,
                    plain: true))
                    .font(.system(size: 16))
            }
        } else {
            standard(content)
        }
        #else
        standard(content)
        #endif
    }

    @ViewBuilder private func standard(_ content: Content) -> some View {
        if let groupHeight {
            content.buttonStyle(BernGroupedButtonStyle(height: groupHeight)).foregroundStyle(.primary)
        } else if onBar && (look == .icon || look == .flat) {
            content.buttonStyle(BernGroupedButtonStyle(height: 0)).foregroundStyle(.primary)
        } else if #available(macOS 26.0, iOS 26.0, tvOS 26.0, *) {
            switch look {
            case .secondary: content.buttonStyle(.bordered).bernPrimaryLabel()
            case .prominent: content.buttonStyle(.borderedProminent).bernAccentTint()
            case .icon: content.buttonStyle(.bordered).bernCircleBorderShape().bernPrimaryLabel()
            case .flat: content.buttonStyle(.borderless).foregroundStyle(.secondary)
            }
        } else {
            switch look {
            case .secondary: content.buttonStyle(.bordered).bernPrimaryLabel()
            case .prominent: content.buttonStyle(.borderedProminent).bernAccentTint()
            case .icon: content.buttonStyle(.bordered).bernCircleBorderShape().bernPrimaryLabel()
            case .flat: content.buttonStyle(.borderless).foregroundStyle(.secondary)
            }
        }
    }
}

private struct BernGroupedButtonStyle: ButtonStyle {
    let height: CGFloat
    func makeBody(configuration: Configuration) -> some View {
        #if os(tvOS)
        BernFocusedGroupButton(configuration: configuration, height: height)
        #else
        configuration.label
            .frame(minWidth: height, minHeight: height)
            .contentShape(Rectangle())
            .opacity(configuration.isPressed ? 0.55 : 1)
        #endif
    }
}

private struct BernLegacyShapedButton: ButtonStyle {
    @ObservedObject private var theme = BernThemeState.shared
    let circle: Bool
    let prominent: Bool
    var radius: CGFloat = 12
    @Environment(\.isEnabled) private var enabled
    @Environment(\.bernAccent) private var accent
    func makeBody(configuration: Configuration) -> some View {
        let shape = circle ? AnyShape(Circle()) : AnyShape(RoundedRectangle(cornerRadius: radius))
        configuration.label
            .padding(.horizontal, circle ? 8 : 12)
            .padding(.vertical, 6)
            .frame(minWidth: circle ? 32 : nil, minHeight: 32)
            .foregroundStyle(prominent ? BernColor.role("on_accent").color : .primary)
            .background {
                if prominent { shape.fill(accent ?? .accentColor) }
                else { shape.fill(.regularMaterial) }
            }
            .overlay(shape.stroke(Color.primary.opacity(0.12), lineWidth: 0.5))
            .brightness(configuration.isPressed ? -0.08 : 0)
            .opacity(enabled ? 1 : 0.45)
    }
}

extension View {
@ViewBuilder func bernCircleBorderShape() -> some View {
        #if os(macOS)
        if #available(macOS 14, *) { buttonBorderShape(.circle) }
        else { buttonStyle(BernLegacyShapedButton(circle: true, prominent: false)) }
        #else
        buttonBorderShape(.circle)
        #endif
    }
}


@MainActor
struct BernCircularIconButton<Fallback: View>: View {
    let systemImage: String
    let label: String
    let target: String
    let shortcut: KeyboardShortcut?
    let fontSize: CGFloat?
    let destructive: Bool
    let defaultFocus: Bool
    let action: @MainActor () -> Void
    @ViewBuilder let fallback: Fallback
    @Environment(\.bernOnBar) private var onBar
    @Environment(\.bernControlGroupHeight) private var groupHeight

    @ViewBuilder var body: some View {
        if #available(macOS 14.0, *) {
            fallback
        } else if onBar || groupHeight != nil {
            fallback
        } else {
            BernCircularIconControl(
                systemImage: systemImage, label: label, target: target, shortcut: shortcut,
                fontSize: fontSize, destructive: destructive, defaultFocus: defaultFocus, action: action)
                .fixedSize()
        }
    }
}

@MainActor
private struct BernCircularIconControl: NSViewRepresentable {
    let systemImage: String
    let label: String
    let target: String
    let shortcut: KeyboardShortcut?
    let fontSize: CGFloat?
    let destructive: Bool
    let defaultFocus: Bool
    let action: @MainActor () -> Void
    @Environment(\.isEnabled) private var enabled
    @Environment(\.controlSize) private var controlSize
    @Environment(\.bernItemKeys) private var keys

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeNSView(context: Context) -> Button {
        let button = Button(frame: .zero)
        button.title = ""
        button.setButtonType(.momentaryPushIn)
        button.bezelStyle = .circular
        button.imagePosition = .imageOnly
        button.target = context.coordinator
        button.action = #selector(Coordinator.activate(_:))
        return button
    }

    func updateNSView(_ button: Button, context: Context) {
        context.coordinator.action = action
        switch controlSize {
        case .mini: button.controlSize = .mini
        case .small: button.controlSize = .small
        case .large: button.controlSize = .large
        default: button.controlSize = .regular
        }
        button.font = NSFont.systemFont(ofSize: fontSize ?? NSFont.systemFontSize(for: button.controlSize))
        button.image = NSImage(systemSymbolName: systemImage, accessibilityDescription: label)
        button.hasDestructiveAction = destructive
        button.isEnabled = enabled
        button.toolTip = label
        button.setAccessibilityLabel(label)
        button.setAccessibilityIdentifier(target + keys)
        button.keyEquivalent = shortcut.map { String($0.key.character) } ?? ""
        var modifiers: NSEvent.ModifierFlags = []
        if let shortcut {
            if shortcut.modifiers.contains(.command) { modifiers.insert(.command) }
            if shortcut.modifiers.contains(.control) { modifiers.insert(.control) }
            if shortcut.modifiers.contains(.option) { modifiers.insert(.option) }
            if shortcut.modifiers.contains(.shift) { modifiers.insert(.shift) }
        }
        button.keyEquivalentModifierMask = modifiers
        button.defaultFocus = defaultFocus
        button.requestDefaultFocus()
    }

    static func dismantleNSView(_ button: Button, coordinator: Coordinator) {
        button.target = nil
        coordinator.action = nil
    }

    @MainActor
    final class Coordinator: NSObject {
        var action: (@MainActor () -> Void)?
        @objc func activate(_ sender: NSButton) {
            guard sender.isEnabled else { return }
            action?()
        }
    }

    final class Button: NSButton {
        var defaultFocus = false
        private var requestedFocus = false

        override func viewDidMoveToWindow() {
            super.viewDidMoveToWindow()
            requestDefaultFocus()
        }

        func requestDefaultFocus() {
            guard defaultFocus, !requestedFocus, isEnabled, let window else { return }
            requestedFocus = true
            DispatchQueue.main.async { [weak self, weak window] in
                guard let self, let window, self.window === window, self.isEnabled else { return }
                window.makeFirstResponder(self)
            }
        }
    }
}

struct BernControlActions {
    var activate: (@MainActor () -> Void)? = nil
    var edit: (@MainActor (String) -> Void)? = nil
    var submit: (@MainActor () -> Void)? = nil
    var setBool: (@MainActor (Bool) -> Void)? = nil
    var setNumber: (@MainActor (Double) -> Void)? = nil
    var select: (@MainActor (String) -> Bool)? = nil
    var back: (@MainActor () -> Bool)? = nil
    var value: (@MainActor () -> String?)? = nil
    var focus: (@MainActor () -> Void)? = nil
    /// Takes a file as if the user chose or dropped it.
    var setFile: (@MainActor (URL) -> Void)? = nil
    /// The kinds of file `setFile` takes, as `files:` names them.
    var fileKinds = "any"
}

struct BernControlEntry {
    let target: String
    let window: String
    let role: String
    let label: String
    let enabled: Bool
    let actions: BernControlActions
}

struct BernCommandFailure: Error {
    let code: String
    let message: String
}

@MainActor
final class BernControls {
    private var entries: [UUID: BernControlEntry] = [:]

    func register(_ token: UUID, _ entry: BernControlEntry) { entries[token] = entry }

    func remove(_ token: UUID) { entries[token] = nil }

    var all: [BernControlEntry] {
        entries.values.sorted { ($0.window, $0.target) < ($1.window, $1.target) }
    }

    func find(_ target: String) throws -> BernControlEntry {
        let matches = entries.values.filter { $0.target == target }
        if matches.isEmpty {
            throw BernCommandFailure(code: "target_not_found", message: "no mounted control `\(target)`; see ui.inspect")
        }
        if matches.count > 1 {
            throw BernCommandFailure(code: "target_ambiguous", message: "`\(target)` is mounted in several places")
        }
        if BernHost.shared.isBlocked(matches[0].window) {
            throw BernCommandFailure(
                code: "target_blocked",
                message: "`\(target)` is blocked by the close confirmation of `\(matches[0].window)`; decide it with window.confirm_close")
        }
        guard matches[0].enabled else {
            throw BernCommandFailure(code: "target_unavailable", message: "`\(target)` is disabled")
        }
        return matches[0]
    }
}

private struct BernItemKeysKey: EnvironmentKey {
    static let defaultValue = ""
}

extension EnvironmentValues {
    /// Keys of the rows around a view, outermost first, as `[a][b]`.
    var bernItemKeys: String {
        get { self[BernItemKeysKey.self] }
        set { self[BernItemKeysKey.self] = newValue }
    }
}

extension View {
    /// A row of a repetition: controls inside it, also in components it
    /// places, add `[key]` to their targets.
    func bernItemKey(_ key: some CustomStringConvertible) -> some View {
        transformEnvironment(\.bernItemKeys) { $0 += "[\(key)]" }
    }
}

/// A mounted control's registration: its token, and whether it is on
/// screen. A reference, so marking it does not draw the control again.
@MainActor
private final class BernControlMount {
    let token = UUID()
    var mounted = false
}

private struct BernControl: ViewModifier {
    let name: String
    let role: String
    let label: String
    let enabled: Bool
    let actions: BernControlActions
    #if os(macOS)
    @EnvironmentObject private var window: BernWindowContext
    #else
    @Environment(BernWindowContext.self) private var window
    #endif
    @Environment(\.bernItemKeys) private var keys
    @State private var mount = BernControlMount()

    init(target: String, role: String, label: String, enabled: Bool, actions: BernControlActions) {
        self.name = target
        self.role = role
        self.label = label
        self.enabled = enabled
        self.actions = actions
    }

    private var target: String { name + keys }

    private func register() {
        BernHost.shared.controls.register(
            mount.token,
            BernControlEntry(
                target: target, window: window.id, role: role, label: label, enabled: enabled,
                actions: actions))
    }

    func body(content: Content) -> some View {
        // Listed as the control appears and dropped as it disappears, both
        // at once. A task registering it may start later (iOS 26 does): for
        // a control that came and went in one update, as a layout shown
        // until the width is measured, it ran after the control had been
        // dropped and left it listed for good.
        content
            .accessibilityIdentifier(target)
            .onAppear {
                mount.mounted = true
                register()
            }
            .bernOnChange(of: "\(window.id)|\(target)|\(label)|\(enabled)") {
                if mount.mounted { register() }
            }
            .onDisappear {
                mount.mounted = false
                BernHost.shared.controls.remove(mount.token)
            }
    }
}



extension View {
func bernControl(
        _ target: String, role: String, label: String, enabled: Bool = true,
        actions: BernControlActions
    ) -> some View {
        modifier(BernControl(target: target, role: role, label: label, enabled: enabled, actions: actions))
    }
}


@MainActor final class BernWindowContext: ObservableObject {let id="fixture"};@MainActor final class BernHost {static let shared=BernHost();let controls=BernControls();func isBlocked(_ id:String)->Bool{false}}

extension View {func bernOnChange<V:Equatable>(of value:V,_ action:@escaping()->Void)->some View {onChange(of:value){_ in action()}}}

extension View {
@ViewBuilder func bernPopover<Content: View>(
        isPresented: Binding<Bool>, @ViewBuilder content: @escaping () -> Content
    ) -> some View {
        #if os(tvOS)
        sheet(isPresented: isPresented, content: content)
        #else
        popover(isPresented: isPresented, arrowEdge: .bottom, content: content)
        #endif
    }
}


extension View {
@ViewBuilder fileprivate func bernPopoverMaterial(scheme: ColorScheme) -> some View {
        #if os(macOS)
        if #available(macOS 13.3, *) {
            presentationCompactAdaptation(.popover)
                .presentationBackground { Rectangle().fill(.regularMaterial).environment(\.colorScheme, scheme) }
        } else {
            // macOS popovers do not adapt to sheets. Before presentationBackground,
            // put the same system material behind the popover's SwiftUI content.
            background(Rectangle().fill(.regularMaterial)).environment(\.colorScheme, scheme)
        }
        #else
        presentationCompactAdaptation(.popover)
            .presentationBackground { Rectangle().fill(.regularMaterial).environment(\.colorScheme, scheme) }
        #endif
    }
}


struct BernPopoverButton<Content: View>: View {
    let label: String
    let systemImage: String?
    let presented: Binding<Bool>?
    let target: String
    #if os(macOS)
    var nativeCircular = false
    var shortcut: KeyboardShortcut? = nil
    #endif
    @ViewBuilder let content: () -> Content
    @Environment(\.colorScheme) private var scheme
    @State private var local = false

    private var isPresented: Binding<Bool> {
        presented ?? $local
    }

    private var standardTrigger: some View {
        Button {
            isPresented.wrappedValue.toggle()
        } label: {
            if let systemImage {
                Label(label, systemImage: systemImage).labelStyle(.iconOnly)
            } else {
                Text(verbatim: label)
            }
        }
    }

    @MainActor @ViewBuilder private var trigger: some View {
        #if os(macOS)
        if #available(macOS 14, *) {
            standardTrigger
        } else if nativeCircular, let systemImage {
            // Requested by the generator only for an unstyled, unconstrained
            // icon outside a toolbar. The native control owns its press.
            BernCircularIconButton(
                systemImage: systemImage, label: label, target: target, shortcut: shortcut,
                fontSize: nil, destructive: false, defaultFocus: false,
                action: { isPresented.wrappedValue.toggle() }) {
                    standardTrigger
                }
        } else {
            standardTrigger
        }
        #else
        standardTrigger
        #endif
    }

    var body: some View {
        let showing = isPresented
        trigger
        .help(label)
        .bernPopover(isPresented: showing) {
            VStack(alignment: .leading, spacing: 12) { content() }
                .padding(16)
                .frame(minWidth: 240, alignment: .leading)
                // A popover also on iPhone, drawn in the appearance of
                // where it opens.
                .bernPopoverMaterial(scheme: scheme)
                .environment(\.colorScheme, scheme)
                .environment(\.bernControlGroupHeight, nil)
        }
        .bernControl(
            target, role: "popover_button", label: label,
            actions: BernControlActions(
                activate: { showing.wrappedValue = true },
                value: { showing.wrappedValue ? "open" : "closed" }))
    }
}

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

