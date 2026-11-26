# Play the Havenline Level 1 trial

The shared playtest download contains the Linux archive and Android APK named below. The GitHub evidence folder contains the checksums and build instructions. [Rebuild both from the reviewed source](../Source/README.md)

## Linux

Download and extract the archive into its own folder. Launch `Play-Havenline.sh` from that folder. It opens the snowy field at Level 1 with an isolated settlement-trial save. Use WASD or the arrow keys to move. [SHA-256 checksum](Package-SHA256SUMS.txt)

```sh
mkdir -p havenline-level1
tar -xzf Havenline-Level-1-Linux-x86_64.tar.gz -C havenline-level1
./havenline-level1/Play-Havenline.sh
```

The package runs Godot 4.7.2 and opens `res://field_opening.tscn` from source commit `a0e83999064b666145a884eed767f68d4d127688`. Its default save is under `$XDG_DATA_HOME/havenline-level1-settlement-trial/Havenline-Level-1-Settlement-Trial/world-one/`. On a default Linux desktop, `$XDG_DATA_HOME` resolves to `~/.local/share`.

All 23 source-to-package checks passed, including the corrected north counter, cooker, workshop machinery, survivor, owl, helper axe mipmaps, recipes and audio. The extracted launcher opened an Xfce game window, accepted physical D-key input, saved a 1.72-metre move and exited normally on window close. The test used a software graphics driver at 704 × 396. [Asset comparison and scene receipt](Packaged-Level-1-verification.json) · [Launch and save receipt](Linux-launcher-and-movement.json) · [Starting frame](Packaged-start.jpg) · [Frame after movement](Packaged-after-movement.jpg)

## Android ARM64

The shared package is `Havenline-Level-1-Android-arm64-debug.apk`. Its dedicated application ID is `com.havenline.levelonesettlementtrial`. The signed trial APK passed Android signature, alignment, architecture, launcher and ZIP integrity checks. The archive includes the survivor, owl, workstations, counter and settlement code. A physical phone test is outstanding. [Android package results](Android-package.json)
