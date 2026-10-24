# Bounded midflight WindowServer evidence

This supplements the frozen README without changing its bytes or historical hash. Success now retains at most **three PNGs**: before, one real in-flight capture, settled. All original time/sample/ownership/normal/front/cache/no-activation boundaries remain.

Within the existing real frame/progress polling, take one direct own-window WindowServer capture on the **first observed actual flight with0.2<progress<0.8**. Do not freeze its clock, assign progress/frame, add a playback timer, wait for five stable buffers, or seek another midflight opportunity. Record uptime and actual manager/flight state/frame immediately before and after the CG capture, so the image's asynchronous timing boundary remains explicit. If that band is never captured, mark the gate incomplete and stop without retry.

Preserve the original PNG ICC for inspection. The midflight image supplies visual evidence that WindowServer actually drew the moving flight; it is not a synchronized13/14 animation sample. Do not treat pixel equality of captures taken at different progress/times as animation acceptance. Before/settled keep their original five-identical-buffer requirement; partial failures retain only acquired images, with no fourth PNG.
