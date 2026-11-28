# Havenline remaining resource and processing-machine audit

Pinned repository base: `79973ab632a0916acec9a6ddad7895f1243a4713`. Additional existing art corpus: `a868ae89cdf2f120b478aa0a48fff35e09cc465c`. Read-only audit; original art and reviews were not modified.

## Resource finding

All **nine** previously missing resource sheets already exist. Each selected PNG is byte-identical to its latest separate critic pass (recorded score 10.0 for the bounded raster-concept scope). The package has a delivery/documentation gap, not a new-generation gap. The current README and checkpoint are stale.

| Identity | Selected sheet | Last review | Exact bytes |
|---|---|---|---|
| `blocks` | `stone-blocks.png` | `REVIEW_R3_02_03_R2_07_09.json` | Match |
| `crude_oil` | `crude-oil.png` | `REVIEW_R3_04_06_09.json` | Match |
| `drive_assembly` | `drive-assembly.png` | `REVIEW_R3_04_06_09.json` | Match |
| `iron_bars` | `iron-bars.png` | `REVIEW_R2_01_03.json` | Match |
| `mechanical_parts` | `mechanical-parts.png` | `REVIEW_R3_02_03_R2_07_09.json` | Match |
| `premium_gems` | `gems.png` | `REVIEW_R1_07_09.json` | Match |
| `relay_component` | `relay-component.png` | `REVIEW_R3_04_06_09.json` | Match |
| `sheet_metal` | `sheet-metal.png` | `REVIEW_R3_02_03_R2_07_09.json` | Match |
| `traction_kit` | `mobility-assembly.png` | `REVIEW_R2_04_06.json` | Match |

There are **42 resource sheets / 336 illustrated views** across the preserved 33 and these nine. They represent **27 current identity families**, not 42 inventory items: 23 ordinary material/component families, two currencies, one container presentation and one finite project object. Fifteen prior sheets are variants or reserve concepts.

## Machine render gaps

The six new industrial producers below have no dedicated selected sheet in the audited base plus pinned art corpus. Generic workshop art is not proof of a dedicated machine design.

| Machine ID | Input → output | Dependency | Site |
|---|---|---|---|
| `coal_smelter` | metal + coal → iron_bars | saw_bench, quarry_drill | inside_expanded_camp |
| `hand_metal_bench` | iron_bars → sheet_metal; iron_bars → mechanical_parts | coal_smelter | inside_expanded_camp |
| `steel_forge` | iron_bars + coal → steel | hand_metal_bench | inside_expanded_camp |
| `assembly_bench` | steel + mechanical_parts + sheet_metal → drive_assembly; steel + mechanical_parts + planks → traction_kit | steel_forge | inside_expanded_camp |
| `manual_oil_pump` | reachable oil site → crude_oil | hand_metal_bench | outside_camp_reachable_manual_oil_site |
| `coal_refinery` | crude_oil + coal → fuel | manual_oil_pump, hand_metal_bench | inside_expanded_camp |

Existing saw, quarry/drill and cooker references remain the foundation. T16 whole-fish processing already names the intake machine and cooker. T19 wheat/bread has a dedicated `world-wheat-processor.png` at the pinned art commit. No mandatory flour step is selected. Hide/fur already have source and equipment uses; this audit does not invent leather/cloth wallets.

## Later-world boundary

The relay component is a finite serialized World 10 project object. Its dedicated recovery/restored-fabrication worksite action/art remains a recorded gap. A future worksite concept can be authored from the existing relay visual language, but the paid replacement recipe quantities and actual serial-custody behavior remain unproved. It must not become an endlessly produced currency.

## Delivery checks still required

1. Bring the exact selected nine PNGs, complete reviews (including external `REVIEW_R3_04_06_09.json`), source crosswalk, prompts and checkpoint into the final package.
2. Update the current delivery status without rewriting rejected attempts or historical reviews.
3. Verify actual remote selected file bodies before claiming GitHub delivery.
4. Generate and independently inspect the missing machines, including coherent intake, output, fuel feed where needed, service access and compatible conveyor interfaces.
5. Keep static concepts distinct from models, animation cycles, functioning recipes and integrated gameplay.

The machine quantities in `RESOURCE_CHAINS.json` are authored fixtures, not playtest-balanced costs. The oil chain must remain manually bootstrappable without needing vehicle fuel before the first fuel exists.

## Evidence

The JSON audit records full paths, selected-image SHA-256, review SHA-256, exact recipe/dependency records and source bindings. No existing source was edited.
