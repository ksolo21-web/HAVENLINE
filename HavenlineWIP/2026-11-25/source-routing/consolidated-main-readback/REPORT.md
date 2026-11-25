# Read-only source routing after remote consolidation

- GitHub reports default branch name `main`; pinned main `b80c61f13ba31bb0940792dd47976a8e2878dbf5` is the consolidation commit (root tree `598ca77bd0635e418e7eced4db6384658f9687d4`), not the old August initializer. GitHub compare `b80c61f…2e194f5` reports diverged: common base `2706cd6b0c6bfa7b4e8ad31d792a365aaf456d08`, replacement 171 ahead / one behind at that exact pair only.
- Latest replacement ref observed `2e194f592055dafa50ea2cd3122aabd2763c040e` and prior `b27670b00d9f8464ded40711ec0814a32416dd9b` have identical `HavenlineLevel1` tree `347841354c748b129724e2f2513969db92719e1d`. Main's corresponding tree is `f836624d97f1a92199f2d9da752793476bd6d67a`. Compared untruncated remote trees: 105 main vs 128 replacement L1 blobs, 23 replacement-only, 3 changed, zero main-only. Exact diff below.
- **Runtime difference:** main's integrated preview still builds the starter tree without regrowth. Replacement explicitly opts in only in `previews/integrated_opening.gd` (`resource_tree.build(CONIFERS[0], true)`). Its `resource_tree.gd` hides the model after credited fall, runs a five-second countdown, resets strike/timers/pose and returns the visible tree to rooted. Its `opening.gd` records the original starter-credit state and acknowledges repeat visual falls without adding starter wood twice. Main lacks these behaviors as a group, so do not cherry-pick a single file and claim parity. Shared/default scene does not opt in. Replacement integrated preview also has explicit optional loose-wood contrast and timber gate-pair preview flags, hooks and supporting art; main retains technical gates/default art and no hooks. These are optional review paths, not production approval.
- **Not active progression:** replacement-only service guard, separate cast/fishing preview and their tests/docs do not amount to integrated Level 1 gameplay, and fish remains excluded by current owner scope. Dry roundtrip tests/docs and WIP render-/device-quality holds remain distinct from product approval. Do not restore these candidates blindly as runtime parity.
- **Navigation and recovery:** use consolidated [repository index](https://github.com/ksolo21-web/HAVENLINE/blob/b80c61f13ba31bb0940792dd47976a8e2878dbf5/REPOSITORY_INDEX.md) and [task custody](https://github.com/ksolo21-web/HAVENLINE/blob/b80c61f13ba31bb0940792dd47976a8e2878dbf5/Docs/RepositoryArchive/Plans/TASK_CUSTODY_T01_T80.md) for plans. Its canonical build-plan blob `74a0122eb009fa19904ac1caf0473ecf94f792b7` matches already pinned canonical `f74a84a…`. The older copy on the replacement branch differs. Consolidation README says authentic T01–T70 and explicitly marks T71–T80 SOURCE_NOT_FOUND; workflow source archive exists but no operational `.github/workflows/` blobs on this main pin. Main snapshot alone is not runtime approval or a replacement for open PR lanes. Preserve replacement branch, test pin `11c14a1c41971067c7dc97db69375f720a408f68` (L1 tree `d764a05246cbff96983aa27af17e2e919a946ae0`), and separate PR/archive refs. Use that exact test pin and opt-in integrated scene for reproducible L1; use developer replacement branch for isolated later WIP, check tip per change. No current code should be rebased onto main and no merges, deletions, changes to workflows, consolidation changes, or releases are warranted by this log.

| Path | Consolidated main blob | Replacement blob |
|---|---|---|
| `HavenlineLevel1/customer/first_service_guard.gd` | absent | `383841d1de20fa10dc1a880432f49d501b8a419f` |
| `HavenlineLevel1/docs/CAST_INPUT_PREVIEW_VERIFICATION.md` | absent | `ef1fb675ee1f9cc453ea7b927bd23f82b89c1ec8` |
| `HavenlineLevel1/docs/FIRST_SERVICE_GUARD_VERIFICATION.md` | absent | `21e37bf968a0748e684b6afe007dfc721324ac16` |
| `HavenlineLevel1/docs/LEVEL1_DEV_CHECKPOINT_2026-11-25.md` | absent | `407b34fef3c866fd69f6045b9b4b041032c70de1` |
| `HavenlineLevel1/docs/LOOSE_WOOD_RENDER_VERIFICATION.md` | absent | `980447667c230b6401a25475089f3d66884717d5` |
| `HavenlineLevel1/docs/MANUAL_CAST_INTENT_VERIFICATION.md` | absent | `f6ac81799375c18aa64020e4bec2a5c2f950877d` |
| `HavenlineLevel1/docs/TIMBER_GATE_PREVIEW_VERIFICATION.md` | absent | `55e557d11f26440a60b55a6a83237da536e69a62` |
| `HavenlineLevel1/opening.gd` | `3213c9fa3f8ee187ebdbfc9ec75dc519c26f84b6` | `8de9499b0a48d920516d3b07c889cfb8a0808038` |
| `HavenlineLevel1/previews/gate_pair_study/GateLeaf.mtl` | absent | `1725ef2f54495cf37fd7217cce45aa963d5337f8` |
| `HavenlineLevel1/previews/gate_pair_study/GateLeaf.obj` | absent | `4ca5906956a77d3e3414eedcb6de5ae14c21dbf2` |
| `HavenlineLevel1/previews/gate_pair_study/GateLeaf_Right.obj` | absent | `f17dea761faacc1a41e65151f31822d99cd532ed` |
| `HavenlineLevel1/previews/gate_pair_study/gate_art_review.gd` | absent | `a7ad614d72ed34bd7460d3c2523480d1cb0efc34` |
| `HavenlineLevel1/previews/gate_pair_study/gate_pair_mount.gd` | absent | `b576fd806043ee8e5c59214059069539c36835aa` |
| `HavenlineLevel1/previews/integrated_opening.gd` | `91a845fdaced38cd1408538a37e7b9f47e3b98c0` | `cc54fb10b5270f513baa2c3743d4879e29ebb41a` |
| `HavenlineLevel1/previews/loose_wood_contrast.gd` | absent | `98c4f3d0355ae52e5adf0423db16b0d23a58de42` |
| `HavenlineLevel1/previews/manual_cast_input_preview.gd` | absent | `824bba2861ce427c5088b5b5487a6b08f969e3cf` |
| `HavenlineLevel1/previews/manual_cast_input_preview.tscn` | absent | `0bbaec02e10bcc741835ec5b35d232d1e354faef` |
| `HavenlineLevel1/previews/manual_fishing_intent.gd` | absent | `9d5ea7e19466703ab0ac85a776c2e91bd11b75af` |
| `HavenlineLevel1/resource_tree.gd` | `1bba66fa0da9840877a5c9c3691fb121404b2c49` | `a0a846551bb574728cedcd3b76bfe785cd0b5192` |
| `HavenlineLevel1/tests/test_field_dry_roundtrip.gd` | absent | `39ba77640cf3d8f4a9eab65c837faddcf619a7c0` |
| `HavenlineLevel1/tests/test_first_service_guard.gd` | absent | `e15c2b8f9b597404d649b4ab81b98424324841cd` |
| `HavenlineLevel1/tests/test_gate_art_optin.gd` | absent | `b98a4174ca67d1419bdf6736ddd5dff26b82199b` |
| `HavenlineLevel1/tests/test_integrated_tree_regrowth.gd` | absent | `8dd73a0192cd01b262c4550e72ab41f0dd64d61e` |
| `HavenlineLevel1/tests/test_loose_wood_contrast.gd` | absent | `de8846b96aeb87fa50120fde3b64e360d1e9b25c` |
| `HavenlineLevel1/tests/test_manual_cast_input_preview.gd` | absent | `825a767e842f5e08766836b1921131d3d9b5039e` |
| `HavenlineLevel1/tests/test_manual_fishing_intent.gd` | absent | `45b8e691b86961ab853319b92ca5793fc41d838c` |
