# C0R Repair Sufficiency Critic Standard

C0R is Havenline's non-voting **Repair Sufficiency Critic**. Its purpose is to stop a builder from spending another candidate/CI cycle on a repair that is plausible for one observed symptom but insufficient for the complete known failure family.

C0R does not approve gameplay, does not score 0-10, does not replace C1-C11, and may never lower a critic, evidence, performance, device, security, or closure threshold.

## Trigger

Run C0R after C0 has produced a validated complete diagnosis and after a repair plan exists, but **before production/tooling repair implementation begins**. T10 is the first canary.

The required repair loop becomes:

`FAILURE -> C0 COMPLETE DIAGNOSIS -> REPAIR PLAN -> C0R SUFFICIENCY REVIEW -> CAUSAL REPAIR -> ROOT-CAUSE PREFLIGHT -> FREEZE SHA -> PROVE -> C1-C11`

A plan rejected by C0R returns to planning. `INSUFFICIENT_EVIDENCE` gathers only the named missing evidence and then re-runs C0R.

## Repair groups

One repair plan may contain several independent causal families. C0R therefore reviews **repair groups**, not one global strategy.

Every C0 blocker must belong to exactly one repair group. A group may contain multiple blockers only when the proposed repair genuinely shares one causal mechanism/failure family. Product, tooling, governance, evidence, and diagnostic blockers are not collapsed into one fake root cause merely to satisfy the gate.

The union of all group `blocker_ids` must equal the complete C0 blocker set with no duplicates and no omissions.

## Questions each repair group must answer

1. What exact invariant failed?
2. What complete failure family is currently observable?
3. Why does the proposed change modify the causal mechanism rather than only the observed number?
4. How is this materially different from prior attempts in the same failure family?
5. What counterexamples could make the repair fail?
6. What blast radius could the repair create?
7. What cheap preflight can falsify the proposal before expensive validation?
8. If the proposal is another scalar/configuration adjustment after repeated same-family failures, where is the full-domain proof?

## Required plan contract

`repair_sufficiency` contains `repair_groups`, an `evidence_frontier`, `cross_group_interactions`, an explicit empty `threshold_changes` collection, and `loop_risk_acknowledged=true`.

The `evidence_frontier` is authored in C0 and copied byte-for-byte into the plan. C0R rejects any difference, so the builder cannot erase a newer failure or move the diagnosis boundary. A newer failure must either be source-bound to an existing repair group as the same causal family, identified as superseded/infrastructure-only, or returned to C0 as a new blocker. Unclassified post-diagnosis failures make the plan insufficient.

Same-family attempt history, the failure frontier, and any full-domain proof are digest-locked to an immutable repair-intelligence manifest outside both C0 and the plan. The manifest retains exact run/candidate/result hashes and a machine-readable proof summary. C0 and C0R validate the lock. C0R derives the attempt count from the locked rows and rejects a plan that omits, rewrites, undercounts, or substitutes them.

Each repair group contains:

- unique `group_id` and exact `blocker_ids`;
- `failure_family.id`, the failed `invariant`, and applicable `scope_dimensions`;
- known failed cases, unexecuted/unknown cases, whether exhaustive observable collection is required/complete, and source-bound collection evidence when completeness is claimed;
- `strategy_kind`, `causal_mechanism`, `why_this_fixes_cause`, and `why_materially_different`;
- same-family attempt count plus prior attempts and lessons;
- one explicit sufficiency row for every blocker assigned to the group, including the exact C0-diagnosed root cause and why the proposed change alters that cause;
- full-domain proof when required;
- cheap falsification preflights;
- counterexamples considered;
- blast-radius hypotheses and residual unknowns.

## Hard anti-loop rules

