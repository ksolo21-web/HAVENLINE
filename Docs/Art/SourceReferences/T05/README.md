# T05 cookbook cooker — owner-authoritative visual sources

Canonical image filenames: `32451.jpg` (front three-quarter), `32450.jpg` (right), and `32441.png` (rear). Exact SHA-256 and original dimensions are specified in [reference-manifest.json](reference-manifest.json).

**Public storage is authorized by the owner.** Do not treat historical checkpoint phrases about *public reference-image restriction* as the current instruction. Nonetheless keep all non-owner secrets, proprietary third-party assets and release signing keys out of public Git.

Only a model actually passing visual critique against the three source images can be promoted into the shipping `HavenlineGodot/assets/` tree. The R28–R33 models are rejected experimental candidates. Shader, geometry and engine import tests alone do not constitute visual approval.

**Import status:** Manifest is versioned; the three exact original image binaries have not yet been written to this Git branch. Upload as actual Git-tracked image files with matching SHA-256 rather than embedding image data in docs or claiming that an Actions upload artifact is durable source control.
