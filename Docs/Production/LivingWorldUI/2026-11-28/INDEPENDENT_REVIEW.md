# Independent review — Aurora and living-world task plan

**Verdict: PASS, 10/10 for the bounded documentation scope. All 12 mandatory review dimensions pass.** No runtime, native layout, motion, audio, physical-device, APK, release, merge or main-integration approval is granted. Runtime score is unverified (`null`).

Reviewer: `/root/requirements_critic`, independent of the builder. Parent: `0a7587cf3e89397a760be4b4c606c54ad09d0e02`. This review binds the frozen working-tree payload bytes below; publication is a separate expected-head and remote-readback gate.

## Checks and scores

| Dimension | Score | Actual result |
|---|---:|---|
| D01 — Owner decisions and authority | 10.0 | All requested additions are present. Aurora remains selected; visible joystick is allowed and movement may start away from it. Earlier no-stick artwork is historical where conflicting. Authored roles, species, time bands, feedback placement and settings are distinguished from owner quotations. Latest Build13 casualty/repurchase, breach, Level 1 equipment replacement and unresolved loss terms are preserved. |
| D02 — Exact task mapping and unchanged lifecycle | 10.0 | 30 unique requirements map to 34 real parent task IDs. Every recorded title, dependency list, historical state and reverse requirement list matches the canonical parent graph; every new-scope approval remains NOT_GRANTED. T71–T80 remain undefined. |
| D03 — Aurora, touch-anywhere controls and input evidence | 10.0 | UI01/UI02/UI05/UI06 require matching themes, movement throughout UI-unclaimed gameplay including over objects, stable pointer ownership, cancellation and fresh input. Joystick feedback may move and must stay inside safe bounds without moving the logical origin. Historical visibility prohibition is withdrawn. The current source observation is qualified and its 10 identities verified; it does not certify an APK. |
| D04 — Enemy variety and concrete counterplay | 10.0 | The six selected hostile families are retained. Eight distinct reserve candidates have preserved render identities and behavior/counterplay beyond recolor or HP. Fourteen is explicitly conditional planned coverage, not a shipped count or cap. Machine, hostile animal, prey and pet identities remain separate. |
| D05 — Passive winter prey and conserved meat | 10.0 | Six passive prey entries include retained Tundra Stag and five explicit new asset gaps. All remain nonaggressive at night and cannot retaliate with quills. Random encounters respect habitat/progression/route eligibility; essential meat is attainable. Defeat, pickup, carry, storage, applicable processing/service and payment are conserved; survivors can hunt and return meat. |
| D06 — Day/night ecology, aggression and continuity | 10.0 | Day and night contain actual different prey and hostile memberships; overlap preserves food access. Night increases valid pressure while retaining readable attacks and escape/recovery. UI appearance cannot change world time, RNG or rewards. Active actors, jobs, drops, saved clock and encounter state survive transitions. |
| D07 — Target priorities, raid warning and recovery | 10.0 | Player/pet priority, camp-assault targeting, attacker-specific survivor retaliation and both-player-and-pets-too-far exceptions remain explicit. Night does not broaden eligibility. Every scheduled raid retains its origin and 300 active-play seconds of named-camp warning before damage; ambient relabeling cannot bypass it. Raid intervals and unresolved casualty accounting remain open. |
| D08 — All pets and prior map/display obligations | 10.0 | Guardian dog, gray wolf, fox, owl, male lion, white tiger and brown bear retain attacks and useful specialties, with multiple useful pets/survivors and no added slot cap. The prior 21-row pet/map/display contract remains byte-identical in the index and has no working-tree diff. UI03/UI04 carry forward map knowledge, scouting value and actual-window adaptation obligations. |
| D09 — Natural decisions and complete motion evidence | 10.0 | MO01–MO06 cover purpose, stable productive jobs, individual/herd variation, avoidance, yielding, routes, gaits, foot/hoof/paw planting, toe/knee/hock mechanics, weight, loaded/tool-ready poses and full lifecycle transitions. Actual normal/slow multi-angle playback, contact closeups and audio listening are required later. Stills, a walk clip or a schema cannot approve motion. |
| D10 — Current campaign and dependency-aware delivery | 10.0 | The plan preserves ten worlds of fifty local levels and World 1 first, without all actors at Level 1 or invented unlocks. P-stage sequencing is explicitly separate from the unchanged task DAG. The full T54/T53 and downstream acceptance dependency mismatch is disclosed, with a scoped World 1 route required before implementation acceptance. |
| D11 — Historical/source/reference preservation and bounded diff | 10.0 | Only five entrypoints plus the new planning/evidence package change. Four entrypoint bodies recover byte-identically after header removal; the build plan also has exactly two disclosed product-prose replacements. Prior contracts, graph, registry, selector, policies, receipts, assets and workflows remain unchanged. Stronger 9.9/exact-10 reference gates remain mandatory for future runtime work. |
| D12 — Documentation consistency and honest completion boundary | 10.0 | All 30 full Markdown rows match their JSON text, task lists and acceptance text. The independently executed validator passes 41 document checks. Nineteen parent-source bindings and ten input-source identities match exact bytes. The one metadata defect is repaired and retested. All 30 runtime obligations remain UNTESTED_FOR_NEW_RUNTIME_SCOPE; publication and merge are not certified by this review. |

