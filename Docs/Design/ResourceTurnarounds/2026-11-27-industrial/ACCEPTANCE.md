# Havenline remaining resource concepts — requirements

## Request and scope

Kaleb selected his attached HAVENLINE hearth image as the app icon and asked: “we need renders for the rest of the resources”. The exact icon selection is recorded separately. This resource package continues the existing eight-direction concept-sheet format and fills the resource-art gaps established by the actual published crafting and whole-game resource catalogues.

The audit found **33 existing resource sheets**. They cover **18 current identity families**, with **15 additional variants or reserve concepts** preserved. The combined authored resource/currency/project catalogue has **27 identities**. Nine standalone sheets are missing: **seven ordinary material/component items**, **one currency**, and **one finite project object**. This is an art coverage result, not a claim that all 27 are implemented in the current game.

## Required new sheets

| ID | Display name | Role |
|---|---|---|
| `iron_bars` | Iron bars | Processed iron for sheets, parts and steel |
| `sheet_metal` | Sheet metal | Processed vehicle, garage-door and machine panels |
| `mechanical_parts` | Mechanical parts | Aggregate construction component |
| `drive_assembly` | Drive assembly | Vehicle/machine drive module |
| `traction_kit` | Mobility assembly | Shared movement-module component |
| `crude_oil` | Crude oil | Raw refinery input, represented by a carried container |
| `blocks` | Stone blocks | Dressed construction material |
| `premium_gems` | Gems | One premium currency; not a mined resource |
| `relay_component` | Relay component | Finite serialized World 10 project object |

Existing coal, metal ore, steel, fuel and planks remain linked to their preserved sheets. The selected Iron ore display maps to the existing saved key `metal`; do not invent another `iron_ore` balance or silently replace the old ore art. Existing bread-like `cooked_food` art maps to `bread`, while `cooked_game_meat` maps to `meal`.

## Dependency-aware milestones

1. Freeze the source audit, resource-ID crosswalk, nine-item roster and style references.
2. Generate each missing eight-view sheet; preserve every original and repair attempt.
3. Independently inspect every full sheet, meaningful views and closeups; repair defects and retest the changed images.
4. Freeze selected bytes, verify preservation of old art, publish the reviewed package on an isolated GitHub branch and read back the actual remote tree/assets.

## Mandatory acceptance checks

- R01 — Source coverage: the nine new IDs are backed by the pinned material/whole-game plans, with currency and finite-project identity distinguished from ordinary inventory.
- R02 — Complete roster: all nine selected sheets are present, totaling 72 illustrated views.
- R03 — Complete directions: each sheet shows front, front-right, right, rear-right, rear, rear-left, left and front-left with readable intended-angle labels and no missing or duplicated orientation.
- R04 — Object identity: primary silhouette, major part count, shafts, connectors, straps, layers, front/back markings and material identity remain consistent across the sheet. Unseen surfaces are explicitly authored, not asserted to be observed reference geometry.
- R05 — Havenline art language: rounded and sculpted stylized forms, clean material separation and restrained navy presentation. Preserve established material identities. No gritty realism, crude placeholder geometry or unrelated UI clutter.
- R06 — Useful resource distinctions: iron bars differ from the existing steel ingot; sheets read as thin metal with readable edge thickness; dressed blocks differ from rough stone; crude oil container differs from the orange fuel jerrycan; parts, drive and mobility items have distinct silhouettes.
- R07 — Framing and labels: the full object is visible in every panel, comfortably separated from captions and borders; the resource name is accurate; no unintended text or duplicate props confuse the item count.
- R08 — Scope honesty: static concept illustrations do not certify calibrated cameras, native shared 3D geometry, recipes, numerical balance, world integration, animations, gameplay or device performance. Gems art does not set prices or payment policy. Relay art does not invent an endlessly farmable currency.
- R09 — Genuine independent review: a separate critic reviews actual output pixels and binds the report to exact image hashes. Scores are 0–10; every mandatory scoped concept check must pass and every scoped score must be strictly above 9.0, aiming for 10. Stricter applicable final reference/native/gameplay standards remain unchanged and are not claimed by this art package. Missing evidence blocks the affected approval.
- R10 — Preserve evidence: retain rejected/superseded images and raw review records. Repaired images invalidate only their affected prior review; obtain fresh retest evidence.
- R11 — Preserve existing work: all 33 old selected resource PNGs retain their exact Git blobs; no active gameplay, historical QA preset, workflow or prior frozen approval is changed.
- R12 — Durable delivery: all selected images, prompts, source crosswalk, reviews and resumable checkpoint are saved as full GitHub file content with exact remote verification. No LFS pointer is delivered in place of a selected PNG.

## Explicit boundaries

The new oil well/manual pump, ore/coal source-state models, smelter, metal bench, forge, assembly bench and refinery are machines or acquisition sites. They are not additional resource IDs, and this nine-sheet package does not silently claim their renders, construction states or gameplay are complete. Existing food species cuts and reserve concepts do not create additional mandatory drops or recipes merely because artwork exists.

Reference and source identities are recorded in [RESOURCE_RENDER_GAP_AUDIT.json](RESOURCE_RENDER_GAP_AUDIT.json). The machine-readable roster is [RESOURCE_ROSTER.json](RESOURCE_ROSTER.json).
