# Upgradeable camp storage house

A proposed compact Havenline storage-house family with three visual upgrade stages and a stocked/empty/loading reference sheet. All resource groups are allocated storage space from the first stage. Open the [gallery](GALLERY.md) for the selected renders.

## Selected render sheets

| Sheet | Coverage | Native size | Independent visual score |
|---|---|---|---|
| [Timber Storehouse](selected/storage-house-starter.png) | Front 0°, right 90°, rear 180°, left 270° | 1254 × 1254 PNG | 9.9/10 |
| [Reinforced Storehouse](selected/storage-house-reinforced.png) | Front 0°, right 90°, rear 180°, left 270° | 1254 × 1254 PNG | 9.9/10 |
| [Insulated Supply Depot](selected/storage-house-advanced.png) | Front 0°, right 90°, rear 180°, left 270° | 1254 × 1254 PNG | 9.9/10 |
| [Storage organization and use states](selected/storage-house-organization.png) | Stocked cutaway, empty cutaway and open loading state | 1254 × 1254 PNG | 9.9/10 |

The selected files are exact byte-for-byte aliases of their generated originals. The [independent visual verdict](reviews/critic-final-visual-verdict-v1.json) binds the accepted images to the actual inspection evidence.

## Upgrade intent

| Stage | Proposed visual change |
|---|---|
| Timber Storehouse | Rounded timber shell, a blue pitched roof and basic divided shelves/crates. |
| Reinforced Storehouse | The same footprint and entry with a substantial stone footing, steel corner straps and improved modular storage. |
| Insulated Supply Depot | The same footprint and entry with a thicker insulated blue/orange envelope, steel reinforcement and taller denser shelving. |

The progression retains one building family and a compact camp plot. No numeric capacity, price, unlock requirement, world-unit dimension or balance value is assigned by these renders.

## Resource coverage

The [coverage mapping](resource-coverage.json) assigns all 33 existing reference IDs from 11 source groups to six proposed storage zones. These are reference concepts; the mapping does not assert that every species drop, recipe or inventory feature is already implemented.

| Storage zone | Existing groups | Contents represented |
|---|---|---|
| Timber racks | timber | logs, plank stack, split firewood |
| Heavy material bins | mineral, metal | rounded stones, flat slate slabs, rough ore chunks, steel ingots in separate slot |
| Partitioned fuel locker | fuel | sealed fuel containers, coal bin |
| Food pantry | raw_meat, fish, grain, prepared_food | separate covered raw-meat and fish boxes, distinct sealed prepared-food shelf, grain sack compartment |
| Dry hide and fur cabinet | hide_fur | folded leather hides, folded pale fur bundles |
| Cargo shelf and secure drawer | cargo, cash | bound cargo parcels, closed cash lockbox |

The food pantry separates raw meat/fish, prepared food and grain. Fuel occupies its own partitioned service compartment. Dry hide/fur and cargo/cash retain separate storage. A clear central aisle connects the centered front entry to the perimeter storage.

Source roster: [existing 33-resource coverage proposal](https://github.com/ksolo21-web/HAVENLINE/blob/74817145ed7be6e8b9aef7eab1369d1e70112a64/Docs/Design/ResourceTurnarounds/2026-11-23-plots/sources/storage-resource-coverage-proposal.json). The [source findings](sources/research-resource-storage-findings.json) preserve the researched resource and storage context.

## Camp placement intent

The proposed position is along the inner camp perimeter, with the front facing inward and a clear loading approach. Placement should preserve the centered furnace, two distinct usable bidirectional camp openings, the existing character scale, and snow beyond the camp. These static sheets do not establish measured scene fit, tested route clearance or native collision geometry.

## Reference and generation custody

The two actual initial image references are the approved fence material/style sheet and Character 1 palette/style sheet. Their exact files already exist in the preserved baseline and are bound by immutable commit, repository path, SHA-256 and Git blob in the [generation manifest](generation-manifest.json). They are not duplicated here. Later generated anchors are retained under [attempts](attempts/). Other researched text is context, not an unrecorded image input.

Every generated original and repair remains under [attempts](attempts/), with its exact prompt under [prompts](prompts/). The generation manifest records native dimensions, bytes, SHA-256, Git blob identity, actual ordered input paths and hashes, requirements versions and selected aliases. The [review evidence index](provenance/review-evidence.json) preserves each captured critic evidence version. Reinforced r1 retains its actual closed-turnaround pass; its later rail refinement was requested by the root before producing use-state views. The initial coverage mapping is preserved in [resource-coverage-v1.json](resource-coverage-v1.json); the current mapping adds the original per-resource source statuses and species-eligibility qualifications.

## Repository and acceptance boundary

This package adds only the dated `Docs/Design/StructureReferences/2026-11-26/upgradeable-storage-house` folder on `art/storage-house-2026-11-26`. Its [baseline record](provenance/baseline.json) binds all 4,512 prior files to commit `74817145ed7be6e8b9aef7eab1369d1e70112a64` and preserves their exact blobs and modes. No runtime, main-branch or operational workflow files are changed.

These are native-resolution static raster reference renders. They do not establish a native mesh, playable building, animation, storage capacity or completed game integration. [Requirements](requirements.json) and the [content freeze](provenance/content-freeze.json) describe the acceptance scope; publication is checked separately.
