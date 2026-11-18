# HAVENLINE — exhaustive branch cleanup audit
**Audit:** 2026-11-18 · **Branch snapshot before handoff:** `b982a2a3339b172b6aaaefac1ae24ecea63307ab` · **Owner decision required before deletion**

**Counts (mutually exclusive):** 79 branches = 1 default main + 19 open-PR heads + 17 ancestor-of-integration + 4 ancestor-only-of-T05 + 4 exact-tip duplicate references + 34 other divergent references. **No branch has been deleted.**

## Method / safety
GitHub REST `/branches` returned 79 names. All 19 open-PR heads were matched using `/pulls?state=open`. For the other 59 non-default branches, `compare(base=branch,head=codex/havenline-sequential-task-01)` was run; if not fully contained, `compare(base=branch,head=havenline/T05-r18-visual-corrections-20261025)` was run. "Fully contained" means `behind_by=0`: deleting that ref does not remove commits from the retained head. This **does not guarantee content is on main**, which is stale. Exact-tip duplicates use identical Git SHA hashes. Diverged means unique commits exist, not necessarily unique files (squash/cherry-pick merges can retain equivalent content).

## A. 17 prune candidates — entire branch history is already in active integration
**Can delete these non-open-PR names once the integration branch has a preserved recovery tag and its upstream integration plan is confirmed.** The commits already exist on `codex/havenline-sequential-task-01`, which is itself an ancestor of active T05.

- `havenline/T04-camera`
- `havenline/T06-character1`
- `havenline/T09-harvesting`
- `havenline/T10-world-transformation`
- `havenline/T11-camp-construction`
- `havenline/T12-progression-architecture`
- `havenline/governance-t12-activation`
- `havenline/governance-t12-assignment`
- `havenline/governance-t12-integration-ready`
- `havenline/governance-t12-preactivation-buildout`
- `havenline/governance-t12-scope-prep`
- `havenline/governance-t12-v32-handoff`
- `havenline/governance-v32-forward-control-plane`
- `havenline/governance-v32-intelligence-closeout`
- `havenline/governance-v32-workflow-registration-fix`
- `havenline/v32-control-plane-lineage-repair`
- `repair/native-timeout-contract-20260926`

## B. 4 more prune candidates — history is contained ONLY in the active T05 branch
**Conditional:** preserve/tag T05 and its unique art sources before deleting these; they are NOT contained in the integration branch yet, so deleting T05 later would risk losing their reachable history.

- `havenline/T05-r01-checkpoint-revert`
- `havenline/T05-r01-full77-staging-20260927`
- `havenline/T05-r10b-materializer-event-20260927`
- `havenline/T05-r18-owner-20261013`

## C. 4 redundant references — exact SHA duplicates, keep the named survivor
After confirming each **keep** branch remains, removing the **delete** branch does not remove its tip commit:

| Delete reference | Retain reference | Identical SHA |
|---|---|---|
| `codex/t03-reviewer-backup-075c9e` | `codex/t03-reviewer-semantics-repair` | `075c9e937d607b0ba28a64ee345e0084e1124091` |
| `havenline/t13-t14-handoff-hardening-final2` | `havenline/t13-t14-handoff-hardening-final` | `4d50285d5faf967d3b9f1f1ed64960397a938665` |
| `havenline/t13-t14-handoff-hardening-lint` | `havenline/t13-t14-handoff-hardening-final` | `4d50285d5faf967d3b9f1f1ed64960397a938665` |
| `havenline/t13-t14-handoff-hardening-validation` | `havenline/t13-t14-handoff-hardening-final` | `4d50285d5faf967d3b9f1f1ed64960397a938665` |

These four branch names have no open PR. **Retain the survivor until its divergent commits are reconciled.** Do not remove BOTH sides of either SHA group.

