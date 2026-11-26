# Havenline World One mining trial

These builds open Level 1 at `res://field_opening.tscn` from commit `fa9d3e987859a1e46c2533f94431b4e9cae3a9e5`. The new deposits are coal, slate and metal ore alongside the existing stone banks. All four use the pickaxe, have separate resource identities and replenish after five seconds of active simulation.

[Download Linux x86-64](Havenline-World-One-Mining-Linux-x86_64.tar.gz) · [Download Android arm64](Havenline-World-One-Mining-Android-arm64-debug.apk)

Alfred can find the two prebuilt packages in the shared Havenline download under `world-one-mining/Build/`. This GitHub directory carries the source manifest, extraction helper, export presets and package checksums.

**Linux x86-64.** Extract the archive, keep its two files together and run the included launcher. It starts the standalone game and directs saves to the mining trial’s own data folder. The launcher uses the current user’s XDG data directory, normally `~/.local/share/havenline-mining-trial/`. Godot is included.

```sh
tar -xzf Havenline-World-One-Mining-Linux-x86_64.tar.gz
./Play-Havenline-Mining.sh
```

**Android arm64.** Open the signed debug APK on the Android device or install it on a connected test device with the command below. Its launcher entry is **Havenline · Mining Trial**. The package ID `com.havenline.worldonemining` gives it its own Android app storage, separate from the preceding World One trial. This is a sideloadable review build. Device-specific performance remains unverified.

```sh
adb install -r Havenline-World-One-Mining-Android-arm64-debug.apk
```

**Verify the downloads.** From the directory containing both downloads and the checksum list, run `sha256sum -c Package-SHA256SUMS.txt`. The verification receipt identifies the tested ELF and the APK signing certificate. [Checksums](Package-SHA256SUMS.txt) · [Package verification](Package-verification.json) · [Native Linux opening](Linux-packaged-opening.jpg)

**Reproduce from Git.** Use Godot 4.7.2 with its matching Linux and Android export templates and a configured Android SDK/debug signing key. Extract the exact source to a new directory with `python3 prepare.py /path/to/HAVENLINE /new/mining-project`. The extractor verifies the SHA-256 of each project input against the reviewed manifest and installs the matching export presets. Then export with the following commands. Local build timestamps and signing keys can produce different package checksums. [Source manifest](Reviewed-files.json) · [Export presets](export_presets.cfg) · [Frozen source](https://github.com/ksolo21-web/HAVENLINE/tree/fa9d3e987859a1e46c2533f94431b4e9cae3a9e5/HavenlineLevel1)

```sh
godot --headless --editor --path /new/mining-project --import
godot --headless --path /new/mining-project --export-release "Linux Mining Trial" /new/Havenline-Mining.x86_64
godot --headless --path /new/mining-project --export-debug "Android Mining Trial" /new/Havenline-World-One-Mining-Android-arm64-debug.apk
```
