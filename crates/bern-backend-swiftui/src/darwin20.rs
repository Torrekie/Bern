//! Swift 5.3 hosts for the shared AppKit/UIKit renderer.
//!
//! Both frontends compile the same Objective-C runtime and model. SwiftUI
//! participates only at the hosting boundary, using the representable APIs
//! shipped with macOS 11 and iOS 14; it does not independently approximate
//! native control sizes, colors, layout, or event handling.

use bern_backend_objc::{Frontend, NativeTarget, Platform};
use bern_ir::Application;
use bern_target_api::{
    BuildContext, BuildPlan, Diagnostic, GeneratedFile, Signing, Target, TargetConfig,
    TargetDescriptor,
};

pub const DARWIN20_MINIMUM_MACOS: &str = bern_backend_objc::MINIMUM_MACOS;
pub const DARWIN20_MINIMUM_IOS: &str = bern_backend_objc::MINIMUM_IOS;

/// The default `swiftui + macos` target, with a Swift 5.3 hosting layer.
pub struct SwiftUiDarwin20Macos;

/// The default `swiftui + ios` target, with a Swift 5.3 hosting layer.
pub struct SwiftUiDarwin20Ios;

macro_rules! shared_target {
    ($target:ty, $platform:expr) => {
        impl Target for $target {
            fn descriptor(&self) -> TargetDescriptor {
                NativeTarget::new($platform, Frontend::SwiftUi).descriptor()
            }

            fn build_hosts(&self) -> &'static [&'static str] {
                NativeTarget::new($platform, Frontend::SwiftUi).build_hosts()
            }

            fn check(&self, app: &Application, config: &TargetConfig) -> Vec<Diagnostic> {
                NativeTarget::new($platform, Frontend::SwiftUi).check(app, config)
            }

            fn generate(
                &self,
                app: &Application,
                context: &BuildContext,
            ) -> Result<Vec<GeneratedFile>, Vec<Diagnostic>> {
                NativeTarget::new($platform, Frontend::SwiftUi).generate(app, context)
            }

            fn plan(
                &self,
                app: &Application,
                context: &BuildContext,
            ) -> Result<BuildPlan, Vec<Diagnostic>> {
                NativeTarget::new($platform, Frontend::SwiftUi).plan(app, context)
            }

            fn package(
                &self,
                app: &Application,
                context: &BuildContext,
                signing: &Signing,
            ) -> Result<BuildPlan, Vec<Diagnostic>> {
                NativeTarget::new($platform, Frontend::SwiftUi).package(app, context, signing)
            }
        }
    };
}

shared_target!(SwiftUiDarwin20Macos, Platform::Macos);
shared_target!(SwiftUiDarwin20Ios, Platform::Ios);
