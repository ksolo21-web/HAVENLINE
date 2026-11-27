# Havenline — actor and combat contract

Planning delta against main `fd2e12c8734f49cda7eb3bbf97887406bd03a704`. Bounded gameplay-source credit uses `3fad812b384335bd8ca9b5e47dc9d9557110eb4a`. No runtime, visual, animation, sound, balance or device approval is granted.

## Finding

**All seven pets must attack, and each must also have a useful specialty.** This is consistent with the existing actor registry: dog, wolf, fox, owl, lion, tiger and bear all already have `attack_allowed=true` and a named attack profile. The new requirement should be made impossible to reinterpret as “the fox only scouts” or “the owl only warns.” A real attack means a valid species-specific action causing authoritative damage in ordinary play. [S05](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ACTOR_CAPABILITY_MATRIX.json) [S06](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ANIMATION_ACTION_MATRIX.json)

The prior gameplay-depth work already established capable survivors, meaningful jobs, large mixed loads, delegated plot funding, complete motion and audio, and failure recovery. This delta preserves that work. It identifies what must be selected, bound to actual implementation or demonstrated; it does not rename all existing requirements as new gaps. The actor/combat domain here is one part of the root whole-game audit.

## What is already covered

| Coverage | Existing obligation | Meaning now |
|---|---|---|
| C01 | All seven species already have attack_allowed=true and an explicit required attack profile. [S05](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ACTOR_CAPABILITY_MATRIX.json) [S06](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ANIMATION_ACTION_MATRIX.json) | Existing commitment; the new user instruction removes any support-only interpretation. |
| C02 | Complete human task-family assistance, substantial mixed loads, delegated ordinary-resource/cash plot spending, protected reserves and no autonomous premium spend. [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json) | GD03–GD05 and AC01–AC03 already cover the requirement; capacity tuning and production proof remain open. |
| C03 | Fourteen AI obligations cover eligibility, stable priorities, reservations, preemption, route/target recovery, custody, save continuity and truthful intent. [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json) | GD06 already establishes intelligent behavior; this delta specifies combat/job boundary cases. |
| C04 | Species-distinct useful jobs, friendly identity, complete actor/equipment/enemy action states and real audio listening. [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S06](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ANIMATION_ACTION_MATRIX.json) | GD07–GD12 already cover usefulness and full presentation. Existing profiles are required, not certified clips. |
| C05 | Late-region compatibility, free-player usefulness, integrated population/device evidence and current reference acceptance. [S01](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/AGENTS.md) [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S09](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md) | GD17–GD18 and the task crosswalk cover whole-game obligations; the missing region/species decisions must now be bound explicitly. |

### Credit the actual current-source groundwork

**O01.** The observed 3fad812 owl source already has takeoff/follow/bank/windup/dive/strike/recover/land/perched states; it selects eligible outside-camp enemies, checks owner distance, intersects actual claw segments with the target surface, and submits a real damage contact. [S14](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_owl.gd) [S15](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_opening.gd)

Source grounding for the current owl only. No playback, contact quality, full target roster, device performance or seven-pet integration approval.

**O02.** The observed hostile-wolf source contains pursuit/leash, brace, bite contact, recovery, hit reception and encounter reset behavior. [S16](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_enemy.gd)

A reviewed hostile-wolf implementation is not the friendly gray wolf and does not prove the complete enemy roster or polished weapon progression.

**O03.** The observed survivor source already schedules an early customer-service opportunity, rotates camp duties, gathers mixed resources during a bounded field shift and streams typed cargo back to storage. [S13](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/CURRENT_BRANCH_NOTE.md) [S17](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_survivor.gd)

Credit this groundwork. It does not prove every future physical task, final worker capacity policy, combat interruption or population-scale intelligence.

The seven-pet designs remain authored Havenline scope. The pet task crosswalk explicitly claims no direct pet demonstration in the reference videos. RF12/RF14 support visible hostile/contact/defense behavior; RF17 is official text evidence, not pet animation footage. The selected GitHub sheets remain the visual starting points with their original provenance and historical scores. [S09](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md) [S10](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ReferenceRefresh/2026-11-27/RENDER_CATALOGUE.md) [S11](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ReferenceRefresh/2026-11-27/REFERENCE_RESEARCH.md)

## Explicit all-pets-attack contract

All12 rules below are adopted forward requirements. The original proposal origin labels are retained as provenance. The current selected behavior and prior-decision dispositions are in [WHOLE_GAME_COMPLETENESS.json](../../WHOLE_GAME_COMPLETENESS.json); these supersede the baseline open-choice wording below. Numerical combat tuning and actual runtime proof remain open.

### PA01 — Seven real combat participants

