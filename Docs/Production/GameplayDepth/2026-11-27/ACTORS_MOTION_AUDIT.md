# Havenline — survivor, companion and full-animation audit

Baseline: `9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c`. Read-only planning audit dated 2026-11-27. No runtime, art, animation, device or gameplay approval is issued.

## Finding

The plan already asks for useful species-specific companions and role-distinct survivor work. It does not yet provide a complete operational definition of “extremely smart,” full human task parity, delegated plot purchasing, or a complete action/state animation inventory. Those requirements need explicit task contracts and real integrated evidence before they can be described as implemented.

The current actor registry contains **11 actor classes**, all marked `REQUIRED_NOT_YET_PROVEN`. Its animation registry has **36 named profiles**. This is a registry-coverage finding; it does not prove that every missing profile is absent from every source branch or archive. Source: [actor matrix](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/ACTOR_CAPABILITY_MATRIX.json), [animation matrix](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/ANIMATION_ACTION_MATRIX.json).

### Existing commitments, new direction and proposed details

- **Existing commitments:** seven specific animal companions; appropriate resource methods/tools; distinct human-role work motion; species-specific attacks; owl aerial movement; T31 arbitration/navigation/population safety; physical typed carrying; current strict reference/motion review.
- **New user requirements:** survivors assist every practical human task, including buying plots and carrying large mixed resource loads; pets/survivors must be highly useful and intelligent; complete meaningful animation across equipment, enemies and pets.
- **Recommended operational design below:** stable need-based job choice, bounded delegated spending, recoverable reservations, species-specific useful scenarios and exhaustive action/state coverage. These details are authored proposals to make the user requirements testable. They are not claimed observations from the videos or completed runtime behavior.

Pet-specific work and tactical examples are authored Havenline scope. The current reference crosswalk explicitly says there is no direct video demonstration claimed for T24–T31. Static GitHub sheets establish visual input, not AI capability, damage balance, load capacity or motion quality. [Current crosswalk](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md).

## Gaps found in the source contracts

| ID | Source-grounded finding |
|---|---|
| AMG01 | Every actor is still recorded REQUIRED_NOT_YET_PROVEN; schema names and historical task statuses do not certify current runtime intelligence or motion. |
| AMG02 | No explicit survivor purchase/upgrade budget authority or full processing/service/resupply/rescue delegation contract in the current actor registry. |
| AMG03 | T08 crosswalk preserves unlimited logical player inventory separately from finite worker capacity; latest request for large player-like mixed carrying needs an explicit policy decision, not guessed counts. |
| AMG04 | Current36profile registry covers specific harvesting/attacks and a few other actions; it does not constitute complete per-actor locomotion/carry/deposit/heal/rescue/purchase/hurt/recovery coverage or equipment/enemy state inventory. |
| AMG05 | T31 has job arbitration/navigation contention intent, but no frozen complete job-phase, lease, preemption, fallback, authorization-revocation or success/utility scenario contract in the four reviewed registries. |
| AMG06 | Pet role families and motion are already required; no per-species measured usefulness/combined-team acceptance scenario is defined in those registries. Pet-specific behaviors are authored Havenline design, not direct video-observed behavior. |
| AMG07 | Survivor metal/fuel/fish/wheat profiles contain T23_FREEZE_REQUIRED, while placeholder_tokens omit that exact token. Existing schema checks do not prove complete action use-state coverage. |

The resource validator currently checks named actor/profile coverage, generic attack-profile existence and resource schema fields. That is useful custody validation, but it does not inspect every capability’s full use states, truthful intelligent behavior, complete playback, or usefulness in the actual game. The current final motion/visual paths remain required in addition to any schema checks. [Validator](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/tools/havenline/production/resource_actor_contract.py), [resource standard](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md).

## Survivors should use the full human work system

Every practical human action must have an eligible survivor path when its training, equipment, progression and environment prerequisites are met. Specialization should improve effectiveness and authored style; it should not permanently remove basic work verbs from otherwise capable survivors. No one survivor must start as a perfect expert, but the workforce must be capable of assisting the whole game.

