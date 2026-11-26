# Run or export the field from GitHub

Use Godot 4.7.2 and Python 3 with an existing Havenline checkout. From the repository root on the trial branch, run the commands below. The helper reads the tested commit directly from Git, verifies the SHA-256 of all 160 field project files, and creates a new directory next to the checkout. The two additional export files supply portable platform settings and the Android monochrome launcher icon. This also works with a local clone that has the trial commit and these review files.

```sh
python3 Docs/QA/Field-Loop-2026-11-26/Build/prepare.py . ../havenline-field-994ace86
godot --headless --editor --path ../havenline-field-994ace86 --import
godot --path ../havenline-field-994ace86
```

The project opens directly into `res://field_opening.tscn` with the separate `Havenline-Field-Loop-Preview` storage identity. For repeated QA with a disposable economy profile, follow the switch and marker instructions in the [field controls](https://github.com/ksolo21-web/HAVENLINE/blob/994ace861fbf132c5924bacc320f5608d75d9187/HavenlineLevel1/docs/Field-Loop.md).

For platform exports, install the matching Godot export templates. Android also needs Godot’s Android SDK/JDK and a developer debug keystore configured. Use absolute paths for the outputs.

```sh
godot --headless --path ../havenline-field-994ace86 --export-release 'Linux Field Review' "$PWD/Havenline-Field.x86_64"
godot --headless --path ../havenline-field-994ace86 --export-debug 'Android Field Review' "$PWD/Havenline-Field-Android-arm64-debug.apk"
```

A fresh extraction, Godot import and both portable export commands completed on the review host. [Reproduction receipt](Reproduction.json)

The delivered packages have their own verified checksums. A local Android export uses the local developer’s signing certificate. [Review package verification](../Package-verification.json) · [Download checksums](../Package-SHA256SUMS.txt) · [Physical device test procedure](../Environment-QA/Available-device-performance.md)