Every one of guardian_dog, gray_wolf, fox, owl, male_lion, white_tiger and brown_bear retains an unlocked, usable species-specific attack. Scouting, warning, retrieval, hauling and other specialties are additional value; they cannot replace attack or turn fox/owl into support-only pets.

Origin: `CURRENT_USER_REQUIREMENT`.

### PA02 — Useful attack outcome

Every species has at least one ordinary eligible-hostile scenario in which a valid attack inflicts real positive damage and helps the player. Cosmetic swipes, an unused animation, a statistics-only aura, a warning marker or merely being marked attack_allowed do not pass. Exact damage and cadence require balanced actor/target evidence.

Origin: `EXPLICIT_ACCEPTANCE_DETAIL`.

### PA03 — Complete attack state and contact

Bind ready/approach/anticipation/commit/contact-or-miss/recovery/return, interruption and resume to the actual species rig. Each intentional contact group has an authoritative attack-instance/event identity; repeat overlap, extra claws, animation callbacks or reload cannot duplicate that group. An intentionally multi-hit attack must declare its separate groups. A miss, invalid target or cancellation before contact causes no damage.

Origin: `EXPLICIT_ACCEPTANCE_DETAIL`.

### PA04 — Legitimate targets and friendly identity

Select and revalidate a living eligible hostile or explicitly authorized hunt target by stable identity, faction, current state and environment. Player, companions, workers, customers and rescue candidates are not ordinary hostile/loot targets. A hostile wolf or wildlife meat concept cannot supply a friendly-pet identity or drop policy. All pet kills use the shared exactly-once defeat/reward pipeline.

Origin: `EXISTING_COMMITMENT_REFINED`.

### PA05 — Stable and readable priorities

Preserve the simple-control and priority language of T07. Its frozen human-context selector does not automatically own animal behavior: species and T31 owners author pet/job arbitration, and any shared-selector change uses the existing authorized scope process. Recommended arbitration is: a current recall/retreat or safety constraint; an immediate threat to the assigned protected ally/area; an authorized player-selected reachable hostile; the assigned defense/hunt objective; then a safe opportunistic hostile. Keep a valid target until a meaningful priority/eligibility change; distribute useful engagement space instead of seven pets repeatedly switching to the nearest enemy.

Origin: `RECOMMENDED_AUTHORED_POLICY`.

### PA06 — Physical range, pursuit and return

Freeze sensed area, line-of-approach/occlusion, actual strike reach, safe route, pursuit leash, disengagement and return point for each profile. Damage must agree with visible contact, target size and obstructions. Do not teleport, clip through gates/walls, use omniscient targeting, chase indefinitely, or obtain a free attack through a sanctuary boundary. Failure to reach a target produces a truthful alternate/return state.

Origin: `EXPLICIT_ACCEPTANCE_DETAIL`.

### PA07 — Recall, preemption and useful resumption

Recall prevents acquiring or extending a pursuit. Before a valid contact commit, a cancellable attack exits without damage; after a committed contact it exits at the authored safe boundary without repeating damage. Immediate defensive contact during withdrawal is permitted only when it does not countermand the return order. Store the suspended job and revalidate its target, reservation, destination, budget and cargo before resuming or choosing another useful job.

Origin: `EXPLICIT_ACCEPTANCE_DETAIL`.

### PA08 — Cargo and tools remain truthful

A pet or survivor switching from carrying/working to combat first uses an authored compatible handling transition. A mouth/talon already holding cargo cannot silently keep that cargo while performing an incompatible bite/strike. Secure, hand off or explicitly set down typed owned cargo with recovery custody; never erase or duplicate it. A construction payment or machine transfer commits once or remains uncommitted.

Origin: `EXISTING_COMMITMENT_REFINED`.

### PA09 — Coordinated attacks and fair rewards

Use shared engagement-space/target state with bounded reservations and cleanup. Multiple allies may attack one durable enemy when appropriate, but contact validation, overkill, simultaneous defeat and reward generation stay authoritative. No repeated kill reward, friendly body-block trap, endless stun loop if control effects are selected, or camera-filling overlap. Defense structures and pets cooperate through the same target truths.

Origin: `EXPLICIT_ACCEPTANCE_DETAIL`.

### PA10 — Recoverable actor lifecycle

Select explicit hurt, retreat, incapacitation-if-used, help/recovery and return-to-job rules shared with the loss/recovery decision. Recommended ordinary-play policy preserves named pet/survivor identity and progress, with free attainable recovery and no autonomous premium revive. The contract must expose what the player protects; invulnerable helpers and destructible helpers are different rules and must not be mixed accidentally.

Origin: `RECOMMENDED_AUTHORED_POLICY`.

### PA11 — Progression and environment continuity

