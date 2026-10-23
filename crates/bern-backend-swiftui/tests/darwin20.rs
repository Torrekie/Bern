//! Contracts between the Swift 5.3 hosts and the shared native renderer.

use bern_backend_objc::{Frontend, NativeTarget, Platform};
use bern_backend_swiftui::{
    DARWIN20_MINIMUM_IOS, DARWIN20_MINIMUM_MACOS, SwiftUiDarwin20Ios, SwiftUiDarwin20Macos,
    SwiftUiIos, SwiftUiMacos,
};
use bern_target_api::Target;

#[test]
fn darwin20_hosts_publish_the_same_capabilities_as_the_native_renderer() {
    for (host, platform, id) in [
        (
            &SwiftUiDarwin20Macos as &dyn Target,
            Platform::Macos,
            "swiftui-macos",
        ),
        (
            &SwiftUiDarwin20Ios as &dyn Target,
            Platform::Ios,
            "swiftui-ios",
        ),
    ] {
        let host = host.descriptor();
        let native = NativeTarget::new(platform, Frontend::ObjectiveC).descriptor();
        assert_eq!(host.id, id);
        assert_eq!(host.ui, "swiftui");
        assert_eq!(host.components, native.components);
        assert_eq!(host.features, native.features);
        let styles = |items: &[bern_target_api::StyleSupport]| {
            items
                .iter()
                .map(|style| (style.component, style.base, style.states))
                .collect::<Vec<_>>()
        };
        assert_eq!(styles(host.styles), styles(native.styles));
        assert_eq!(host.motion, native.motion);
        assert_eq!(host.windows, native.windows);
        assert_eq!(host.window_chrome, native.window_chrome);
        assert_eq!(host.text_marks, native.text_marks);
        assert_eq!(host.dynamic_items, native.dynamic_items);
    }
    assert_eq!(DARWIN20_MINIMUM_MACOS, "11.0");
    assert_eq!(DARWIN20_MINIMUM_IOS, "14.0");
}

#[test]
fn modern_generators_remain_an_explicit_separate_choice() {
    let macos = SwiftUiMacos.descriptor();
    let ios = SwiftUiIos.descriptor();
    assert_eq!(macos.id, "swiftui-modern-macos");
    assert_eq!(ios.id, "swiftui-modern-ios");
    assert_eq!(macos.ui, "swiftui-modern");
    assert_eq!(ios.ui, "swiftui-modern");
}
