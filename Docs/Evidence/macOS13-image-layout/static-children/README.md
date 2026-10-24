# Static child composition isolation, actual13 and14

The earlier manual NSHostingView fixture used ForEach for the first image grid; the generated Showcase layout has four literal Column/VStack children. This diagnostic changes only that composition, retaining all nine variant/min-row cases and public anchor measurements. Build40065027427 used SDK26.2/Swift6.2.4 ARM64/min13; exact binary SHA657c377dd40d8ccfc34693e1ab4f773a313e0476af11f301f351a253ca9edfa5 ran locally on13 and in normal-profile14 run40065166712. Runtime14/profile.json independently verifies all three appearance flags false.

All nine native Images cards remain129pt on both systems; HDR147pt, layers200pt, fixed109129pt and single caption36pt are unchanged. validation.json retains every compared public-frame delta and PNG-byte comparison with the old ForEach fixture, plus cross-OS deltas. This excludes that first-grid child composition alone as a sufficient explanation in this fixture. It does not reproduce or fix full-app14 cards124/125pt; App/Scene context and remaining simplified wrappers stay open.

Each runtime preserves its report, original27 PNG hashes and three unedited representative PNG names. Identical retained originals reference the prior authoritative raw file by relative symlink; the other24 PNG bytes were removed after hashing. No compensation or product source change was made.
