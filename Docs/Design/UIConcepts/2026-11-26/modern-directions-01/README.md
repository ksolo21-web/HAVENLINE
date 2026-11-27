# Havenline — modern UI concepts

Three complementary landscape UI proposals: camp gameplay HUD, storage and upgrades, and survivor assignment. These are separate screen treatments that could inform one visual system; they are not three complete interchangeable UI systems.

[Open the render gallery](GALLERY.md).

## Selected screens

| Screen | Design intent | Native image | Independent visual score |
|---|---|---|---|
| [Camp HUD — world-led layout](selected/ui-camp-hud.png) | Compact resource rail, a small objective, one movement joystick and a contextual Build action around an open camp illustration. | 1672 × 941 PNG | 9.5/10 |
| [Storage — bright inventory and upgrade view](selected/ui-storage.png) | A prominent approved house preview, readable resource quantities, a current-to-next upgrade distinction and one primary upgrade action. | 1672 × 941 PNG | 9.6/10 |
| [Survivor — midnight profile and assignment view](selected/ui-survivor.png) | The approved Character 1 design in an idle pose, a restrained status display and a clear camp-assignment choice. | 1672 × 941 PNG | 9.7/10 |

## Design rationale

### Camp HUD

Keep the playable scene visually dominant. Resources occupy one aligned rail, the objective stays compact, and navigation sits near the lower edge. The orange primary action gives the player one clear next step. The camp illustration follows the established winter materials, centered furnace and two-opening intent.

### Storage and upgrades

Use an ivory background, strong navy typography and open inventory rows so material quantities can be compared quickly. The house is the visual anchor. Current and preview upgrade states are distinguished, while the warm-orange action remains easy to locate.

### Survivor assignment

Use a deeper midnight palette to give the approved character a clear focal point. Slim status rows and selectable assignments keep the menu legible, with one visible selection and one matching primary action.

### Shared direction

Carry Havenline’s sculpted blue/orange assets through restrained interface surfaces, sparse geometric navigation, line icons for actions, 3D resource thumbnails, careful spacing and a small number of type scales. Orange primary actions share a subtle cut-corner signature. The art provides the personality; the controls provide structure. Phone-size checks in the critic evidence assess static visual legibility only.

## Proposal boundary

All displayed resource quantities, upgrade costs, status values, assignment choices and ordering are illustrative UI copy. They do not establish game economy, implemented abilities, character-role canon or a frozen progression plan. Landscape was explored from the inspected 1920 × 1080 native viewport; this package does not approve a permanent orientation decision.

The camp background is an original concept illustration, not a live gameplay capture or measured native scene. These PNGs do not establish working controls, touch-target behavior, animation, performance or runtime accessibility. No active game source is changed.

## Source and generation custody

The [actual input index](sources/actual-input-index.json) lists the six inspected component references actually supplied across the recorded calls. The [generation manifest](generation-manifest.json) binds each prompt, ordered input, original output and selected alias to exact bytes and hashes. All six initial source PNGs already exist in the immutable baseline and are linked there, rather than duplicated in this package.

The [bounded UI context findings](sources/ui-context-findings.json) preserve seven inspected source-document bindings. Located candidate references in that report remain distinct from the actual input list.

Every generated original and repair is retained under [attempts](attempts/), and every exact prompt is retained under [prompts](prompts/). The selected aliases are unmodified copies of their original generated PNGs. The [review index](provenance/review-evidence.json) preserves actual independent evidence versions; the [aggregate visual verdict](reviews/critic-final-visual-verdict-v1.json) identifies the selected visual approvals.

## Archive boundary

This package adds only `Docs/Design/UIConcepts/2026-11-26/modern-directions-01` on `art/ui-concepts-2026-11-26`. All 4,569 files in the [baseline](provenance/baseline.json) remain intact, including earlier art, plans, source references and historical evidence. Active Codex/runtime work, main and operational workflow configuration are outside this task.

The [content freeze](provenance/content-freeze.json) records the visual package. Publication and complete-byte readbacks are checked separately.
