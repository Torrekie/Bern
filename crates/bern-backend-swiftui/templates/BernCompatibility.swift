// Shared deployment compatibility. Generated build input; do not edit.
import SwiftUI
import QuartzCore

#if os(macOS)
import Combine
typealias BernObservableObject = ObservableObject
#else
import Observation
protocol BernObservableObject: AnyObject {}
typealias BernDisplayLink = CADisplayLink
#endif

private struct BernOptionalWindowKey: EnvironmentKey {
    static var defaultValue: BernWindowContext? { nil }
}

extension EnvironmentValues {
    var bernOptionalWindow: BernWindowContext? {
        get { self[BernOptionalWindowKey.self] }
        set { self[BernOptionalWindowKey.self] = newValue }
    }
}

@MainActor
extension View {
    #if os(macOS)
    func bernEnvironment<Object: ObservableObject>(_ object: Object) -> some View {
        environmentObject(object)
    }

    func bernEnvironment(_ window: BernWindowContext) -> some View {
        environmentObject(window).environment(\.bernOptionalWindow, window)
    }
    #else
    func bernEnvironment<Object: Observable>(_ object: Object) -> some View {
        environment(object)
    }
    #endif

    @ViewBuilder
    func bernOnChange<Value: Equatable>(
        of value: Value, initial: Bool = false,
        _ action: @escaping @MainActor (Value, Value) -> Void
    ) -> some View {
        #if os(macOS)
        if #available(macOS 14.0, *) {
            onChange(of: value, initial: initial, action)
        } else {
            modifier(BernLegacyOnChange(value: value, initial: initial, action: action))
        }
        #else
        onChange(of: value, initial: initial, action)
        #endif
    }

    func bernOnChange<Value: Equatable>(
        of value: Value, initial: Bool = false,
        _ action: @escaping @MainActor () -> Void
    ) -> some View {
        bernOnChange(of: value, initial: initial) { _, _ in action() }
    }

    func bernOnChange<Value: Equatable>(
        of value: Value, initial: Bool = false,
        _ action: @escaping @MainActor (Value) -> Void
    ) -> some View {
        bernOnChange(of: value, initial: initial) { _, newValue in action(newValue) }
    }
}

#if os(macOS)
/// Canvas captures resolved colors when its content is evaluated. Observation
/// used to discover these reads; Combine needs the explicit subscriptions.
@MainActor
struct BernCanvasState<Content: View>: View {
    @ObservedObject private var pictures = BernPictures.shared
    @ObservedObject private var theme = BernThemeState.shared
    private let content: () -> Content

    init(@ViewBuilder content: @escaping () -> Content) { self.content = content }

    var body: some View { content() }
}

/// The old API reports only the new value. Keep the previous value in
/// SwiftUI-owned storage, without recreating or identifying the content.
@MainActor
private struct BernLegacyOnChange<Value: Equatable>: ViewModifier {
    @MainActor
    private final class ActionBox {
        var value: Value
        var initial: Bool
        var action: @MainActor (Value, Value) -> Void

        init(value: Value, initial: Bool, action: @escaping @MainActor (Value, Value) -> Void) {
            self.value = value
            self.initial = initial
            self.action = action
        }
    }

    let value: Value
    let initial: Bool
    let action: @MainActor (Value, Value) -> Void
    @State private var previous: Value
    @State private var latest: ActionBox

    init(value: Value, initial: Bool, action: @escaping @MainActor (Value, Value) -> Void) {
        self.value = value
        self.initial = initial
        self.action = action
        _previous = State(initialValue: value)
        _latest = State(initialValue: ActionBox(value: value, initial: initial, action: action))
    }

    func body(content: Content) -> some View {
        // The legacy callback retains the old view's closure. Its stable box
        // must therefore be refreshed while evaluating the new view, before
        // SwiftUI delivers that callback. Updating it does not publish a change
        // or replace the content's identity.
        let latest = latest
        latest.value = value
        latest.initial = initial
        latest.action = action
        return content
            .onAppear {
                let current = latest.value
                previous = current
                if latest.initial { latest.action(current, current) }
            }
            .onChange(of: value) { next in
                let old = previous
                previous = next
                latest.action(old, next)
            }
    }
}
#endif