## D. 34 divergent, no-open-PR branches — DO NOT BLINDLY DELETE
These branch tips each have commits not reachable from either retained integration or active T05 head (after accounting for exact-tip aliases above). Some are old merged/squashed PRs, closed but unmerged trials, or unused governance preparations. **Audit exact file changes/commit SHAs and save distinct work before deletion.** Historical PR status alone is insufficient to prove that all changes were integrated.

- `astra-webgl-review/2026-09-06`
- `codex/havenline-environment-calibration`
- `codex/havenline-visual-critic`
- `codex/t03-reviewer-semantics-repair`
- `havenline/QA-integration`
- `havenline/T03-reference-art-20260926`
- `havenline/T05-props`
- `havenline/T05-r01-v4-review-20260927`
- `havenline/T05-r10-final-review-20260927`
- `havenline/T05-r10c-source-check-20260927`
- `havenline/T07-context-director`
- `havenline/T08-visible-inventory`
- `havenline/global-asset-pipeline-v1-20261026`
- `havenline/governance-all-t13-t70-ready`
- `havenline/governance-c0-terminal-evidence`
- `havenline/governance-c0r-workstream-authorization`
- `havenline/governance-image-reconstruction-probe`
- `havenline/governance-reference-style-lock-20260922`
- `havenline/governance-reference-style-scope-repair-20260922`
- `havenline/governance-t09-strict-review`
- `havenline/governance-t10-prep`
- `havenline/governance-t11-prep`
- `havenline/governance-t12-prep`
- `havenline/governance-t13-build-pending`
- `havenline/governance-t13-c2-evidence-repair`
- `havenline/governance-t13-preactivation-sync`
- `havenline/governance-trusted-lineage-test`
- `havenline/permanent-native-material-critic-20261027`
- `havenline/reference-whiteout-ad-pack-20260922`
- `havenline/t13-t14-handoff-hardening`
- `havenline/t13-t14-handoff-hardening-final`
- `havenline/t13-t70-activation-frontier`
- `havenline/t13-t70-metadata-hardening`
- `havenline/t13-t70-provenance-hardening`

## E. 19 open-PR head branches — HOLD until PR disposition is recorded
No branches from this category belong to immediate delete candidates.