- Repeated-family operation contract version 2 is mandatory. Each operation's `with` value must byte-equal `IMPLEMENT_SYMBOLS[` plus its exact ordered, unique, identifier-validated `target_symbols` joined by commas plus `]`. Free-form replacement prose, numeric or spelled quantities, whitespace variants, suffixes, extra symbols and alternate order reject structurally. Old or missing operation contract versions require an integration-owner-reviewed migration and regenerated C0R bindings.
- `target`, `invariant_enforced` and causal rationales explain a proposal but cannot authorize source symbols or parameter effects. The English scalar heuristic is defense in depth, not a claim of universal semantic parsing. Typed operations, the executable-source/diff gate and the exact derived-parameter proof channel are authoritative. A rationale cannot substitute for a declared, source-bound parameter effect.
- Two or more failed/partial attempts in the same failure family raise `REPEATED_FAILURE_FAMILY` and require an explicit architectural escalation with a named mechanism and reason.
- A repeated family must declare symbol-bound structured architectural operations, use their deterministic machine rendering as `causal_mechanism`, bind the exact latest failed-candidate comparison base, provide reachable executable-symbol markers, and declare every scalar sink effect one-to-one. Fixed scalar changes raise `SERIAL_SCALAR_PATCH_RISK` and are rejected. A per-case derived parameter is allowed only when its exact normalized RHS depends on named per-case symbols, its bounds have zero violations in the complete domain, and its binding hashes the proof artifact plus the exact proof-source commit/path/file SHA. The proof slice is the canonicalized whole source file, excluding only exact metadata lines named by locked C0 evidence; every such line must occur at most once and, if present, must be inside the single static `contract()` function. The plan must reproduce that policy exactly and cannot add exclusions. The current candidate must match the resulting transitive slice exactly. The post-build gate reconstructs before/after multiline statements and requires the implemented sink RHS to equal that proof-bound expression. Free prose is non-authoritative.
- A product defect cannot be closed by an evidence-only, test-only, or diagnostic-only strategy.
- A group cannot claim its whole failure family is closed unless the complete observable set was collected with source evidence and no required case remains unexecuted or unknown.
- Every blocker must bind to C0's exact diagnosed root cause and explain why the proposed change alters that cause, the expected result, falsifying result, and cheap disproof.
- A claim of complete observable failure-family collection is rejected without collection evidence.
- Every C0 blocker must be assigned exactly once across repair groups.
- C0R rejects stale repair reasoning: the evidence frontier must match C0's diagnosis boundary and account for the latest observed failed candidate.
- Any post-diagnosis failure that cannot be causally bound to an existing group returns `INSUFFICIENT_EVIDENCE` and requires C0 rather than builder improvisation.
- Any critic/quality threshold weakening rejects the entire plan. C0R reads both canonical threshold registries, records their exact hashes and values, and compares the strict `>9.0` unrounded/no-waiver contract rather than trusting an empty plan list.
- The reviewed plan must be bound to the canonical C0 path and exact C0 report SHA-256.
- A provided full-domain proof must equal the locked C0 proof and name positive dimensions whose product equals the case count, an artifact ID, hexadecimal artifact SHA-256, and a retained machine-readable summary whose digest and required results C0R verifies.
- Primary build workflows must fetch and resolve the pinned canonical integration branch, export both its exact name and resolved head, then run the exact builder repair gate in the same direct prerequisite job after C0R and before any build job starts. Neither the plan nor the candidate-editable registry may select the active integration branch.

## Outcomes

- `REPAIR_PLAN_ACCEPTED`: bounded implementation may begin. This is not task approval.
- `REPAIR_PLAN_REJECTED`: revise the proposed repair; do not build another candidate.
- `INSUFFICIENT_EVIDENCE`: collect only the named evidence gap; do not guess.

C0R remains read-only and non-voting. Final task approval remains exclusively with the normal source-bound tests, evidence, C1-C11 critics, integration owner, and closure gates.

