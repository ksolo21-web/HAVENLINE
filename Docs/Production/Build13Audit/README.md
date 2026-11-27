# Havenline Build 13 · Audit and decisions

**Phase:** Planning. Implementation begins when Kaleb gives the go-ahead.

**Gameplay baseline:** Build 13, Godot scene `res://field_opening.tscn`, game source `2654f5019b7212968d28600cb071bf1c231c9030`, QA and trial head `2f46e72e300a719f34ca9b0e9b718282a5a88ddd`. APK SHA-256 `af81181c81bc623310b00680ea4467615c6f9ffd4c21c1197bc75aff3b71bd75`. PR #108 was closed as superseded. The production plan compared in the whole-plan audit is pinned at `a4e643aeb563b6f9cfda8b840c0651d13326eec8`. [Signed Build 13 receipt](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Verification/Android.json) · [Production plan](https://github.com/ksolo21-web/HAVENLINE/blob/a4e643aeb563b6f9cfda8b840c0651d13326eec8/Docs/Production/HAVENLINE_BUILD_PLAN_V2.md) · [Closed PR #108](https://github.com/ksolo21-web/HAVENLINE/pull/108)

## Submitted audits

- [Build 13 dynamic gameplay audit](Havenline-Build-13-Dynamic-Gameplay-Audit.md) records source findings, gameplay gaps, the first tests that would prove fixes, and open design choices.
- [Whole task-plan audit](Havenline-Whole-Task-Plan-Audit.md) contains the task-by-task findings for all 70 defined tasks and the ten undefined entries. World levels 71–80 belong to T50. Both submissions are preserved verbatim, including earlier wording. Use the owner decisions below to resolve conflicts between them.

## World 1 launch and later updates

World 1, Frozen Home Camp, is the initial release focus. Worlds 2–10 follow as connected updates. Design World 1 as a continuous sandbox and test a 50-level local progression target. The camp keeps operating after its last milestone. The final count, global numbering and older Level 1–100 launch contract need reconciliation before production sign-off. [World 1 progression and adaptive sandbox](World-Progression.md)

## Owner decisions to carry forward

### Player routes and acceptance

Use several player-chosen routes through the forest, quarry, lakeshore, gates and camp. Check both gates in both directions at each camp stage, loaded and unloaded, including turning back, yielding to a worker and returning under pressure. Check each accessible service face and repeat with relocated equipment and active conveyors. Reproducible input tests establish the failure conditions. Uncoached playtests establish whether players can navigate, redirect and recover on their own. Apply this across gameplay, visual review and T54 audio listening, including equivalent muted cues.

### Counter, work and resource costs

- Customers take requested processed goods from a visible goods area on the counter and leave cash in a separate visible stack. Use distinct stacks for multiple goods types. The counter needs no register or spawned attendant.
- The player or an unlocked survivor can bulk-stock the counter and collect all available cash in the same visit. A survivor can haul both raw and processed goods, stock what customers are requesting, and carry earnings back to storage. An eligible conveyor supplies the same counter stock. The player can run the opening solo. Test the existing 500-per-resource survivor carry target against useful mixed loads and each new processed good. The player has no per-resource cap.
- Adjust resource types and quantities for orders, plots and upgrades as the player progresses. A required item can come from an owned source or a plot the player can realistically fund and unlock at that stage. Validate the complete acquisition path and quantity, including route, inputs and producer availability. A plot cannot require the output only it would unlock.
- Current planning proposes freezing a payable quote and carrying it through partial funding and reload. If destruction makes the original requirement unattainable, pause or visibly reissue it and settle any paid contributions once. Count specifically reserved inventory toward a sale. A single durable sale transfers the requested basket and credits the matching payment.

### Conveyor appearance · T05 and T18