## Defect, repair and retest

The review found one documentation defect: `forward_consumer_reconciliation[0]` described already-updated build-plan prose but labeled it unimplemented. The builder changed it to `DOCUMENTATION_UPDATED_RUNTIME_CONSUMPTION_PENDING`; the remaining 11 consumers retain their future-work status. The validator now distinguishes these cases. I read the repair and reran the checker: **41/41 document checks pass**. No known mandatory documentation defect remains.

The owner changed the input direction during review. I reopened that criterion and reviewed the final visible-allowed, touch-anywhere candidate. The earlier no-joystick concept package remains preserved as historical art where conflicting. No final pass was issued against the earlier core hashes in this task.

## Evidence actually inspected

I read the actual five-entrypoint diff, both complete plan formats, source bindings, input-source audit, checkpoint and validator. All 30 full Markdown requirement rows match JSON requirement text, task lists and acceptance text. All 34 exact canonical task mappings and reverse requirement lists match the parent graph. I recomputed 19 parent-source bindings and 10 current-input source identities. The prior 21-row pet/map/display contract remains byte-identical in the Git index with no working-tree diff. Four entrypoint bodies recover byte-identically after removing only the new header; the build-plan body additionally has the two disclosed control/campaign prose replacements.

I independently fetched/read and recomputed both blob and SHA-256 identities for the pinned Build13 owner decisions and the 10×50 world contract. The newer casualty, targeting and warning decisions control their explicit conflicts; old sanctuary/free-revival clauses are not silently revived. The source authority is precisely bounded and unresolved loss terms remain open.

For the current-input note, I independently read the pinned touch-origin, visible feedback, pinch, inherited UI routing, field routing, dock handling and cancellation excerpts. The code centers active feedback at `touch_origin` without an edge clamp; the audit accurately qualifies the UI/multitouch and lifecycle coverage. These are source observations. I did not execute the existing test definitions, run an APK or operate a device.

The first supplementary reviewer command tried to open a preserved file omitted from this sparse checkout and raised `FileNotFoundError`. I confirmed its `S` index status, changed the inspection to exact index/parent Git bytes and reran it successfully. This was a reviewer read-path correction; the candidate was not changed to make it pass.

## Preserved requirements and future evidence

All seven attacking/useful pet species, simultaneous pets/survivors, survivor hunting, the minimap/larger-map and actual-window adaptation obligations remain. Six selected hostile families are retained; eight reserve roles and five new passive-prey assets are explicitly proposed future work. Six passive prey entries remain nonaggressive at night. Distinct day/night memberships and stronger night pressure do not alter hostile target eligibility, erase actor/loot state, or bypass the full five-active-minute raid warning. Aurora Dark is independent of world night.

