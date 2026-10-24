# PNG parser revision: small source-only review

Reviewed the new script9d98d461…658e7f and policy e89de719…d48b7. **No blocking defect found; it can run within the original offline scope.** The actual old→new diff exactly matches `source-parser.patch`. Static AST/source checks confirm `scaled_box`, `rows_at`, `tuple_count`, `evaluate` are unchanged; only source_gate/parser_revision policy entries change.

The decoder matches [W3C PNG filter algorithms, chapter6](https://www.w3.org/TR/PNG-Filters.html): RGBA16 uses8byte bpp; predictors use already reconstructed left/previous-row bytes, zero at boundaries. Average floors the unoverflowed sum. Paeth uses exact integers and left→above→upper-left tie priority. Mod256 applies only to the final byte reconstruction. All five filter types restore bytes without changing16bit endian order or applying color operations. Filter counts are added only as scalar evidence.

Encoded source SHA, CRC/IHDR/IEND, exact bounded inflate length, alphaFFFF and dual-source decoded-byte equality remain. The correction supports legal source encoding after the first filter0-only refusal; it does not relax snapshot geometry or select a direction using observed colors.10flat/3fixed-band/5bin checks, two y mappings and unique/unknown result policy remain exact.

This review did not execute either script, decode source PNG payloads, read snapshot raw, change algorithms/product/repository, compile, operate UI or trigger CI. No successful structure result, lane semantics, color equivalence or causal conclusion is implied. Original unsuccessful attempt remains untouched.
