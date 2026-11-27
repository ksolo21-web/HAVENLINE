# Havenline acceptance tightening — evidence and handoff

This package records the authorized change from a general 9.5 review floor to explicit final reference acceptance, with executable checks and an independent repair/retest cycle. It does not assign a gameplay score or certify a build.

## Current rules

Use [REFERENCE_ACCEPTANCE_STANDARD.md](../../REFERENCE_ACCEPTANCE_STANDARD.md) and [REFERENCE_ACCEPTANCE_POLICY.json](../../REFERENCE_ACCEPTANCE_POLICY.json). Reference-sensitive final dimensions require at least 9.9 individually and unrounded. Preserve the existing stronger exact-10 requirements across all mandatory visual dimensions. A reference-sensitive 9.5 result is an interim checkpoint only. Other mandatory specialist dimensions retain at least 9.5; every concrete mandatory check still passes independently.

New reviews require current policy binding, complete source-bound evidence, actual independent reviewer outputs, zero known unapproved deviations and all existing owner approvals. The current external review format is documented in [EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md](../../EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md).

## Reproduce the scoped checks

From the repository root, with Python 3.11+, Git, Pillow, FFmpeg and ffprobe:

```sh
python3 tools/havenline/production/validate_migration.py --forward-policy-only
python3 Docs/Production/AcceptanceTightening/2026-11-27/validate_scope.py
python3 Docs/Production/AcceptanceTightening/2026-11-27/run_regression_checks.py
```

The reports are [SCOPE_VALIDATION.json](SCOPE_VALIDATION.json), [TEST_RESULTS.json](TEST_RESULTS.json), and [TEST_OUTPUT.txt](TEST_OUTPUT.txt). Test cases use explicitly synthetic reviews and local fixture media to prove validator behavior. They are not real game approvals. T12 cross-record consistency tests isolate bundle identity with an explicit synthetic fixture; the inactive historical workflow-dependent bundle is not claimed operational. Architecture-wide legacy workflow suites are outside this bounded run.

[INITIAL_INDEPENDENT_FINDINGS.md](INITIAL_INDEPENDENT_FINDINGS.md) preserves the critic's initial rejects. The final independent review identifies the frozen content it inspected and the outcome after repairs. `FREEZE.json` binds the policy, code, templates, tests and handoff text. Mutable verification/publication/checkpoint receipts are excluded from that digest to avoid circular hashes.

## Preserved work

The original 70 task definitions, dependencies and lifecycle states are unchanged. T71–T80 remain undefined. Eleven original completion receipts remain byte-identical, with fourteen recorded task/source bindings. The twenty files inside the earlier frozen reference-refresh package remain byte-identical. Current ownership, invalidations, renders, runtime sources and the repository archive remain preserved. A historical receipt validates history and never supplies a new approval.

The active shipping project is selected from source-bound build evidence. The current canonical active root is `HavenlineLevel1/`; unused preserved `HavenlineGodot/` does not automatically ship. New roots and actual dependencies cannot be silently omitted.

## Capability and deployment boundaries

The contact-sheet C5 runner performs interim static screening. A final motion review needs an actual separate playback session and complete decoded clip coverage; changing a label cannot promote a static review. Deterministic performance/security evidence and independent judgment remain distinct required evidence where applicable.

This change publishes current policy and gate code on `main`. It does not restart archived jobs, install branch protection, merge active gameplay branches or manufacture owner approval. Active candidate branches must incorporate and run the current tools before claiming compliance. Current dependency approval is bound to the requested candidate; old task status alone cannot satisfy it.

No new actual game, APK, audio-listening, physical-device, performance or whole-game 9.9 approval is issued here. The independent score in this package applies to the policy/tooling work only.

## Resumption

Read `CHECKPOINT.json` for the exact base, completed milestones, open actions and publication status. Read `PUBLICATION.json` for the remote commit and readback once published. `BRANCH_BASELINE.json` is a read-only branch snapshot taken during this task; other branches may advance independently. Publication updates only `main`, using an expected prior SHA and a normal fast-forward.
