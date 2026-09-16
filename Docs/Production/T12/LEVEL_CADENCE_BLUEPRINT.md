# T12 non-shipping Level 1–100 cadence blueprint

**Status:** PREPARATION ONLY. This is not `progression_levels_v1.json`, does not activate T12, and must not be treated as shipping progression data. Exact T10/T11 IDs remain provisional until those tasks are approved/integrated and T12 activation reconciliation passes.

## Purpose

Pre-decide the structural cadence T12 must enforce so the builder does not spend activation time inventing progression rules. The blueprint defines *roles and validation expectations*, not final rewards, prices, difficulty values, region content or upstream IDs.

## Permanent cadence constraints

1. Exactly 100 ordered shipping levels, 1–100.
2. Every level has at least one practical progression effect/unlock; counter-only filler is invalid.
3. No more than three consecutive levels may pass without a declared visible-progression hook.
4. Each ten-level band ends in a major milestone/transition hook unless an accepted design record explicitly moves that milestone within the same band.
5. Level eligibility is spend-blind: purchase history, VIP and premium-spend signals are invalid prerequisites.
6. No energy-wall prerequisite and no logical carry-capacity progression.
7. T13 owns adaptive difficulty; T12 may expose progression context to T13 but may not pre-tune Challenge Director behavior.
8. T14 owns persistence/versioning; T12 IDs must be stable and persistence-ready but T12 must not define the global save schema.
9. T44–T52 own authored later-region content; T12 reserves progression bands/hooks only.

## Reusable ten-level role pattern

Each approximate ten-level band follows this architecture unless later accepted content requires a documented substitution that still satisfies all cadence checks:

| Relative level | Structural role | Mandatory result |
|---|---|---|
| x1 | Band entry / state establishment | Establish current region/band objective and a practical new state or route. |
| x2 | Resource / interaction expansion | Add a meaningful resource, interaction, destination, recipe-family hook or equivalent practical capability owned by the proper downstream task. |
| x3 | Visible progression | Require a visible world/camp/production/route presentation hook. |
| x4 | Loop expansion | Add a practical loop branch, automation/helper/processing hook or equivalent non-filler progression effect. |
| x5 | Mid-band capability | Add a meaningful capability/system hook; no stat-only filler. |
| x6 | Visible progression | Require a second visible improvement hook within the band. |
| x7 | Exploration / system expansion | Unlock a new route, interaction class, hazard-response hook, production destination or equivalent practical change. |
| x8 | Mastery / integration hook | Combine earlier band capabilities in a meaningful progression requirement without T13 difficulty tuning. |
| x9 | Visible pre-milestone progression | Require a visible world/system improvement and prepare the milestone transition. |
| x0 | Major milestone | Major visible/system milestone and next-band transition hook. |

This produces a default visible-progression cadence at relative levels x3, x6, x9 and x0, keeping the maximum ordinary gap at three levels while leaving downstream content owners freedom to add more visible changes.

## Reserved connected-world bands

| Levels | Stable preparation band ID | Shipping content owner | T12 preparation role |
|---|---|---|---|
| 1–10 | `band_opening_frozen` | T32 integrates the complete opening region/loop | Define topology and hooks; do not prebuild T32 content. |
| 11–20 | `band_forest` | T44 | Reserve IDs/hooks only. |
| 21–30 | `band_desert` | T45 | Reserve IDs/hooks only. |
| 31–40 | `band_underwater` | T46 | Reserve IDs/hooks only. |
| 41–50 | `band_sky` | T47 | Reserve IDs/hooks only. |
| 51–60 | `band_volcanic` | T48 | Reserve IDs/hooks only. |
| 61–70 | `band_swamp` | T49 | Reserve IDs/hooks only. |
| 71–80 | `band_ruins` | T50 | Reserve IDs/hooks only. |
| 81–90 | `band_underground` | T51 | Reserve IDs/hooks only. |
| 91–100 | `band_alien` | T52 | Reserve IDs/hooks only. |

## Opening-band dependency-aware hooks

The Level 1–10 architecture may eventually bind to accepted T07/T08/T10/T11 state, but preparation uses abstract hook classes only:

- `context_action_completed` — read-only result from T07/integration authority.
- `resource_delivery_completed` — authoritative delivered-resource result; never presentation stack count.
- `world_transform_completed` — accepted T10 transform/state ID after exact-once commit.
- `camp_state_completed` — accepted T11 camp-state ID after T10/T11 exact-once completion.
- `visible_progression_required` — requires a real visible result owned by the correct content/system task.
- `major_milestone_completed` — T12 progression event emitted only after its accepted prerequisites are true.

No concrete T10/T11 shipping IDs are frozen here.

## Static validator acceptance targets

A future shipping progression manifest fails if any of these are true:

- fewer or more than 100 shipping levels;
- missing integer in 1–100;
- duplicate `level` or `level_id`;
- empty practical progression-effect set;
- prerequisite points to a missing level;
- prerequisite graph has a cycle or an unreachable level;
- visible-progression gap exceeds three consecutive levels without a declared hook;
- any ten-level band has no major milestone hook without an explicit accepted exception record;
- purchase/VIP/premium-spend/energy fields affect eligibility;
- a progression event directly debits/grants inventory, commits a transform, spawns camp content or changes T13 difficulty;
- provisional T10/T11 hook IDs reach shipping data before activation reconciliation.

## Activation conversion rule

After T11 is approved/integrated, this blueprint is input to the T12 builder, not an output to copy blindly. The builder must reconcile exact accepted T10/T11 IDs and then generate/author shipping progression records under `HavenlineGodot/data/`. Any conflict between this preparation blueprint and accepted upstream behavior is resolved in favor of the accepted upstream contract plus the frozen T12 product requirements; unresolved conflict blocks activation rather than being guessed around.
