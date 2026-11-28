# Havenline — pet combos, navigation map and automatic screen fit

Version 1 · Owner direction: November 28, 2026 · **Required forward scope; gameplay implementation and device evidence remain unverified.**

## Authority and scope

Kaleb requires every pet to have one attack combo appropriate to that pet, including all other pets; a minimap that opens into a larger map for navigation and finding important things; and automatic game/UI fitting to the user's phone size in any orientation without cutoff. These three outcomes are owner requirements. The concrete combo choreography, marker organization and layout behavior below are authored implementation specifications for those outcomes, not completed animations or separately approved numerical balancing.

Read this addendum and its [machine-readable contract](PET_COMBOS_MAP_DISPLAY.json) before the older count/orientation-specific plan. **Portrait and landscape support now supersede the landscape-only restriction** in the earlier CD10 decision and `selected_policy.orientation` in `WHOLE_GAME_COMPLETENESS.json`, the landscape paragraph in `COMPLETENESS_STANDARD.md`, older AGENTS instructions, and the retained landscape field of the separate `GAMEPLAY_RULES_CONTRACT.json` where that later branch is consumed. Historical records and their original scopes stay intact. A passing historical landscape-only checker cannot approve this added scope. The existing packet/checker automation has not been extended by this documentation change; it must include this contract before it can certify a changed candidate.

Preserve the current **10 worlds × 50 local levels**, World 1 first, multiple simultaneously useful pets and survivors, species-specific useful jobs, simple automatic combat, selected art references and normal gameplay camera scale. No pet unlock level, team cap, damage value, cooldown or purchase price is newly fixed here. Seven species does not mean seven simultaneous expedition slots or all seven unlocked in World 1. The earlier staged three-pet/two-escort policy remains a reconciliation input, not measured capacity. Earlier 100-level prose remains historical where it conflicts with the newer world plan.

This change adds requirements and task responsibilities. It changes no production runtime, live gameplay owner, task state, dependency edge, workflow, asset, historical receipt or gameplay-source selector. The observed Codex gameplay head is recorded for resumption only; it was not run or approved here.

## One complete combo for each of the seven pets

Each pet automatically executes its sequence when an eligible target and safe engagement space exist under the existing targeting rules. A new manual combo-button system is unnecessary. Each sequence includes anticipation, committed movement, distinct strikes, a miss/cancel path, recovery and a return to the pet's useful job. Movement phases are not additional damage events unless separately registered and reviewed.

| Task / pet | Authored combo | Retained useful role |
|---|---|---|
| **T24 — Guardian dog** | Intercepting lunge → bite → grounded pivot → second bite → return to guard. | Escort and protect allies; suitable light retrieval. |
| **T25 — Gray wolf** | Pursuit → forward pounce → bite → lateral reposition → follow-up bite → recover. | Track and pursue eligible prey/targets within its safe leash. |
| **T26 — Fox** | Side dart → quick bite → springing reposition → pounce-and-nip → quick disengage. | Agile ground scouting and suitable light retrieval. |
| **T27 — Owl** | Take off when grounded → bank → diving talon strike → clear-air turn → second talon pass → climb and recover. | Aerial scouting, warnings and suitable retrieval. |
| **T28 — Male lion** | Short charge → heavy pounce → forepaw strike → bite-and-release → weighted recovery. | Hold an exposed approach and protect working allies. |
| **T29 — White tiger** | Low approach → lateral pounce → alternating claw strikes → bite-and-release → low reset. | Reachable flanking, ambush and interception. |
| **T30 — Brown bear** | Heavy rush → broad forepaw swipe → opposite forepaw strike → short bite → full weighted reset. | Suitable heavy hauling and registered obstacle work. |

These retain the exact seven friendly species and existing attack-profile IDs. Domestic cats stay removed; hostile animal variants are not additional pets. Future approved pets must receive a fitting combo before acceptance. The fox and owl must do actual useful combat damage as well as scouting. Bear obstacle work does not silently grant universal mining or tree harvesting. Existing tools, resource permissions and specialty rules remain in force.

### Combat and animation requirements

