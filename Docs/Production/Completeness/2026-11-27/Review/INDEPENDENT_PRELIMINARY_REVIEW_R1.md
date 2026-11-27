# Havenline completeness — preliminary independent review R1

**Status: changes requested; no final candidate score or game approval.** The builder is still integrating the package.

Reviewed actual12 selected design decisions,24 core requirements,10 transaction boundaries and100 authored progression rows against the preserved main source. Four reviewed design snapshots are retained under `PreliminaryReviewR1/`. The independent validator reject and regional false-pass probes are preserved separately.

## Findings

| ID | Area | Finding and required disposition | Current status |
|---|---|---|---|
| PR01 | CD09 / event_reward | Offline event participation and earned-but-unclaimed-at-expiry behavior were left as pending-or-unavailable alternatives. **Fix:** Select an explicit online verification/claim policy; preserve a verified completion claim across expiry and lost commit response; keep core offline play usable. | ROOT_ACCEPTED_REPAIR_PENDING_RETEST |
| PR02 | CD04 / CG13 | No permanently idle actor and always-useful reserve wording can reject legitimate rest/no-eligible-job state and pretend a guard inside an invulnerable camp is necessarily useful. **Fix:** Distinguish selected expedition pets, escort survivors, independently assigned local workers and valid ready/rest states. Stuck idle only fails when valid authorized work exists. | ROOT_ACCEPTED_REPAIR_PENDING_RETEST |
| PR03 | M2/M3 implementation order | The selected milestone sequence puts a survivor loop/stakes before the T21 combat foundation, although T23 depends on T21. **Fix:** Put T21 shared combat/contact prerequisites before survivor production integration; independent preparation may continue. Preserve DAG. | ROOT_ACCEPTED_REPAIR_PENDING_RETEST |
| PR04 | CD02 / PE08 / Level1-3 | Last restored safe camp differs from nearest established safe point, and neither defines early zero-health recovery before the first restored camp at Level3. **Fix:** Choose one return rule, retain a guaranteed initial recovery anchor, restore a playable health/control state, and leave exact HP/care duration as honest tuning. | SENT_TO_ROOT_AND_ECONOMY |
| PR05 | PE10 owner mapping | Worker reservations/scheduling are still assigned to T07 despite its frozen human-selector scope and actor draft correction. **Fix:** Use worker/job owners; T07 is an authorized shared-control integration consumer. | SENT_TO_ECONOMY |
| PR06 | Levels75/95/98 | Level95 and98 currently read as implementation/acceptance demonstrations rather than specific player outcomes; Level75 unconditionally invokes pet defense while pet availability is marked optional. **Fix:** Bind95/98 to actual existing-scope world changes or objective receipts. Clarify the no-deployed-pet equivalent for75 or deliberately select and disclose a free companion prerequisite. | SENT_TO_ROOT_AND_ECONOMY |
| PR07 | CD07 versus underwater region details | Root selected protected dry underwater routes while detail text introduces swimming/work approaches where needed. **Fix:** Reconcile the actual selected locomotion/work policy; do not silently add a swimming/gear system under a dry-route decision. | SENT_TO_ROOT_AND_ECONOMY |
| PR08 | PE12 / T53 | The global transport owner is later than all region tasks; detail must not make T53 implementation a backward prerequisite for their local entrances/exits. **Fix:** State that each introducing region authors/proves its local transition interface and T53 integrates the complete network afterward. | SENT_TO_ROOT |
| PR09 | resource_actor_contract.py acquisition action map | New map used chop→chop and fishing→fish but canonical actions are gather_wood/fishing, rejecting valid untouched registries. Independent run recorded34 methods with25 failures including subtests. **Fix:** Correct code alias mapping, preserve registry bytes, retain reject and rerun. | BUILDER_REPAIRED_PENDING_INDEPENDENT_RETEST |
| PR10 | T44 resource profile coverage / C5 | A new regional resource with valid new human profiles passed while omitting player/helper coverage; human-only scope also skipped C5 when animation_delta=false. **Fix:** Derive applicable phase-specific profile coverage and require truthful regional contact review without forcing new clips or backward T09 dependencies. | BUILDER_REPAIRED_PENDING_INDEPENDENT_RETEST |

## Positive findings

- All seven pets must cause useful legitimate damage; specialties remain additional value.
- Protected earned value, free recovery, simple controls and no mandatory new survival meters fit the existing ordinary-play scope.
- Unlimited logical worker cargo is explicitly a new selected forward rule, with bounded job reservations/visuals.
- No obvious commodity unlock cycle found in the100 outcome ordering; resource first-source/use timing still needs actual quantities and runtime tests.
- Optional premium identity, render reserve and no new launch event token avoid unnecessary economy proliferation.
- Every core row preserves unproved implementation state and undefinedT71–T80 remain open.

## Verification limits

The first independent focused validator run executed34 test methods and reported25 failures including subtests, caused by the new action-name mapping regression; its complete raw output is retained. Subsequent builder repairs require independent retest. Two synthetic regional-resource probes reproduced real false passes in coverage/motion-gate handling. These are planning-tool tests, not gameplay or visual evidence.

No production runtime or archive file was edited by this critic. No remote write was performed. Final review will bind an exact freeze and evaluate all18 mandatory checks.
