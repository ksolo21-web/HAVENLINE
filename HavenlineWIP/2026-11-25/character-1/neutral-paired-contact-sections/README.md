# Original C1 neutral-contact extraction from the exact held chest frame

Read-only extraction on the existing owner-source detached 52-joint lineage (visual 7e3ed20e…, rig a540243d…); no pose replay, Blender, Godot, renderer, geometry or external writes. The five inputs are byte-pinned in the script and result. The **existing** complete held arrays were last regenerated independently using the narrow 52-joint parent plus exact recorded chest transform. Their 727,442 face rows exactly equal the full-detail indexed bind; all 617 right and 567 left cuff points in the independently frozen material/section fixture reconstruct from indexed held edges and stored interpolation with zero error, establishing the same physical frame. This is an extraction from a prior held chest pose toward a neutral design, not a newly authored neutral stance.

Wrist basis columns are original signed transverse (X), long toward digits (Y) and inward palm (Z); palm center offsets are given in both this named wrist frame and common chest frame. The tool stays the original intrinsic 512 triangles, anatomical right headward at face 124 and left buttward at face 276, never sorted by world height. Direct decoding and transformed triangle matching each produce one original GLB triangle and zero vertex error at reported precision. Outward geometric normals are supplied in both frames.

The original joined surface is intersected at the actual named palm vertex's wrist-longitudinal station and, separately, a web role-boundary station frozen from native weighted source edges. Right yields 306 palm and 359 web segments; left yields 327 and 363. Reconstructed original routed cuff chains are [520,56,41] right and [519,48] left, retaining source face/edge/UV indices, not manufactured seams. No successor patch was included. A narrow thumb-index named root role boundary has just **one** qualifying edge right vs six left; it selects the web cut station, **does not** supply complete right or bilateral material web authority. The legacy larger 133-edge left material trace is different scope; these counts do not supersede it.

Side ownership follows the exact parent arm range; original coat is excluded using the original non-arm/central bind rule (600,396 retained source triangles) and no excluded coat faces enter the selected cuts. Source segments carry forearm-incidence classification. Keeping the coat out of the section doesn't establish clearance: the independently frozen earlier same pose had zero narrowly proximal slice pairs but 4 right/18 left full-forearm tool overlap pairs. Neither count is a new clearance test. No approved/rebuilt glove, sleeve/hand geometry or alternate placement. Endpoint ranges to the infinite tool plane in the result are geometric guides, not finite-face signed collision or penetration depth.

**Completion boundary:** the requested same-frame data intake is present, but right web material continuity, actual bilateral finite tangent bearing and retained forearm/coat clearance remain needed before proposing another pose. Keep using original labels, tool, cuff UVs and source IDs; don't infer support from the point-level screen alone.

## Reproduction

```
python3 extract.py <original-bind.npz> <exact-held.npz> <frozen-seam.npz> <chest-result.json> <original-axe.glb> <new-local-output-directory>
```

NumPy only. stdout equals `result.json`. `sections-private.npz` holds original source coordinates and UV/edge geometry; keep it local and do not transfer or archive its bytes externally. `SHA256SUMS` covers the shareable source/summary files only; the private-array digest is provided as a replay receipt in result.json.
