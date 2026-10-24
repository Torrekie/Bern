# Picture observer CI — private draft

Root-review draft: publish as `.github/workflows/macos14-picture-scene-observer.yml`; root owns the observer/build.py/patch.py package. Fixed9dd on mac15/Xcode26.3/Rust1.99/jobs2/min13, restore-only existingcache, prepare→cargo→collect→strictsign/min13/tar; one same-run artifact is captured on14 without product recompilation. Retain the build tar for later samebinary13.

Bothprepare/cargo set absoluteDRIVER/EVIDENCE; rawbuild.full.log stays runner-local, collect preserves boundedbuild.log, actualbuild.exit-code.txt propagates originalfailure. Collect runsalways only after prepare succeeds; defaultsuccess packaging/capture cannot hide an earlierfailure. Bothartifact uploads runalways.

Original fullmacos14-reference.swift suppliesnormal/en/en_US/920×668 and fullpage order; its Layout0.8s wait remains. No newpixel/stability/Scene gate. CIgreen does not prove observercoverage, unchanged125/147 heights, pixelagreement or lack of observereffect; root must check these offline before interpreting environment/layout values. The originalsession-first startup readiness behavior also remains.

The draft records source/harness and package/dependency/collector hashes; source/strictsignature/tar are verified again on14. No observerdataset/schema assertions are invented here. Current build.py API/log/env names were read and aligned; package may still be underauthor review. This directory is not yet frozen pendingroot review. LocalYAML and bash-n only; no repo/index change, build, UI ordispatch.
