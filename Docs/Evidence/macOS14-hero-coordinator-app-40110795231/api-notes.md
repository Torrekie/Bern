# AppKit event-loop exit references

Root inspected the local SDK14.2 AppKit NSApplication.h declarations and Apple's documentation for this observer change.

- [NSApplication.stop](https://developer.apple.com/documentation/appkit/nsapplication/stop%28_%3A%29?language=objc): the flag is checked after dispatching an NSEvent. Calling stop from a timer alone does not stop the loop. Therefore the proposed terminal path invalidates sampling, calls stop and posts one application-defined event solely to permit return; it does not wait or take further samples.
- [NSApplication.postEvent](https://developer.apple.com/documentation/appkit/nsapplication/postevent%28_%3Aatstart%3A%29?language=objc): queues an event. The private terminal wake is not mouse/keyboard input or a render fence.

These API references do not prove a cause for prior mid-PNG positions, actual run-return behavior, pixel synchrony, or platform equivalence. Runtime evidence is still required. No local compilation was performed for these reads.

The current SwiftUI backend emits `@main struct BernApplication: App` and the macOS `@NSApplicationDelegateAdaptor` in `crates/bern-backend-swiftui/src/swift/app.rs:179-185`. This supports investigating an ordinary application event lifecycle rather than a manually pumped host, but the new fixture remains an isolated NSHostingView scene, not the full generated app. A bounded source search of `examples/**/*.rs` found the explicit `hero:` uses in Planner Text at lines127/129; Gallery's `animate: hero` is a different motion property. This does not claim image-hero or full-animation coverage from existing demo PNGs and does not remove the component's acceptance requirements.
