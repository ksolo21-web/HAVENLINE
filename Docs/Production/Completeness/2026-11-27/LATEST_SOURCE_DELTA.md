# Latest gameplay source delta — fixed 2f46 snapshot

**Scope:** read-only comparison of `3fad812b384335bd8ca9b5e47dc9d9557110eb4a` with `2f46e72e300a719f34ca9b0e9b718282a5a88ddd`. The prior audit remains preserved. Planning/main remains pinned to `fd2e12c8734f49cda7eb3bbf97887406bd03a704`. No runtime, motion, visual, device or task-closure approval is issued.

## Result and source binding

The newer source improves physical warehouse collection, pack visibility, the compact character roster, hostile-wolf gate clearance and a save-revision fast path. It also supplies a substantial Build 13 evidence package. These are useful improvements; the all-seven-pet and whole-game requirements remain forward work where the actual implementation has not been demonstrated.

The complete `--no-renames` comparison has **1,016 paths** (983 added, 12 deleted, 21 modified): **949** new QA-package files and **67** game paths. No files outside those two scopes changed. The two commits are `2654f5019b7212968d28600cb071bf1c231c9030` (game changes) and `2f46e72e300a719f34ca9b0e9b718282a5a88ddd` (QA package).

Build 13 binds game source **`2654f5019b7212968d28600cb071bf1c231c9030`**. Its `HavenlineLevel1` tree is byte-identical to the cutoff tree (`992ff7068090c7a98bc8be966bfba24f936d7a78`). The package reports Android version 13, 253,643,210 bytes, SHA-256 `af81181c81bc623310b00680ea4467615c6f9ffd4c21c1197bc75aff3b71bd75`. This audit read the committed receipts; it did not download or execute the APK. [Docs/QA/Camp-Field-2026-11-27/Verification/Android.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Verification/Android.json)

## Bounded findings

### LSD01 — Release/source binding

Build 13 records exact game source 2654f501, whose HavenlineLevel1 tree is byte-identical to the 2f46 cutoff; 2f46 adds the QA package. Android package hash and signing results are reported, not independently replayed or downloaded in this audit.

**Planning effect:** Use Build 13 as the newest located reported playtest receipt at this cutoff; retain Build 11 and 3fad audit as historical evidence.

**Evidence:** [Docs/QA/Camp-Field-2026-11-27/Verification/Android.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Verification/Android.json) · [Docs/QA/Camp-Field-2026-11-27/Source/Reviewed-files.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Source/Reviewed-files.json) · [Docs/QA/Camp-Field-2026-11-27/README.md](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/README.md)

### LSD02 — Physical warehouse withdrawal

Whole-shelf withdrawal replaces amount-based UI withdrawal. The actor stops at an interior stocked bay for 0.17 seconds, or taps nearby visible stock; ten raw/product/cash bays are mapped. The quantity dialog and remote withdrawal choices are removed. Existing withdrawal protection preserves collected stock for the visit. Door unloading and interior collection have distinct approach tests; stockroom movement is slowed and valid saved interior positions are retained.

**Planning effect:** Credit more direct in-world interaction and reported signed-resource shelf checks. This adds transfer usability, not a cash-consuming economic sink.

**Evidence:** [HavenlineLevel1/field_goods_exchange.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_goods_exchange.gd) · [HavenlineLevel1/field_camp_dock.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_camp_dock.gd) · [HavenlineLevel1/field_depot.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_depot.gd) · [HavenlineLevel1/field_storage_house.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_storage_house.gd) · [HavenlineLevel1/field_opening.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_opening.gd) · [HavenlineLevel1/field_conveyor_aisles.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_conveyor_aisles.gd) · [Docs/QA/Camp-Field-2026-11-27/Verification/Signed-shelf-walk.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Verification/Signed-shelf-walk.json)

### LSD03 — Cargo capacity and display