Repeated Python causal files require integration-owned whole-source review bindings. Static scalar heuristics are not a completeness proof for Python. The fixed canonical `Docs/Production/ChangeRequests/Txx-repeated-python-source-review.json` binds task, diagnosis, C0 bytes, full repair-group contract, comparison base, every exact before/after regular-file blob and mode, reviewed commit/tree and independent evidence. Missing, extra, duplicate, stale or changed bindings reject. Candidate-local declarations cannot grant authorization. Non-Python derived scalar effects still require the existing whole-source/full-domain proof.

Before any candidate promotion, the integration owner must fetch the pinned canonical branch and execute its exact `verify_python_repair_bindings.py` using `python -I` against the final candidate Git objects. The verifier uses only standard-library code from canonical authority, disables Git replacement objects, and never imports or executes candidate code. Its report binds canonical commit/verifier blob, canonical authorization record, exact candidate commit/tree and every base/reviewed/candidate blob and mode. Preserve the report outside candidate authority. Only the exact reported candidate may be promoted; any merge, rebase, metadata edit or different commit requires a fresh owner run. Candidate workflow results cannot substitute for this mandatory external promotion check. This is an owner-controlled promotion prerequisite, not a claim of preventing arbitrary actors with direct push rights.

The sequence is: independently review and integrate verifier; independently review frozen Python sources and integrate their exact record; reconcile metadata and freeze final candidate; run canonical owner verifier; promote exact verified candidate; run full normal validation and critics. Source review is non-voting and cannot approve T10 or lower thresholds, model/runtime contracts, or GDScript domain-proof requirements. B059 reuses the existing 640-byte projection bound; the exact binding rejects an unreviewed 641-byte substitution without requiring a Python parser to infer its meaning.

The authority lifecycle has three distinct identities: H is the immutable `plan.reconciled_integration_head`; A is the freshly fetched pinned canonical tip; C is the resolved candidate commit. Isolated repair admission requires A=H with H a strict ancestor of C. Integrated repair admission requires A=C with H a strict ancestor of C. Every other relationship rejects, including a stale task branch or a candidate that is only an ancestor of the active tip. No candidate-authored mode flag grants admission. Never rewrite H to C: a commit cannot contain its own hash.

Both contexts read the fixed source-review record from H. The verifier, record and every inherited authorization blob must retain exact bytes and regular-file modes across H, A and C. Both contexts revalidate C0, the complete repair-group contract, exact source blobs, reviewed commit/tree ancestry and the strict reviewed-tree delta policy. The builder invokes this full verifier as a defensive check in both contexts; the separate canonical owner run remains mandatory before promotion. Reports include H, A, C and the derived execution context. A final pinned-ref recheck rejects an in-flight advance. All four existing workflow callers continue fetching the pinned branch and passing active A separately from plan-owned H.

After isolated acceptance, the owner verifies exact S against H=A before canonical promotion. Fresh integrated validation then observes the same immutable H with A=C=S. Closeout leaves the frozen C0/plan/C0R and H intact; subsequent separately authorized evidence records name S. Once the canonical task leaves FIX_REQUIRED, closeout validators govern later metadata rather than rewriting historical repair authority.

Completion also re-queries `origin` with a bounded `git ls-remote --exit-code` call. Exactly one full SHA and the exact pinned branch ref are accepted; the returned tip must equal A. Rechecking only a local remote-tracking ref cannot detect a remote-only advance. Real bare-origin tests preserve the stale local ref while advancing the remote branch.

Canonical promotion requires the owner to run the canonical verifier with `--promotion-check`. This flag adds checks and cannot select an admission context. Exact P must have ordered parents [R,H], where R is the record's reviewed source and H is the immutable authority; H must not be an ancestor of R. Preserve the DAG, exact externally verified P/tree, fresh remote H, request using `force:false`, response, and fresh remote P. Under the mandatory owner-controlled no-force policy (no forced rewinds, deletion or recreation), these constraints make the server's atomic fast-forward-only update accept only H or an already-published identical P. Any competing forward descendant rejects; never retry against a moved tip. This is bounded concurrency protection under that policy, not unrestricted compare-and-swap against forced history changes. Source validation without the promotion flag cannot authorize a branch update.
