/// Generated from the `frame` component.
@MainActor
struct AppView_frame: View {
    @EnvironmentObject private var bernEngine: BernEngine
    @EnvironmentObject private var session_GalleryDraft: App_GalleryDraft
    @EnvironmentObject private var bernWindow: BernWindowContext
    @ObservedObject private var bernLanguage = BernLanguage.shared
    @ObservedObject private var bernTheme = BernThemeState.shared

    var body: some View {
        SwiftUI.Group {
            BernLayers(alignment: .center, fillsWidth: true) {
                BernCanvasState {
                    SwiftUI.Canvas { context, size in
                        BernDraw.shape(&context, "rect", CGRect(x: 0.0, y: 0.0, width: size.width - 0.0, height: size.height - 0.0), corner: 8.0, fill: .role("surface.canvas"), fade: nil, stroke: nil, strokeWidth: 1.0, opacity: 1.0)
                    }
                    .frame(width: nil, height: nil).frame(maxWidth: .infinity, maxHeight: .infinity)
                    .accessibilityElement(children: .ignore)
                    .accessibilityAddTraits(.isImage)
                    .accessibilityLabel(SwiftUI.Text(verbatim: BernText.string("frame.0.0.0.label")))
                    .bernFillsLayers()
                }
                SwiftUI.VStack(alignment: .center, spacing: 12.0) {
                    BernVideo(target: "frame.clip", label: BernText.string("frame.0.0.1.0.label"), binding: .source(bernEngine.clip.url), controls: false, fit: .contain, corner: Double(((bernWindow.idle) ? (Int64(0)) : (Int64(20)))), cornerMotion: BernMotion(period: 0.48, damping: 0.86))
                    .animation(BernMotion(period: 0.48, damping: 0.86).animation, value: [AnyHashable(((bernWindow.idle) ? (Int64(0)) : (Int64(20))))])
                    if !(bernWindow.idle) {
                        BernRow(alignment: .center, spacing: 12.0) {
                            BernSplitButton(label: BernText.string("frame.0.0.1.1.if0.0.0.label"), systemImage: "captions.bubble", more: BernText.string("bern.split.more"), isOn: SwiftUI.Binding(get: { bernEngine.caption }, set: { newValue in bernEngine.setCaption(newValue, from: bernWindow) }), capsule: false, height: 34.0, target: "frame.caption") {
                                SwiftUI.Text(verbatim: BernText.string("frame.0.0.1.1.if0.0.0.0.content"))
                                .font(.headline)
                                SwiftUI.Slider(value: SwiftUI.Binding(get: { session_GalleryDraft.captionSize }, set: { session_GalleryDraft.captionSize = $0 }), in: 11.0...20.0) {
                                    SwiftUI.Text(verbatim: BernText.string("frame.0.0.1.1.if0.0.0.1.label"))
                                } onEditingChanged: { editing in
                                    _ = editing
                                }
                                .bernAccentTint()
                                .bernControl("frame.caption_size", role: "slider", label: BernText.string("frame.0.0.1.1.if0.0.0.1.label"), actions: BernControlActions(setNumber: { value in session_GalleryDraft.captionSize = value }, value: { BernText.text(session_GalleryDraft.captionSize) }))
                            }
                            SwiftUI.Menu {
                                SwiftUI.Button(action: {
                                    session_GalleryDraft.captionSize = Double(12.0)
                                }) {
                                    SwiftUI.Text(verbatim: BernText.string("frame.0.0.1.1.if0.0.1.0.label"))
                                }
                                SwiftUI.Button(action: {
                                    session_GalleryDraft.captionSize = Double(18.0)
                                }) {
                                    SwiftUI.Text(verbatim: BernText.string("frame.0.0.1.1.if0.0.1.1.label"))
                                }
                            } label: {
                                SwiftUI.Label(BernText.string("frame.0.0.1.1.if0.0.1.label"), systemImage: "textformat.size")
                            }
                            .menuStyle(.button)
                            .bernButtonLook(.secondary)
                            .bernControl("frame.caption_sizes", role: "menu", label: BernText.string("frame.0.0.1.1.if0.0.1.label"), actions: BernControlActions())
                            .bernControl("frame.small", role: "button", label: BernText.string("frame.0.0.1.1.if0.0.1.0.label"), enabled: true, actions: BernControlActions(activate: { session_GalleryDraft.captionSize = Double(12.0) }))
                            .bernControl("frame.large", role: "button", label: BernText.string("frame.0.0.1.1.if0.0.1.1.label"), enabled: true, actions: BernControlActions(activate: { session_GalleryDraft.captionSize = Double(18.0) }))
                            BernPopoverButton(label: BernText.string("frame.0.0.1.1.if0.0.2.label"), systemImage: "speaker.wave.3.fill", presented: nil, target: "frame.volume", nativeCircular: true, shortcut: nil) {
                                SwiftUI.Text(verbatim: BernText.string("frame.0.0.1.1.if0.0.2.0.content"))
                                .font(.headline)
                                SwiftUI.Slider(value: SwiftUI.Binding(get: { session_GalleryDraft.volume }, set: { session_GalleryDraft.volume = $0 }), in: 0.0...1.0) {
                                    SwiftUI.Text(verbatim: BernText.string("frame.0.0.1.1.if0.0.2.1.label"))
                                } onEditingChanged: { editing in
                                    _ = editing
                                }
                                .bernAccentTint()
                                .bernControl("frame.volume_level", role: "slider", label: BernText.string("frame.0.0.1.1.if0.0.2.1.label"), actions: BernControlActions(setNumber: { value in session_GalleryDraft.volume = value }, value: { BernText.text(session_GalleryDraft.volume) }))
                            }
                            .bernButtonLook(.icon)
                            SwiftUI.Group {
                                if bernEngine.caption {
                                    SwiftUI.Text(verbatim: BernText.string("frame.0.0.1.1.if0.0.3.if0.0.content"))
                                    .foregroundStyle(.secondary)
                                    .bernTransition(insertion: AnyTransition.opacity, insertionMotion: BernMotion(period: 0.45, damping: 1.0), removal: AnyTransition.opacity, removalMotion: BernMotion(period: 0.45, damping: 1.0), appear: BernAppear.fade)
                                }
                            }
                            .animation(BernMotion(period: 0.45, damping: 1.0).animation, value: [bernEngine.caption])
                        }
                    }
                }
                .padding(Double(((bernWindow.idle) ? (Int64(0)) : (Int64(40)))))
                .animation(BernMotion(period: 0.48, damping: 0.86).animation, value: [AnyHashable(((bernWindow.idle) ? (Int64(0)) : (Int64(40))))])
                SwiftUI.Group {
                    if session_GalleryDraft.dragging {
                        BernCanvasState {
                            SwiftUI.Canvas { context, size in
                                BernDraw.shape(&context, "rounded", CGRect(x: 0.0, y: 0.0, width: size.width - 0.0, height: size.height - 0.0), corner: 20.0, fill: nil, fade: nil, stroke: .role("accent"), strokeWidth: 4.0, opacity: 1.0)
                            }
                            .frame(width: nil, height: nil).frame(maxWidth: .infinity, maxHeight: .infinity)
                            .accessibilityHidden(true)
                            .bernFillsLayers()
                        }
                        .bernTransition(insertion: AnyTransition.opacity, insertionMotion: BernMotion(period: 0.45, damping: 1.0), removal: AnyTransition.opacity, removalMotion: BernMotion(period: 0.45, damping: 1.0), appear: BernAppear.fade)
                    }
                }
                .animation(BernMotion(period: 0.45, damping: 1.0).animation, value: [session_GalleryDraft.dragging])
            }
            .environment(\.colorScheme, .dark)
            .background(BernAppearanceRegion(dark: true))
            .bernNudge(session_GalleryDraft.dragging, motion: BernMotion(period: 0.42, damping: 0.42))
        }
        .modifier(BernDrop(kinds: "video", over: SwiftUI.Binding(get: { session_GalleryDraft.dragging }, set: { session_GalleryDraft.dragging = $0 }), opens: true, give: { url in session_GalleryDraft.file = App_MediaSource(url: url.absoluteString); bernEngine.play(session_GalleryDraft.file, from: bernWindow) }))
        .bernControl("frame.drop_clip", role: "drop", label: BernText.string("frame.0.label"), actions: BernControlActions(value: { session_GalleryDraft.file.url }, setFile: { url in session_GalleryDraft.file = App_MediaSource(url: url.absoluteString); bernEngine.play(session_GalleryDraft.file, from: bernWindow) }, fileKinds: "video"))
    }
}

