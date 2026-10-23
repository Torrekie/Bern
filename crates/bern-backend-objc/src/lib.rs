//! Darwin 20 native renderer, shared byte for byte by Objective-C and SwiftUI hosts.
//!
//! Business state and commands continue to cross the existing Bern C ABI. The
//! manifest is the typed IR, not a second UI description maintained by hand.
mod glue;
mod package;
mod resources;
use bern_ir::{Application, IR_VERSION};
use bern_target_api::{
    BuildContext, BuildPlan, BuildStep, ColorSource, Diagnostic, GeneratedFile, MediaSupport, Run,
    Signing, SimulatedSystem, Target, TargetConfig, TargetDescriptor, WindowCapabilities,
    check_common,
};
use std::path::{Path, PathBuf};

pub const MINIMUM_MACOS: &str = "11.0";
pub const MINIMUM_IOS: &str = "14.0";
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Platform {
    Macos,
    Ios,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Frontend {
    ObjectiveC,
    SwiftUi,
}
#[derive(Clone, Copy, Debug)]
pub struct NativeTarget {
    pub platform: Platform,
    pub frontend: Frontend,
}
impl NativeTarget {
    pub const fn new(platform: Platform, frontend: Frontend) -> Self {
        Self { platform, frontend }
    }
    fn system(self) -> &'static str {
        if self.platform == Platform::Macos {
            "macos"
        } else {
            "ios"
        }
    }
    fn minimum(self) -> &'static str {
        if self.platform == Platform::Macos {
            MINIMUM_MACOS
        } else {
            MINIMUM_IOS
        }
    }
}
pub struct AppKitMacos;
pub struct UIKitIos;
macro_rules! target_wrapper {
    ($name:ident,$platform:ident) => {
        impl Target for $name {
            fn descriptor(&self) -> TargetDescriptor {
                NativeTarget::new(Platform::$platform, Frontend::ObjectiveC).descriptor()
            }
            fn build_hosts(&self) -> &'static [&'static str] {
                &["macos"]
            }
            fn check(&self, a: &Application, c: &TargetConfig) -> Vec<Diagnostic> {
                NativeTarget::new(Platform::$platform, Frontend::ObjectiveC).check(a, c)
            }
            fn generate(
                &self,
                a: &Application,
                c: &BuildContext,
            ) -> Result<Vec<GeneratedFile>, Vec<Diagnostic>> {
                NativeTarget::new(Platform::$platform, Frontend::ObjectiveC).generate(a, c)
            }
            fn plan(
                &self,
                a: &Application,
                c: &BuildContext,
            ) -> Result<BuildPlan, Vec<Diagnostic>> {
                NativeTarget::new(Platform::$platform, Frontend::ObjectiveC).plan(a, c)
            }
            fn package(
                &self,
                a: &Application,
                c: &BuildContext,
                signing: &Signing,
            ) -> Result<BuildPlan, Vec<Diagnostic>> {
                NativeTarget::new(Platform::$platform, Frontend::ObjectiveC).package(a, c, signing)
            }
        }
    };
}
target_wrapper!(AppKitMacos, Macos);
target_wrapper!(UIKitIos, Ios);

