# Character 1 right rear panel 28093: interior-only HOLD

One exact neutral/0 ms test of the separately approved retained-face interior. No edited surface was authored. Both blockers involve the **retained face's own pinned outer edges**, rather than the previously identified (13771,14452) stitch piercing its old interior. The latter can cease to pierce after bending the interior; the former two cannot.

| Immutable edge on 28093 | Immutable obstructing face | Edge interpolation | Strict face barycentric |
|---|---|---:|---|
| 12949→13127 | 28305 | 0.269562780 | 0.307830027, 0.577048558, 0.115121415 |
| 13127→13919 | 42401 | 0.760000910 | 0.310717367, 0.256599700, 0.432682933 |

Feet and all original vertices, clips, and surfaces were read from the exact sealed source without writes. Neutral produces no strict intersections on any of the six tested edge/obstacle combinations. Verified opposing signed plane distances, strictly positive barycentrics, interior segment fractions, and reconstructed point residual below 1 pm. Full native arrays match the independent four-face coordinates bit-for-bit on the relevant pairs. The output NPZ keeps exact native geometry for all three two-face perimeter incidences, the fixed obstacles, separate 27920 baseline, and exact stitch.

Any retriangulation attached to the same unchanged perimeter includes these same two crossing points. Splitting either edge into collinear subsegments leaves its geometric support unchanged. Changing a perimeter edge instead would change the attachment to its still-fixed second incident face, and is outside the approval. In addition, the independent 27920/42401 overlap does not involve 28093 at all. For any larger repair, the next dependency is authorization and proof for a connected panel template that includes **both** affected old perimeter-edge incidences or reauthors the corresponding fixed obstacles; not a new interior offset sweep or permission to change silhouettes. No later poses or third-party action were necessary; no mesh, renderer, engine, spend, or publishing.

Replay from the parent workspace with Blender 4.3.2 background, isolated HOME/XDG/TMP, and the serial Blender geometry lease. CLI: `blender -b -t 4 --python-exit-code 1 --python hvn-l1-c1-rear-adjacent-panel-hold-v1/audit.py`. The replay verifies both sealed parent manifests and the exact authoring inputs.
