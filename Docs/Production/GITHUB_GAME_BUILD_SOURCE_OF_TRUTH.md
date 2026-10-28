# HAVENLINE — GitHub as the single source of truth for the full game

**Owner decision: 2026-10-28.** All active game development, including source code, original owner-provided art references, generated and edited meshes/textures, scenes, scripts, tests, render evidence, and reproducible Android builds, belongs in the `ksolo21-web/HAVENLINE` GitHub repository. GitHub Actions is the build executor. Do not require additional paid services or new accounts for ordinary project work.

## Which project is built

- **Active game:** `HavenlineGodot/` using Godot **4.7.2** and its Android export templates, with Java 17 and installed Android SDK; Godot is the authoritative Android runtime.
- **Legacy/reference:** `Assets/`, `Packages/`, and `ProjectSettings/` hold historical Unity content. Retain that source in GitHub, but do not accidentally treat the Unity starter project as a second active Android release.
- **Art and assembly:** source images in `Docs/Art/SourceReferences/`; executable Blender/modeling and test scripts in `tools/havenline/`; validated gameplay assets in `HavenlineGodot/assets/`. **Failed or unreviewed T05 cooker meshes remain candidates, not shipping assets.**

## Build workflow and resulting artifacts

`.github/workflows/havenline-godot-android.yml` is the authoritative **full-game native Android development build**, runs on GitHub's free standard Linux runners for allowed triggers or manually via Actions:

1. Checkout the exact repository commit; archive the exact relevant Godot/game-modeling/art/reference source and record SHA-256 hashes.
2. Install checksum-pinned official Godot 4.7.2 and matching Android export templates, Java 17 and Android SDK tools.
3. Run asset/environment audits, import/build the real Godot project and execute gameplay, persistence, motion, population, outpost, environment, rendering and adaptive-device tests.
4. Capture actual native Godot mobile-renderer evidence and disclose software GPU limitations.
5. Export the actual arm64 **development review** APK, verify its signature, APK internals and checksums, and upload downloadable workflow artifacts.

**Technical CI green is not a release or visual-critic pass.** No script can self-approve missing owner art review, actual shipping-scene rendering, phone/tablet frame pacing or a complete production game. The separate device/release gate stays fail-closed.

`workflow_dispatch` allows rebuilding a known branch on demand. Branch development and PR paths now include T05 source-reference artwork; the game is built in GitHub rather than only in a local workspace. Do not merge/ship any failed T05 candidate.

GitHub Actions artifacts expire (currently configured 30 days). Preserve accepted game asset *sources* in Git and promote approved release builds to GitHub Releases with permanently referenceable hashes once real release gates pass. Do not publish debug keystores or production signing keys.

## Public reference-image authorization

The owner has explicitly authorized **game photos and game art references to be committed to the public HAVENLINE repository**. After project completion the owner intends to switch the repository to private. This supersedes older T05 *privacy-only* restrictions in historical checkpoint records. It does **not** supersede any art-quality, gameplay, release, third-party copyright or asset-license restriction.

Reference images `32451.jpg`, `32450.jpg`, and `32441.png` remain the authoritative T05 cooker front three-quarter, right-side and rear references; record hashes and exact bytes when adding them under `Docs/Art/SourceReferences/T05/`. Generated derivatives must be labeled as such. Do not substitute AI-invented stone ovens or fake reference views.

**Public-history warning:** making the repository private in the future does not erase past public downloads, fork histories, caches, Git blobs or GitHub Actions artifacts. Avoid committing passwords, private signing material, user personal data or unlicensed third-party artwork. Public owner game art is authorized, but release signing secrets are not.

## Current unclosed work

T05 R33 and all earlier cooker trials have not passed source-fidelity C1/C2 critic, owner sign-off, shipping integration, or physical Android performance testing. GitHub builds can produce and validate review APKs without falsely marking T05 or the whole game complete. The reference images and fresh neural reconstruction candidates must be committed into their appropriate source locations before claiming full source reproducibility.