Player PACK_TOP changes from 9.8 to 1.86 and presentation fits objective/status regions and rack corners. Overflow maps to the last modeled packet while ledger quantities remain exact. No new logical player inventory cap is introduced in these diffs. Worker load still uses six raw types and a per-type 500 displayed-unit ceiling; field_survivor and settlement definitions are unchanged.

**Planning effect:** Credit compact readable cargo presentation and newly reported large-load evidence. Preserve unlimited logical player inventory. The selected CD03 requirement for unlimited logical mixed survivor cargo remains unproved in implementation; current source still has its per-type ceiling. Do not report the worker as a single-item helper.

**Evidence:** [HavenlineLevel1/field_carry.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_carry.gd) · [HavenlineLevel1/field_inventory.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_inventory.gd) · [HavenlineLevel1/field_settlement.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_settlement.gd) · [HavenlineLevel1/field_survivor.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_survivor.gd) · [Docs/QA/Camp-Field-2026-11-27/Crew/Field-notes.md](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Crew/Field-notes.md) · [Docs/QA/Camp-Field-2026-11-27/References/Independent-review.md](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/References/Independent-review.md)

### LSD04 — Survivor jobs and plot funding

Survivor routing, mixed-load work, customer priority, and job families are unchanged from 3fad. Newly committed crew receipts describe service, mixed returns, moved equipment and early construction. worker_payment still rejects Progress.LINES before using _pay_from; the two conveyors remain excluded.

**Planning effect:** Credit reported worker demonstrations. Do not mark complete all-task survivor parity, delegated spending controls, future human task families, or universal construction assistance.

**Evidence:** [HavenlineLevel1/field_survivor.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_survivor.gd) · [HavenlineLevel1/field_inventory.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_inventory.gd) · [HavenlineLevel1/field_progression.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_progression.gd) · [HavenlineLevel1/field_worksites.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_worksites.gd) · [Docs/QA/Camp-Field-2026-11-27/Crew/Field-notes.md](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Crew/Field-notes.md)

### LSD05 — Pet combat and hostile gate behavior

Owl combat and crew ownership source are byte-identical to 3fad. New receipts report actual owl talon contacts and separate roost purchases. Hostile wolves gain open-gate shoulder steering and temporary player-body collision exceptions, restored after separation/reset; jaw/tool reach remains the intended contact authority. This is hostile enemy behavior, not implementation of the friendly gray-wolf companion or all seven pets.

**Planning effect:** Credit source-level doorway accommodation and reported owl evidence; retain all-seven attack and distinct useful specialty requirements and motion/identity gates.

**Evidence:** [HavenlineLevel1/field_owl.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_owl.gd) · [HavenlineLevel1/field_crew.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_crew.gd) · [HavenlineLevel1/field_enemy.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_enemy.gd) · [HavenlineLevel1/field_encounters.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_encounters.gd) · [Docs/QA/Camp-Field-2026-11-27/Crew/Field-notes.md](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Crew/Field-notes.md)

### LSD06 — Economy and useful sinks

Earned cash already existed at 3fad. This delta makes cash shelf retrieval physical and direct. The same 13 progression offers consume wood/stone/meat; no cash, coal, slate, metal, plank or block sink is added in the reviewed source delta. Product/cash movement is not terminal consumption.

**Planning effect:** Keep the purpose/sink design requirements open for implementation. Do not describe cash as merely decorative, nor claim transfers resolve reward value.

**Evidence:** [HavenlineLevel1/field_progression.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_progression.gd) · [HavenlineLevel1/field_goods_exchange.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_goods_exchange.gd) · [HavenlineLevel1/field_settlement_loop.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_settlement_loop.gd) · [HavenlineLevel1/field_inventory.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_inventory.gd)

### LSD07 — Stakes, hearth and drop recovery

