# Character 1 — supplied design 18617

Three static reference sheets cover the complete eight-angle body rotation and four dedicated hand views for the supplied Character 1 design. Open the [gallery](GALLERY.md) to inspect the selected sheets and the exact source image.

## Selected sheets

| Sheet | Coverage | Selected original | Native size | Independent visual score |
|---|---|---|---|---|
| [Cardinal](selected/character-1-cardinal.png) | Front 0°, anatomical right 90°, rear 180°, anatomical left 270° | `character-1-cardinal-r2` | 1254 × 1254 PNG | 9.8/10 |
| [Oblique](selected/character-1-oblique.png) | Front-right 45°, rear-right 135°, rear-left 225°, front-left 315° | `character-1-oblique-r1` | 1254 × 1254 PNG | 9.8/10 |
| [Hand details](selected/character-1-hands.png) | Right palm, right back, left palm, left back | `character-1-hands-r1` | 1254 × 1254 PNG | 9.9/10 |

The selected aliases contain the exact original image bytes. The [aggregate visual verdict](reviews/critic-final-visual-verdict-v1.json) accepts every mandatory static check and scores the set 9.8/10, bounded by the weakest accepted sheet.

## Source and design lock

The [exact supplied source](sources/18617-original.jpg) is 1229 × 1536, 211,049 bytes. The user attachment was named `18617.png`; its actual format is JPEG. This archive uses a `.jpg` name and preserves every source byte. Its SHA-256 is `d73c3860d5aca2cdf92a7c337c9a720acdda477c08f5b54dd1695dd7f312447c`.

The design retains the compact chibi proportions, warm brown skin, dark curls and beard, black glasses with white temples, royal-blue winter jacket, orange trim, cream shearling, navy scarf, right hip pouch, left front hem patch, purple knee pads and orange-brown boots. The body views use a fixed neutral T-pose. Brown five-digit gloves provide four separated fingers and an opposed thumb, with dedicated palm and back views for both hands.

The camera convention proceeds from the front toward the character's anatomical right. The pouch remains on that side through the complete rotation. Exact side views use natural hand foreshortening.

## Complete generation and review history

All four generated originals remain under [attempts](attempts/), with all four exact generation prompts under [prompts](prompts/). The [generation manifest](generation-manifest.json) records each original's native dimensions, SHA-256, Git blob, literal prompt-file identity, ordered actual image inputs, requirements version and selected alias.

| Original | Disposition |
|---|---|
| [Cardinal r1](attempts/character-1-cardinal-r1.png) | Retained rejected attempt; profile hand orientation and rear hand identity required repair. |
| [Cardinal r2](attempts/character-1-cardinal-r2.png) | Selected after the independent repair retest. |
| [Oblique r1](attempts/character-1-oblique-r1.png) | Selected after independent inspection of all four views and native hand crops. |
| [Hands r1](attempts/character-1-hands-r1.png) | Selected after independent inspection of all four complete palm/back details. |

[Requirements v1](requirements-v1.json) is retained because it was used by the first actual invocation. The [current requirements](requirements.json) correct the thumb orientation and upright palm/back chirality identified during independent preflight. Each actual prompt remains unchanged and bound to the requirements version recorded for its invocation.

The [raw review evidence index](provenance/review-evidence.json) maps every captured review and crop version to its exact bytes. Initial cardinal-r2 profile crops were recentered before the final verdict; both earlier files remain under [review history](reviews/history/). The critic's [correction record](reviews/critic-evidence-correction-001.json) explains the change and binds the final verdict to the corrected crop evidence.

## Repository preservation

This package is additive beneath `Docs/Design/CharacterTurnarounds/2026-11-26/character-1-design-18617` on `art/character-1-2026-11-26`. Its [baseline record](provenance/baseline.json) identifies commit `26bb649e0a8090c9c9af7e91e62f384fc86372d8` and tree `55a829d09dfb11bf28d83515e37fddbad1323978`. All 4,463 baseline files, including earlier character selections and artwork, retain their exact Git blob identities and modes. The archive adds no operational `.github` configuration and makes no runtime or build changes.

## Scope of acceptance

These are static multi-angle raster references at the native returned resolution. They are not a native mesh, skinned rig or animation, and they do not establish a mathematically derived camera orbit. The [content freeze](provenance/content-freeze.json) preserves the selected-byte and visual-acceptance bindings; publication and exact remote content are verified separately.