The plan requires natural AI decisions and full species/load-specific motion evidence, including feet/toes/knees, contacts, turns, starts/stops, work, complete cycles, transitions, useful angles and actual audio listening. The stricter 9.9 reference and exact-10 gates remain intact. This review assigns 10 only to preservation of those documentation obligations; no visual or motion match score is assigned.

Ten worlds × fifty local levels and World 1 first remain explicit. The proposed work stages do not alter the task DAG. Formal World 1 activation/acceptance reconciliation and updates to forward packet/checker consumers remain required. No runtime source, asset, workflow, dependency edge, ownership selector or task lifecycle state changes are included.

## Frozen payload identities

| Path | SHA-256 |
|---|---|
| `AGENTS.md` | `eb594e86adc467989ea149006be5d39d5c58c755645c9b371faa465ec85f9da7` |
| `BUILD_GAME.md` | `ed6605171050350168bffe21b145b96761b961fbc6cae83795370f3f6a093333` |
| `Docs/Production/COMPLETENESS_STANDARD.md` | `130251fa72b2cfd9e7aee21ccb2cae06152049972d122ea05b5e89d09ace1f3a` |
| `Docs/Production/HAVENLINE_BUILD_PLAN_V2.md` | `f7e6811b94544b733d6a7c69f777e12ddacbf17e039a7c9d44d7cc0196815388` |
| `Docs/Production/LIVING_WORLD_UI_PLAN.json` | `8112aae30e001abe4f70f7930bece791933507835e5aa46a765b21eb1033164d` |
| `Docs/Production/LIVING_WORLD_UI_PLAN.md` | `a1a2287563aa17b4a4d12dcc42240a9f7d29e51a68a39a7a9f269e27fa3f988a` |
| `Docs/Production/LivingWorldUI/2026-11-28/CHECKPOINT.json` | `ae66fe944caae7093195802e3e83bbc722e07b80c9b0e4713e02da15e4b38d92` |
| `Docs/Production/LivingWorldUI/2026-11-28/CURRENT_INPUT_SOURCE_AUDIT.json` | `c7e9c7c88472b1413f448717e010f895bc197c8ccb7250d43d715d34641d30b6` |
| `Docs/Production/LivingWorldUI/2026-11-28/SOURCE_BINDINGS.json` | `9e5e82af29757c66292f469e5f3723b33a34ae4a3437919c1a6f63fc5b8787d2` |
| `Docs/Production/LivingWorldUI/2026-11-28/validate_plan.py` | `cb860df6c9cfd051d00d4e66c4022a9031b3b7eea14db0d484cb150c9b777e69` |
| `REPOSITORY_INDEX.md` | `0beec0b89af39808ac22b3a2fe21c1b78569fe75bfcde275b2d0a673981fb0d4` |

The review files are excluded from their own manifest. `VALIDATION.json` is the output of the independently rerun checker; a later identical run can change only its path inventory when these reports exist. Its script and the frozen core are bound above. Full byte sizes, Git blob identities, check names and source identities are in `INDEPENDENT_REVIEW.json`.

## Completion boundary and next gate

Documentation is complete against the reviewed scope. The current input audit still identifies edge-safe feedback and UI ownership gaps, and all 30 runtime rows remain `UNTESTED_FOR_NEW_RUNTIME_SCOPE`. The new themes, wildlife, hostile roles, day/night behavior, animation, audio and physical-device behavior are not approved here. Numerical tuning, exact artwork approval and unresolved casualty/furnace decisions retain their recorded status.

Publication is pending: extend the authorized existing draft PR109 branch with the exact reviewed content, then verify its remote commit/tree/bytes and draft PR base/head separately. This review performs no remote mutation and does not certify merge readiness or main integration. Core-content changes reopen this review.