The reviewed player-hit/return/hearth sections are unchanged: camp rejects player damage; zero HP returns to safe_start and restores health, while paid hopper stock and machine work remain in the ledger. No carried resource/product/cash/plot/companion debit is added in this delta. Gradual camp healing still requires the fired hearth. Loose field-drop lifetime remains 100 played seconds in unchanged lifecycle code.

**Planning effect:** Do not imply implementation of the newly selected safer loss/recovery design or any new harsh/premium/permanent-death penalty. Continue to distinguish current expiry from future recovery policy.

**Evidence:** [HavenlineLevel1/field_opening.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_opening.gd) · [HavenlineLevel1/field_settlement_loop.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_settlement_loop.gd) · [HavenlineLevel1/field_lifecycle.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_lifecycle.gd) · [HavenlineLevel1/field_hearth_fire.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_hearth_fire.gd)

### LSD08 — Roster, rigs and save integrity

Three compact replacement character models, fitted same-name joint mapping, support-foot/hip/pack adjustments, safer unit-scale wrist rotation, and matching HUD portraits replace the older alternate-rig path. Save fast-path now compares the last verified payload revision rather than the mutable current revision. Source and declared review records credit these corrections; this audit did not inspect model pixels, complete animation cycles or execute save tests.

**Planning effect:** Credit source corrections and reported 9.9 movement reviews without granting exact-10 final visual/C5 approval.

**Evidence:** [HavenlineLevel1/field_player_wardrobe.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_player_wardrobe.gd) · [HavenlineLevel1/field_glove_clearance.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_glove_clearance.gd) · [HavenlineLevel1/gait_motor.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/gait_motor.gd) · [HavenlineLevel1/field_hud.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_hud.gd) · [HavenlineLevel1/field_save.gd](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_save.gd) · [Docs/QA/Camp-Field-2026-11-27/References/Rigs/Rig-release-gates.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/References/Rigs/Rig-release-gates.json)

### LSD09 — Project scene, orientation and device proof

project.godot and field_opening.tscn are byte-identical. Main scene remains res://field_opening.tscn, configured viewport 1280x720, canvas_items/expand and window/handheld/orientation=6. This audit does not infer measured device behavior from that enum. Build 13 explicitly marks physical Fold7 testing unmeasured; its signed shelf replay runs on desktop headless resources, not the phone.

**Planning effect:** Keep physical orientation/input/frame-time/4K and sustained device acceptance unproved.

**Evidence:** [HavenlineLevel1/project.godot](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/project.godot) · [HavenlineLevel1/field_opening.tscn](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/HavenlineLevel1/field_opening.tscn) · [Docs/QA/Camp-Field-2026-11-27/Verification/Android.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Verification/Android.json) · [Docs/QA/Camp-Field-2026-11-27/Verification/Signed-shelf-walk.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Verification/Signed-shelf-walk.json)

### LSD10 — Review thresholds and footage binding

Camp Independent-camp-review is bound to 3fad with threshold9.5 and 9.5 counter/ballista scores. The release binding records identical exhibit files and a current-source native rerun. The broader Verdict binds 2654, reports seven feature scopes at9.5, shelf/pack at9.9, and five locomotion rigs at9.9; it explicitly states that final per-dimension9.9/exact10 reapproval is separate.

**Planning effect:** Preserve raw reported passes as checkpoint evidence. Do not round, average, retag or inherit them as current task closure.

**Evidence:** [Docs/QA/Camp-Field-2026-11-27/Camp/Independent-camp-review.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Camp/Independent-camp-review.json) · [Docs/QA/Camp-Field-2026-11-27/Camp/Release-check/Pinned-source-and-results.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Camp/Release-check/Pinned-source-and-results.json) · [Docs/QA/Camp-Field-2026-11-27/References/Verdict.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/References/Verdict.json) · [Docs/QA/Camp-Field-2026-11-27/References/Independent-review.md](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/References/Independent-review.md)

### LSD11 — Reference-video custody