pub fn product_name(app: &Application) -> String {
    bern_target_api::names::pascal(&app.app.id)
}
/// The actual renderer sources. Both frontend modes consume exactly these bytes.
pub fn native_files(app: &Application) -> Vec<GeneratedFile> {
    let mut manifest = serde_json::to_value(app).expect("serializable IR");
    manifest["file_kinds"] = serde_json::to_value(
        bern_ir::spec::FILE_KIND_EXTENSIONS
            .iter()
            .map(|(kind, extensions)| (*kind, *extensions))
            .collect::<std::collections::BTreeMap<_, _>>(),
    )
    .expect("file kinds");
    let existing = app
        .texts
        .iter()
        .map(|t| t.key.clone())
        .collect::<std::collections::BTreeSet<_>>();
    let mut extra =
        std::collections::BTreeMap::<String, std::collections::BTreeMap<String, String>>::new();
    for (language, table) in bern_target_api::texts::tables(app) {
        for (key, value) in table {
            if !existing.contains(&key) {
                extra
                    .entry(key)
                    .or_default()
                    .insert(language.clone(), value);
            }
        }
    }
    for (key, translations) in extra {
        manifest["texts"]
            .as_array_mut()
            .expect("texts")
            .push(serde_json::json!({"key":key,"translations":translations,"params":[]}));
    }
    let json = serde_json::to_vec(&manifest).expect("serializable IR");
    // Numeric bytes avoid C/Objective-C literal escaping, trigraphs, embedded NUL
    // and compiler source-encoding dependence, including arbitrary localized text.
    let mut model = String::from("static const unsigned char BNModelBytes[] = {\n");
    for chunk in json.chunks(32) {
        model.push_str("    ");
        for byte in chunk {
            model.push_str(&format!("{byte},"));
        }
        model.push('\n');
    }
    model.push_str("};\n");
    model.push_str(&format!(
        "static const uint64_t BNFingerprint = UINT64_C({});\n",
        app.protocol.fingerprint()
    ));
    let mut files = vec![
        GeneratedFile::text(
            "Sources/BernNative.h",
            include_str!("../templates/BernNative.h"),
        ),
        GeneratedFile::text(
            "Sources/BernNative.m",
            include_str!("../templates/BernNative.m"),
        ),
        GeneratedFile::text(
            "Sources/BernRenderer.inc",
            include_str!("../templates/BernRenderer.inc"),
        ),
        GeneratedFile::text(
            "Sources/BernMotion.inc",
            include_str!("../templates/BernMotion.inc"),
        ),
        GeneratedFile::text(
            "Sources/BernNavigation.inc",
            include_str!("../templates/BernNavigation.inc"),
        ),
        GeneratedFile::text(
            "Sources/BernSearch.inc",
            include_str!("../templates/BernSearch.inc"),
        ),
        GeneratedFile::text(
            "Sources/BernGestures.inc",
            include_str!("../templates/BernGestures.inc"),
        ),
        GeneratedFile::text(
            "Sources/BernText.inc",
            include_str!("../templates/BernText.inc"),
        ),
        GeneratedFile::text(
            "Sources/BernQueries.inc",
            include_str!("../templates/BernQueries.inc"),
        ),
        GeneratedFile::text(
            "Sources/BernMedia.inc",
            include_str!("../templates/BernMedia.inc"),
        ),
        GeneratedFile::text(
            "Sources/BernDrop.inc",
            include_str!("../templates/BernDrop.inc"),
        ),
        GeneratedFile::text("Sources/bern.h", include_str!("../templates/bern.h")),
        GeneratedFile::text("Sources/BernModel.inc", model),
        GeneratedFile::text(
            "Sources/BernFeatures.inc",
            format!(
                "#define BERN_USES_SVG {}\n",
                u8::from(bern_target_api::svg::used(app))
            ),
        ),
    ];
    if bern_target_api::svg::used(app) {
        files.push(GeneratedFile::text(
            "Sources/BernSvg.inc",
            bern_target_api::svg::template(include_str!("../templates/BernSvg.inc"), false),
        ));
    }
    files
}
fn xml(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}
fn info_plist(
    app: &Application,
    product: &str,
    target: NativeTarget,
    context: &BuildContext,
) -> String {
    let name = app.app.name.get(&app.languages.default).unwrap_or(product);
    let mut s = format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n<plist version=\"1.0\"><dict>\n<key>CFBundleExecutable</key><string>{}</string>\n<key>CFBundleIdentifier</key><string>{}</string>\n<key>CFBundleName</key><string>{}</string>\n<key>CFBundleDisplayName</key><string>{}</string>\n<key>CFBundleVersion</key><string>{}</string>\n<key>CFBundleShortVersionString</key><string>{}</string>\n<key>CFBundlePackageType</key><string>APPL</string>\n<key>CFBundleDevelopmentRegion</key><string>{}</string>\n",
        xml(product),
        xml(&app.app.bundle_id),
        xml(name),
        xml(name),
        xml(&app.app.version),
        xml(&app.app.version),
        xml(&app.languages.default)
    );
    s.push_str("<key>CFBundleLocalizations</key><array>");
    for language in &app.languages.supported {
        s.push_str(&format!("<string>{}</string>", xml(language)));
    }
    s.push_str("</array>\n");
    if target.platform == Platform::Macos {
        s.push_str(&format!("<key>LSMinimumSystemVersion</key><string>{MINIMUM_MACOS}</string>\n<key>NSHighResolutionCapable</key><true/>\n<key>NSPrincipalClass</key><string>NSApplication</string>\n<key>CFBundleIconFile</key><string>AppIcon</string>\n"));
    } else {
        s.push_str(&format!("<key>MinimumOSVersion</key><string>{MINIMUM_IOS}</string>\n<key>LSRequiresIPhoneOS</key><true/>\n<key>UIDeviceFamily</key><array><integer>1</integer><integer>2</integer></array>\n<key>UILaunchScreen</key><dict/>\n<key>UISupportedInterfaceOrientations</key><array><string>UIInterfaceOrientationPortrait</string><string>UIInterfaceOrientationLandscapeLeft</string><string>UIInterfaceOrientationLandscapeRight</string></array>\n"));
    }
    if target.platform == Platform::Ios {
        s.push_str(&resources::icon_plist(app, context));
    }
    if target.platform == Platform::Ios && app.uses_media() {
        s.push_str("<key>UIBackgroundModes</key><array><string>audio</string></array>\n");
    }
    s.push_str(&bern_target_api::apple_documents::document_types(
        app,
        target.platform == Platform::Ios,
    ));
    s.push_str("</dict></plist>\n");
    s
}
const SWIFT_HOST: &str = r#"// Generated by Bern. Swift 5.3 syntax; one shared native renderer.
import SwiftUI
#if os(macOS)
import AppKit
struct BernNativeContent: NSViewRepresentable {
    func makeNSView(context: Context) -> NSView { BernNativeCreateRootView() }
    func updateNSView(_ view: NSView, context: Context) {}
}
@main struct BernApplication: App {
    @NSApplicationDelegateAdaptor(BernNativeLifecycleDelegate.self) var lifecycle
    init() { BernNativeStart() }
    var body: some Scene {
        WindowGroup { BernNativeContent().edgesIgnoringSafeArea(.all).onOpenURL { BernNativeOpenURL($0) } }
        .commands { CommandGroup(replacing: .newItem) {} }
    }
}
#else
import UIKit
struct BernNativeContent: UIViewRepresentable {
    func makeUIView(context: Context) -> UIView { BernNativeCreateRootView() }
    func updateUIView(_ view: UIView, context: Context) {}
}
// A public hosting controller forwards the same window behavior as the
// Objective-C controller. No private selectors or runtime subclassing.
final class BernHostingController: UIHostingController<AnyView> {
    private var behaviorObserver: NSObjectProtocol?
    override var prefersStatusBarHidden: Bool { BernNativeIsImmersive() != 0 }
    override var prefersHomeIndicatorAutoHidden: Bool { BernNativeIsImmersive() != 0 }
    override var supportedInterfaceOrientations: UIInterfaceOrientationMask { UIInterfaceOrientationMask(rawValue: UInt(BernNativeOrientationMask())) }
    override var shouldAutorotate: Bool { true }
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        behaviorObserver = NotificationCenter.default.addObserver(forName: Notification.Name("BernNativeBehaviorChanged"), object: nil, queue: .main) { [weak self] _ in
            self?.setNeedsStatusBarAppearanceUpdate()
            self?.setNeedsUpdateOfHomeIndicatorAutoHidden()
            UIViewController.attemptRotationToDeviceOrientation()
        }
    }
    deinit { if let observer = behaviorObserver { NotificationCenter.default.removeObserver(observer) } }
}
@main final class BernApplication: UIResponder, UIApplicationDelegate {
    var window: UIWindow?
    func application(_ application: UIApplication, didFinishLaunchingWithOptions options: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        BernNativeStart()
        let native = UIWindow(frame: UIScreen.main.bounds)
        native.rootViewController = BernHostingController(rootView: AnyView(BernNativeContent().edgesIgnoringSafeArea(.all)))
        window = native
        native.makeKeyAndVisible()
        return true
    }
    func application(_ application: UIApplication, supportedInterfaceOrientationsFor window: UIWindow?) -> UIInterfaceOrientationMask { UIInterfaceOrientationMask(rawValue: UInt(BernNativeOrientationMask())) }
    func application(_ application: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey: Any] = [:]) -> Bool { BernNativeOpenURL(url); return true }
    func applicationWillTerminate(_ application: UIApplication) { BernNativeStop() }
}
#endif
"#;