Every species retains a real usable attack throughout applicable progression; this does not require each animal to fight in every region or terrain cell. Region owners bind safe deployment, reachable attacks, local target compatibility, transport, return and cargo continuity. An unsuitable environment may have an explicit inapplicable combat disposition with a useful safe alternative assignment and a retained combat role elsewhere in the progression. Use already selected compatible routes/staging or appropriate equipment only where it fits the region; do not invent new facilities/gear merely to fill a matrix, ordinary owl underwater flight, quadruped free flight or invisible remote damage. No silent conversion of a species to support-only and no mandatory paid environmental competence.

Origin: `EXPLICIT_ACCEPTANCE_DETAIL`.

### PA12 — Actual evidence, current standard

Bind each species to the existing selected GitHub sheet and actual mesh/rig/profile/scene. Prove successful attack, miss, interrupted attack, target loss, recall, return-to-specialty and a later-region use case with exact-source full-cycle multi-angle playback and actual sound listening. Shared busy-scene/device evidence is additional. Historical 9.3/9.4 reference-sheet scores do not grant current approval; retain current reference >=9.9 and stronger exact-10 visual requirements.

Origin: `EXISTING_COMMITMENT_REFINED`.

### Seven distinct combat roles

| Companion / owner | Existing attack language | Additional useful role | Required combat example |
|---|---|---|---|
| [guardian_dog](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/RenderArchive/2026-11-23/selected/animal-companions/pet_dog_01.png) / T24 | `dog_attack`: lunge bite intercept | Close escort and recovery of eligible light cargo. | An enemy closes on an assigned carrier; the dog visibly lunges/bites, causes valid damage, then returns to escort without stealing the carried load. |
| [gray_wolf](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/RenderArchive/2026-11-23/selected/animal-companions/pet_wolf_01.png) / T25 | `wolf_attack`: pursuit pounce bite | Tracking and bounded pursuit of eligible threats or authorized prey. | Pursue an eligible hostile, pounce/bite with real contact, break off at the safe leash and return. Repeat with a friendly same-species actor present and prove identity separation. |
| [fox](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/RenderArchive/2026-11-23/selected/animal-companions/pet_fox_01.png) / T26 | `fox_attack`: dart pounce bite | Agile ground scouting and suitable light retrieval. | Dart into a legitimate opening, pounce/bite for meaningful damage and disengage. Demonstrate the attack during ordinary play; a fox that only fetches, warns or evades fails. |
| [owl](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/RenderArchive/2026-11-23/selected/animal-companions/pet_owl_01.png) / T27 | `owl_attack`: aerial dive talon strike | Aerial reconnaissance, warning and suitable light retrieval. | Take off, bank/anticipate, dive and strike with actual talon contact, recover in clear air and return/perch. A circling bird with a damage timer or a warning-only owl fails. |
| [male_lion](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/RenderArchive/2026-11-23/selected/animal-companions/pet_lion_01.png) / T28 | `lion_attack`: charge pounce claw bite | Defense of an exposed approach and protection of working allies. | Commit visibly to a charge/pounce/claw/bite against an eligible threat, apply authored contact damage and recover with believable mass. Keep mane, turning and ally clearance readable. |
| [white_tiger](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/RenderArchive/2026-11-23/selected/animal-companions/pet_tiger_01.png) / T29 | `tiger_attack`: low ambush pounce claw bite | Focused flanking and interception. | Use a reachable approach for a low ambush/pounce/claw/bite; no teleport flank. Show distinct timing/posture from the lion and return to its assigned objective. |
| [brown_bear](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/RenderArchive/2026-11-23/selected/animal-companions/pet_bear_01.png) / T30 | `bear_attack`: heavy charge swipe bite | Approved heavy hauling/obstacle work plus protection. | Secure an incompatible heavy load, charge/swipe/bite with weight-aware contact and damage, then reclaim or deliver conserved cargo. Slow mass must not stall the whole control loop. |

The table inherits existing species motion language and proposes ordinary-play demonstrations; it does not assert that all seven are implemented. Every render binding in the JSON retains exact image path, archive URL, Git blob and SHA-256 copied from the existing source-pinned actor contract. Ownership of all seven does not imply simultaneous deployment of all seven. [S05](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ACTOR_CAPABILITY_MATRIX.json) [S06](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ANIMATION_ACTION_MATRIX.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json)

## Remaining gap register

“Existing open design” describes the audited baseline. Current choices are selected in [the whole-game contract](../../WHOLE_GAME_COMPLETENESS.json), with tuning and implementation evidence still open. “Implementation evidence gap” means the requirement exists, but this audit cannot certify its implementation. “Current user clarification” or “explicit requirement refinement” closes an ambiguity in acceptance. No row claims that a missing proof means no code exists anywhere.

### ACG01 — All seven attacks are non-optional

**Classification:** `CURRENT_USER_CLARIFICATION`. **Owners:** T24, T25, T26, T27, T28, T29, T30.