New reference metadata identifies exactb.mp4 and two supplemental ads by SHA256, native FPS, frames and seconds, with committed still proofs/comparison films. Full-tree path inventory finds neither locked original owner recording filename nor these three full source-film filenames. The new exactb hash differs from locked original B; it is traceability for that retrieved source, not byte custody of the locked original recording. Existing locked excerpts remain present.

**Planning effect:** Credit added provenance and excerpts. Use the bounded statement that complete originals were not located in this Git tree; do not assert all reference footage unavailable. No media was played back in this audit.

**Evidence:** [Docs/QA/Camp-Field-2026-11-27/References/Sources.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/References/Sources.json) · [Docs/Design/ReferenceVideoLock/reference-video-sources.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/Design/ReferenceVideoLock/reference-video-sources.json)

## Reported checks, with preserved limitations

| Receipt | Reported result | Boundary |
| --- | --- | --- |
| Native regression | 69 suites / 92 launches, passed | Source `2654f50`; not rerun here |
| Progression | 16 launches / 222 checks, passed | Reported isolated profiles; not rerun here |
| Signed shelf replay | 41 checks, passed | Desktop headless execution of extracted signed Android resources |
| Camp counter and ballista | 9.5 each | Filmed source `3fad812`; checkpoint below current final threshold |
| Warehouse retrieval and extreme pack visibility | 9.9 each | Reported scoped gameplay review, not universal final approval |
| C1–C4 and forester motion | 9.9 each | Reported motion review; exact-10 designated final critic gates remain |
| Physical Fold7 | Unmeasured | No 4K, sustained frame-time or hardware acceptance |

The wider Verdict explicitly labels itself a scoped playtest checkpoint and preserves the stronger final policy. Its older Character2/3/4 asset rows explicitly record their absence in the signed source; those rows do not falsely assert the removed models remain present. [Docs/QA/Camp-Field-2026-11-27/References/Verdict.json](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/References/Verdict.json)

## Identity checks actually performed

Computed exact SHA-256 and Git blob identities for **27** selected current source/configuration files and their baseline counterparts. **27/27** current hashes match the new `Source/Reviewed-files.json` entries. Hashed the **16** named receipt/narrative files read here and the original reference lock. These checks establish source and document identity only. The complete pins, runtime changed-path list and new video blob inventory are in the companion JSON.

