# Correction: executable was retained; original validators now run directly

The earlier review incorrectly treated permission to clean up as evidence that the executable had been removed. artifact-cleanup.json actually recorded binary.removed=false: only modules were deleted. The prior in-memory binary-hash substitution was unnecessary.

The actual614,208B HeroCGDirectProbe was freshly read before and after this pass, with unchanged SHA be263dfbd54a965003c8adc82c2294475963cb9463fc86c6daedcc89a09d8fd0. Original validate-direct.py was directly executed once for default and once for direct, with no replacements. Both exit0; each invoked the original complete base gate with float on/13. Both validator files remain byte-identical80b0…/663026….

Original README.md, review.json and SHA256SUMS are unchanged historical records. addendum.json corrects the cleanup assumption and records both actual gate outputs; SHA256SUMS.addendum freezes only the two new addendum files. No native app, build, UI, CI or pixel analysis was rerun. Root may now remove the executable.
