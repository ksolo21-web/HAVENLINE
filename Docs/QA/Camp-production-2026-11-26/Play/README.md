# Play the camp production trial

The shared download contains the Linux archive and signed ARM64 Android debug APK. Both use the Level 1 trial application and the gameplay scene `res://field_opening.tscn`. The reviewed source on GitHub can also rebuild both packages. [Checksums](SHA256SUMS) · [Source build instructions](../Source/README.md)

## Try the machines immediately on Linux

Download the Linux archive, `Play-expanded-camp.sh` and `Expanded-camp.save.json` into the same folder. Run the following commands there. The launcher makes a fresh private copy of an earned Level 1 checkpoint each time.

```sh
tar -xzf Havenline-Level-1-Camp-Production-Linux-x86_64.tar.gz
sh Play-expanded-camp.sh
```

Enter through the south gate and walk north. The saw is behind the blue-roofed storehouse, the cooker is beside it, and the drill sits east of the customer counter. Keep to the open floor to pass a machine. Approach its inlet to load the matching carried resource. The machine continues after you leave. Pick up a roast at the cooker's opposite end and take it to the camp side of the north counter for payment. The rescued survivor can carry surplus shelf stock to a machine while you do other work.

The checkpoint came from the previous trial’s player-controlled owl encounter. Its original SHA-256 appears in the play folder’s checksums. For a fresh opening use the ordinary `Play-Havenline.sh` included in the Linux archive. [Previous earned route](https://github.com/ksolo21-web/HAVENLINE/tree/f55128d744d3ac610dc6667673c9d040770a9da2/Docs/QA/Level-1-Settlement-2026-11-26/Gameplay)

## Android

The APK uses the existing trial package ID `com.havenline.levelonesettlementtrial`. Use a test device or Android test profile for a fresh run. Its signature, 16 KiB library alignment, launcher, archive contents and ARM64 ABI were checked. A physical phone run is still pending. The Android SDK also reports the same optional themed-icon resource warning as in the preceding trial APK. [Android package verification](../Verification/Android.json)