| PR | Live head | Notes |
|---:|---|---|
| [#106](https://github.com/ksolo21-web/HAVENLINE/pull/106) | `havenline/governance-t12-activation-20261028` | Active/open PR; retain until reviewed |
| [#105](https://github.com/ksolo21-web/HAVENLINE/pull/105) | `havenline/governance-permanent-native-material-critic-20261028` | Active/open PR; retain until reviewed |
| [#103](https://github.com/ksolo21-web/HAVENLINE/pull/103) | `havenline/global-asset-pipeline-integration-20261026` | Active/open PR; retain until reviewed |
| [#101](https://github.com/ksolo21-web/HAVENLINE/pull/101) | `havenline/T05-r18-visual-corrections-20261025` | T05 stacked visual-repair chain; no merging until art acceptance |
| [#100](https://github.com/ksolo21-web/HAVENLINE/pull/100) | `havenline/T05-visual-repair-20260926` | T05 stacked visual-repair chain; no merging until art acceptance |
| [#99](https://github.com/ksolo21-web/HAVENLINE/pull/99) | `havenline/T05-r01-v4-exact-ci` | T05 stacked visual-repair chain; no merging until art acceptance |
| [#92](https://github.com/ksolo21-web/HAVENLINE/pull/92) | `havenline/governance-current-pr-base` | Active/open PR; retain until reviewed |
| [#88](https://github.com/ksolo21-web/HAVENLINE/pull/88) | `havenline/T13-challenge-director` | Active/open PR; retain until reviewed |
| [#19](https://github.com/ksolo21-web/HAVENLINE/pull/19) | `havenline/governance-t62-t70-prep` | Active/open PR; retain until reviewed |
| [#18](https://github.com/ksolo21-web/HAVENLINE/pull/18) | `havenline/governance-t53-t61-prep` | Active/open PR; retain until reviewed |
| [#17](https://github.com/ksolo21-web/HAVENLINE/pull/17) | `havenline/governance-t44-t52-prep` | Active/open PR; retain until reviewed |
| [#16](https://github.com/ksolo21-web/HAVENLINE/pull/16) | `havenline/governance-t33-t43-prep` | Active/open PR; retain until reviewed |
| [#15](https://github.com/ksolo21-web/HAVENLINE/pull/15) | `havenline/governance-t21-t32-prep` | Active/open PR; retain until reviewed |
| [#13](https://github.com/ksolo21-web/HAVENLINE/pull/13) | `havenline/governance-t13-t20-prep` | Active/open PR; retain until reviewed |
| [#5](https://github.com/ksolo21-web/HAVENLINE/pull/5) | `codex/havenline-sequential-task-01` | Central integration lineage (preserve) |
| [#4](https://github.com/ksolo21-web/HAVENLINE/pull/4) | `codex/havenline-environment-review` | Legacy integration chain, evaluate before moving main |
| [#3](https://github.com/ksolo21-web/HAVENLINE/pull/3) | `codex/havenline-native-completion-20260907` | Legacy integration chain, evaluate before moving main |
| [#2](https://github.com/ksolo21-web/HAVENLINE/pull/2) | `codex/havenline-godot-android` | Legacy integration chain, evaluate before moving main |
| [#1](https://github.com/ksolo21-web/HAVENLINE/pull/1) | `agent/havenline-v7-unity-review` | Legacy integration chain, evaluate before moving main |

## F. Default branch — retain, do not delete
- `main` — `0c3625b745d1729121ec13e3e0a267eb3a91e68b`, still at 2026-08-02 baseline; branch API returned `protected=false`. Set up suitable protection/rulesets and get the Godot integration history released safely rather than force-pushing active T05 experiments directly to main.
- Integration `codex/havenline-sequential-task-01` — `f74a84a2a288ab3d3935fba7a6cb9b975c2df239`, 1,502 commits ahead of main.
- Active T05 `havenline/T05-r18-visual-corrections-20261025` — pre-handoff `b982a2a3339b172b6aaaefac1ae24ecea63307ab`, 401 ahead of integration, 0 behind; PR #101 draft, DO NOT MERGE while cooker art fails.

## Cleanup sequence (without data loss)
1. Capture git SHA manifest/tag backup of all 79 refs, build artifacts and open PR references; verify no hidden rulesets or branch dependencies. Obtain explicit authorization for actual deletion.
2. Preserve main, integration and active T05; clear up the nested PR #2 → #4 → #5 integration chain and #99 → #100 → #101 T05 chain without bypassing art/authorization gates.
3. Prune A's 17 fully-contained refs and B's four T05-contained refs **only after T05's source safety is guaranteed**.
4. Prune C's four same-SHA alias names while retaining each corresponding survivor.
5. Review D's 34 divergent branches via merge-base, diff and PR ancestry; bring forward only valuable unique work; archive rejected branches and delete only after verification. Priority: old T05 staging, T03/QA, governance v32, T13/T14, superseded material-critic PR and reference pack.
6. Resolve the 19 open PRs individually, close stale stacked PRs with clear supersession notes, and only then delete their head branches if no unique code remains. Do NOT silently close PR #101 or overwrite the still-unapproved T05 artwork.
7. Target topology: protected `main` + one tested integration branch while migration is incomplete + one active T05 feature branch + genuinely active parallel tasks. New short-lived work flows via reviewed PRs, not nested governance branches.
8. After cleanup, re-list branches, compare exact saved SHAs, run Godot build/regression and candidate authorization gates, and publish a new audit. Mark failures honestly.

**Current cleanup execution:** ZERO deleted / ZERO PRs closed / ZERO merges or rebases done. This file is a verified candidate list, not authorization to destroy work.
