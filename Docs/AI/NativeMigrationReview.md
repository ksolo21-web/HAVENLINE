# Native migration review — 2026-09-07

Source: `codex/havenline-godot-android`, Godot 4.7.2 official `ed1daf0bf`.

| Check | Result | Evidence / limit |
| --- | --- | --- |
| Preserved four supplied/recovered GLBs | PASS | SHA-256 values in asset-manifest.json and native-assets-audit.json |
| Runtime gameplay and save checks | PASS | 24 actual Godot checks; gameplay-test-results.json |
| Godot headless scene startup | PASS | Actual scene imported and ran; not a visual test |
| ARM64 APK export | PASS | Native libgodot_android.so and libc++_shared.so; no Unity/IL2CPP payload |
| APK signature | PASS | Verified APK v2 and v3 signing |
| Physical installation/lifecycle | UNTESTED | No connected Android device |
| Native graphical rendering | PASS for execution only | Godot Forward Mobile, Vulkan 1.4, llvmpipe software device |
| Reference composition/environment | FAIL | Cropped furnace, overbright snow, candidate environment below requested art standard |
| Crew motion presentation | FAIL | C1 locomotion clips present; C2–C4 have no clips and remain in rest poses |
| Whole-rig 9/10 approval | UNTESTED | No independent complete part-by-clip audit performed in this migration |
| Native 4K render path | PASS for resolution only | Second real mobile-renderer frame is 3840×2160 at scale 1.0, using software Vulkan |
| Sustained 4K/60 on Android | UNTESTED | No physical device benchmark; software render execution is not performance evidence |
| Complete game | FAIL | Detailed remaining scope in release-status.json |

The supplied C1 source has 66 joints and 52,898 vertices. Recovered V7 C2/C3/C4 have 52-joint skins and 35,806/51,854/51,219 vertices respectively. All four identities remain distinct; C1 was not substituted for the other crew members.

The first rendered frame is retained only as failed review evidence. The native review scene includes developer-only protection against invisible wolf damage because the wolf visual has not yet been integrated. This is a known incomplete scene integration, not an alteration of the original gameplay contract or a finished defense loop. The deterministic simulation retains and tests the original wave gates.

The second frame fixes the camera conversion: Unity's orthographicSize is a half-height, while Godot Camera3D.size is the full span. The preserved 7.15 reference value therefore maps to 14.3 with KEEP_HEIGHT. Exposure was reduced after the first frame. See `NativeEvidence/native-4k-frame.png` and `render-4k-evidence.json` for the resulting frame and its scene-script hash. Crew motion and production environment quality still fail; the new frame is not an approved game presentation.

Next work must resolve the failed visual evidence with proper assets and motion, then render and independently review the real native scene again. Do not promote the candidate environment, frozen rest poses, numeric-only progression or source-test successes into a claim that Havenline is complete.
