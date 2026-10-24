# Initial-only macOS13 scroll-position candidate — not product acceptance

Base is exact diagnostic commit744e3168abf388a6bd881a6eb6f00bc6a4542123. Its native-snapshot logger and original f9 Runtime remain intact. BernStyle.baseline.swift is the source baseline; BernStyle.swift and initial-position.patch are the candidate. prepare.py reproduces the delta. No production working-tree template, app binary, UI session or CI was changed. After independent read-only review, an isolated local branch ci/film-initial-position-candidate was created at d14655fbd634c59a1e036cc9a6eb0bc550d64c75, parent744, onlyBernStyle121insertions/9deletions. It has not been pushed or dispatched; branch.json records provenance.

This is a behavior candidate, not a pure logger. It targets only the measured generated IR domain: initial still-owned target, center anchor, positive center-snap margin, finite measured target length L<=V−2m. The normalized Reader anchor is .5*(V−2m−L)/(V−L), only along the declared scroll axis. Film happens to yield0; there is no hard-coded leading/id/pixel offset. m0/unknown/nonfinite/L>effective/degenerate dimensions return the original anchor. No universal arbitrary-anchor or later-scroll equivalence is claimed.

## Ownership and callbacks

- A non-Observable owner, lazily allocated only on the macOS13 path, records the first onAppear key once. No published field is added.
- Existing margin and target callbacks keep their original scrollTo calls, substituting a valid initial anchor only while that exact key remains owned.
- Existing viewport and nearest callbacks may retry after the initial geometry batch. Their signature contains key, axis, viewport, margin and target length; it excludes origin. A scroll-induced origin/nearest change alone therefore cannot reapply itself. Original callbacks can still make their original duplicate calls.
- Actual initial Gallery frames are available before first settle. If target length later changes below a stable largest length without any viewport/margin/nearest change, there is no new observation to retry it. This is a remaining generic dynamic-layout boundary, not claimed complete support.
- The owner retires synchronously on the original quiet-stop callback, any explicit scroll(to:), real userScroll callback, and the new13-only Reader onDisappear. No begin/rearm after retirement for the same retained StateObject. A new View identity creates a new owner. This deliberately limits the candidate to the first owner lifetime; native14 reappearance equivalence is not measured.
- Same-identity disappear before the150ms callback immediately retires ownership; later reappearance follows the original Reader route. No closed view must wait for an observed stops publication to release this gate.

## Pending snap and quiet time

Snap allowed/generation hooks exist only for a position owner with center snap and positive margin. In that domain, initial waiting blocks new programmatic-bounds snap work. begin and finish each advance generation. A pending160ms snap captures generation at scheduling and rechecks both generation and allowed state at execution, so work created before quiet release cannot act after the150ms release. m0/noncenter/snap-only retain nil hooks and their old route.

There is no new Task, timer, wait call or fixed delay. The existing150ms quiet and160ms snap deadlines are unchanged. Candidate scrollTo can produce normal geometry reports, and those reports can naturally restart the existing quiet task; the candidate itself never calls expect/wait. Once geometry signature stabilizes, origin feedback cannot schedule another candidate application. User takeover and explicit Last/First permanently retire the initial gate, retaining the existing later target/snap route.

The only new View modifier is onDisappear in the13 Reader branch, explicitly required for retirement. Existing onAppear/onGeometryChange/onChange counts are unchanged. The14 native scrollPosition/contentMargins path, nearest/frame computation, phase mapping, default3 and shared release/follow behavior are not rewritten. On14 the new owner stays lazy/unread.

## Review and validation boundary

validation.json records exact source/patch hashes and callback/timer count checks. Local Swift5.9 frontend parsing verifies syntax only. Owner-check.swift checks the extracted owner and explicitly MainActor weak hook closures with target13/strict concurrency; neither replaces whole-app Swift6 typing. No candidate application has been built or run. Whole-project CI and a single isolated13 direct+Last+resize observer pass remain required.

Acceptance must distinguish inactive13 internal diagnosis from active14 visual references. The first two-second trace remains one-shot; later Last/resize PNG/window/CLI observations are external and must not be described as a second internal trace. Last was previously within1point of14 and must not regress. A missing/invalid initial measurement, changed UI identity, failed raw-buffer stability, late user takeover, or reappearance discrepancy must stay explicit rather than be papered over by defaults or offsets.
