# Havenline render-pack exporter

The exporter produces an 18-page landscape PDF and a compact ZIP containing all 15 original PNGs, a responsive relative HTML gallery, README, exact selected-file manifest, recipe graph and final review records. The PDF is separate from the ZIP to keep the archive compact.

No source image is edited, cropped, overwritten or recompressed. The PDF scales each original full sheet. SHA-256 checks verify original bytes in the gallery folder and ZIP.

## Before final export

Wait for the root's final-selection notice. The exporter is not a visual approval tool. It will refuse any missing machine selection or changed selected resource byte. Root-provided final machine review records must already be retained in the repository.

Use the primary Python runtime when available:

```bash
"${CODEX_PRIMARY_RUNTIME_PYTHON:-python3}" build_render_pack.py preflight \
  --repo /workspace/scratch/59f000bd1476/HAVENLINE-processors
```

The exact selected machine filenames are:

- `01-coal-smelter.png`
- `02-metalworking-bench.png`
- `03-steel-forge.png`
- `04-assembly-bench.png`
- `05-manual-oil-pump.png`
- `06-coal-refinery.png`

## Freeze and build

After final selection, replace the review-record path below with the actual retained final machine review. Repeat `--review-record` when the final selections are covered by more than one file.

```bash
"${CODEX_PRIMARY_RUNTIME_PYTHON:-python3}" build_render_pack.py freeze \
  --repo /workspace/scratch/59f000bd1476/HAVENLINE-processors \
  --selection /workspace/scratch/59f000bd1476/delivery-builder/FINAL_SELECTION.json \
  --review-record /absolute/path/inside/repository/to/actual-final-review.json

"${CODEX_PRIMARY_RUNTIME_PYTHON:-python3}" build_render_pack.py build \
  --repo /workspace/scratch/59f000bd1476/HAVENLINE-processors \
  --selection /workspace/scratch/59f000bd1476/delivery-builder/FINAL_SELECTION.json \
  --output /workspace/scratch/59f000bd1476/deliverables
```

The build rejects an existing `Havenline_Render_Pack` directory to preserve prior deliverables. For a revised build, select a new output directory.

## Layout verification

The build checks all 15 image hashes, ZIP integrity, all PDF sheet headings and the exact 18-page count. It deliberately leaves visual layout status pending.

Render the final PDF using `pdftoppm`, then inspect the pages. Record that inspection separately without modifying the original raster images. PDF page order is cover; nine resources; six machines; production routes; review scope.

Neither a successful build nor layout inspection proves a native 3D model, animation, recipe balance, game integration or device performance.
