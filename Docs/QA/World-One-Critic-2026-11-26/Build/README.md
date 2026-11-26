# Havenline World One review builds

Both packages launch `res://field_opening.tscn` from commit `949af6f0916839ac702725cbd7a0a7c3f1033a5a`. The source manifest verifies 237 project files against Git. The native Linux executable and the arm64 Android APK were exported with Godot 4.7.2.stable.official.ed1daf0bf.

The shared Havenline review download contains both prebuilt packages in critic-95/Build. The rebuild helper here extracts the exact Git source.

## Play

Linux x86_64. Extract the Linux archive from the shared review download, then open `Play-Havenline-Review.sh`. The launcher gives this build a separate save directory under `$XDG_DATA_HOME/havenline-critic-trial` or the default `~/.local/share/havenline-critic-trial`.

Android arm64. The debug APK from the same download has application ID `com.havenline.criticreview`. APK signing, zip alignment, launcher activity, architecture and resource mappings were verified. Installation, touch input and performance on a physical Android device remain untested.

## Verification

The Linux archive’s executable digest matches the one that opened a native game window. A separate run unpacked it, launched the supplied shell script, sent movement input, verified 1.35 m of saved travel, and closed it through the window system. That run reported 0 leak warnings. The embedded resource pack passed 20 checks, including opening save initialization, physical mineral banks, six stock balances and both storehouse door states.

[Package checksums](./Package-SHA256SUMS.txt) · [Full packaging and renderer receipt](./Package-verification.json) · [Native launcher, input and save receipt](./Launcher/Linux-launcher-and-movement.json) · [Source manifest](./Reviewed-files.json).

To reconstruct this exact game project from a Git checkout that contains the commit, run `python prepare.py /path/to/HAVENLINE /new/path/WorldOne` from this folder. Import that directory using the Godot version above.

The first direct native window close exceeded the 60-second probe timeout under software rendering. A later launcher probe waited for the actual visible gameplay frame, performed movement, verified the saved position and closed successfully. The runnable version of that probe is under Launcher/qa-launcher.py. The renderer was llvmpipe, and the only warning in the successful launch concerned unsupported V-Sync control.