**Baseline:** Seven attack flags and seven required profiles already exist. The role table can still be read as fox/owl support-only, and no single explicit seven-species attack acceptance row prevents that interpretation. [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S05](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ACTOR_CAPABILITY_MATRIX.json) [S06](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ANIMATION_ACTION_MATRIX.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json)

**Required disposition:** Adopt PA01–PA12 and seven species scenarios; strengthen GD07/task projections to require real attack plus useful specialty for every species.

**Fits Havenline when:** Each animal feels useful and distinct while the player retains simple movement/context controls.

**Closure evidence:**

- Seven exact actor/profile rows; attack removal or support-only substitution fails planning validation.
- Seven real ordinary-play successful-damage demonstrations plus miss/recall/return cases; no untested species averaged away.

**Consumers:** T21, T31, T32, T62, T67, T70.

### ACG02 — Freeze the hostile, prey and weapon roster

**Classification:** `EXISTING_OPEN_DESIGN`. **Owners:** T21.

**Baseline:** T21 reference crosswalk explicitly leaves the complete handheld weapon-upgrade roster unresolved and separates observed hostiles, authored invader concepts, huntable wildlife and pets. [S02](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/HAVENLINE_BUILD_PLAN_V2.md) [S07](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md) [S09](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md) [S11](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ReferenceRefresh/2026-11-27/REFERENCE_RESEARCH.md) [S16](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_enemy.gd)

**Required disposition:** Bind each selected hostile/prey/weapon to an actual ID, source/render disposition, action profile, unlock, target eligibility, useful combat purpose, reachable counterplay and resource/reward lifecycle. Unselected art remains a concept; do not create an enemy or weapon solely to fill a render list.

**Fits Havenline when:** Combat protects and supplies the visible camp loop; weapon choice/progression does not create button-heavy RPG combat.

**Closure evidence:**

- Selected ID/profile/target/unlock matrix with exact render bindings.
- Each selected archetype creates a readable response beyond additional HP; player weapon/tool switch and damage use actual contact.

**Parameters still requiring selected values and validation:** Selected roster and unlock sequence; Damage/reach/cadence and reward values.

**Consumers:** T06, T07, T09, T13, T22, T23, T24, T25, T26, T27, T28, T29, T30, T33, T44, T45, T46, T47, T48, T49, T50, T51, T52.

### ACG03 — Resolve sanctuary, exposure and defense together

**Classification:** `EXISTING_OPEN_DESIGN`. **Owners:** T13, T21, T22.

**Baseline:** The observed current source rejects hits in camp. The gameplay-depth standard proposes recoverable damage/disruption to routes and operations, but does not freeze the exact attackable domains or their boundary rules. [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S13](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/CURRENT_BRANCH_NOTE.md) [S15](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_opening.gd) [S16](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_enemy.gd)

**Required disposition:** Publish one zone/target policy for player, survivors, pets, customers, defenses and production. Preserve current safe-camp behavior unless the owning task explicitly replaces it with a selected readable rule. Define threat warning, reachable response, maximum exposure, retreat and free recovery; prevent damage crossing protected geometry and permanent safe-zone reward farming.

**Fits Havenline when:** Danger is visible and recoverable while the camp remains understandable; the design does not silently add destructive raids or absence punishment.

**Closure evidence:**

- Zone-by-actor attackability table with source-accurate protection and defense-resupply rules.
- Boundary crossing, expanding camp, returning worker, tower/pet overlap, new player and repeated-failure sessions.

**Parameters still requiring selected values and validation:** Attackable domains; Exposure and recovery limits; Spawn/pursuit/return parameters.

**Consumers:** T03, T07, T10, T11, T23, T31, T32, T33, T44, T45, T46, T47, T48, T49, T50, T51, T52.

### ACG04 — Define companion injury and rescue lifecycle

**Classification:** `EXISTING_OPEN_DESIGN`. **Owners:** T13, T21, T23.

**Baseline:** D01 recommends recoverable loss and protection of named companions; actual pet/survivor health, incapacitation, help, return and repeat-failure states remain owner decisions. [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json) [S13](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/CURRENT_BRANCH_NOTE.md)

**Required disposition:** Select a common lifecycle with actor-specific presentation. Recommended normal play retains named identities, earned upgrades and bought entitlements; use readable retreat/incapacitation if chosen and an attainable free recovery action. Specify what happens to cargo, reserved work, escorts and purchased plots at every transition. A pet cannot be simultaneously treated as invulnerable support and injured population.

**Fits Havenline when:** The player has people and pets worth protecting without a maintenance dashboard, permanent surprise loss or a paid revive trap.

**Closure evidence:**

- Actor lifecycle/cargo/recovery state table and exact persistence events.
- Down/retreat during carry, rescue, payment and region transfer; repeat failure and interrupted recovery without duplicate penalties/rewards.

