from pathlib import Path
import difflib
D=Path(__file__).resolve().parent
base=(D/'ProductHero.base.swift').read_text()
old='                MainActor.assumeIsolated { self?.tick() }\n'
new='''                #if compiler(>=6.0)
                MainActor.assumeIsolated { self?.tick() }
                #else
                // Diagnostic SDK14.2 only: this static-endpoint fixture must
                // never start the coordinator's clock. Keep the actual14 call.
                if #available(macOS 14, *) {
                    MainActor.assumeIsolated { self?.tick() }
                } else {
                    preconditionFailure("Static endpoint fixture unexpectedly started its excluded timer")
                }
                #endif
'''
assert base.count(old)==1
adapted=base.replace(old,new)
(D/'ProductHero.swift').write_text(adapted+(D/'Driver.swift.inc').read_text())
(D/'sdk14-unused-clock.patch').write_text(''.join(difflib.unified_diff(base.splitlines(True),adapted.splitlines(True),fromfile='exact/ProductHero.base.swift',tofile='diagnostic/ProductHero.swift')))
