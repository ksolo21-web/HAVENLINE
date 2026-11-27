# Havenline acceptance tightening — independent review

**Verdict: PASS for the bounded policy and forward-tooling change. Minimum assessed score: 9.9/10. All mandatory checks passed; no known mandatory finding remains open.**

This is a separate critic review by `/root/plan_critic`, completed on 2026-11-27T11:06:29+00:00. The critic did not edit candidate implementation. This verdict is suitable for the reviewed policy/tooling publication step. It does **not** approve a Havenline task, game build, APK, visual match, motion sequence, audio result or release. The current game score is **unassessed (`null`)**. Publication and remote readback are **pending at this review**.

## 1. Exact reviewed candidate and evidence lineage

- Repository worktree: `/workspace/scratch/e15437dc7c94/HAVENLINE-acceptance-tightening`.
- Base main commit: `7180d1315af56228e7629735c2bd50bda3c43596`.
- Final manifest: `Docs/Production/AcceptanceTightening/2026-11-27/FREEZE.json`.
- Final reviewed content: **63 files**.
- Final content SHA256: **`8f529b23b682c8256b36750786a88065ed859ae9b76206a40899f8fc52027fca`**.
- The final freeze was independently checked before and after final packaging verification. The report and named delivery/checkpoint receipts are excluded from content hashing to avoid self-reference; that exclusion does not make them game approval records.

The full independent regression rerun and 28 separate positive/adversarial probes were completed against the preceding 66-file freeze, `5c1fbd3c446d95b397a730952358e5c52730f2ace588da1ce96ae9a460ac2042`. Publication preflight then found three generated Python cache files inside the evidence package. The builder removed those cache files, added cache rejection to `freeze_snapshot.py` and `validate_scope.py`, and retained the finding in `VALIDATION_HISTORY.json`. The builder reports no production-policy, production-tool or test-source change in that correction.

I inspected that packaging correction, independently reran all 15 preservation checks, verified the corrected freeze, and tested both helpers against injected `__pycache__` and standalone `.pyc` paths. **All 7 final packaging checks passed**, including four negative injections. A separate old full manifest was not retained, so I do not claim a row-by-row old/new manifest comparison. The earlier regression/probe receipts retain their original candidate identity; they have not been relabelled as runs performed after the packaging correction. The final conclusion carries the completed production review across this inspected packaging-only correction.

## 2. Scores and acceptance decision

| Assessed implementation dimension | Score /10 |
|---|---:|
| Requirements fidelity and preservation | 10.0 |
| Numeric and phase enforcement | 10.0 |
| Source and evidence integrity | 9.9 |
| Producer/consumer coherence | 9.9 |
| Coverage and negative-case enforcement | 9.9 |
| Verification and failure history | 10.0 |
| Authority and scope honesty | 10.0 |

The reported minimum is **9.9**, not an average. Every mandatory check below passed independently of the score. These are judgments about the reviewed policy/tooling implementation, not measured similarity percentages or a claim that the game now matches its references. No missing evidence or known failed mandatory requirement was waived to obtain the verdict.

## 3. Mandatory acceptance checklist

| Requirement | Result | Verified behavior or evidence |
|---|---|---|
| Final candidate identity | PASS | Corrected 63-file freeze verified before and after the final packaging checks. |
| Reference threshold and interim boundary | PASS | Every declared relevant final dimension requires at least 9.9 without rounding; 9.5 reference evidence is interim only. |
| Existing stronger visual requirements | PASS | The mandatory dimensions of C1/C2/C3/C4/C5/C11 retain exact 10; ordinary other specialist dimensions retain 9.5 unless a stronger rule applies. |
| Mandatory checks and missing evidence | PASS | No averaging, outvoting, score normalization, missing evidence or known unresolved required defects can authorize final approval. |
| Frozen requirements and review identity | PASS | Policy identity, candidate, task, declared reference dimensions, complete evidence index and original independent reviewer records are bound and checked. |
| Strict original dispositions | PASS | Explicit non-PASS, interim, historical, false/nonboolean pass flags, duplicate JSON keys and invalid/nonfinite score values block current final approval. |
| C1/C2 visual evidence | PASS | Valid distinct-view fixtures pass; coherent relabeling of identical image bytes as multiple views fails for both lanes. |
| C5 motion evidence | PASS | Static specialist is explicitly interim-only. Final external model review requires actual decoded media, full cycle/transition ranges and required coverage. |
| C6 performance producer and consumer | PASS | Original independent scores are preserved; exact measured supplement and valid finite metrics are required. Score-only terminal transport is blocked. |
| C9 deterministic producer and consumer | PASS | Task/index are bound before execution; the consumer checks the current canonical attack matrix, assertions, protocol and actual harness record. |
| Forward closure and authority | PASS | Current signoff, effective dependencies, invalidations and required critic union are enforced; generic status edits and historical exports cannot manufacture approval. |
| Current/discovered project roots | PASS | Active scope, project identity and actual dependencies are bound. Level1 is covered; unused preserved Godot content does not independently decide a scoped current signoff. |
| Artifact bytes and source provenance | PASS | Required raw reports, inputs and media are read and validated; frozen integration media use the selected Git bytes rather than substituted workspace files. |
| Historical preservation | PASS | 70 task definitions/dependencies/statuses, 20 files inside the dated reference-refresh package, protected registries and 11 original receipt files/14 bindings are preserved. |
| T12 lifecycle semantics | PASS | The pre-disposition aggregate wrapper is separately validated and remains non-approving; individual final critic rows require explicit PASS and boolean passed=true. |
| Packaging and deployment limits | PASS | Both scope and freeze helpers reject Python cache artifacts. No game/runtime/assets/archive/workflow changes or current game approval are included. |