**Parameters still requiring selected values and validation:** Whether incapacitation is used; Recovery action, time and limits; Health/protection scaling.

**Consumers:** T14, T24, T25, T26, T27, T28, T29, T30, T31, T33, T43, T54, T55.

### ACG05 — Owned roster, active deployment and switching

**Classification:** `EXISTING_OPEN_DESIGN`. **Owners:** T24, T25, T26, T27, T28, T29, T30, T31.

**Baseline:** D04 explicitly leaves active population/team limits and offscreen work unresolved. All seven owning an attack does not establish that seven pets are simultaneously active. [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json) [S12](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/DEPENDENCY_GRAPH.json)

**Required disposition:** Separate permanently owned identities from active assignments. Select understandable active-team rules and return/switch/transport behavior. Preserve health/recovery, cargo, job and attack-instance state through switching; do not permit infinite attack/cooldown resets. Offscreen jobs, if selected, use source-conserving simulation and cannot invent combat rewards.

**Fits Havenline when:** A small contextual roster/goal choice creates useful team tradeoffs without mandatory micromanagement or seven overlapping visual attacks.

**Closure evidence:**

- Owned/active/assigned/returning state model and selected population limits.
- Switch at windup/contact/recovery, with cargo, after reload and during travel; prove no duplicate actor/reward or reset exploit.

**Parameters still requiring selected values and validation:** Active pet/worker counts; Switching and offscreen policy.

**Consumers:** T14, T23, T33, T43, T53, T55, T56, T58.

### ACG06 — Late-region actor and attack compatibility

**Classification:** `EXISTING_OPEN_DESIGN`. **Owners:** T44, T45, T46, T47, T48, T49, T50, T51, T52, T53.

**Baseline:** T44–T52 and T53 require actor/environment compatibility but have no complete chosen species/region deployment matrix in the reviewed actor sources. [S02](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/HAVENLINE_BUILD_PLAN_V2.md) [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json) [S09](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md) [S12](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/DEPENDENCY_GRAPH.json)

**Required disposition:** For frozen, forest, desert, underwater, sky, volcanic, swamp, ruins, underground and alien bands, bind each introduced human task and each pet to safe travel/work/attack applicability. Where a species cannot sensibly fight, record the reason and a useful safe alternative assignment; preserve its real usable attack across applicable progression. Use compatible routes/staging/equipment already selected for the region or justified by its gameplay, not a new facility or feature solely to complete the matrix.

**Fits Havenline when:** The world changes what the player plans and equips, without changing the core move/work/carry/defend loop or forcing every animal into every terrain cell.

**Closure evidence:**

- Ten-band actor/task/target/travel applicability matrix with explicit supported route or justified useful alternative assignment.
- Every species demonstrates real usable combat across applicable progression; unsuitable regions may be explicitly inapplicable with useful safe alternatives. Transitions conserve identity/cargo/jobs.

**Parameters still requiring selected values and validation:** Selected region adapters and compatible routes; Protection and travel requirements.

**Consumers:** T08, T21, T22, T23, T24, T25, T26, T27, T28, T29, T30, T31, T32, T33, T54, T62, T63.

### ACG07 — Combat must safely interrupt and resume useful work

**Classification:** `IMPLEMENTATION_EVIDENCE_GAP`. **Owners:** T23, T31.

**Baseline:** GD04–GD06 already require reservations, preemption, budget withdrawal and conservation. The inspected survivor source contains real service/gathering work, but no whole-game proof of every combat/work/transaction boundary is supplied by this audit. [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json) [S17](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_survivor.gd) [S18](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/T07/FROZEN_SCOPE.md)

**Required disposition:** Use the existing shared job state and typed custody contract for the complete combat transition. Revalidate ownership, work target, destination capacity, tool readiness, budget and navigation before returning. If the former job is no longer valid, release claims and select a useful authorized replacement with a short truthful reason.

**Fits Havenline when:** Smart helpers actually finish jobs and protect the camp; the user should not repeatedly rescue broken AI logic.

**Closure evidence:**

- AC03–AC05/AC08 extended at each precommit/postcommit boundary for work→fight→return.
- Enemy during mixed delivery, plot last-payment race, storage full, revoked budget, claimed/depleted target and save/reload; exact conservation and no thrashing.

**Consumers:** T07, T08, T09, T10, T11, T14, T16, T17, T18, T19, T20, T21, T22, T43.

### ACG08 — Survivor readiness and useful capacity progression

**Classification:** `EXISTING_OPEN_DESIGN`. **Owners:** T08, T23, T31.

