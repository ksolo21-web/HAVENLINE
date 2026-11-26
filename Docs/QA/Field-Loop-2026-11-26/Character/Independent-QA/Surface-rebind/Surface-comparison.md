# Character 1 garment rebind

The reviewed V12 asset preserves the V9 rest mesh and all 450 animation channels across Idle, Walk and Run. The rebind distributes influence across the rear boot cuff, padded trousers and coat as the knee bends. All 442 vertices below 90 mm keep their original joints and weights. Every sampled animated sole position is identical to V9.

| Measurement | V9 | V12 |
|---|---:|---:|
| Longest camera-exposed intersection in Walk, sampled at 40 Hz across three gameplay headings | 20.34 mm | 1.16 mm |
| Longest camera-exposed intersection in Run under the same conditions | 14.66 mm | 1.76 mm |
| Maximum newly crossing triangle pairs in Idle at 120 Hz | 11 | 4 |
| Maximum newly crossing triangle pairs in Walk at 120 Hz | 109 | 72 |
| Maximum newly crossing triangle pairs in Run at 120 Hz | 202 | 53 |

The V12 taper keeps the lower part of each shin on its own leg. A 9.59 mm inner-shin edge previously stretched to 76.17 mm in V11. The same edge reaches 14.45 mm during V12 Run and 13.04 mm during Walk. Independent eight-heading review found a smooth, continuous parka surface at the largest remaining exposed sleeve strain.

The longest remaining sampled exposure is on the rear waist seam. The numerical scan excludes pairs already intersecting in rest pose and includes concealed crossings in the full-surface counts. These figures address the garment change. The independent rig ledger covers the assembled character and movement motor.

The GLB and V9 triangle indices, rest positions, UVs and normals match exactly. Re-running the provided Blender authoring produced the reviewed V12 GLB byte for byte. Godot 4.7.2 successfully loaded the updated character in the active field scene.

| File | Bytes | SHA-256 |
|---|---:|---|
| Character1Fresh.glb | 8,707,948 | 4491c830fce1b2f5ca455dd0c853d46fe94b6d1996bb71173977b48fad330ee5 |
| Character-1-editable.blend | 12,773,837 | e7f447a9ef29e9548234f5c0117b3cfd11e6e153564778802399708e41619dc5 |

[Five matched V9 and V12 gait phases at 1× and 2×](native-comparison.jpg) · [Normal gameplay camera](full-1.0.jpg) · [2× gameplay camera](full-2.0.jpg) · [Editable rig](../../Character-1-editable.blend) · [Rebuild instructions](../../Authoring/README.md)
