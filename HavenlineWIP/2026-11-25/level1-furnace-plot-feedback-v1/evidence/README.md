# Level 1 furnace purchase marker: detached presentation contract

**A tested control model, not a game patch.** Does not change the opening, asset, ledger, saves, collider, furnace, camp, or storage. No Godot run or rendered art approval.

**Reference:** owner supplied 124510 at approximately 5.30s (gray deck and white corner marks); 5.38s (green corners on overlap); ~5.55–5.94s (green front-to-back fill following arriving wood); ~6.02s (full green); ~6.10–6.18s (marker shrinks away on the original ground anchor as the furnace becomes visible). Timing and colors are a visual reference, not exact physical or color-managed measurements. Never adopt the ad’s 200-unit UI; Havenline stays at **3 wood**. The rear receiving plot at ~27.35–28s is a different widget: dark deck and cream/gold marker, with wood arriving on top; it must not take this purchase shader or animation.

| Stage | Render contract |
| --- | --- |
| Idle | Existing matte slate/gray deck, light corner inlays and cost, fill weight zero. |
| Armed | After trusted contact/reach **and** eligibility, give all four corners a vivid lime accent; no fill, deduction, or furnace reveal. Leaving returns to gray. |
| Paying | Only after authoritative success, show the three owned presentation subjects from their validated left/right carry anchors. Each distinct accepted arrival advances the target by exactly 1/3. A 4-tick sweep cannot pass the number arrived. Near cost edge remains the authored edge even as the camera follows the player. Keep white/icon/cost overlays separate and legible. |
| Complete | After the third arrival and its short sweep finish, hold full lime for 5 ticks, then shrink and fade from the existing ground anchor over 8 ticks. The controlled reveal overlaps the start of the shrink. Logical receipt and collision state are not controlled by this view. |
| Recovered / fail-back | With an already-paid snapshot, just reflect the paid furnace and hide the marker. If optional animation cannot finish in time, immediately restore the same authoritative paid presentation without pretending remaining wood arrived. No visible fake full state. |

Tick counts are first bounded 60Hz fixture values, not final pacing. The 45-tick window is a visual recovery guard, not persistence, game action or a tick-rate guarantee. Isolated Python test:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v
```

The executable is renderer-neutral: output values identify corner role, fractional near-edge mask and target, anchored marker scale/opacity, cost line, and whether to expose the **already committed** furnace. Use a local projected deck mask on `PurchaseDeck_Surface` only, not uniform green coloring or the surrounding terrain, border geometry, icon, or text. The cost must remain legible at normal phone camera during approach, arrival, and exit. Colors should be chosen under the actual game light from the approved grate art, keeping the test render comparable to the reference; this module does not specify color-space-correct material values.

## Exact baseline hook and checks before implementation

Pinned 11c14a1c41971067c7dc97db69375f720a408f68: opening source blob 8de9499b…; integrated preview cc54fb10…; purchase bridge 4b00374a…; V5 adapter 43f88e9d…. Exact receipt is `{offer:"center-hearth", typed_debit:{wood:3}, grant:"center-hearth", revision:1}`.

1. Current integrated input attempts `fund_opening_receiver` each physics tick through logical-reach .72. Ordinary approach/affordance is the only place to drive armed corners. Never condition authority on this Python diagnostic or on presentation arrival.
2. In current `_commit_opening_progress`, save (if applicable) can fail before `ledger = next`. It then synchronously calls `sync_progress_visuals` which clears spent stock presentation, updates gate/camp, and immediately calls `reflect_published_state(built)` (available/accepted only, straight to hidden). A future adapter must capture the **pre-commit** presentation subjects and true transforms without changing source ownership yet; **after** confirmed success it would detach only those three cloned or transferred presentation subjects as explicitly admitted. No current three IDs are established by this test. Never pass fake IDs, mint spendable objects, hide stock before success, or animate from build input/cloud save replay alone.
3. Existing accepted stock, routes, fence/gate timers and collisions must remain unchanged. The furnace is centered away from the plot. Any conceal/reveal hold risks an invisible authoritatively solid furnace or obscured gate/floor: require exact scene branch and route proof for the full hold; if that is not guaranteed, reflect the authoritative furnace immediately and take no hold/reveal dependency. This contract is not an approved integration, and it intentionally cannot write or modify the existing scene.
4. Bind genuine arrivals to a private per-scene sender and subject identity, not public arbitrary puzzle/UI calls. The Python methods only model trusted adapter events; their type/schema guards do not prove payment or motion. Use native success/failure/reload tests and independent normal-camera review, including stable world anchor, visible paint/text, distinct larger real logs, real input/receipt and no changes to storage, gates, stock, or player collision.
