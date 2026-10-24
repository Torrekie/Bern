import SwiftUI
import AppKit
@MainActor
fileprivate final class BernLegacyInitialScroll {
    struct Signature: Equatable {
        let key: AnyHashable
        let horizontal: Bool
        let viewport: CGFloat
        let margin: CGFloat
        let length: CGFloat
    }
    private(set) var key: AnyHashable?
    private(set) var waiting = true
    private(set) var generation: UInt64 = 0
    private var started = false
    private var applied: Signature?

    func begin(_ key: AnyHashable) {
        guard !started, waiting else { return }
        started = true
        self.key = key
        generation &+= 1
    }
    func owns(_ key: AnyHashable) -> Bool { waiting && started && self.key == key }
    func note(_ signature: Signature, retryOnly: Bool) -> Bool {
        if retryOnly && applied == signature { return false }
        applied = signature
        return true
    }
    func finish() {
        guard waiting else { return }
        waiting = false
        key = nil
        applied = nil
        // Invalidates all pending work from the initial programmatic wave,
        // even if it wakes after the existing 150ms target release.
        generation &+= 1
    }
}
@MainActor
private struct HookCheck {
    var snapAllowed: (@MainActor () -> Bool)?
    var snapGeneration: (@MainActor () -> UInt64)?
    static func make(_ owner: BernLegacyInitialScroll?) -> Self {
        Self(snapAllowed: owner.map { owner in { [weak owner] in owner?.waiting != true } },
             snapGeneration: owner.map { owner in { [weak owner] in owner?.generation ?? 0 } })
    }
}
