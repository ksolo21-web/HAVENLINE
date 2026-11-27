# Havenline reference acceptance — current forward standard

Effective 2026-11-27. Kaleb approved tightening the final reference-match standard after the task-plan/reference audit. The machine-readable authority is [REFERENCE_ACCEPTANCE_POLICY.json](REFERENCE_ACCEPTANCE_POLICY.json). This standard applies to new reviews, changed candidates and reapprovals across the full authentic T01–T70 plan. T71–T80 still have no authentic task definitions and cannot be approved.

## Acceptance rules

| Review scope | Required result |
|---|---|
| Interim checkpoint | Scores at least 9.5 may document progress. The result cannot close a reference-sensitive task, authorize integration or become final approval. Remaining work stays explicit. |
| Final reference-sensitive comparison | Every applicable dimension at least 9.9, unrounded, with complete evidence. |
| Existing final visual/reference gates | Keep the stronger exact-10 rules. Under the existing whole-frame fidelity and shipping policies, every mandatory dimension for C1, C2, C3, C4, C5 and C11 must equal 10.0. |
| Other mandatory specialist dimensions | At least 9.5 unless a named requirement is stronger. A matched-reference dimension in another specialist review still requires at least 9.9. |
| Concrete functional, security, performance, audio, device and ownership requirements | Every applicable mandatory check passes using the required evidence. Scores cannot compensate for a failed check. |
| Missing or unreviewed evidence | BLOCKED for approval. Never assign a passing score to an untested area. |

The strongest applicable requirement controls. The 9.9 floor does not lower the [whole-frame fidelity standard](REFERENCE_FIDELITY_STANDARD.json), [shipping visual policy](SHIPPING_VISUAL_APPROVAL_POLICY.json), [material/style lock](REFERENCE_STYLE_LOCK.json), or any other stricter requirement. There is no averaging or upward rounding. Each required dimension is evaluated separately; missing, extra, duplicated, boolean, nonnumeric, nonfinite or out-of-range score data is rejected by the applicable validator.

A review score is a judgment, not a measured percentage of visual similarity. Exact 10 means every required comparison passed across the complete inspected scope, with zero known unapproved deviations from the agreed references and explicit owner-approved adaptations. It is not a claim of mathematically identical pixels or a guarantee that a later defect cannot emerge. A newly discovered defect reopens the affected approval.

## The source of truth for each feature

Before building or reviewing, the task packet identifies the exact primary video source and relevant time ranges, the selected GitHub render commit/path/hash, and any explicit owner-approved adaptation. Use the [T01–T80 crosswalk](ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md) and [render catalogue](ReferenceRefresh/2026-11-27/RENDER_CATALOGUE.md) to locate the evidence. Historical alternatives are not interchangeable with the selected design.

Kaleb's explicit changes control the features they name. Resolve a conflict between a video, selected render and later instruction in the task's decision record before treating it as a requirement. An unseen rear surface, inferred recipe or proposed upgrade must be labeled as authored design; it cannot be described as observed reference evidence. Do not invent numeric tolerances or timings from edited footage. Measure what the source actually establishes and record uncertainty.

Repeat comparisons against the frozen approved reference, including after integration. This catches cumulative drift across revisions. A comparison only with the immediately preceding build does not establish reference conformance.

## Evidence that is required to close reference-sensitive work

1. **Exact candidate and inputs.** Record the full candidate commit, policy ID and SHA-256, source manifests, selected images/video moments, editable/runtime asset identities, scene and relevant instances. Keep the raw independent review and its hash.
2. **Complete applicable coverage.** The task packet freezes required dimensions, views, use states and reference-sensitive dimensions in otherwise nonvisual reviews. Critic applicability is the union of the task graph, critic matrix and stronger resource/action/style contracts. C5 is mandatory for T09/T16/T19/T21/T23 and for any new actor or region action that requires motion evidence. Omitting a critic from an older graph cannot waive it.
3. **Actual in-game appearance.** Inspect the normal gameplay camera, meaningful additional angles and close-ups. Compare proportions, silhouette, material/palette, scale, contact and composition with the selected references. A static archive receipt or attractive studio render cannot approve the implemented asset.
4. **Complete behavior.** Motion reviews inspect full cycles and transitions, including feet/toes/knees, grip, weight transfer and clipping. Machines and transport need their relevant idle, running, empty, full, blocked and resumed states. A passing run clip cannot approve an entire character rig.
5. **Evidence appropriate to the claim.** Audio claims require listening; timing and transitions require actual playback; physical-device claims require the specified device evidence. A contact sheet cannot prove unseen motion or sound. Desktop geometry cannot prove physical folding or sustained device performance.
6. **Named differences and their disposition.** Record concrete deviations with reference and candidate locations, responsible owner and repair/retest evidence. Zero known unapproved reference deviations and zero unresolved mandatory defects are required. An upstream visible defect routes to its owner and remains a blocker to the affected approval while independent authorized work continues.
7. **Independent review and integration retest.** A separate reviewer inspects the frozen candidate and full required evidence. Keep rejects unchanged. Repairs invalidate the affected reviews and require fresh evidence and retesting. Existing explicit user signoff requirements remain in force.