| Task family | Required survivor assistance | Owners |
|---|---|---|
| harvest and extract | Chop, mine, registered salvage, fish, crop harvest and hunt using the actual tool/resource method. Training and equipment may gate readiness; no permanent arbitrary survivor-only exclusion. | T09, T16, T19, T21, T23, T31 |
| mixed cargo and storage | Pick up, visibly carry large mixed loads, reserve destination capacity, deposit, retrieve and transfer every permitted registered resource with typed conservation. | T08, T23, T31 |
| process and restock | Feed, operate where attended operation is real, empty and restock machines; preserve recipe/input/output identity, manual-only goods and conveyor restrictions. | T05, T16, T18, T19, T23, T31 |
| service and cash collection | Fulfil reserved orders, visibly hand off goods, collect committed ordinary payment and reinvest only under delegated authority. | T15, T17, T20, T23, T31 |
| plot purchase and upgrade | Fund and complete player-authorized plot purchases, unlocks and upgrades through the same exactly-once world transaction contract; protected resource reserves and per-order budget apply. | T10, T11, T23, T31, T33 |
| construction repair and recovery | Build, repair, clear approved jams and restore interrupted production; player layout changes require an explicit work order, never autonomous base rearrangement. | T10, T11, T18, T22, T23, T31 |
| defense and resupply | Guard, fight, hunt, intercept and restock authorized defensive structures using valid target, weapon, ammunition and friendly-safety contracts. | T21, T22, T23, T31 |
| rescue escort and care | Rescue, escort, move an injured ally where supported, deliver to shelter/care and heal with valid equipment and actual animations; use safe roles rather than all workers charging danger. | T23, T31 |
| transport and region logistics | Load, unload, deliver and operate an approved transport role in every applicable region; region access and equipment apply equally, and industrial belts do not carry living actors. | T20, T23, T31, T44, T45, T46, T47, T48, T49, T50, T51, T52, T53 |
| scout and coordinate | Notice only information actually available to that agent, identify a useful safe job, respond to a small set of player priorities and communicate the present task or concrete blocked reason. | T07, T23, T31 |

### Large mixed loads: one unresolved design decision must stay visible

T08 currently preserves unlimited logical **player** inventory while treating worker capacity separately and as finite. The latest request demands large useful survivor loads like the player. This audit does not silently pick a capacity, a relative percentage, or unlimited worker inventory. The actual worker model must be reconciled and frozen explicitly before acceptance.

Both candidate models—large upgradable finite worker loads or player-like logical capacity—can be evaluated against the requested usefulness, reference presentation, economy, navigation and performance. The chosen model must share the authoritative human custody/capacity/progression schema. Visible stacks can summarize large amounts without becoming the authoritative quantity. Two rows and mixed resource identities must remain clear; a one-item scripted helper does not satisfy the request. Actual trips, delivery throughput, reserved output capacity, full destinations, handoffs and interruption must be tested. [T08 requirements](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t08).

### Buying plots without spending behind the player’s back

The player should be able to choose a plot or bounded construction goal, set a permitted ordinary resource/cash budget and minimum stock to retain, then let eligible survivors collect, haul, contribute and complete it. They use T10’s actual world transaction and T11’s visual states. This is real assistance: it does not require the player to stand on every purchase pad.

- Order identifies exact target plot/upgrade or an explicit allowlist; actor may not invent an expansion chain.
- Player authorizes ordinary in-game resource/cash budget, stock minimums, job priority and whether already reserved partial payments may finish.
- Immediately before commit revalidate target revision/prerequisites, cost, budget remainder, current permissions and safety. Price/target change cannot silently increase the approved budget.
- Cancellation or budget withdrawal releases uncommitted reservations and restores any uncommitted escrow through the same authoritative transaction. A committed purchase remains correctly recorded and cannot be charged again.
- No autonomous premium-currency spend, paid purchase, VIP entitlement change, billing or real-money checkout. Such user-owned decisions remain explicitly initiated by the player.
- Human survivors may physically deliver approved resources and complete plots. Pet assistance stays within species capabilities; pets do not become human cashiers, purchase agents or tool users.
- Show locked, affordable, partial, paid, building and complete state using actual transaction state and selected pad renders; fade only after completion.
- No debt, negative inventory, double spending, duplicated grants or hidden reassignment of a player-reserved input; retained audit identifies actor, order and exact transaction.

