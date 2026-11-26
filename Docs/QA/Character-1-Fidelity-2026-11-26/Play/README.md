# Play the Character 1 review build

Extract **Havenline-Character-1-Linux-x86_64.tar.gz** from the shared Character 1 review download. Run **Play-Havenline.sh** on x86_64 Linux. Use WASD to move and the desktop wheel to zoom. The launcher keeps trial data in a dedicated havenline-character-fidelity-trial folder under your XDG data directory.

The package opens `res://field_opening.tscn` from [92d5aebe1740d0d7beebdc1f6b01ffbcf0604736](https://github.com/ksolo21-web/HAVENLINE/commit/92d5aebe1740d0d7beebdc1f6b01ffbcf0604736). The tested window moved 3.31 metres after holding D and closed through the normal window control. The signed save contained the new player position. Both frames came from the distributed binary in a fresh test profile. [Opening](Packaged-start.jpg) · [After movement](Packaged-after-movement.jpg) · [Launch receipt](Linux-launcher-and-movement.json)

The final reviewed source is [37540b6d1d6e0657dd6776db136a46534e6a66d5](https://github.com/ksolo21-web/HAVENLINE/commit/37540b6d1d6e0657dd6776db136a46534e6a66d5). Its two changes are excluded QA scripts. I checked every file in the project’s Git tree and checked the exclusions inside the delivered executable. [Source compatibility](Final-source-compatibility.json)

The first launch test used a bare X server whose window did not advertise a valid close protocol. Movement rendered, but that harness timed out on close. The successful test used an isolated Xfce window manager with WM_DELETE_WINDOW advertised by the game.

The compiled coat texture, bindings, body mesh, animation inventory, carrier behavior and all 18 measured load positions matched the frozen editor project. [Packed asset verification](Packaged-asset-verification.json) · [Archive checksum](Package-SHA256SUMS.txt)

[Rebuild from the reviewed source](../Source/README.md)
