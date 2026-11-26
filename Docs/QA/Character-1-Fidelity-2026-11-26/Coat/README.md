# Character 1 parka in the Level 1 camera

The final paint uses the approved compact Character 1 turnaround, source 18617. Blue winter cloth is brighter in the folded sleeve, chest and back. The authored orange shoulders, hem and zipper retain their placement and have stronger coverage at gameplay scale. The body, face, boots and equipment use the original rig and scale. [Visual comparison](Coat-comparison.jpg) · [Owner's original sheet](../References/18617-original.jpg)

I tested the normal 1× lens and 2× pinch at four headings in the signed Level 1 scene. For each image a separate UV material-ID capture located the authored fabric and trim. Across eight camera and heading combinations, the average blue difference from the source swatches fell from 21.75 to 14.45 CIE76 units. Orange fell from 13.48 to 10.76. The same fixed screen-space pigment masks contained 3,278 distinctly blue samples before and 5,027 afterward. Distinctly orange samples rose from 1,223 to 1,262. The snowy field has stronger directional shadows than the studio sheet. [Measurements and samples](Paint-verification.json) · [Original 1×](baseline-gameplay-1x.png) · [Final 1×](final-gameplay-1x.png) · [Final 2×](final-gameplay-2x.png)

The correction affects one embedded 2,048 × 2,048 base-color image. All other 465 binary buffer views match the baseline byte for byte, including body geometry, normals, weights, animations and physically based material maps. A second run of the paint recipe from the baseline produces the identical final GLB. It uses NumPy, SciPy and Pillow. The hashes and unaffected pixel counts are in the verification record. [Paint recipe](rebuild.py)

    python3 rebuild.py BASELINE_CHARACTER.glb REPAIRED_CHARACTER.glb

The baseline GLB was taken from gameplay commit 949af6f0916839ac702725cbd7a0a7c3f1033a5a. The replacement file SHA-256 is 77a5cbf925a82004b003c8c73428d00492b858a3e01f36c483b9f5315e3223fe. This is builder evidence for the independent critic.