**Baseline:** Complete human task families and no permanent specialization bans are already binding. D02 has not selected future worker logical capacity/scaling; current source supports six raw load kinds and mixed shifts, not a universal full-game capacity policy. The current-source note also records that worker_payment still excludes the conveyor offers, which requires reconciliation with authorized all-plot assistance. [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json) [S13](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/CURRENT_BRANCH_NOTE.md) [S17](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_survivor.gd)

**Required disposition:** Freeze one visible readiness/upgrade model for all physical human work families, including future production, service, rescue/care, transport and every authorized plot type. Training/equipment/safety gates are achievable; specialization changes effectiveness and preference. Choose substantial mixed carrying using trip throughput, keep unlimited logical player inventory and separate visual stack count from owned quantity.

**Fits Havenline when:** Workers become visibly more effective while a few goals/priorities remain enough; no skill tree or new stamina/hunger chore is implied.

**Closure evidence:**

- Readiness/physical-task matrix, substantial-load capacity decision and shared schema.
- Player versus worker route/throughput comparisons at early/mid/late stages; every selected plot type and future work family demonstrated.

**Parameters still requiring selected values and validation:** Worker logical capacity and scaling; Training/equipment prerequisites and useful throughput targets.

**Consumers:** T09, T10, T11, T16, T17, T18, T19, T20, T21, T22, T33, T44, T45, T46, T47, T48, T49, T50, T51, T52, T53.

### ACG09 — Keep every companion useful through Level 100

**Classification:** `EXISTING_OPEN_DESIGN`. **Owners:** T13, T21, T24, T25, T26, T27, T28, T29, T30, T31, T33.

**Baseline:** D04 role parameters and GD16 free-player progression require balance proof, but the selected role/counter/threat curves are not frozen by the actor registries. [S02](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/HAVENLINE_BUILD_PLAN_V2.md) [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json) [S09](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md)

**Required disposition:** Keep a real basic attack and useful specialty for each species across eligible milestones. Compare measured safety, meaningful damage, delivery or discovery value against an idle companion. Introduce enemy combinations and environmental decisions rather than only health inflation. Ensure helpers reduce repetition without erasing player route, expansion and threat-response decisions.

**Fits Havenline when:** Unlocks broaden useful choices and visible progress; they do not force replacing a favorite pet or paying for basic competence.

**Closure evidence:**

- Early/mid/late free-player scenarios for every species and selected mixed team.
- No species becomes support-only/obsolete through scaling; no single team trivializes all threats; counterplay remains visible.

**Parameters still requiring selected values and validation:** Damage/health/ability/upgrade curves; Target interactions and encounter mixes.

**Consumers:** T12, T32, T44, T45, T46, T47, T48, T49, T50, T51, T52, T62, T63, T64.

### ACG10 — Bind complete action coverage to real clips and equipment

**Classification:** `IMPLEMENTATION_EVIDENCE_GAP`. **Owners:** T06, T21, T22, T23, T24, T25, T26, T27, T28, T29, T30, T31, T54.

**Baseline:** GD09–GD12 already require full state/transition coverage and listening. The 36-profile registry and REQUIRED_NOT_YET_PROVEN flags remain a requirements inventory; historical unresolved survivor profiles cannot establish final coverage. [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S05](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ACTOR_CAPABILITY_MATRIX.json) [S06](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ANIMATION_ACTION_MATRIX.json) [S07](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json)

**Required disposition:** Each introducing owner resolves every applicable actor/tool/cargo/enemy/equipment state to a real clip/mechanism and authoritative event. Maintain distinct human role motion, species-specific attacks, full contact/recovery and partial/blocked/interrupted states. Justified static/shared motion is allowed where it is an explicit fit; final attack/work placeholders are not.

**Fits Havenline when:** Everything doing meaningful work visibly performs that work; variety reflects task and anatomy instead of random animation noise.

**Closure evidence:**

- Action/transition→clip/mechanism→event→source-bound capture coverage, with unresolved profile references blocking applicable production proof.
- Full cycles and interruptions from useful angles; feet/hands/paws/wings/tool/cargo contact; actual listening and muted/reduced-motion equivalent.

**Consumers:** T05, T08, T09, T10, T11, T15, T16, T17, T18, T19, T20, T44, T45, T46, T47, T48, T49, T50, T51, T52, T53, T55, T59, T60, T61, T67.

### ACG11 — Prove coordinated combat at real population scale

**Classification:** `IMPLEMENTATION_EVIDENCE_GAP`. **Owners:** T31, T32, T56, T58.

**Baseline:** GD17/AC10 already require busy-shift/device evidence. A single owl attacking one wolf is not evidence of all pet/human/enemy/defense combinations or target-device budgets. [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json) [S12](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/DEPENDENCY_GRAPH.json)

