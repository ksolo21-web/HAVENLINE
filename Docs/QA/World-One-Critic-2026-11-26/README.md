# World One review for November 26

**Overall verdict: HOLD.** The minimum is 9.5/10, inclusive, on each reviewed dimension. Applicable artwork still requires 10.0 for reference fidelity and visual language. Of 46 dimensions, 30 passed, 14 fell short and 2 could not be verified. Earlier scores retain their original commits.

The playable source is [949af6f0916839ac702725cbd7a0a7c3f1033a5a](https://github.com/ksolo21-web/HAVENLINE/commit/949af6f0916839ac702725cbd7a0a7c3f1033a5a) on trial/world-one-expansion-2026-11-26. The scene is res://field_opening.tscn. The evidence commit documents this gameplay commit.

## Play and watch

The gameplay reel follows an earned Level 1 opening from snow before the hearth through construction, the corner storehouse, the eastern tower and the orbit upgrade. It includes both gates in both directions. The extended view of the newly built hearth comes from a second fresh profile that made the same purchase. Its 1280 × 720 frames were recorded at 24 fps and preserve the game mixer. Normal and pinched Ultra views were captured separately at 3840 × 2160. [Gameplay reel](Gameplay/Level-1-critic-replay.mp4) · [Both gates and the opening](Gameplay/Opening-and-gates.jpg) · [Playback verification](Gameplay/Playback.json) · [Normal 4K](Gameplay/default-camera-4k.jpg) · [Pinch 4K](Gameplay/closest-camera-4k.jpg) · [Build and installation](Build/README.md)

## What changed

- Character 1 uses revised parka weights and turning motion. Repeated redirects preserve the authored bone scales. Walk/run/turns, coat and boot deformation, and loaded motion each earned 9.5. [Exact-skin movement review](Rig/Final/Review.md)
- The fitted Meshy axe has a narrower shaft. Two rear supports carry the additional mineral lanes. The full load clears the axe throughout its orbit, and the same donor head hits wood at normal and close zoom. [Tool and gameplay comparison](Orbit/README.md) · [Independent gear review](Rig/Final/Orbit-clearance-dimension.json)
- The opening snow, purchase brackets, pictogram and counts were compared with original reference pixels. The paid palisade has revised rope spacing and pointed snow caps. The revised metal ore and slate were fitted against five matched views and tested by mining in the playable scene. [Visual comparison](Visual/Independent-review.md) · [Mineral comparison](Minerals/README.md)
- The cutaway exposes the loading aisle. Six resource types stay on separate shelves, and the HUD shows exact balances. A million units fits on each shelf label without overlap. Interrupted deposits and payments settle once. [Storage and purchase review](Storage-review/README.md)
- Respawn protection and the remaining fall time survive closing and reopening the game. The candidate passed 22 native test suites. [Final systems review](Systems/Final/README.md) · [Test receipts](Build/Native-suite-results.json)

## Remaining acceptance gaps

The visual critic found differences in the coat, timber, foliage, tool and mineral surfaces, and storehouse detailing. The original Reference B recording had audio. Its retained visual excerpts are silent, so the mix comparison is open. The source ledger identifies the missing recording as Screen_Recording_20260817_124510_YouTube.mp4. No physical Android handset was attached for sustained 4K60/120 or thermal measurements. [Art and camera](Visual/Independent-review.md) · [Character reference](Rig/Final/Character-reference.jpg) · [Audio and device checks](Audio-and-delivery/README.md)

The rigging skill’s standalone verifier was unavailable. The character review used the independent joint and clip ledger, native gait checks and the frozen-source gate. [Joint ledger evidence locations](Rig/Final/Ledger-evidence-locations.json)

The stricter threshold also applies to later reviews of this World One trial. [All scores](Scores.md) · [Machine-readable review](review.json) · [9.5 review rule](Gate/policy.json) · [Existing art requirement](https://github.com/ksolo21-web/HAVENLINE/blob/949af6f0916839ac702725cbd7a0a7c3f1033a5a/Docs/Production/REFERENCE_STYLE_LOCK.json) · [Earlier work and prototypes](History.md) · [T01–T11 production status](Storage-review/T01-T11.md)

Run the following command from this directory. Exit code 1 identifies an open mandatory item.

    python3 Gate/verify_review.py 949af6f0916839ac702725cbd7a0a7c3f1033a5a
