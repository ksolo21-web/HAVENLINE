# 11c14a1c furnace intake: no three unit-bound stock visuals

**Source-pinned fail-closed result**: even when the opening has earned all 3 wood, the exact stock source cannot support a faithful three-arrival animation. Keep the current authoritative buy result and bought-state reflection. This audit makes no runtime, shader, purchase logic, stock, world, or save changes and issues no engine-dependent claim.

| Exact stock count | Root stock presentation (successful asset fit) | Visible mesh parts | Saved/earned opening IDs eligible | Independently source-bound visible units |
| ---- | ---- | ---- | ---- | ---- |
| 0 | hidden | 0 | 0 | 0 |
| 1 | one representative | 6 | 1 | 0 |
| 2 | same one representative | 6 | 2 | 0 |
| 3 | same one representative | 6 | 3 | 0 |

The six visible GLB parts are three log-model meshes, one lashing and two hitch tails. The same asset's count-independent visibility is the key result, not a lack of mesh components. No ledger lineage maps its three log shapes to the three exact opening wood grants. The native headless checkpoint already retained in `hvn-l1-wood-paid-carry-capture-v1` observed this same exact stock-view code/asset on **two postpaid wood** under isolated paid-pine code, with all six parts at one representative-root transform (not exact baseline 0/1/3 playback). Internal names or GLB node indices are not per-log custody IDs, even where the rendered number happens to match. The unscaled detached two-log transfer experiment does not establish the missing third opening-purchase unit.

## Smallest honest bridge for the larger log lane

1. The detached larger-log presenter should register one distinct real visual for each **outstanding original opening source** (`wood-a`, `wood-b`, `wood-c`) at the actual hero mount, with a one-to-one source key, stable live object ID, kind, real mesh and current affine transform; maps type and quantity from the existing successful ledger read. Only assign source key after authoritative earned stock; 0/1/2/3 must show matching counts with no unregistered representative meshes rendered for the same units. The scale/fit/visual readability decision stays in the larger-log lane; the plot bridge inherits the true visual bounds, not the old 0.40 × 0.22 × 0.24 m representative cap or fixed positions from a two-log test. Keep the postpaid rear storage route separate from this one-shot opening purchase.
2. Observe exactly three currently mounted/visible native units from the same exact alive actor, expected nodes and source registry while approaching the real purchase pad. Cross-check object uniqueness, type/owned source/debit coverage, finite current transforms, actual game camera/route and anchors. This inspection is non-mutating and cannot be an eligibility gate for the existing buy or form a receipt.
3. Exact integrated purchase path `fund_opening_receiver` computes a detached next ledger in the admitted .72m overlap. Its base `_commit_opening_progress` first performs optional save; only after success publishes `ledger = next` and immediately invokes `sync_progress_visuals` (stock becomes zero, paid camp/furnace/gates exposed, V5 pad hides). If a real transfer hook is later authorized, keep transient references and transforms from the pre-commit read. In the same successful synchronous commit **before stock presentation clears or frees sources**, prepare only a render-only handoff of those same three still-valid identities to a scene-local effect, with exact current world transforms and at most one visible owner at every frame. Never remove/reparent before payment success or ask forecasted animation callbacks to delay/succeed the grant. No adapter fault may break authoritative publication. On absence/mismatch, fail to existing safe bought-view behavior with no pretended green progress, no false duplicates and no effect.
4. Only the trusted renderer's real arrivals at the authoritatively paid **purchase** deck advance the three-step fill, with scene/receipt/unique subject guards; model never uses storage deposit callbacks or arbitrary timers to manufacture logs. Paid reload has no live precommit sources: immediately represent already purchased without replay. Keep visible furnace state in sync with any actual colliders; no visual delay that leaves an invisible obstacle. Any new deck shader is opt-in, deck-only, independent of actual collision/save/grant, and needs normal-camera native check.
5. Before any integration, observe ordinary exact pre-pay 0/1/2/3 stock + failed save/invalid target on an isolated native route, capture real transforms and source-bound IDs. On the successful attempt, prove exactly 3 real visual departures/arrivals and 0 retained/presentation duplication. Independently check actual larger-log clearances, receipt identity, original cost/debit/furnace gate outcome, unchanged saves/default project, and normal-camera alpha/green/text readability. A separate replay must show no arrival callbacks/partial fill.

### Repeat the source audit

```bash
cd hvn-l1-furnace-plot-native-intake-v1
export EXACT_HVN_PROJECT=/abs/path/to/pinned/HavenlineLevel1
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v
python preflight.py "$EXACT_HVN_PROJECT"
```

The source pins are the exact Git blob digests embedded in `preflight.py`. Test checks count-independent behavior, exact representative component membership, and fail-closed source/GLB tamper handling. It intentionally never invents instance IDs. No engine or renderer started.
