# Havenline — reference-video tree coverage and 360° reconstruction

## Current result

**Two reference appearances are being covered.** Both original recordings show three-tier snow-blue conifers. The fishing/camp footage has broader, flatter angular tabs; the forest/harvesting footage has narrower cuts and a different visible crown treatment. No third appearance was found in the sampled coverage. The footage does not establish the original mesh count or a separate-species count.

**The forest sheet has passed a bounded static review. The fishing/camp sheet remains an unapproved draft and is being rebuilt with controllable geometry. A literal 100% original-source match around the entire tree is not certified.**

## Reviewable outputs

| Target | Current sheet | Native pixels | Review status |
|---|---|---:|---|
| Tree A — fishing/camp appearance | [Best retained eight-view draft, r3](candidates/tree-A-360-r3.png) | 1536 × 1024 | Unapproved: visible fidelity 9.5; static coherence 9.4; 12/13 checks. Rounded middle hems remain. |
| Tree B — forest/harvesting appearance | [Reviewed eight-view reconstruction, r5](candidates/tree-B-360-r5.png) | 1536 × 1024 | Scoped static pass: visible fidelity 9.9; static coherence 9.9; 13/13 checks. |

Each sheet contains the labeled azimuth conventions 0°, 45°, 90°, 135°, 180°, 225°, 270° and 315°. These are reconstruction guides. Raster sheets alone do not establish exact model rotations or one verified underlying mesh.

[A source-facing r1](candidates/tree-A-source-facing-r1.png) is the best retained single-view A draft, at 9.6. Later offset edits did not improve its source registration and are preserved as rejected evidence. [B source-facing r1](candidates/tree-B-source-facing-r1.png) passed its bounded visible-face review at 9.9 and supplied the later B sheets.

The scores are independent visual judgments, not measured percentages of similarity. They do not waive the repository's stronger exact-10 or complete-evidence requirements and do not authorize native integration, task closure or shipping.

## Source coverage and custody

The two exact original MP4 hashes and byte sizes match the existing reference-video lock. The audit inspected **96 source/time samples**: 63 from A at one-second intervals, 27 from B at two-second intervals, and six additional B ending samples. This is sampled coverage, not every decoded video frame.

| Source | Recording | Best clean source crop |
|---|---|---|
| A — fishing/camp | Screen_Recording_20260817_124839_YouTube.mp4 | [A61 tree](source-a-audit/crops/A61-shoreline-three-tier.png) |
| B — forest/harvesting | Screen_Recording_20260817_124510_YouTube.mp4 | [B20 tree](source-crops/02-b20-individual-tree.png) |

[TREE_APPEARANCE_CENSUS.json](TREE_APPEARANCE_CENSUS.json) records the count, appearance targets and sampling limits. Eight supplied source crops are exact, unscaled, unretouched pixel slices with timestamp, rectangle and hash provenance. The round-looking A examples and smaller B examples do not independently establish additional tree designs. The three pre-existing Havenline pine filenames are not evidence for three trees in the original videos.

Original phone-screen frames and source contact sheets are internal analysis inputs rather than clean publication assets. Their hashes are retained in the audit metadata; the published source images are the eight clean crops. Relative raw-frame paths inside reports identify retained analysis inputs and are not claims that every raw frame is included here.

## Open work and approval boundaries

1. **A source-facing geometry:** restore the actual A61 upper-cap/apex and middle-tier placement with controlled geometry. Repeated generated offset edits did not hold that registration. A separate Blender calibration is in progress under the isolated reconstruction-a workspace; no completed native candidate is claimed by this checkpoint.
2. **A reconstructed rotations:** after the visible-face comparison passes, render meaningful additional views from one controlled asset and obtain a fresh independent review. The current A sheet's middle-hem issue remains open.
3. **Original hidden surfaces:** neither recording demonstrates a full orbit of one identified tree. Unseen surfaces are authored reconstruction. Exact original 360° identity requires additional original geometry or sufficient additional source views.
4. **Game integration and task approval:** this art package changes no production asset, scene, gameplay branch, reference lock, historical receipt or task approval. A studio/static review does not certify in-game appearance or behavior.

## Evidence and resumption

- [Original task requirements](REQUIREMENTS.json) preserve the owner requests and initial milestones.
- [Checkpoint 01](CHECKPOINT_01.json) records completed evidence, unresolved checks, dependencies and the concrete next action.
- [Candidate index](CANDIDATE_INDEX.json) binds all twelve generated originals, native dimensions, prompts and review receipts.
- [Source/provenance review](reviews/source-package-review.md) records 12/12 bounded custody checks; this is not an art approval.
- [A latest raster retest](reviews/tree-A-source-facing-r3-review.md) documents why generated offset retries stopped and identifies the best retained drafts.
- [B r5 retest](reviews/tree-B-360-r5-review.md) records the eight inspected views and the repaired side-volume/label defects.
- [Current acceptance binding](ACCEPTANCE_CONTEXT.json) preserves the stronger repository requirements without promoting these informal static reviews into task closure.

Every generated original, prompt, rejection, repair receipt and derived review image is preserved. Inspection enlargements are explicitly analysis evidence; original native resolutions are recorded without calling upscales native or 4K. The file manifest lists the exact published bytes.
