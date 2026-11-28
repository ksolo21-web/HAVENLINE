# Havenline — remaining resource concept turnarounds

This package fills nine standalone art gaps identified by the latest published crafting and whole-game resource plans. Seven are ordinary materials/components. Gems is the selected premium currency, and the relay component is a finite World 10 project object.

**Status: generation and independent review pending.** The nine required items are defined in the [roster](RESOURCE_ROSTER.json). No new image is approved by this draft.

## New gallery

| Item | Planned selected file | Role |
|---|---|---|
| Iron bars | `selected/iron-bars.png` | Processed material |
| Sheet metal | `selected/sheet-metal.png` | Processed material |
| Mechanical parts | `selected/mechanical-parts.png` | Aggregate component |
| Drive assembly | `selected/drive-assembly.png` | Drive module |
| Mobility assembly | `selected/mobility-assembly.png` | Movement module; ID `traction_kit` |
| Crude oil | `selected/crude-oil.png` | Raw refinery input |
| Stone blocks | `selected/stone-blocks.png` | Dressed construction material |
| Gems | `selected/gems.png` | Premium currency |
| Relay component | `selected/relay-component.png` | Finite serialized project object |

The final selection will use eight illustrated directions per item, with 72 views across the nine sheets. These are AI-generated concept references for later modeling and review, not native renders of shared 3D geometry or proof of implemented gameplay.

## Existing resources remain available

The [original 13-sheet set](../2026-11-23/README.md) and [20-sheet expansion](../2026-11-23-expansion/README.md) are preserved. They already include coal, metal ore, steel, fuel, planks, raw and processed foods, hide, fur, money and cargo. The new Iron ore display maps to the existing saved key `metal`; this package does not create a second ore balance or silently overwrite its old render.

Those 33 sheets cover 18 current identity families and 15 variants/reserve concepts. The full [coverage audit](RESOURCE_RENDER_GAP_AUDIT.json) records each existing path and exact Git blob, and distinguishes what is present from what is merely planned. Prior concept approvals do not certify current game integration.

## Requirements and evidence

[Acceptance checks](ACCEPTANCE.md) · [Design notes](DESIGN_NOTES.md) · [Source/coverage audit](RESOURCE_RENDER_GAP_AUDIT.json) · [Checkpoint](CHECKPOINT.json)

The exact user-selected app icon is recorded separately. This resource package changes no active gameplay file, recipe balance, resource wallet, historical QA preset or workflow.
