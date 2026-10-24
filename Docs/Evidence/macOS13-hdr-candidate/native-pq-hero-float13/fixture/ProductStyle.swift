import SwiftUI

// MARK: - Motion

/// A spring from `style!`: undamped period and damping ratio.
struct BernMotion: Equatable, Sendable {
    let period: Double
    let damping: Double

    var animation: Animation {
        .spring(response: period * bernMotionScale, dampingFraction: damping)
    }
}

/// An application may request reduced motion without overriding the
/// user's accessibility setting. Descendants honor either preference.
private struct BernReduceMotionKey: EnvironmentKey { static let defaultValue = false }
extension EnvironmentValues {
    var bernReduceMotion: Bool {
        get { self[BernReduceMotionKey.self] }
        set { self[BernReduceMotionKey.self] = newValue }
    }
}
@propertyWrapper
struct BernReducedMotion: DynamicProperty {
    @Environment(\.accessibilityReduceMotion) private var system
    @Environment(\.bernReduceMotion) private var application
    var wrappedValue: Bool { system || application }
}

/// Whether motion is reduced: by the system, or by `BERN_MOTION=reduce`
/// for repeatable screenshots.
let bernForcedReduceMotion = ProcessInfo.processInfo.environment["BERN_MOTION"] == "reduce"

/// How much slower springs and staggering run: ten times with
/// `BERN_MOTION=slow`, so motion can be checked frame by frame.
let bernMotionScale: Double = ProcessInfo.processInfo.environment["BERN_MOTION"] == "slow" ? 10 : 1

/// Images travel above the native split-view columns on macOS. Other
/// Apple platforms retain SwiftUI's shared-element implementation.
struct BernPictureHero: ViewModifier {
    let id: String?
    let picture: BernImage.Picture?
    let fit: BernImageFit
    let corner: CGFloat
    let motion: BernMotion
    @BernReducedMotion private var reduce
    @State private var flying = false

    func body(content: Content) -> some View {
        if let id {
            #if os(macOS)
            content
                .opacity(flying ? 0 : 1)
                .background(BernPictureHeroProbe(id: id, picture: picture, fit: fit,
                    corner: corner, motion: motion, reduced: reduce || bernForcedReduceMotion,
                    visibility: { hidden in
                        var transaction = Transaction()
                        transaction.disablesAnimations = true
                        withTransaction(transaction) { flying = hidden }
                    }))
            #else
            content.bernHero(id)
            #endif
        } else {
            content
        }
    }
}