- **PC01 — Complete roster:** all seven species have their own combo definition, animation binding and useful specialty. Cosmetic variants use compatible species behavior without silently replacing the roster.
- **PC02 — Automatic, distinctive action:** separate posture, rhythm, anticipation and recovery fit each species. No human punching, identical retimed motion for every animal, orbiting damage object or teleporting to finish a combo. Upgrades preserve this identity while adding their separately defined, worthwhile capability/appearance gains.
- **PC03 — Authoritative contacts:** every intended strike has its own contact group. The contact ledger applies each allowed hit once per attack instance, group and target; the damage window must match actual reach and contact. Multiple hitboxes cannot multiply one strike. Misses do no damage. Defeat/reward commits happen once even with several attackers.
- **PC04 — Safe interruption:** revalidate target identity, hostility, life state, reach, route, sanctuary/attack domains and recall before each strike. On loss, obstruction, stun/down or recall, cancel safely or finish only the currently valid committed contact; do not deliver later damage to an invalid target. A new target requires a new validated engagement. Save/reload, pause/resume and team switching cannot replay consumed hits or erase recovery.
- **PC05 — Useful concurrent pets:** multiple pets and survivors act together with shared engagement-space rules, stable priorities and safe paths. Secure mouth/talon cargo before incompatible strikes; never delete or duplicate cargo. Resume a valid job after combat. Prevent path deadlocks and unavoidable stun/control loops. Numerical balance remains to be tested.
- **PC06 — Full evidence:** review full cycles, misses, interruptions and transitions at normal speed and in slow playback, from front/rear/left/right/three-quarter, gameplay camera and contact closeups. Inspect feet/toes/knees, jaws, shoulders, tails, mane, wings and equipment clipping. Owl proof includes flight, takeoff, banking, each talon contact, wing clearance and landing. Listen to attack/impact/recovery audio and check equivalent visible feedback when muted. Still images do not approve motion.

## Minimap that opens into a useful larger map

The compact HUD map gives position, heading and nearby known landmarks at a glance. Tapping it opens a larger map that can pan, zoom, recenter and select a destination. The default authored presentation is north-up with a clear player-heading arrow in both views; any future rotation option must keep labels upright and transformations consistent. The larger map uses the available safe screen area with a readable legend and a reachable Close control; Android Back closes it before leaving play.

- **NM01 — Open and close:** one obvious tap opens the map. Closing returns to the same game state and appropriate camera. Map touches, drags and pinches are consumed by the map and cannot move the player or trigger world purchases/interactions underneath it.
- **NM02 — Find important things:** when present in the current world, show camp/home and furnace; storage house; machines and counters; gates, build/upgrade sites; vehicles and garage; useful resource areas; objectives, rescues and survivors; active pets; known threats; and recoverable cargo. Marker registration belongs to the feature introducing the object. No placeholder destination is advertised as usable.
- **NM03 — Readable live markers:** distinguish categories with shape/icon plus label, not color alone. Filter or cluster busy areas and reveal an individual item on selection. Track stable world/object/actor identities and authoritative positions. Update movement, resource depletion/regrowth, construction, recall/down/recovery and removal without ghost or duplicate markers. All seven pet species remain identifiable when active.
- **NM04 — Navigation:** select, replace or clear a waypoint; show useful direction/distance and arrival feedback. Directions must respect traversable connections, gates and world locks. A straight bearing is labeled as direction, never passed off as a valid route. An unreachable destination gives a clear unavailable/blocked reason; it does not guide through fences, water or unopened gates. This does not add automatic walking or teleportation.
- **NM05 — Truthful knowledge:** distinguish known/unavailable/locked/depleted/dangerous destinations. Reveal only information the game legitimately knows; hidden enemies and undiscovered loot do not become an omniscient overlay that removes owl/fox scouting value. A new fog-of-war or reveal-everything system is not implicitly approved.
- **NM06 — Lifecycle and map time:** preserve valid selection, filters and waypoint state across closing, resizing and save/reload. Clearly update or invalidate a moved, removed or other-world destination. The expanded map follows the current explicit modal pause contract: the implementing owner must bind and test that exact policy before integration. Map opening cannot reset combat, farm pause/resume rewards, silently grant invulnerability or alter timer/value rules. Existing app background behavior remains intact.
- **NM07 — World scope:** ship real authored World 1 map data with World 1. Use stable world IDs and local-level/progression state compatible with ten worlds of fifty local levels; this does not require 500 separate maps or decide global UI numbering. Later world owners provide their own real POIs and connections without blocking the first usable World 1 map.

