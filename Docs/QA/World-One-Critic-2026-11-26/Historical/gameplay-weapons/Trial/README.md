# Reproduce the stationary Level 1 equipment check

Use a disposable checkout of `alfred/character-1-final` at `48c6c53a0dfda117ef12c68b32cfe2b3732d5239`. The scene is `HavenlineLevel1/opening.tscn`. Use an isolated Godot user directory and no persistence flag.

The exact commit preloads a missing `assets/studio/hearth_trial_02.glb`. The test mounted the existing recovered `Havenline-L1-Meshy-Furnace-Trial-02.glb` at that path in the disposable copy. Its SHA-256 is `35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a`.

The baseline uses the checked-in `opening.gd`, character and tool models. Copy `qa_gameplay_capture.gd` to the project root if recording it.

For the Option A trial, copy `character_kit.gd` and `qa_gameplay_capture.gd` to the disposable project root. Copy the earlier `Winter-Welcome-Harvest.glb` to `assets/characters/WinterWelcome.glb` and use that path for the `HERO` preload in the disposable `opening.gd`. Copy the two delivered calibrated models to `assets/tools/`. The earlier fitted studio props are also preloaded by the fixture for its comparison mode. Copy them there as `axe_meshy_fit.glb` and `pickaxe_meshy_fit.glb` using the earlier rig package's `Axe-Fitted.glb` and `Pickaxe-Fitted.glb`.

Import with Godot. Run `res://qa_gameplay_capture.gd` using the default scene, camera and 1280×720 viewport. Set `HAVENLINE_QA_CAPTURE` to an absolute output directory. Use `HAVENLINE_QA_PROPS=tracked` for the exact checked-in tools or `HAVENLINE_QA_PROPS=calibrated` for the fitted trial. `HAVENLINE_QA_SHOW_GRIP=1` hides the tree prompt after initial default-HUD frames solely for inspection. The harness starts just outside reach, steers the actor into range, sends the scene's ordinary F interaction and captures the resulting equipped pose and resource response.

The kit is a stationary test fixture for the supplied harvest-only export. It does not wire full locomotion and carry animations or real gameplay saves.
