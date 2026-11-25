# Detached native Character 1 socket semantics

The frozen stock Character1.glb is the one used by the pinned 11c14a1c41971067c7dc97db69375f720a408f68 playable opening, Git blob 1145d7820892f4f95fdecc4246ed9b2f64578c45 and SHA-256 checked by the runner. This uses stock idle/walk/run from that GLB. It does not launch the opening, import the PR asset, install edits, render, or establish fit, contact, or gameplay readiness.

The test reproduces the exact PR108 `_socket` attachment operations and offsets for both hand bones and Spine02, then checks against independently evaluated bone world frames after nine sampled native animation phases. A parallel child marker under a bone-follow node is the positive control. Two-run concerns: Godot must report the correct executable version; the test must achieve three recognized clips and actual pose variation. Do not infer actual PR world-space offset magnitudes or a shipping fix from this stock-derived engine witness.

Run with `./run.sh <exact stock Character1.glb> <existing Godot headless lease>` on Godot 4.7.2. No user save is opened. The runner uses a disposable headless project and HOME/XDG/TMP and will refuse an occupied lease. Do not archive source GLB bytes.

## Observed

Godot 4.7.2 official ed1daf0bf: 83/83 checks with no failures across all nine evaluated baseline phases. Exact stock socket assignment on the attachment itself was overwritten on every phase: both palm markers and the sheath ended exactly at the associated live bone origin, losing approximately 18.760, 15.341 and 118.744 mm respectively in this probe's stock GLB dimensions under a translated and rotated parent. A separate child marker preserved the offset to exact reported world-coordinate agreement in every measured phase. Maximum consecutive wrist-origin changes were 190.3 and 224.6 mm, verifying that the sampled poses actually changed. See `run.log`. This is not an independently reviewed candidate release or testing of the PR108 mesh, but it is a native control for the operation used in its source.
