# HAVENLINE Character V7 — Unity review gate

Status: **staging only; not final; not human-approved**.

## Why this branch exists

The V7 character candidates are rigged GLB sources with a validated 52-joint skin. The previous review contract assumed a Blender-to-FBX conversion before Unity, but that conversion must not be faked when Blender is unavailable. Unity's official `com.unity.cloud.gltfast` package supports Editor import of GLB/glTF, so this branch adds a direct, non-lossy Unity review path while leaving the legacy production-FBX requirement explicitly unsatisfied.

Unity project version: `6000.5.6f1`.

Unity glTFast version on this branch: `6.19.0`.

## Exact staging path

Copy the four verified V7 files into:

`Assets/Havenline/Art/Characters/Staging/V7/`

Required files:

| Character | File | SHA-256 | Bytes |
| --- | --- | --- | ---: |
| 1 | `Havenline_Character_1_Rigged_Refined_V7.glb` | `a14352ab6fb483609c91712dceab6a3be8ae35ae6c3733e431df49de3f9c55db` | 9149476 |
| 2 | `Havenline_Character_2_Rigged_Refined_V7.glb` | `6252680d0fd990f8d6819b6255e1d9b13c7ff77c34eacb84551efcad6d1dc839` | 9799036 |
| 3 | `Havenline_Character_3_Rigged_Refined_V7.glb` | `88ecef677472ed63fce98f0e75e60507555dd9d8becfb75aa02f59f59eb4d360` | 10931132 |
| 4 | `Havenline_Character_4_Rigged_Refined_V7.glb` | `bea67fe847c2c1f05bd0a0822cbca4b16b95f6e844a1d9aba66f56b2dc374a6e` | 10884332 |

## Run the gate

In the Editor use:

`HAVENLINE > Characters > V7 > Validate + Capture Review Proof`

Or in batch mode:

```text
Unity -batchmode -quit -projectPath <project> -executeMethod Havenline.Editor.HavenlineV7CharacterReview.RunBatchMode
```

The gate:

- verifies exact SHA-256 and byte count for all four candidates;
- forces synchronous Unity import through the installed GLB importer;
- requires one or more `SkinnedMeshRenderer` components;
- requires exactly 52 uniquely referenced rig bones;
- rejects missing materials and Unity internal-error shaders;
- records mesh/material/bounds statistics;
- captures neutral front, 3/4, side, and back views;
- applies a combined torso/shoulder/head stress pose using the known Mixamo bone names and captures front + 3/4 proof;
- writes `Artifacts/HavenlineCharacterReview/V7/review.json`;
- never flips any approval flag or claims an FBX exists.

The stress pose is a visual clipping/deformation probe, not a substitute for the shipping animation set.

## Remaining truth gates

Even after this machine gate passes, do **not** promote the characters until all of the following are completed:

1. Human side-by-side review against each approved turnaround sheet.
2. Shipping-animation pose/clipping review.
3. Gameplay-scale readability in the shipping landscape camera.
4. A real `CharacterN_production.fbx` conversion only if the production contract still requires FBX; otherwise deliberately revise that contract in a separate reviewed change.

## V7 source status

Character 1, 2 and 4 are visual carry-forwards from the stronger V5 direction. Character 3 keeps the V5 garment geometry but uses nearest-base-surface skin-weight projection for the burgundy shirt, cream vest and open-coat trim. Its synthetic pose-deformation audit passed before this Unity gate was introduced.
