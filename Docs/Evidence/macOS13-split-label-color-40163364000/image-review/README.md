# Candidate13: unchanged image, no strict color improvement

The actual candidate whole PNG is byte-for-byte identical to the frozen original13 reference: 1840×1336 at2x, SHA256 `ece61b2d4e05da32f3598e1f56da8369bb2029814fb3a66b4129bf363aff37f3`; the same PNG bytes include the same ICC (`e2473ef4…b64d4`). Only a direct byte/hash comparison was performed; no decoding, RGB conversion, resampling, candidate adapter or new mask was run.

The frozen957-pixel original13 foreground mask therefore gives unchanged R/G/B mean absolute errors toward the frozen14 target: **74.56116618185584 /50.14906756286067 /13.173675242640757**. Each channel has0 improved,0 regressed and957 tied pixels. No channel strictly improves, so the predeclared color rule fails. All fixed label/body/background/Frame and outside regions are unchanged by whole-file identity. This is an exact-case negative result; it does not explain why the style candidate had no visible effect.

Collector success remains true (exit0,8.766746997833252s, App stopped0). The independent wrapper remains **success=false /cleanup_success=false** because `defaults delete` of its exact fresh domain exceeded5s. This report preserves that failure and sets overall_gate_pass=false; later root cleanup cannot change this original result.

`result.json` binds source ce462, manifest product/private GUI/CLI, actual helper/source receipts, the successful actual14 gate, locks/isolation and both reference inputs. No original image/report/gate/source was changed. No helper/App/UI/CI/build or retry was performed. The earlier failed Row-ledger cohort is unrelated and unchanged. This candidate stops here under the frozen rule.