The actor may help carry and apply ordinary resources; the player retains ownership of major expansion/layout choices and monetary decisions. A small contextual goal/priority interface can support this without turning Havenline into a management dashboard or adding dedicated buttons for every action.

## What “smart” should mean during play

An agent should observe an eligible need, choose an authorized useful job, reserve the real target/inputs/capacity/budget, reach it, perform a valid action, finish the result and release unused reservations. It must handle each failure between those phases. Repeating an animation beside a target is not evidence that any of those steps worked.

| ID | Required behavior |
|---|---|
| AI01 — Eligibility before desire | Check actor capability, task ownership, equipment/training, known targets, environmental readiness, budget authorization, input availability and output capacity before claiming work. |
| AI02 — Stable useful priorities | Use a small number of player goals plus world safety/need priorities. Emergency protection/rescue, critical fuel or food supply and useful throughput must outrank decorative idle; commit/hysteresis prevents rapid job flipping. |
| AI03 — Shared reservations | Reserve job target/work position, actual typed inputs, destination capacity and permitted ordinary spend atomically. Two agents cannot reserve the same final unit or complete the same plot twice. |
| AI04 — Safe preemption | Define preemptible phases and the authoritative commit point. On danger, recall, priority change or target loss, preserve carried items, unwind unused reservations and either resume or reassign without double payment/damage/yield. |
| AI05 — Player agency | Player can reprioritize, recall, pause or revoke a delegated order through a small set of contextual controls. Crew cannot override a current player operation or consume its reserved resources. |
| AI06 — Path and population recovery | Prove both bidirectional gates with loaded humans and large animals, occupancy handoffs, bounded replan, blocked-route retry and visible safe fallback. No pushing the player, ghosting through walls or permanent crowd deadlock. |
| AI07 — Target-claimed recovery | If a target is claimed, depleted, moved, upgraded, destroyed or unsafe before arrival, reassess. A worker switches to useful eligible work or states a concrete reason; it does not hammer empty air. |
| AI08 — Cargo custody | Carry records identify type, quantity, owner, reservation and destination. Partial unload, spill/recovery if designed, interruption, full destination and handoff cannot delete, duplicate or silently transmute cargo. |
| AI09 — Fairness and bottlenecks | Share targets and work positions fairly, age delayed valid jobs, and relieve a useful bottleneck without starving fuel/food/defense or circulating storage OUT back into storage IN. |
| AI10 — Survival-aware assistance | Agents recognize readable danger and their own ability to complete an order, seek shelter/care if required, escort vulnerable actors and avoid repeatedly entering the same failed route. |
| AI11 — Truthful perception | No omniscient target selection, hidden resources, attacks through geometry or benefits from a scouting action before discovery actually occurs. |
| AI12 — Save and interruption integrity | Persist actor identity, current phase, carried items, committed costs and reservation ownership. Reload/app interruption, retry and migration recreate neither actors nor rewards nor debits. |
| AI13 — Performance without gameplay cheating | Bound decision/path/animation cost at realistic populations on target phones. Presentation detail or evaluation cadence may change only without altering authoritative outcomes, cargo, contact/hit timing or protected ownership. |
| AI14 — Explainable useful behavior | At normal gameplay camera the player can tell what the helper is doing, why it stopped, and what useful outcome it achieved. No high-frequency popups or complex management dashboard is required. |

**Example, proposed:** while the player is expanding the camp, a survivor keeps a nearly depleted production input supplied; another finishes the explicitly authorized plot; the dog protects an exposed carrier; the owl reports a discovered approaching threat. On the threat, the appropriate agents interrupt or escort safely, preserve their cargo, and return to the remaining useful jobs. The player sees the cause and result with a small number of readable cues. This scenario is a design target, not a claim that the current build does it.

