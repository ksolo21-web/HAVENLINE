# Havenline · World One

Commit `87f703f2a62c3651314b66084bcfb32858728364` opens `res://field_opening.tscn`. All three downloads use the same 201 reviewed files.

The prebuilt packages are in the shared World One review download. GitHub carries the checksums, complete versioned source and the extraction helper. To run from this repository, use the commands below.

```bash
git clone --filter=blob:none --single-branch --branch trial/world-one-expansion-2026-11-26 https://github.com/ksolo21-web/HAVENLINE.git
python HAVENLINE/Docs/QA/World-One-2026-11-26/Build/prepare.py HAVENLINE ./WorldOne
godot --editor --path ./WorldOne --import
godot --path ./WorldOne
```

## Play

- **Linux x86-64.** Extract the archive and run `./Havenline-World-One.x86_64`. Its Godot game pack is embedded in the executable. WASD or the arrow keys move the character, the mouse wheel zooms, and E operates a nearby gate.
- **Android arm64.** Install the signed debug review APK on an arm64 Android handset. One finger moves, two fingers pinch to zoom, and the on-screen gate control operates the nearby gate. Over ADB, use `adb install -r Havenline-World-One-Android-arm64-debug.apk`. Its application ID is `com.havenline.worldonereview`. APK integrity, its launcher and signature were checked locally. Physical handset performance and touch remain unverified.
- **Godot Editor.** Extract the source ZIP into a fresh folder. In Godot 4.7.2, choose **Import**, select `HavenlineLevel1/project.godot`, let the initial asset import finish, then press **F6** with `field_opening.tscn` open or **F5** to run the default scene. First import needs additional disk space for Godot’s generated cache.

World One stores its review progress separately. The Linux app uses Godot’s `Havenline-World-One-Review/world-one` data directory. Android uses the review application’s private data.

## Verify or export

Run `sha256sum -c Package-SHA256SUMS.txt` in the download folder after fetching all three packages. Each download also has an individual `.sha256` file. The native verification opened the exported Linux executable in a private graphics session, captured the playable opening, sent the window-manager close request and checked exit code zero. [Checksums](Package-SHA256SUMS.txt) · [Package and signature results](Package-verification.json) · [Packaged opening](Linux-packaged-opening.jpg)

To rebuild from a checkout containing that commit, place `prepare.py`, `Reviewed-files.json`, `export_presets.cfg` and `field-icon-mono.png` together. Run `python prepare.py /path/to/HAVENLINE /new/world-one-project`. This extracts the manifest from Git and checks every file hash. The source ZIP contains the equivalent project and portable export presets.

Install matching Godot 4.7.2 export templates. For Android, configure the Android SDK, JDK and a debug signing key in Godot. Choose **Linux World One Review** or **Android World One Review** in **Project → Export**. The verification report lists the equivalent command-line invocations. A build signed with a different key has a different certificate and APK checksum.