The threshold interpretation is coherent: **9.5 is only an interim reference-review threshold; 9.9 is the unrounded minimum for each relevant final reference dimension; existing exact-10 requirements remain stronger.** Exact 10 describes completion of the agreed observable requirements with no known unapproved deviations. It does not assert pixel identity, a numerical percentage of artistic similarity or infallibility of a reviewer. Named mandatory specifications remain pass/fail requirements in addition to scores.

## 4. Substantive findings repaired and retested

This was an actual reject/repair/retest cycle. Initial findings and the failed pre-final T12 run remain in the evidence package. The final result does not overwrite them.

1. **Stale numeric and historical approval routes.** Current task packets, metadata and forward projections now state the current rule. Legacy quorum classifications, old receipts and task-specific exports are retained as history and cannot authorize a new final approval. New reviews of old candidates are subject to the current policy.
2. **Unfrozen reference dimensions and score manipulation.** Reference-sensitive dimensions now come from frozen inputs. Review outputs cannot silently omit them, round up a deficient score, substitute an average, invent all-10 scores or convert a nonfinal original disposition into PASS. Strict parsing blocks duplicate keys, nonfinite numbers and invalid boolean/disposition forms.
3. **Weak original-report and transport binding.** Empty or mismatching raw reports, missing actual input manifests, altered evidence-index identities, contradictory original scores and failed/interim/historical original responses are rejected. The original request/session and reviewer response remain part of approval evidence rather than being replaced by a summary claim.
4. **C5 contact-sheet overclaim.** The static specialist lane is expressly interim-only. A legitimate final C5 route requires an independent model session and actual decoded motion evidence with full cycle and transition coverage. Human owner signoff supplements the required model lane; it cannot replace it by changing a label.
5. **Lane spoofing and producer/consumer gaps.** External transport is limited to C1/C2/C5; specialist transport is restricted to its real supported lanes. C6 now has a usable independent scored-performance import route that preserves original scores and checks the exact measurement supplement. C9 terminal approval consumes the current validated deterministic attack record, prebound to task and evidence index. Neither can be replaced by generic score JSON.
6. **C9 canonical assertions.** A substituted weaker attack matrix with the same attack IDs no longer passes. The current canonical matrix path, bytes/hash, protocol and assertions are checked, along with the actual result record.
7. **Current-source signoff and dependency reuse.** Current closure checks effective dependencies, active invalidations, current visual signoff and required critics. Historical approvals, old candidate identities, a clean diagnostic scan or generic state mutation cannot manufacture current approval.
8. **Project scope and real artifact custody.** Active Level1, preserved Godot, actual runtime dependencies and newly discovered projects are distinguished through bound source scope. A preserved unused project does not independently invalidate an otherwise valid selected current scope; relevant new/dependent sources cannot be omitted. Frozen integration review reads the selected Git media bytes even if workspace media later changes.
9. **Aggregate-versus-critic disposition.** T12's legitimate `CRITIC_REVIEWS_COMPLETE` wrapper remains a separately checked, non-approving lifecycle result. Each actual final critic row still requires PASS and boolean `passed=true`. The repaired positive cases and negative interchangeability cases pass without weakening the final status rule.
10. **False multi-view coverage.** Identical image bytes relabelled as front and side views previously passed C1/C2 structural coverage. The final code rejects duplicate candidate bytes and requires distinct capture bytes and camera identities. I independently confirmed the coherent negative case fails for both critics and legitimate distinct-view positives still pass.
11. **Generated cache packaging.** Three compiled cache files were removed before remote mutation. Both content freezing and scope validation now reject these artifacts; four independently injected cache cases were rejected.

## 5. Independent verification

The critic independently reran the packaged suite, directing only report output to a separate scratch directory. The implementation and test sources remained in the candidate worktree. This was an actual execution, not acceptance of the builder's summary.

**Regression result: 207/207 tests passed across 18/18 groups, with 0 failures, 0 errors and 0 skips.** The earlier smaller runs are not added to this total.