**Reopened by Kaleb.** The Build 13 gameplay view shows thin, dark-edged runs, many narrow legs, and longer loops around the machines. The selected Havenline sheets show broader orange sideguards, substantial gray supports, visible roller decks, and short, readable connections. The comparison uses different camera angles, so those are visual findings to recheck at equal gameplay scale. [Build 13 gameplay view](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Play/Gameplay.jpg) · [D01 transport modules](https://github.com/ksolo21-web/HAVENLINE/blob/e501bea5ed9e6f8737abb5b39799cade78b22af1/Docs/Design/ConveyorReferences/2026-11-26/connected-logistics-01/selected/conveyor-transport.png) · [D06 camp arrangement](https://github.com/ksolo21-web/HAVENLINE/blob/e501bea5ed9e6f8737abb5b39799cade78b22af1/Docs/Design/ConveyorReferences/2026-11-26/connected-logistics-01/selected/conveyor-camp.png)

- Compare straights, supported roller corners and cleated inclines at normal gameplay zoom and at 2×. Check rail depth, leg proportion, blue drive details, and whether the shape and direction read with goods on the deck.
- Check close-fitting, supported connections at the storehouse, processors and self-service counter. Prefer compact runs where the route permits. Use the owner sheets for the hardware and apply the latest separate goods and cash areas at the counter.
- Review the default and valid relocated layouts through several player and worker approaches. Record empty, moving and full states. Prove that cargo rides on the visible deck, usable aisles and both gates stay clear, and transfers resume correctly after relocation. Build 13's surface and aisle checks are a functional baseline. Conveyor appearance needs a new reference review. [Storehouse and machine interfaces](https://github.com/ksolo21-web/HAVENLINE/blob/e501bea5ed9e6f8737abb5b39799cade78b22af1/Docs/Design/ConveyorReferences/2026-11-26/connected-logistics-01/GALLERY.md) · [Build 13 functional checks](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/Verification/Native/qa_surface_conveyor_layout-1.log)

### Hunting, targeting and camp damage

- Owned survivors can proactively hunt wildlife. They may defend themselves when attacked.
- Hostile targeting follows Kaleb's latest correction. Hostiles prioritize the player and pets, or the camp when assaulting it. A survivor who attacks a hostile can draw retaliation. If the player and pets are both too far away, hostiles can target anyone nearby and attack camp structures and equipment. Sheltering alone does not make an unprovoking survivor the first target. This supersedes that sentence in the dynamic gameplay audit.
- Survivors and pets can be killed and must be bought again. Separate the active life record from long-term purchase or entitlement records. Exact compensation, carried goods and retained upgrades on casualty still need a documented decision. Recovery through ordinary earned resources must remain available.
- Fences and gates have high HP, can be breached, and can be restored through repair plots. Equipment can take damage and be destroyed. Repurchase destroyed equipment at Level 1. Repair requirements depend on the material or equipment and damage severity. A breach must update navigation, collision and protection together. Choose a recorded disposition for goods in a destroyed machine or on its conveyors.
- The furnace penalty is open. The proposal is a cold emergency that suspends hearth healing and heat-dependent services until a Level 1 rebuild, with a safe fallback and an attainable route to the rebuild resources. Exact cost and any effect on customer demand or interior protection still need a decision.

These choices affect older provisions for permanent sanctuary, free restoration and companion recovery. Reconcile those provisions explicitly from the planning record before approving their replacements. Set the far-away threshold, active settlement eligibility in later regions, raid termination and retargeting in the relevant task packets. The five-minute warning is fixed below. Test travel during active play and saved recovery separately. [Prior completeness standard](https://github.com/ksolo21-web/HAVENLINE/blob/a4e643aeb563b6f9cfda8b840c0651d13326eec8/Docs/Production/COMPLETENESS_STANDARD.md)

### Raid warning and balance · T13, T21 and T22

Give the player a full **five-minute warning** before a raid can start damaging the threatened camp. Name the camp and show a 5:00 countdown from wherever the player is exploring, with an audible cue and an equivalent visible warning when muted. Use the existing active-play timing rule. Save the remaining time and restore it on resume.

Raids should be hard, beatable, and survivable. A player who uses the warning to prepare should be able to repel the raid with equipment and defenses obtainable at that progression stage. If the defense fails, the player needs a real retreat route and a way to rebuild. Breaches, casualties and equipment losses apply under the rules above.

Test the full countdown and verify that the camp takes no raid damage before it expires. Start outside camp, return by different gates, resume during the countdown, successfully defend with earned equipment, and test retreat and recovery after a breach. T54 and T55 cover the warning's sound and readability.

### Proposed raid frequency · T13 playtest tuning

Use the following active-play intervals for the opening camp. Each interval is measured to the start of the attack and includes the full five-minute warning.

| Case | Warning | Earliest attack |
|---|---|---|
| First raid | After 20 minutes of active play with basic camp defenses available to build. | 25 minutes after that defense unlock. |
| After a successful defense | 40–55 minutes after the last raid ends. | 45–60 minutes after the last raid ends. |
| After a failed defense | At least 55 minutes after the last raid ends. | At least 60 minutes after the last raid ends. |

Select the repeat interval once and save it. If the camp is ineligible when the warning becomes due, wait until it qualifies and give the full warning then. Allow one pending or active raid at a time in the opening. Begin the next interval only after the current raid ends. Pause the clocks out of active play and resume from the recorded time. Regional cadence can be evaluated with longer playtests.

Test a short opening session, a long session with successive wins, and a failed defense followed by rebuilding. Check for a meaningful preparation window and enough time afterward to explore, gather and repair. Tune strength, composition and attack patterns with progression before shortening the intervals. The five-minute warning is an owner requirement. These intervals are the initial playtest proposal.

## Recommended order after authorization

| Order | Scope and acceptance |
|---|---|
| 1 · T03–T05 foundation | Start with multiple approaches to the two gates, then review camera, HUD and actual props at normal and pinch zoom. Include different camp stages, routes, queues and layouts. Compare the installed assets with Kaleb's selected render sheets, including the reopened conveyor appearance. Capture the gate collision and navigation interface for future breach work. |
| 2 · First gameplay integration | Build the shared typed stock and order ledger, attainable quotes and save migration on the signed foundation. Prove the opening counter with the player alone and with the unlocked survivor, including mixed stock, interrupted payment, simultaneous cash pickup and a full destination. Keep an opening service interface available before later fishing and road service. Staged integration needs an explicit dependency decision where the frozen order conflicts. |
| 3 · Threat and recovery integration | Prove legal targeting, wildlife hunting, five-minute raid warnings, active-play raids, breach, casualty, repair, Level 1 replacement and a guaranteed path back to production. Run a combined-loss scenario beginning with empty stock and no helper. Verify save and reload before and after the committed events. |
| 4 · Progression and release | Bind T12 to the accepted Build 13 successor interfaces from T07, T08, T10 and T11. T12's existing T10 and T11 proofs reference the older project. Keep frozen task dependencies visible as the work is staged. The whole-plan audit tracks later regions, events, entitlements, cloud conflicts, audio and device certification. |

The first gameplay integration spans T08 and T10–T14, with T15/T17/T18 customer and conveyor interfaces and T23/T31 worker behavior. T33 tunes the economy after the early eligibility rules exist. Threat and recovery span T03, T10/T11, T13/T14, T21/T22 and T23–T31. T54/T55 cover sound and readable cues. The attached whole-plan audit records the remaining consumer tasks and their proof obligations.

## Evidence and open decisions

- Build 13 already records 69 regression suites, 222 opening progression checks, 168 fixed-input gate approaches, and on-foot withdrawal of all ten warehouse goods. The independent 9.9 movement review covers the four playable rigs and the working survivor. Reuse relevant evidence for its tested scope. The production registry carries visual holds for T03, T04, T05, T08, T09, T10 and T11. [Build 13 review and test reports](https://github.com/ksolo21-web/HAVENLINE/blob/2f46e72e300a719f34ca9b0e9b718282a5a88ddd/Docs/QA/Camp-Field-2026-11-27/README.md)
- The physical Fold 7 cover and inner-screen flow, orientation policy, actual audio listening, and sustained native 4K/60 certification still require evidence. The optional 120-FPS goal is a separate measurement. Reference-sensitive acceptance uses the current 9.9 per-dimension requirement and the stricter 10.0 visual gates where applicable. [Reference acceptance standard](https://github.com/ksolo21-web/HAVENLINE/blob/a4e643aeb563b6f9cfda8b840c0651d13326eec8/Docs/Production/REFERENCE_ACCEPTANCE_STANDARD.md)
- The audit also records open decisions on inter-region raid eligibility, casualty and replacement inventory, payable demand policies, and which affected frozen requirements need a formal update. T09 and T21 must reconcile the player's automatic orbit and survivor hand-tool work with the older held-tool production contract. Confirm these as their task packets are scheduled.