| Source path | Changed since 3fad | Cutoff SHA-256 |
| --- | --- | --- |
| `HavenlineLevel1/field_camp_dock.gd` | Yes | `05a49dada73e6bc65f6d028db191678456d130291fa17c98ed16c9203c210cf0` |
| `HavenlineLevel1/field_carry.gd` | Yes | `7b8212c85af49d69391710081f89a0d1e6b8bc9f744a7d41bf65e0f1d49c146e` |
| `HavenlineLevel1/field_conveyor_aisles.gd` | Yes | `046848dbe4333420b57e41052e5790d6f32610980040254dbf6a6a2695dee5f3` |
| `HavenlineLevel1/field_depot.gd` | Yes | `f7ea8c1f5edc3b31d7be4f515e7d65564b12fba41a4a7f0b10c6adfe1b253cdb` |
| `HavenlineLevel1/field_encounters.gd` | Yes | `e5ee56b58e66b3178f8cc032b378193f7c7e773508b6033a5df34b6b68ffe240` |
| `HavenlineLevel1/field_enemy.gd` | Yes | `66ef417e4a594ebbd7e0a8dca8b577c482305a3aba49e158d94176fdf50a44f0` |
| `HavenlineLevel1/field_glove_clearance.gd` | Yes | `3b2c1ec61689dc172900c72d19dc28491e7643e3d7cb88fdf03ab044a7b69041` |
| `HavenlineLevel1/field_goods_exchange.gd` | Yes | `de9c8c225604445ab2f6852b0045e9775abd0c8f95174650a63bc4e583da5409` |
| `HavenlineLevel1/field_hud.gd` | Yes | `1da1e8254d30a261fc901748618cd9d2a68fa48418f273c8d49a1476ab3ceda1` |
| `HavenlineLevel1/field_opening.gd` | Yes | `fbf55a0fb457db36b0b04725192c2fb7c05a062ce7d2f8c42aa58a6408a58686` |
| `HavenlineLevel1/field_player_wardrobe.gd` | Yes | `81331b7afd0105bee24efca27a059f026816e40b898a6aa16bcdc6e68187933a` |
| `HavenlineLevel1/field_save.gd` | Yes | `a96586b538307cc45be2bdda5cb56213447e0de101b76075d5cd03091f912ec3` |
| `HavenlineLevel1/field_settlement_loop.gd` | Yes | `d72e8085687f24da6a118b0256ed36d9edf5fe7a000cc158e523c4ec6d01b91b` |
| `HavenlineLevel1/field_storage_house.gd` | Yes | `82c05042fbfe54763c0bb6f897f4a3407e39701db705fe71df2d816a473b4185` |
| `HavenlineLevel1/gait_motor.gd` | Yes | `60afa5b663929b4bdce9af4b19be24d92d722c0ad0f83af4f758d3d839bf3232` |
| `HavenlineLevel1/field_survivor.gd` | No | `c2c7d9b368ee59d2dfbb691daa6bce2a1b750494da16b346d4cb01d1bcb8696f` |
| `HavenlineLevel1/field_owl.gd` | No | `ed476d1ebc69d658aab8d66bc5f0c76f3da7168783bf5a3ba296cd0a89428376` |
| `HavenlineLevel1/field_inventory.gd` | No | `e29ceacd0006b8697731911ac69bee6c75e49dccebf012ec2fd1465f507af773` |
| `HavenlineLevel1/field_settlement.gd` | No | `29081375e0f121b3b366c0c7bcbafdd971fc237de8f6f482cabcd1129838f27e` |
| `HavenlineLevel1/field_progression.gd` | No | `395f8ef3129b107357bfad280aee07f7beec4c1de6a77c8fdabc3ef6d59f3a62` |
| `HavenlineLevel1/field_crew.gd` | No | `369296fdfe74f36e6171f9f313e7a91e359c4b6289247a98ed1a34432f6fc886` |
| `HavenlineLevel1/field_worksites.gd` | No | `2e71383ad3741770e83afefd534b9df5237a1341366d5c1e0750c525ead2b803` |
| `HavenlineLevel1/field_lifecycle.gd` | No | `60df9234222b8c25ad5f99fa9561de12a3455fd386c4bbba8b1cdce603495a7c` |
| `HavenlineLevel1/field_goods_pack.gd` | No | `4e477f221db507956829d5c4ff063b6c7a948b42aa9d6672d9305c142973e499` |
| `HavenlineLevel1/project.godot` | No | `c8a12b96cc7c2580b60d896965d77ac0c69dfeec1adcf8e2963710018b878137` |
| `HavenlineLevel1/field_opening.tscn` | No | `3c96bf2883747ed3c9d3f7a5f9736d78b9804e39720cb0e27cee1b189eeabfc5` |
| `HavenlineLevel1/field_hearth_fire.gd` | No | `4fc5b0800eda58b8560eacf8cb79d2236b4f0250e07208cee5839cd5bd2dd166` |

## Preserved audit limits

No candidate files, task states, canonical registries, historical packages, active branch or remote were changed. Git reads may retrieve objects in the existing partial clone. This note stops at the exact `2f46` cutoff. Media paths and source metadata were inspected; no new film was played back. Complete original owner recordings were not located under their locked filenames in this Git tree, while locked excerpts, new still proofs and comparison/gameplay films are present. Absence from this tree is not a claim that the owner or another service lacks the originals.

[Machine-readable audit](LATEST_SOURCE_DELTA.json)