| Test group | Tests | Result |
|---|---:|---|
| production/test_reference_acceptance.py | 18 | PASS |
| production/test_specialist_safeguards.py | 16 | PASS |
| production/test_specialist_critic_runner.py | 9 | PASS |
| production/test_forward_review_evidence.py | 14 | PASS |
| production/test_performance_review_transport.py | 4 | PASS |
| production/test_workstream_status_authority.py | 5 | PASS |
| production/test_reference_style_lock.py | 15 | PASS |
| production/test_shipping_visual_gate.py | 21 | PASS |
| production/test_forward_acceptance_policy.py | 8 | PASS |
| production/test_repair_sufficiency_critic.py | 33 | PASS |
| production/test_future_prep_packets.py | 4 | PASS |
| production/test_t05_completion.py | 5 | PASS |
| task12/test_critic_review_records.py | 17 | PASS |
| task12/test_final_candidate_gate.py | 22 | PASS |
| task10/test_aggregate_critics.py | 7 | PASS |
| preserved_historical_raw_and_aggregate_semantics | 4 | PASS |
| legacy_quorum_is_nonapproving | 4 | PASS |
| historical_export_cannot_authorize_current_approval | 1 | PASS |

**Separate independent probes: 28/28 passed.** These include coherent C1/C2 positives; coherently rebound identical-byte multi-view negatives; PENDING/lowercase-fail/UNKNOWN and nonboolean disposition negatives; empty raw evidence; evidence-index relabeling; original FAIL normalization; exact-10 acceptance and 9.99 rejection for each of C1/C2/C3/C4/C5/C11; ordinary specialist 9.5; and rejection of 9.899999 versus acceptance of 9.9 on a declared reference dimension.

**Preservation: 15/15 passed again on the final corrected package.** This includes unchanged task definitions/dependencies/statuses, protected registry and invalidation bytes, 20 files physically inside the dated ReferenceRefresh directory, 11 original receipt files across 14 task/candidate bindings, stronger gate values and inactive historical workflows. T71–T80 are still not invented as defined tasks. Root navigation files intentionally updated by this authorized change are not misrepresented as unchanged merely because an earlier refresh manifest also listed them.

**Forward-policy consistency: PASS.** The dedicated forward check was independently executed before the packaging-only correction; the relevant policy and validator implementation were unchanged by that correction. It explicitly does not grant game approval.

**Final packaging: 7/7 passed.** Final content identity matched before/after, the 15-check scope validator passed, and both helpers rejected each of the two cache forms.

## 6. Remaining limits and publication conditions

There are **no open mandatory defects within this bounded change**. The following are limits of what was reviewed, not completed game work:

- No real Havenline visual/reference match, APK behavior, full animation, audio listening, physical-device run or actual game-performance result is certified here. Test review records and media are explicitly synthetic fixtures, even where actual decoding is exercised.
- Structural validation can prove matching identities, retained source bytes and complete declared evidence. It cannot mechanically establish that an independent reviewer truthfully watched every sequence or that an artistic judgment is correct. Actual independent source comparison and required playback remain mandatory. The C5 static runner still cannot supply that final approval.
- The T12 consistency tests use an explicitly synthetic bundle identity because the historical consolidated workflows remain inactive. They do not certify the full historical workflow environment. All legacy architecture/workflow-wide suites and live external reviewer-service operation are outside this scoped run.
- This report does not activate workflows, remove owner holds, revise old receipts, approve another branch or grant a build a score by inheritance. Future candidate/source changes require current evidence under the new policy.
- Remote publication and readback were pending when this report was signed. The parent must complete the intended expected-main publication and verify its resulting content before reporting delivery. This critic makes no remote-deployment success claim.

Any later discovered mandatory defect reopens this verdict. Any change to the reviewed content requires a new freeze and a proportionate review of the change.

## 7. Evidence custody

The following independent evidence is outside the candidate so the parent can preserve it without changing reviewed implementation. The complete structured review is `/workspace/scratch/e15437dc7c94/acceptance-critic-checks.json`. Final package evidence is under `/workspace/scratch/e15437dc7c94/acceptance-critic-final-package`; the original independent regression evidence is under `/workspace/scratch/e15437dc7c94/acceptance-critic-final-suite`.

| Independent artifact | SHA256 |
|---|---|
| `FREEZE.json` | `2069b676c1b48eb080c95f476905e026406e44ae865dc0f99b8ee19e38b2de76` |
| `PACKAGING_CHECKS.json` | `b2f220042ec58b0858f995c7f7ed8cfd41c2a54259438f95d27ebfbcb3241060` |
| `SCOPE_VALIDATION.json` | `2b81724c0c3a64da8d402f91daefd7be79c6306db22b2ba549f249b5e59f1986` |
| `TEST_RESULTS.json` | `adc5d9525bb69f8745c97f3ddc38371245be18f8632e1ed267377794f89a4271` |
| `TEST_OUTPUT.txt` | `d9aa81ea1da225c4e07c7289b6bb606bd02e7855232876810a04b06c77429e03` |
| `acceptance-critic-final-probes.py` | `7d557b7042847429fd13aebdc8c83cdab1aa9d3ffa70ccee75df28363d743809` |
| `acceptance-critic-final-probes.json` | `355a9969d073f01453a50479e6cc5f850a89896ebb97428c8e309d020b9cebe8` |
| `acceptance-critic-initial-findings.md` | `ca3b2f3633bdc99549413c7bb34133600ede2173f2ec71fc9e8065a21ad1a2f9` |

The parent may copy this review and its structured summary byte-identically into the named excluded independent-review receipt paths. The scoped verdict remains **PASS, minimum 9.9/10, no current game score, publication pending at review**.