**Required disposition:** Run representative bounded teams alongside machines, large carriers, customers and hostiles. Coordinate approach space, gates and danger cues; preserve damage/transaction truth if visuals or decision frequency scale. Reset/disconnect/pause cannot duplicate combat rewards or strand jobs. Diagnose bounded stuck/abandoned-job failures without spending-based adaptation.

**Fits Havenline when:** The camp stays lively and readable without blocking its own gates or hiding danger under effects and sound.

**Closure evidence:**

- Busy-shift continuous session with combat/work/recall/routing/save cases and attributable failures.
- Actual source-bound target-device frame, CPU/GPU/memory, collision/readability and listening results; declared budgets and active counts.

**Consumers:** T03, T07, T13, T15, T21, T22, T23, T42, T43, T53, T54, T55, T62, T67, T68, T69, T70.

### ACG12 — Separate contact, reward and save authority

**Classification:** `EXPLICIT_REQUIREMENT_REFINEMENT`. **Owners:** T14, T21, T31.

**Baseline:** AC08 and GD08 already demand authoritative contact and legitimate loot. The observed owl/wolf paths contain local protection, but the full-game multi-actor attack/defeat/loot/swap/resume contract must be common. [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json) [S14](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_owl.gd) [S15](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_opening.gd) [S16](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_enemy.gd)

**Required disposition:** Bind stable attacker/target/attack/contact-group/defeat/reward identities and a single authority for each commit. Save/reload or region transport restores committed outcomes once; uncommitted animation can restart/cancel without phantom damage. Concurrent final strikes, target removal and active-pet switching cannot multiply drops or XP.

**Fits Havenline when:** Visible contact earns an honest result while interruption and recovery cannot steal progress or create free infinite rewards.

**Closure evidence:**

- Concurrent pet/player/tower last-hit and one defeat/reward transaction.
- Save before/after contact, before/after defeat, during recall/swap/travel and with a vanished target; exact once-only outcomes and no stale actor IDs.

**Consumers:** T08, T09, T13, T22, T23, T24, T25, T26, T27, T28, T29, T30, T33, T43, T53, T62, T67.

## Concrete acceptance scenarios

All scenarios below are **NOT RUN AGAINST THE ACTUAL GAME** in this audit. Reuse the prior AC01–AC12 evidence framework; these are focused actor/combat extensions and are not a second competing approval system.

| ID | Scenario | Required demonstration |
|---|---|---|
| PC01 | Seven-species ordinary attack | For each of seven species, show one normal eligible-hostile hit with positive authoritative damage, a miss, full recovery and its additional useful specialty. |
| PC02 | Target and friendly identity | Place friendly same-species actors, workers, customers, rescue candidates, eligible prey and hostiles together; only explicit legitimate targets can take attack damage or produce selected loot. |
| PC03 | Recall at every attack phase | Recall during approach, windup, contact and recovery; stop new pursuit, preserve committed damage once, return without target-thrashing and resume/reassign a valid useful job. |
| PC04 | Geometry and boundary | Use moving/small/large targets, occluded routes, a closing gate, sanctuary edge and vanished target; valid contact is visible and unreachable targets are safely abandoned. |
| PC05 | Work interruption and cargo | Interrupt heavy/mixed cargo, talon/mouth retrieval, cooking, rescue and a last plot payment; every unit and unspent budget remains accounted for through fight and return. |
| PC06 | Shared defeat and recovery | Player, pet and tower strike the last HP concurrently; persist one defeat/reward, reload and repeat around the commit boundary, with no duplicate loot/XP or lost valid result. |
| PC07 | Roster switch and save | Switch active pets with health/recovery/cargo/work/attack state and pause/reload/travel; preserve owned identity, no attack-reset exploit and no duplicated actor. |
| PC08 | All human task families | Run qualified survivors through all physical work families, every authorized plot type, substantial mixed loads and late-region jobs using minimal goals; no unexplained permanent specialization ban. |
| PC09 | Actor recovery | Apply the selected pet/survivor hurt/retreat/down/recovery rule while an escort/cargo/plot job is active; retain identity/entitlements and demonstrate attainable free recovery. |
| PC10 | All region bands | Verify each region/species applicability disposition: real combat where suitable, explicit useful safe alternatives where unsuitable, and conserved arrival/return/cargo. Every species keeps a real usable attack across applicable progression; do not force every species into every region or add facilities merely to fill the matrix. |
| PC11 | Early/mid/late value | Compare each species and selected mixed teams with an idle companion in ordinary free-player play; measure safety/damage/throughput or discovery while preserving player decisions. |
| PC12 | Busy scene with actual motion and listening | Run the selected population on target devices through complete combat/work transitions, crowded gates, machines and customers; inspect multi-angle motion/contact, actual audio and muted/reduced-motion readability. |

## Dependencies and execution