The current C5 contact-sheet runner performs interim static screening only. Final C5 approval requires a separate, source-bound independent session that actually plays the full required cycles and transitions. Use the [external independent-review contract](EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md). Its stored review must identify the decoded video artifacts and complete reviewed ranges; a static screening result cannot be promoted by changing its label.

The deterministic checks verify identity, declared coverage, score boundaries, evidence custody and dispositions. They cannot themselves judge the artistic correctness of pixels or prove that a reviewer watched a full cycle. The independent visual/motion/audio inspection is still required.

## Concrete rejection examples

Wrong character proportions or scale; thin or incorrectly oriented fence/gate geometry; cooker-side reversal; altered material language; paths painted outside the approved camp; a displaced central furnace; fewer than the required usable bidirectional openings; unreadable mixed carry types; sliding feet; incorrect grip; a transfer without the required custody/accounting; and obscured or off-reference UI cannot be excused by a high overall score. These examples do not replace the complete task-specific requirements.

An observed mandatory mismatch fails even when the numeric result is 9.9 or 10. A reviewer must report honest uncertainty, low scores and missing evidence. Prompts and schemas must not force a passing number because a defect list is empty. Repeatedly rescoring unchanged work to force a pass is forbidden. A genuinely erroneous review can be corrected through documented evidence-based adjudication; preserve the original finding and explain the correction. No quorum can overrule an unresolved mandatory defect or the owner's explicit rejection.

## Forward enforcement and historical custody

- `reference_acceptance.py` is the shared forward score/binding contract. The critic harness, specialist runner and final closure gate consume it. Final records bind the current policy; stale/missing bindings and interim dispositions cannot approve a task.
- `reference_style_lock.py` detects relevant changes across the declared and discovered current project roots. `shipping_visual_gate.py` checks the source-bound active build project, every selected shipped dependency and explicit final signoff. The current active root is `HavenlineLevel1/`; preserved `HavenlineGodot/` does not automatically ship. A changed or newly selected project root must be declared and bound to build evidence; arbitrary candidate exclusion rules cannot hide shipped content. Source-resolution failures cannot produce an empty-scan approval.
- `validate_migration.py --forward-policy-only` checks the current graph/matrix/policy projections. Its result is policy consistency, not game approval. The migration program's historical receipt checks retain their original recorded scoring rules.
- Historical receipt preservation requires the exact task, candidate, receipt path and pinned SHA-256 bytes. It returns `HISTORICAL_RECEIPT_ONLY` with `approval_allowed: false`. Reusing an old candidate SHA in a new review does not select the historical rule.
- The frozen research package under `ReferenceRefresh/2026-11-27/` remains the evidence of the earlier audit. Its acceptance snapshot is superseded for forward work by this standard. Reproduce a dated audit at its pinned commit; do not relabel old scores or alter its freeze and critic receipts.

The original task identities, dependencies, lifecycle states, ownership, rejected evidence and invalidation records are preserved. No game-wide match score is assigned by this policy work.

## Use on the current candidate

From a checkout containing this policy and the current production tools:

```sh
python3 tools/havenline/production/validate_migration.py --forward-policy-only
python3 -m unittest discover -s tools/havenline/production/tests -p 'test_reference_acceptance.py'
```

Generate a current binding with `reference_acceptance.acceptance_binding()` when preparing a new review packet. Each required raw critic record carries that binding, exact source identity, the full required score map, explicit coverage and defect disposition. Validate each record through `critic_harness.py validate-raw`; use the complete final closure and visual signoff checks for approval. A standalone score check is insufficient.

The source and media gates require Python 3.11+, Git, Pillow, FFmpeg and ffprobe. Missing source objects or media tooling block the relevant check; they do not produce a pass. Historical T03 quorum/supplement and T10 transport/export outputs are explicitly non-approving diagnostics. T12 record/bundle consistency checks also remain pre-disposition checks and do not replace current full closure.

The main-branch tools are available for candidate review. Active development branches must incorporate and run them on the actual candidate before claiming the new standard. This update does not activate archived workflows, alter branch protection, merge gameplay branches or manufacture owner approvals. Those deployment boundaries must remain explicit in any delivery report.