## Automatic screen, orientation and foldable fit

**DS01 — Measure the current app window.** Read current usable dimensions, aspect ratio, scaling/density information and applicable safe insets/cutouts. Recalculate at startup and when the actual window changes. A phone model list or a single launch-time size measurement is insufficient.

**DS02 — Every delivered orientation.** Support portrait and both landscape rotations; support inverted portrait where the device/OS delivers it. Respect the user's system rotation preference. Keep project/export settings and runtime layout rules consistent. Record unsupported OS configurations honestly; do not claim they were tested or try to bypass the system rotation lock.

**DS03 — Safe and readable UI.** Keep HUD text, touch controls, minimap, dialogs, confirmations, notifications and map controls inside usable regions, clear of notches, camera holes, rounded corners, status/navigation/task bars and relevant gesture zones. Use distinct compact portrait, wide landscape and large-screen arrangements. Reflow or deliberately scroll secondary information while retaining reachable controls; shrinking everything until it is unreadable fails.

**DS04 — Correct game framing.** Fit the complete render viewport without stretching or cropping the framebuffer. Adapt camera composition so the player, action/target cues and immediate routes remain readable at the approved gameplay scale. Respect the existing ban on extreme gameplay zoom. The larger world naturally extends beyond the camera; the required result is an undistorted, correctly fitted, usable game view. Edge-to-edge background decoration may extend behind system areas while essential content stays safe.

**DS05 — Folding and resizing.** Handle cover-to-inner and inner-to-cover transitions, fold/unfold, split-screen/window resizing where provided, system-bar changes and resume without requiring a restart. Treat a truly occluding or separating hinge according to platform-reported geometry; a non-occluding crease is not automatically a missing strip of pixels. Keep essential controls and immediate play out of an occluded region. If the engine cannot expose required hinge information, the implementing owner must supply the platform adapter and prove it.

**DS06 — Input remains aligned.** Apply identical window/safe-area/scale transformations to rendering and hit testing. Cancel or release held joystick/map gestures safely during a layout change, then accept fresh input. No stuck movement, shifted buttons, accidental purchases or touches leaking into world actions.

**DS07 — State survives.** Rotation, folding and resize preserve position, cargo, currency, pet/survivor identities, jobs, combat progress and committed contacts, progression, open-menu state and valid map destination. No duplicate grants, dropped cargo or resets. If the OS recreates the app, restore through the established save/lifecycle contract.

**DS08 — Accessibility and performance.** Preserve text/UI scaling and existing control preferences, readable touch targets, non-color cues, reduced-motion options and muted feedback. Display correctness cannot be traded for missing controls, altered logical actor counts or a different economy. Existing quality presets and performance gates remain applicable; layout screenshots do not certify sustained native performance.

### Required device and transition evidence

Use the actual candidate on compact and tall phones, 16:9 and 20:9 shapes, tablet 4:3, narrow foldable cover and near-square unfolded displays, plus an arbitrary resizable window to catch hardcoded presets. Include portrait, both landscape rotations and supported inverted portrait. Test asymmetric cutouts/insets, gesture and button navigation, system bars, relevant hinge geometry and enlarged text. Include the owner's Fold7-class cover/inner use case; a generic square screenshot does not prove it.

For each applicable configuration, capture gameplay HUD, larger map with markers/legend, menus and a dialog. Exercise rotation/folding/resizing during walking, carrying, pet combat, map pan/zoom, a confirmation and background/resume. Verify visible bounds and actual touch alignment, and record the complete transitions. Desktop/synthetic checks support development; named physical-device/OS results must establish real input, safe-area and folding behavior. All runtime rows remain **UNTESTED** until that evidence exists.

## Existing tasks and implementation sequence