The JSON supplies exact existing task names and prerequisite lists for every mapped owner/consumer. These are source observations, not new dependency edges. In particular, do not make early pet tasks wait for later T31/T33 integration: each introducing owner proves its local contract; later tasks prove the combined system. T71–T80 remain undefined source gaps and are not invented here. [S01](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/AGENTS.md) [S12](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/DEPENDENCY_GRAPH.json)

1. Add the explicit seven-attacking-pets invariant and per-species acceptance to current planning projections, preserving existing role/animation contracts.
2. T21/T13 owners freeze selected target/weapon/zone/recovery interfaces; pet and survivor owners author their feature-local use cases against those interfaces without adding backward dependencies.
3. Prove one conserved survivor work→combat→return loop and one contact-authoritative pet attack loop, then all seven species individually.
4. T31 combines selected teams/jobs/targets/defenses and T33 checks early-to-late usefulness; every region binds deployment and action compatibility before its own integration.
5. Run current-source complete motion/listening, persistence, multi-actor adversarial, full progression and target-device evidence before any game approval.

### Scope protections

- No new tasks T71–T80, invented dependency edges, reassigned ownership or changed task statuses.
- No new button-heavy combat, mandatory management dashboard, co-op/guild warfare, random permanent specialization exclusions or hunger/stamina chore system.
- No new enemy, weapon, recipe, special status effect or equipment item solely because an art sheet exists.
- No mandatory paid basic AI, pet attack, free recovery or environmental competence.
- No fresh visual, animation, audio, runtime, balance, whole-game or device approval; source checks and planning coverage only.

## Source identity and deliverables

The companion JSON contains 18 exact source bindings, the twelve attack rules, seven species rows, twelve gap dispositions, twelve proposed runtime scenarios and authentic task mappings. Source file hashes bind this audit to the inspected commits. The planning choices and final runtime evidence are separate responsibilities.

[Machine-readable audit](ACTORS_COMBAT_GAPS.json)

| Source | Commit | Path |
|---|---|---|
| [S01](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/AGENTS.md) | `fd2e12c8734f` | `AGENTS.md` |
| [S02](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/HAVENLINE_BUILD_PLAN_V2.md) | `fd2e12c8734f` | `Docs/Production/HAVENLINE_BUILD_PLAN_V2.md` |
| [S03](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) | `fd2e12c8734f` | `Docs/Production/GAMEPLAY_DEPTH_STANDARD.md` |
| [S04](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json) | `fd2e12c8734f` | `Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json` |
| [S05](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ACTOR_CAPABILITY_MATRIX.json) | `fd2e12c8734f` | `Docs/Production/ACTOR_CAPABILITY_MATRIX.json` |
| [S06](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ANIMATION_ACTION_MATRIX.json) | `fd2e12c8734f` | `Docs/Production/ANIMATION_ACTION_MATRIX.json` |
| [S07](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md) | `fd2e12c8734f` | `Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md` |
| [S08](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json) | `fd2e12c8734f` | `Docs/Production/GameplayDepth/2026-11-27/ACTORS_MOTION_REQUIREMENTS.json` |
| [S09](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md) | `fd2e12c8734f` | `Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md` |
| [S10](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ReferenceRefresh/2026-11-27/RENDER_CATALOGUE.md) | `fd2e12c8734f` | `Docs/Production/ReferenceRefresh/2026-11-27/RENDER_CATALOGUE.md` |
| [S11](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/ReferenceRefresh/2026-11-27/REFERENCE_RESEARCH.md) | `fd2e12c8734f` | `Docs/Production/ReferenceRefresh/2026-11-27/REFERENCE_RESEARCH.md` |
| [S12](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/DEPENDENCY_GRAPH.json) | `fd2e12c8734f` | `Docs/Production/DEPENDENCY_GRAPH.json` |
| [S13](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/GameplayDepth/2026-11-27/CURRENT_BRANCH_NOTE.md) | `fd2e12c8734f` | `Docs/Production/GameplayDepth/2026-11-27/CURRENT_BRANCH_NOTE.md` |
| [S14](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_owl.gd) | `3fad812b3843` | `HavenlineLevel1/field_owl.gd` |
| [S15](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_opening.gd) | `3fad812b3843` | `HavenlineLevel1/field_opening.gd` |
| [S16](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_enemy.gd) | `3fad812b3843` | `HavenlineLevel1/field_enemy.gd` |
| [S17](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_survivor.gd) | `3fad812b3843` | `HavenlineLevel1/field_survivor.gd` |
| [S18](https://github.com/ksolo21-web/HAVENLINE/blob/fd2e12c8734f49cda7eb3bbf97887406bd03a704/Docs/Production/T07/FROZEN_SCOPE.md) | `fd2e12c8734f` | `Docs/Production/T07/FROZEN_SCOPE.md` |

Planning draft completed; actual game behavior remains unapproved. Root integration and independent review are pending.
