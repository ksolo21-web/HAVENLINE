# Reproduce the Level 1 trial

The manifest pins the Git commit and the SHA-256 of each gameplay and test input. Godot 4.7.2 runs the ordinary entry point `res://field_opening.tscn`. From this evidence directory, extract a clean project from the Havenline checkout.

    python3 prepare.py /path/to/HAVENLINE /new/path/level1
    godot --headless --editor --path /new/path/level1 --import
    XDG_DATA_HOME="$(mktemp -d)" godot --path /new/path/level1

The third command creates a fresh Linux test profile. The extraction helper also reconstructs the stored furnace and the fitted axe’s original texture files.

## Build the trial packages

With Godot 4.7.2 and its export templates installed, run the Linux export from the verified project. Place the included launcher beside the executable. It creates a dedicated data directory for the trial.

    mkdir -p /new/path/build
    godot --headless --path /new/path/level1 --export-release 'Linux World Review' /new/path/build/Havenline-Level-1.x86_64
    cp Play-Havenline.sh /new/path/build/
    chmod +x /new/path/build/Play-Havenline.sh

For the Android playtest, configure Godot's Android SDK, JDK and debug keystore, then export the ARM64 package. Its application ID is `com.havenline.levelonesettlementtrial`.

    godot --headless --path /new/path/level1 --export-debug 'Android World Review' /new/path/build/Havenline-Level-1-Android-arm64-debug.apk