// Keep this list synchronized with the native renderer's implementation. Unsupported
// contracts fail at check time rather than creating an inert approximation.
const COMPONENTS: &[&str] = &[
    "Column",
    "Row",
    "Accordion",
    "Grid",
    "Stack",
    "ScaleBox",
    "Positioned",
    "Modal",
    "Flow",
    "Timer",
    "Shortcut",
    "PickerOption",
    "Rail",
    "Spacer",
    "WindowButtons",
    "Divider",
    "ScrollView",
    "SplitView",
    "Sidebar",
    "SidebarHeader",
    "SidebarFooter",
    "Detail",
    "SidebarItem",
    "Section",
    "Form",
    "Navigation",
    "Destination",
    "NavLink",
    "ControlGroup",
    "Tabs",
    "TabAccessory",
    "Tab",
    "SplitButton",
    "PopoverButton",
    "Inspector",
    "Toast",
    "Toolbar",
    "Adaptive",
    "Layout",
    "Menu",
    "MenuItem",
    "LanguagePicker",
    "List",
    "ForEach",
    "Text",
    "Canvas",
    "Shape",
    "Series",
    "Pattern",
    "Label",
    "Svg",
    "Image",
    "Progress",
    "Button",
    "IconButton",
    "TextInput",
    "Search",
    "SearchItem",
    "Switch",
    "Slider",
    "Picker",
    "Video",
    "Query",
    "Drop",
    "Pinch",
    "Swipe",
    "Marquee",
];
const FEATURES: &[&str] = &[
    "controlled_values",
    "session_actions",
    "bound_lengths",
    "text_lines",
    "image_corners",
    "adaptive_images",
    "sidebar_width",
    "axis_padding",
    "icon_labels",
    "icon_tabs",
    "toolbar_leading",
    "dynamic_items",
    "size_classes",
    "page_search",
    "search_results",
    "form_layout",
    "fill_buttons",
    "popover_button",
    "button_content",
    "sidebar_header",
    "untitled_detail",
    "row_baseline",
    "modal_flow_timer",
    "capsule_controls",
    "page_badges",
    "tab_accessory",
    "accordion_layout",
    "scaled_scene",
    "window_short",
    "appearance",
    "runtime_theme",
    "dialog_windows",
    "shortcuts",
    "text_weights",
    "icon_menus",
    "image_template",
    "runtime_images",
    "file_pick",
    "text_formats",
    "idle_control",
    "window_landscape",
    "modal_cover",
    "rails",
    "scroll_snap",
    "picture_fills",
    "reveal",
    "toggle_button",
    "toolbar_search",
    "grid_cells",
    "edge_grow",
    "delayed_appear",
    "search_palette",
];
impl Target for NativeTarget {
    fn build_hosts(&self) -> &'static [&'static str] {
        &["macos"]
    }
    fn descriptor(&self) -> TargetDescriptor {
        let (id, ui) = match (self.platform, self.frontend) {
            (Platform::Macos, Frontend::ObjectiveC) => ("appkit-macos", "appkit"),
            (Platform::Ios, Frontend::ObjectiveC) => ("uikit-ios", "uikit"),
            (Platform::Macos, Frontend::SwiftUi) => ("swiftui-macos", "swiftui"),
            (Platform::Ios, Frontend::SwiftUi) => ("swiftui-ios", "swiftui"),
        };
        TargetDescriptor {
            id,
            ui,
            platforms: if self.platform == Platform::Macos {
                &["macos"]
            } else {
                &["ios"]
            },
            version: env!("CARGO_PKG_VERSION"),
            ir_versions: IR_VERSION..=IR_VERSION,
            color_source: ColorSource::Native,
            components: COMPONENTS,
            windows: WindowCapabilities {
                native: self.platform == Platform::Macos,
                virtual_windows: self.platform == Platform::Ios,
                floating: self.platform == Platform::Macos,
            },
            channels: &["ipc"],
            media: Some(MediaSupport {
                contract_versions: bern_media::MEDIA_CONTRACT_VERSION
                    ..=bern_media::MEDIA_CONTRACT_VERSION,
                backend: "avfoundation",
                backend_version: "1",
                presenter: "avplayerlayer",
                presenter_version: "1",
                background_playback: true,
                multi_view: true,
            }),
            styles: bern_target_api::style::APPLE_NATIVE_SUPPORT,
            motion: &[
                "appear",
                "appear_delay",
                "disappear",
                "reflow",
                "hero",
                "animate",
                "scroll_scale",
                "scroll_opacity",
                "scroll_origin_x",
                "scroll_origin_y",
                "nudge",
                "nudge_key",
                "nudge_scale",
                "reduce_motion",
                "stagger",
                "idle_area",
            ],
            window_chrome: true,
            text_marks: true,
            dynamic_items: true,
            features: FEATURES,
        }
    }
    fn check(&self, app: &Application, config: &TargetConfig) -> Vec<Diagnostic> {
        let mut diagnostics = check_common(self, app);
        diagnostics.extend(resources::check(app, self.platform));
        for channel in &config.channels {
            if !self.descriptor().channels.contains(&channel.as_str()) {
                diagnostics.push(Diagnostic::error(format!(
                    "target `{}` cannot provide channel `{channel}`",
                    self.descriptor().id
                )));
            }
        }
        for w in &app.windows.windows {
            if w.id == app.windows.primary && w.initial != bern_ir::WindowInitial::Open {
                diagnostics.push(Diagnostic::error(format!(
                    "window `{}` must initially be open: it hosts the application content",
                    w.id
                )));
            }
        }
        diagnostics
    }
    fn generate(
        &self,
        app: &Application,
        context: &BuildContext,
    ) -> Result<Vec<GeneratedFile>, Vec<Diagnostic>> {
        bern_target_api::svg::validate(app, context)?;
        let errors = self
            .check(app, &context.target)
            .into_iter()
            .filter(|d| d.severity == bern_target_api::Severity::Error)
            .collect::<Vec<_>>();
        if !errors.is_empty() {
            return Err(errors);
        }
        let product = product_name(app);
        let bundle = PathBuf::from(format!("{product}.app"));
        let mut files = native_files(app);
        files.extend(resources::files(app, context, self.platform, &bundle)?);
        files.extend([
            GeneratedFile::text("glue/Cargo.toml", glue::cargo_toml(context, app)),
            GeneratedFile::text("glue/src/lib.rs", glue::lib_rs(context, app, self.platform)),
            GeneratedFile::text("glue/src/cli.rs", glue::cli_rs(context, app)),
            GeneratedFile::text("glue/src/mcp.rs", glue::mcp_rs(context, app)),
            GeneratedFile::text(
                "glue/src/native_links.rs",
                include_str!("../templates/native_links.rs"),
            ),
            GeneratedFile::text(
                bundle.join(if self.platform == Platform::Macos {
                    "Contents/Info.plist"
                } else {
                    "Info.plist"
                }),
                info_plist(app, &product, *self, context),
            ),
        ]);
        if self.frontend == Frontend::SwiftUi {
            files.push(GeneratedFile::text("Sources/BernHost.swift", SWIFT_HOST));
        }
        if let Ok(lock) = std::fs::read(context.workspace_dir.join("Cargo.lock")) {
            files.push(GeneratedFile {
                path: "glue/Cargo.lock".into(),
                contents: lock,
            });
        }
        let manifest = serde_json::json!({"target":self.descriptor().id,"ui":self.descriptor().ui,"platform":self.system(),"destination":if self.platform==Platform::Macos {"native"}else{context.target.destination.as_deref().unwrap_or("simulator")},"generator":"bern-backend-objc","generator_version":env!("CARGO_PKG_VERSION"),"minimum_os":self.minimum(),"minimum_macos":MINIMUM_MACOS,"minimum_ios":MINIMUM_IOS,"swift_language_version":if self.frontend==Frontend::SwiftUi { Some("5") } else { None },"swift_source_compatibility":if self.frontend==Frontend::SwiftUi { Some("5.3") } else { None },"renderer":"shared-objective-c-native","engine_deployment":"in-process","ui_bridge":"c-abi","protocol_fingerprint":format!("{:016x}",app.protocol.fingerprint()),"app_bundle":bundle});
        files.push(GeneratedFile::text(
            "build.json",
            serde_json::to_string_pretty(&manifest).expect("manifest"),
        ));
        Ok(files)
    }
    fn plan(
        &self,
        app: &Application,
        context: &BuildContext,
    ) -> Result<BuildPlan, Vec<Diagnostic>> {
        let product = product_name(app);
        let output = &context.output_dir;
        let bundle = output.join(format!("{product}.app"));
        let ios = self.platform == Platform::Ios;
        let device = ios && context.target.destination.as_deref() == Some("device");
        let arm = std::env::consts::ARCH != "x86_64";
        let arch = if device || arm { "arm64" } else { "x86_64" };
        let host = if arm {
            "aarch64-apple-darwin"
        } else {
            "x86_64-apple-darwin"
        };
        let rust = if !ios {
            host
        } else if device {
            "aarch64-apple-ios"
        } else if arm {
            "aarch64-apple-ios-sim"
        } else {
            "x86_64-apple-ios"
        };
        let sdk = if !ios {
            "macosx"
        } else if device {
            "iphoneos"
        } else {
            "iphonesimulator"
        };
        let triple = if !ios {
            format!("{arch}-apple-macos{MINIMUM_MACOS}")
        } else {
            format!(
                "{arch}-apple-ios{MINIMUM_IOS}{}",
                if device { "" } else { "-simulator" }
            )
        };
        let profile = if context.release { "release" } else { "debug" };
        let glue_target = context.workspace_dir.join("target/bern-glue");
        let rust_output = glue_target.join(rust).join(profile);
        let host_output = glue_target.join(host).join(profile);
        let native_libs = rust_output.join("libbern_app.native-libs");
        let path = |p: &Path| p.display().to_string();
        let env = vec![(
            if ios {
                "IPHONEOS_DEPLOYMENT_TARGET"
            } else {
                "MACOSX_DEPLOYMENT_TARGET"
            }
            .into(),
            self.minimum().into(),
        )];
        let cargo = |target: &str, listing: bool| {
            let mut args = vec![
                if listing { "rustc" } else { "build" }.into(),
                if listing { "--lib" } else { "--bins" }.into(),
                "--manifest-path".into(),
                path(&output.join("glue/Cargo.toml")),
                "--target".into(),
                target.into(),
                "--target-dir".into(),
                path(&glue_target),
            ];
            if context.release {
                args.push("--release".into());
            }
            if listing {
                args.extend([
                    "--".into(),
                    "--print".into(),
                    format!("native-static-libs={}", path(&native_libs)),
                ]);
            }
            args
        };
        let run = |description: &str,
                   program: &str,
                   args: Vec<String>,
                   env: Vec<(String, String)>| BuildStep::Run {
            description: description.into(),
            program: program.into(),
            args,
            cwd: output.clone(),
            env,
        };
        let executable = if ios {
            bundle.join(&product)
        } else {
            bundle.join("Contents/MacOS").join(&product)
        };
        let resources = if ios {
            bundle.clone()
        } else {
            bundle.join("Contents/Resources")
        };
        let mut steps = vec![
            run(
                "Build the Rust engine and bridge",
                "cargo",
                cargo(rust, true),
                env.clone(),
            ),
            run(
                "Build the command line tools",
                "cargo",
                cargo(host, false),
                vec![("MACOSX_DEPLOYMENT_TARGET".into(), MINIMUM_MACOS.into())],
            ),
            BuildStep::CreateDir {
                path: executable.parent().unwrap().into(),
            },
            BuildStep::Mirror {
                dir: resources,
                files: app
                    .resources
                    .iter()
                    .map(|r| (context.project_dir.join(&r.name), PathBuf::from(&r.name)))
                    .collect(),
                keep: resources::keep(app, self.platform),
            },
        ];
        steps.push(run(
            "Validate native link flags",
            &host_output.join("_bern_link_flags").display().to_string(),
            vec![path(&native_libs)],
            vec![],
        ));
        steps.extend(resources::steps(app, context, self.platform, &bundle)?);
        let sources = output.join("Sources");
        let object = output.join("BernNative.o");
        let mut clang = vec![
            "--sdk".into(),
            sdk.into(),
            "clang".into(),
            "-target".into(),
            triple.clone(),
            "-fobjc-arc".into(),
            "-fblocks".into(),
            "-Werror=unguarded-availability".into(),
            "-Werror=unguarded-availability-new".into(),
            "-g".into(),
            if context.release {
                "-O2".into()
            } else {
                "-O0".into()
            },
            "-c".into(),
            path(&sources.join("BernNative.m")),
            "-o".into(),
            path(&object),
        ];
        if self.frontend == Frontend::SwiftUi {
            clang.push("-DBERN_SWIFTUI_HOST=1".into());
        }
        steps.push(run(
            "Compile the shared Objective-C native renderer",
            "xcrun",
            clang,
            env.clone(),
        ));
        let mut link = vec![
            "--sdk".into(),
            sdk.into(),
            if self.frontend == Frontend::SwiftUi {
                "swiftc".into()
            } else {
                "clang".into()
            },
            "-target".into(),
            triple,
        ];
        if self.frontend == Frontend::SwiftUi {
            link.extend([
                "-swift-version".into(),
                "5".into(),
                "-parse-as-library".into(),
                "-import-objc-header".into(),
                path(&sources.join("BernNative.h")),
                path(&sources.join("BernHost.swift")),
                "-framework".into(),
                "SwiftUI".into(),
            ]);
        }
        link.extend([
            path(&object),
            "-Xlinker".into(),
            "-fatal_warnings".into(),
            "-L".into(),
            path(&rust_output),
            "-lbern_app".into(),
            format!("@{}", path(&native_libs)),
            "-framework".into(),
            if ios { "UIKit".into() } else { "AppKit".into() },
            "-framework".into(),
            "Foundation".into(),
            "-framework".into(),
            "CoreGraphics".into(),
            "-framework".into(),
            "QuartzCore".into(),
            "-framework".into(),
            "AVFoundation".into(),
            "-framework".into(),
            "AVKit".into(),
            "-framework".into(),
            "CoreMedia".into(),
            "-framework".into(),
            "UniformTypeIdentifiers".into(),
            "-g".into(),
            "-o".into(),
            path(&executable),
        ]);
        if self.platform == Platform::Macos {
            link.extend(["-framework".into(), "CoreVideo".into()]);
        }
        if bern_target_api::svg::used(app) {
            link.extend(["-framework".into(), "WebKit".into()]);
        }
        steps.extend([
            run("Link the native application", "xcrun", link, env),
            run(
                "Generate debug symbols",
                "xcrun",
                vec![
                    "dsymutil".into(),
                    path(&executable),
                    "-o".into(),
                    path(&output.join(format!("{product}.app.dSYM"))),
                ],
                vec![],
            ),
            BuildStep::CreateDir {
                path: output.join("bin"),
            },
            BuildStep::Copy {
                from: host_output.join(app.app.id.replace('_', "-")),
                to: output.join("bin").join(app.app.id.replace('_', "-")),
            },
            BuildStep::Copy {
                from: host_output.join(format!("{}-mcp", app.app.id.replace('_', "-"))),
                to: output
                    .join("bin")
                    .join(format!("{}-mcp", app.app.id.replace('_', "-"))),
            },
            run(
                "Sign the application for local use",
                "codesign",
                vec!["--force".into(), "--sign".into(), "-".into(), path(&bundle)],
                vec![],
            ),
        ]);
        let listens = bern_target_api::skill::listens(&context.target.channels);
        let place = listens.then(|| {
            let place = bern_target_api::skill::Place::beside_bin(app, false);
            if ios && !device {
                place.connect(bern_target_api::skill::simulator_connect(app))
            } else {
                place
            }
        });
        steps.extend(bern_target_api::skill::steps(app, output, place.as_ref()));
        let cli = app.app.id.replace('_', "-");
        let mut products = vec![
            bundle.clone(),
            output.join("bin").join(&cli),
            output.join("bin").join(format!("{cli}-mcp")),
            output.join(format!("{product}.app.dSYM")),
        ];
        if listens {
            products.push(output.join(bern_target_api::skill::path(app)));
        }
        let mut plan = BuildPlan {
            steps,
            products,
            run: if !ios {
                Some(Run::Program(executable))
            } else if device {
                None
            } else {
                Some(Run::Simulator {
                    app: bundle,
                    bundle_id: app.app.bundle_id.clone(),
                    system: SimulatedSystem::Ios,
                })
            },
            notes: vec![],
        };
        if device {
            plan.notes.push("Device bundle uses an ad hoc signature. Installable distribution requires the application's provisioning profile and signing identity; no device installation is performed.".into());
        }
        Ok(plan)
    }
    fn package(
        &self,
        app: &Application,
        context: &BuildContext,
        signing: &Signing,
    ) -> Result<BuildPlan, Vec<Diagnostic>> {
        if self.platform == Platform::Macos {
            package::macos(app, context, signing)
        } else {
            Err(vec![Diagnostic::error(
                "iOS packaging requires an application provisioning/export workflow; build the simulator or device bundle with bern build",
            )])
        }
    }
}