## Seven companions with distinct reasons to use them

Existing capabilities and attack languages below come from the current actor standard/matrix. The operational role and example are recommended uses within that scope; balance values and new physical attachments remain authored decisions. [Species contracts](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md#animal-companion-rule).

| Companion | Recommended useful role | Required motion language / evidence |
|---|---|---|
| guardian dog (T24) | Close escort and protection of vulnerable carriers or rescued survivors. Protect a specified nearby ally, intercept an eligible pursuer, then return to its escort job; retrieve suitable light items without abandoning an active rescue. | lunge/bite/intercept; complete approach, contact/miss, recovery, recall and job transitions. |
| gray wolf (T25) | Tracking and pursuing an assigned hunt/threat within a safe leash. Track a discovered eligible prey or hostile, approach from an available flank, abort at the pursuit boundary and return without dragging new threats into workers. | pursuit/pounce/bite; complete approach, contact/miss, recovery, recall and job transitions. |
| fox (T26) | Fast scouting and collection of suitable small recoverable items. Find an unclaimed accessible light pickup and take a safe route to its reserved destination; use actual narrow-route clearance rather than clipping through solids. | dart/pounce/bite; complete approach, contact/miss, recovery, recall and job transitions. |
| owl (T27) | Aerial reconnaissance and timely warning of a visible approaching threat. Take off, inspect an authorized visible area, report a discovered threat with a readable marker/cue, perform a justified dive or light retrieval, and land/perch safely. | aerial dive/talon strike; complete approach, contact/miss, recovery, recall and job transitions. |
| male lion (T28) | Strong defensive interception at an assigned exposed approach. Hold a defensive area and prioritize an attacker endangering the camp or workforce instead of chasing harmless targets; cooperate with another defender. | charge/pounce/claw/bite; complete approach, contact/miss, recovery, recall and job transitions. |
| white tiger (T29) | Focused flanking and interception of an exposed dangerous target. Use an available approach to engage an authorized target while the lion or guards hold the front; break off and recover rather than continuing a suicidal pursuit. | low ambush/pounce/claw/bite; complete approach, contact/miss, recovery, recall and job transitions. |
| brown bear (T30) | Heavy hauling and clearing specifically approved obstacles, with defensive support. Take an authored heavy-haul job with an approved species-compatible carry method, reserve gate/route clearance, deliver intact cargo and only break designated breakable obstacles. | heavy charge/swipe/bite; complete approach, contact/miss, recovery, recall and job transitions. |

Animals keep species-appropriate jobs. The owl does not use a ground-animal animation; the bear does not swing a human hammer; the dog does not become a cashier. Heavy hauling needs a physically coherent, approved carry method and clearance. Each species needs a concrete beneficial outcome, then an integrated team scenario so all seven are useful choices rather than cosmetic followers or one universally superior pet.

Friendly companion identity must stay separate from hostile and huntable wildlife. The wolf/tiger crosswalk already requires this separation. Wild-bear/wolf/fox meat concepts are qualified proposals for separate wildlife; they do not authorize friendly companion loot tables. Combat animation requirements do not decide permanent pet death or purchased-entitlement loss. Those are separate loss-policy decisions.

## Full animation means every meaningful state and transition

Full coverage includes the approach, anticipation, working/attack cycle, authoritative contact, result, interruption and return to normal behavior. “Idle + walk + one attack” is insufficient for a character with ten work families. Machines need their real use states; they must visibly change when input is absent, the output is full, power/fuel is unavailable where applicable, or the route is blocked. Static architecture can remain static when that is truthful and intentional.

| Coverage family | Required use states | Main evidence obligation |
|---|---|---|
| human locomotion | idle, start, walk, run, stop, turn, loaded movement, partial/full mixed load, blocked route, resume | Foot/toe/knee contact, grip and gear/cargo clearance at actual gameplay speed; scale stays bound to approved renders. |
| human work actions | approach, align, equip, anticipation, work loop, impact, success/yield, miss/denied, interrupt, finish, stow | Each actual method/tool has authored role-appropriate motion; impact triggers exactly one authoritative resource event. |
| cargo and transactions | pickup, grip/attach, carry, queue, first/last transfer, partial transfer, destination full, cancel, committed purchase, build/reveal, reload recovery | Visible item identity and contact match custody; no free material from gestures, success on denial or visual pad disappearance before completion. |
| human rescue and care | notice, approach, assist/lift if supported, escort, shelter arrival, heal start, treatment, heal end, interrupted recovery | Meaningful rescue and care actions require hand/body contact, target response and actual improved state. |
| human combat | detect, draw, approach, aim, windup, strike/fire, contact/miss, recoil, recover, reload if applicable, hurt, retreat, defeat/recovery as designed | Weapon-specific mechanics, human-role motion and damage authority; legibility and friendly safety. |
| animal motion and jobs | species idle, walk/run or flight, start/turn/stop, job approach, species work/retrieve, attack telegraph, contact/miss, recovery, hurt, recall/retreat, rest, interruption | Paws, shoulders, tails, fur/mane, jaws/talons and carry contacts; meaningful species jobs, not a scaled shared attack loop. |
| owl aerial | perch, takeoff, full wing cycle, turn, climb/descent, glide if authored, dive, talon strike, retrieve grip, landing, abort/clearance recovery | Full aerial navigation, wing clearance and perch transitions in actual playback; no ground-animal substitute. |
| production equipment | idle, input delivered, start, working cycle, output release, empty/missing input, output full, stalled, stop, repair/maintenance if designed, restart, upgrade/reconnect | Different machines visibly perform their actual function, and stop/respond to shortages/backpressure. Central warming furnace stays distinct from an unapproved smelter recipe. |
| conveyor storage service | inlet handoff, travel, corner/port turn, queue, outlet handoff, full, jam, clear, restart, service request, wait, goods handoff, payment, depart | Cargo remains supported and typed; service and cargo ports separate; actual paid handoff and cash states readable. |
| defensive structures | idle, target acquired, aim/traverse, load, fire, recoil, reload, empty, refill, damaged, repair, resume | Visible aim/shot/reload/contact corresponds to actual target and ammunition; no ornamental firing or invented ore ammunition. |
| enemy archetypes | patrol/approach, notice, pursue, telegraph, attack, hit/miss, stagger if designed, recover, retreat/return, defeat, drop/recovery | Each shipped archetype/weapon/locomotion family needs readable unique authored behavior and full transitions; separate friendly companions, huntable wildlife and hostile roles. |
| environment and feedback | gate open/close/latch, construction/reveal, weather onset/change/clear, resource depletion/regrowth, warning, success, denial, recovery | Animate functional changes and authored ambient life where appropriate. Static architecture need not move without purpose; critical state changes remain clear with sound muted and reduced-motion settings. |

Every animation entry should bind the actual actor/asset/model/rig/scene/version, applicable action, eligibility, start/loop/exit states, cancel/preempt points, contact or transaction event, sound/visual equivalents and evidence. The logical result controls presentation: misses and denied/cancelled work do not create damage, resources, purchase success or payment because a clip happened to play.

Enemy roster proposals remain separate from observed reference hostiles and friendly companions. Every shipped archetype, weapon family and movement type needs its own readable tells, contact, miss/recovery, pursuit/return and defeat/drop behavior as actually designed. New art alone does not close this. Machine states must match selected cooker/saw/drill/conveyor/defense references; the central warming furnace is not silently reinterpreted as a smelter or an unapproved production recipe. [T05, T18, T21 and T22 source requirements](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md).

### Sound is part of the action contract

The build plan already makes each feature owner emit accurate events and provide relevant audio coverage while T54 owns cue direction, music, mix and listening approval. Extend that same register to tool contacts, machine states, animal calls/work/attacks, warnings, damage, healing, recall, blocked work, payment and recovery. Deliberate silence or controlled shared cues can be valid; an unexplained blank is missing coverage. Real listening under simultaneous machines, crowd and combat is required, with muted equivalents for important cues and sensible concurrency so repeated worker/pet sounds do not become noise. [Audio/event contract](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/HAVENLINE_BUILD_PLAN_V2.md#t54--music-sound-effects-and-event-coverage).

### Review evidence

- Use the exact selected GitHub render commit/path/hash, actual model/rig/scene identity and current policy binding. This audit reads the catalogue; it does not claim new visual inspection of those images.
- Capture full cycles and every required transition from distinct meaningful angles, including normal gameplay camera and close contact views. Inspect feet/toes/knees, hands/tools/cargo, paws, jaws, wings, tails, mane/fur and clipping where applicable.
- Review normal speed and slowed inspection; verify the actual gameplay event and resulting custody/damage/transaction state. Listen to real candidate audio.
- C5 static contact sheets remain interim-only. Final independent review must actually inspect required playback. Preserve >=9.9 per applicable final reference dimension and all stronger exact-10 visual/motion gates.
- A planning matrix or fixture test does not establish runtime intelligence, animation quality, game score or device performance.

## Concrete acceptance scenarios

All of these remain **NOT RUN against the actual game** in this audit. They should become source-bound candidate evidence under their owning tasks.

| ID | Scenario | Required demonstration |
|---|---|---|
| AC01 | Human task parity | For every human gameplay task family and applicable resource/region, demonstrate the trained/equipped survivor route and actual action result; exceptions require an explicit owner decision, not an accidental missing capability. |
| AC02 | Useful large mixed cargo | Compare actual trip throughput and readable mixed-load handling with the player/logistics goal; validate selected capacity policy rather than claiming an unchosen count. Full/partial destinations and two-gate congestion retain every unit. |
| AC03 | Delegated plot completion | Player approves a target and budget; workers gather/transport/contribute/commit/build once. Concurrent player/worker arrival, partial funding, cancellation, budget withdrawal and reload never duplicate debit or unlock. |
| AC04 | Emergency preemption | During delivery or work, introduce a threat or vulnerable ally. Eligible agents protect/retreat/reassign while conserving cargo and unused reservations, then resume useful work. |
| AC05 | Target and route failure | Claim/deplete/move the target, close one route, fill the output, interrupt an animation and revoke authorization. Each agent chooses a valid recovery or a truthful blocked state without thrashing/deadlock. |
| AC06 | Pet value by species | Each of seven pets completes a distinct useful scenario, then a mixed-team scenario. Compare resulting safety, useful delivery, discovery or throughput with an idle companion; do not claim a tuned numeric benefit without measurement. |
| AC07 | Complete motion inventory | Every introduced action/state has an authored clip/mechanism or explicit justified static/reused disposition and source-bound evidence. Play full cycles and transitions at normal speed and slow inspection with distinct meaningful views. |
| AC08 | Animation/accounting alignment | Verify one authoritative yield, transaction, damage or reward event per valid contact/commit; miss, cancelled and replayed animation produce none. Reload at the commit boundary cannot duplicate outcomes. |
| AC09 | Listening and mute equivalence | Listen to actual candidate cues and music transitions under simultaneous machines/crowds/combat. Alerts retain visual equivalents, concurrency is bounded, and optional idle variety does not mask danger or force noise. |
| AC10 | Population/device integration | Run realistic population, wildlife, pets and working machinery on required devices/modes, including app interruption and long sessions; keep gameplay authority and critical readability under the budget. |
| AC11 | Progression and autonomy | At early and late milestones, helpers reduce repetitive chores while meaningful player route, defense and expansion choices remain. Every major action is automatable when unlocked without mandatory paid help. |
| AC12 | Reference and asset identity | Selected GitHub render commit/path/hash maps to actual model/rig/scene and full use-state clips; do not treat static render approval or an old source review as current motion/AI approval. |

## Task placement and dependency boundaries

T23 owns survivor eligibility/identity/permissions and authored survivor motion; T31 integrates useful jobs and population behavior. Those tasks consume the actual action owners rather than duplicating inventory, purchase, production or combat authority. The complete mapping is below and in the companion JSON. Existing task IDs, dependencies, statuses and path owners remain unchanged. Any required upstream runtime repair follows its authorized task/change-request path; this audit does not activate LOCKED tasks.

| Task | Forward requirement |
|---|---|
| T05 | For new or modified equipment, bind the selected design to complete truthful idle/input/run/output/full/stall/recovery states and actor contact; preserve frozen historical scope/receipts. |
| T06 | Character1 full human action/contact foundation; preserve approved scale and actual two-handed grip where selected. |
| T07 | Stable contextual priority and safety-preemption rules shared by player/AI actions; small goal/priority controls without new mandatory action-button sprawl. |
| T08 | Large mixed survivor/core-helper carrying requirements and typed custody; explicitly reconcile existing finite-worker premise with new request before choosing capacity. |
| T09 | Human method/tool parity for every registered opening resource; distinct full work cycles and impact authority. |
| T10 | Shared exactly-once delegated-purchase transaction, reservation and budget-revocation semantics. |
| T11 | Authorized survivor plot payment/construction/upgrade; selected pad states and player-owned layout work orders. |
| T13 | Assistance and enemy reactions obey bounded, spend-blind challenge and readable recovery; intelligent behavior does not secretly punish purchasing or exploit impossible threat knowledge. |
| T14 | Persist actor IDs, job phase, custody, reservation ownership and committed purchase/result IDs without duplicating or losing state after interruption. |
| T15 | Population/queue/gate occupancy and customer animation; safe coexistence of large carriers and companions. |
| T16 | Survivor/helper fishing and food-processing readiness plus whole action and equipment state coverage. |
| T17 | Survivor counter service, committed payment collection and permitted ordinary reinvestment. |
| T18 | Useful shared job arbitration for machines/manual logistics; typed port reservations, bottleneck response, backpressure and full machinery motion. |
| T19 | Survivor/helper crop and additional food work; recipe and output reservations with full authored motion. |
| T20 | Survivor vehicle-service/logistics roles with safe customer/vehicle/cargo routing and transactional handoff. |
| T21 | Intelligent enemy/animal/human combat and hunting, per-archetype actions, clear tells and damage/contact truth. |
| T22 | Guard/repair/resupply cooperation and all defense equipment states. |
| T23 | Survivor identity plus all-human-task eligibility, skill/tool readiness, rescue/care, large-load and purchase permissions; role-distinct motion. |
| T24 | guardian_dog: preserve existing capabilities; make its distinct role useful in an actual scenario; complete species motion and AI recovery evidence. |
| T25 | gray_wolf: preserve existing capabilities; make its distinct role useful in an actual scenario; complete species motion and AI recovery evidence. |
| T26 | fox: preserve existing capabilities; make its distinct role useful in an actual scenario; complete species motion and AI recovery evidence. |
| T27 | owl: preserve existing capabilities; make its distinct role useful in an actual scenario; complete species motion and AI recovery evidence. |
| T28 | male_lion: preserve existing capabilities; make its distinct role useful in an actual scenario; complete species motion and AI recovery evidence. |
| T29 | white_tiger: preserve existing capabilities; make its distinct role useful in an actual scenario; complete species motion and AI recovery evidence. |
| T30 | brown_bear: preserve existing capabilities; make its distinct role useful in an actual scenario; complete species motion and AI recovery evidence. |
| T31 | Integrate shared planner, permissions, reservations, safety preemption, useful roles, save continuity and population safety across human helpers/survivors and all7pets. |
| T32 | Frozen-region integrated assisted-production/rescue/defense/playback/listening scenarios. |
| T33 | Worker usefulness, load capacity and ordinary-spend budgets aligned with source/sink and F2P progression; no unmeasured balance claims. |
| T34 | Premium/economic authority prohibits autonomous paid currency spend; protects actual entitlement/balance operations. |
| T35 | No survivor or pet initiates real-money checkout; player-confirmed purchase flow remains authoritative. |
| T42 | Privacy-respecting job failure/stuck/abandonment/throughput diagnostics; no spend-based assistance degradation. |
| T43 | Persist identities, jobs, custody and budget commitments correctly through cross-device/cloud recovery. |
| T44 | Extend trained human task coverage, species suitability and every new resource/tool/enemy/equipment state to this region; no silent generic fallback. |
| T45 | Extend trained human task coverage, species suitability and every new resource/tool/enemy/equipment state to this region; no silent generic fallback. |
| T46 | Extend trained human task coverage, species suitability and every new resource/tool/enemy/equipment state to this region; no silent generic fallback. |
| T47 | Extend trained human task coverage, species suitability and every new resource/tool/enemy/equipment state to this region; no silent generic fallback. |
| T48 | Extend trained human task coverage, species suitability and every new resource/tool/enemy/equipment state to this region; no silent generic fallback. |
| T49 | Extend trained human task coverage, species suitability and every new resource/tool/enemy/equipment state to this region; no silent generic fallback. |
| T50 | Extend trained human task coverage, species suitability and every new resource/tool/enemy/equipment state to this region; no silent generic fallback. |
| T51 | Extend trained human task coverage, species suitability and every new resource/tool/enemy/equipment state to this region; no silent generic fallback. |
| T52 | Extend trained human task coverage, species suitability and every new resource/tool/enemy/equipment state to this region; no silent generic fallback. |
| T53 | Human logistics and companion compatibility with transport/routes/region transitions; no living actors on industrial belts. |
| T54 | Feature-local events extended to species, action, machine and recovery audio; music/mix/listening ownership and nonspam/mute behavior. |
| T55 | Readable low-complexity goals, blocked reasons, danger cues and reduced-motion equivalents. |
| T56 | Real population/machine/animation/path budgets in player quality modes; preserve outcomes and clarity. |
| T58 | Actual phone/tablet/foldable interaction, suspension and viewport coverage. |
| T59 | Character-specific complete human work/combat/cargo/transaction state compatibility and real full-cycle contact evidence. |
| T60 | Character-specific complete human work/combat/cargo/transaction state compatibility and real full-cycle contact evidence. |
| T61 | Character-specific complete human work/combat/cargo/transaction state compatibility and real full-cycle contact evidence. |
| T62 | WholeL1–100 actor/resource/action coverage, useful assistance and complete motion/audio acceptance. |
| T63 | Unpaid path includes useful survivor/pet progression and realistic labor/load/currency balance. |
| T64 | Paid conveniences cannot make basic survivor competence, safety or recovery deliberately poor for F2P. |
| T67 | Repeat exact-source reference/render, complete cycle/transition, listening and integrated AI regression. |
| T68 | Certify sustained phone behavior with representative completed-world worker/pet/enemy/machine population; reuse no unsupported synthetic-only performance claim. |
| T69 | Certify sustained tablet/foldable behavior with representative completed-world worker/pet/enemy/machine population and relevant screen/mode transitions. |
| T70 | Release only with closed action/role/animation/evidence coverage and no fabricated current gameplay approval. |

## Scope and handoff

This read-only audit provides source-grounded findings, ten human task families, fourteen intelligent-behavior requirements, seven distinct companion roles, twelve animation coverage families and twelve integrated acceptance scenarios. It includes exact source hashes and selected render bindings in `ACTORS_MOTION_REQUIREMENTS.json`. These are proposed forward requirements and unresolved authoring decisions, not implemented mechanics or new approvals. No repository file, source asset, task record or GitHub state was changed by this audit.

Before implementation acceptance, resolve worker capacity and useful throughput, approved delegated purchase behavior, each species’ exact job/target rules, future equipment/weapon methods, and any failure/permanent-loss policy. Then test actual play. The requirement is a capable, understandable workforce that makes the camp feel alive while the player retains meaningful decisions.