| Existing owner/consumer | Added responsibility |
|---|---|
| T21; T24–T30; T31 | Shared combat contacts; seven species combos; concurrent pets/jobs and marker state. |
| T04 | Responsive camera/UI composition, minimap/larger-map presentation and safe-area layout. |
| T07 | Map gestures, Back/open/close, waypoint interaction, input cancellation and simple controls. Animal AI remains with species/T31 owners. |
| T12; T14 | World/local-level identities; map/waypoint persistence and migration where needed. |
| T32 | World 1 POIs and traversable destination data under the current 50-local-level scope. |
| T44–T52; T53 | Later-world map data and inter-world continuity when introduced. No backward dependency blocking World 1. |
| T54; T55 | Actual map/combat sound coverage and listening; accessible legend, text, cues and controls. |
| T58; T67 | Physical device/transition acceptance and affected integrated regression. |
| T62; T68; T69; T70 | Progression validation and existing performance/release evidence once the features are integrated. |

First bind the live Codex source, existing owner and this addendum to the implementing work packets. Reconcile old orientation assertions in current machine contracts/export settings and generators using this owner instruction; preserve historical copies. Then build shared combat/contact support and seven species sequences in their authorized paths. In parallel, build safe-window/layout/input handling and the map data/presentation interface. Integrate those with real World 1 objects, multiple companions and save state. Capture evidence, obtain independent specialist review, repair and retest before approval. No task IDs or dependency graph edges are changed by this crosswalk.

## Acceptance checklist and completion boundary

The [JSON contract](PET_COMBOS_MAP_DISPLAY.json) contains **21 requirement rows: PC01–PC06, NM01–NM07 and DS01–DS08**, a complete seven-pet registry and acceptance scenarios. Every row is a required implementation/evidence obligation, not a claim that writing it completed the feature.

Documentation acceptance requires complete roster coverage, all three requested features, explicit orientation supersession, valid existing-task mappings, current-world compatibility, independent review, exact publication and preservation of unrelated work. Runtime acceptance additionally requires every applicable check above and source-bound functional results, actual rendered screens/full motion/transition recordings, listening, physical-device evidence and current stricter Havenline critic gates. Unknown evidence blocks runtime approval. A document review score cannot approve the game.

Implementation status: **not implemented or tested in this requirements change**. No APK or device certification is produced. The next executable step is to bind this exact contract to the current gameplay work packets and implement it on the selected Codex foundation with the existing owner.

## Sources and technical references

- Main plan/roster snapshot: [`a4e643a`](https://github.com/ksolo21-web/HAVENLINE/tree/a4e643aeb563b6f9cfda8b840c0651d13326eec8/Docs/Production), especially `HAVENLINE_BUILD_PLAN_V2.md`, `COMPLETENESS_STANDARD.md`, `WHOLE_GAME_COMPLETENESS.json` and `Completeness/2026-11-27/ACTORS_COMBAT_GAPS.json`.
- Latest inspected world-plan contract: [`e9fe6c1` — 10×50 and multi-actor upgrade direction](https://github.com/ksolo21-web/HAVENLINE/blob/e9fe6c1bf28bef1dd630b73b33aceed43ef4f174/Docs/Production/WorldProgression/2026-11-28-10x50/WORLD_PROGRESSION_CONTRACT.json). Its source branch remains independent of this additive documentation change.
- Observed current gameplay ref: [`fad3af0`](https://github.com/ksolo21-web/HAVENLINE/commit/fad3af0a45e94262737077ae513827b5042adb41) on `trial/world-one-expansion-2026-11-26`. Re-resolve before implementation; observation is not a runtime review.
- [Godot multiple resolutions](https://docs.godotengine.org/en/stable/tutorials/rendering/multiple_resolutions.html) and [DisplayServer](https://docs.godotengine.org/en/stable/classes/class_displayserver.html), consulted November 28, 2026: use engine window/scaling and platform safe-area capabilities with the actual project version. Headless display results cannot establish real device safety.
- [Android game resizability](https://developer.android.com/games/develop/multiplatform/support-large-screen-resizability) and [fold information](https://developer.android.com/develop/ui/compose/layouts/adaptive/foldables/make-your-app-fold-aware), consulted November 28, 2026: resize/fold continuity and occlusion need platform-aware handling. Compose examples are not Godot code; any adapter must match the project's real Android export/template.

See [review and resumption evidence](PetMapDisplay/2026-11-28/README.md) for the exact documentation candidate and remaining runtime gates.
