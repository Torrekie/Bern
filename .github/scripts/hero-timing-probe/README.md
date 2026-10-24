# Bounded native/sampler timing observation

This five-file overlay reuses the committed hero-coordinator-sdr-probe source
package, exact image/style/dependency inputs, named asset and run-one wrapper.
Build copies that package and overwrites these five files. Assemble the same
AppKit/SwiftUI imports + ProductHero.swift + FlightSDR.swift.inc + Driver.swift.inc
into CoordinatorSDR.assembled.swift; only the executable name is HeroTimingProbe.
SDK26.2/arm64/min13 and ordinary NSApplication.run remain. This cohort runs only
default on13/14; no repeated SDR candidate experiment is performed.

The diagnostic adds bounded in-memory scalar timing around the existing native
timer registration, first tick/applied progress, sampler callback/prologue and
weak-wrapper matching. No extra native/window/image queries, timers, dispatches,
layout/flush, image retention or animation assignments are added. Original
motion, phase band, deadlines, PNG limits and native/execution/SDR assertions
remain. Partial acquisition stays failed even if timing coverage is complete.
All serialization follows original teardown. Recorded monotonic boundaries are
not rendered-frame synchronization, first-visible-frame timestamps or a unique
root cause. No product code/UI widget or deployment baseline is changed.
