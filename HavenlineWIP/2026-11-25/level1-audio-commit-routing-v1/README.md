# Level 1 SFX commit-route diagnostic

This isolated observer proves only the first two cue-routing contracts, not physical audio playback or asset quality. Candidate starts from source `11c14a1c41971067c7dc97db69375f720a408f68`, archives only exact `HavenlineLevel1`, and adds two tests under its temporary `tests/` directory. A pinned existing disposable fixture subclasses the real opening; the playable scene and persistent runtime are untouched. Intent lists are local to the test and do not invoke AudioServer, emit sounds, or alter receipts. Do not run this with any user save.

- `wood_pickup:{source}`: classify one actual committed +1 wood and one appended existing source ID with unchanged empty receipt. Existing sources only; no pine regrowth extension.
- `hearth_build:center-hearth:1`: classify unchanged collected provenance, −3 and first existing authorized receipt. This is build confirmation, not a transfer, chop or furnace-loop cue.
- Require superclass commit success before observation. If the live routing path has an unexpected committed edge, the test fails. Separate in-process unique keys block repeats as defense in depth. The fixture reload does not use that publish method: it publishes already-committed visuals silently.
- Verify the same ordinary-input native route under four separate processes: unmuted first run, true cold reload of the writer's successful file, separate forced save-stage failure with an unchanged primary, and separate mute/unmute on otherwise successful gameplay. Also exercise unfunded/invalid/duplicate actions. A native resource/receipt transition, not a fabricated success callback, drives the observer.

Reproduce from this folder with `bash replay.sh <path-to-repo-with-pinned-commit>` only under the coordinator's one-at-a-time Godot functional slot. Requires no graphical renderer; uses the existing marked disposable path rule, workspace-local cache, tiny unique temporary save dirs, and a dummy audio driver.

Still required: independent routing replay; actual audio owner asset selection, provenance and mix review; event timestamps, retry semantics and duplicate rejection across real async playback; a separate ambience/music/SFX mix, verified native game/device capture and feedback accessibility. No audio was generated, selected or integrated.

Verified native replay: exit 0; 95/95 (27 write, 14 true cold, 26 save-failure, 28 mute). See evidence/*.txt, with actual checked native outcomes. The only post-run change to the runner resolved the repo argument before changing directories; gameplay/observer/test bytes unchanged.
