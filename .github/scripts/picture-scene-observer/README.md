# Actual Picture Scene observer

This diagnostic uses the exact 9dd generated Showcase source exported by run
40136458675. The uninstrumented complete application reproduced the historical
macOS 14 Picture screenshot in run 40135147500: first card 125pt, HDR card 147pt.

`build.py prepare SOURCE EVIDENCE` adds one environment-gated hook to the build
tool, after generation and before the original target plan. The hook invokes
`build.py patch OUTPUT_ROOT`, then continues the original build. `patch.py`
requires the complete generated file and component hashes and appends exactly
21 background measurement modifiers. Removing the insertions restores every
original byte. The helper is appended at file scope; no replacement Scene,
container, image, font, padding or row height is introduced.

Observer.swift passed standalone type checking with Swift5.9.2/SDK14.2/min13.
The complete Swift6/SDK26.2 product build and actual runtime remain separate gates.
The uninstrumented control is the original 9dd application. Omitting the output
environment variable disables export but does not remove the background modifiers.

The observer exports inherited environment and public resolved coordinates to
an existing BERN_PICTURE_OBSERVER_OUTPUT_DIR, with a PID-specific filename.
It keeps a bounded prefix of changed callback observations (256 events/512KiB).
Synchronous serialization and file writes may affect execution. Reaching a cap
or an I/O failure stops recording; it never claims a complete or settled end state.
Probe font values do not resolve Text's internal font; coordinates are not the
original proposed size or native card bounds.

Use the original complete macOS 14 collector, language, navigation/actions,
920x668 frame and normal appearance. Its Layout wait remains 0.8s. Build/collector
success does not accept geometry, event completeness or observer neutrality:
first verify all required labels and original PNGs and that first/HDR card
geometry remains 125/147. If the observer changes it, retain that result and stop
the environment interpretation. Do not add compensating layout or another Scene.
