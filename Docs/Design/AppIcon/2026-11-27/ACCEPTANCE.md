# Havenline app icon refresh

## Scope and request

Kaleb: “we need a better app icon”. Subsequent steering: “the name of the game too”. The latter is being implemented as including the exact existing name **HAVENLINE** in the icon. No game rename is claimed.

The deliverable is a new raster app icon and Android export artwork, reviewed at launcher sizes, with a narrowly scoped integration package. The existing camp hearth identity, polished sculpted shapes, snow, deep blue and warm orange are retained. New branding composition is authored art, not a claim of final native prop or gameplay visual approval.

## Milestones

1. Source and brand audit: verified current icon and bindings at trial commit `429cb7ea56d98f7d023d7d6eeb18c89feb711fbc` (Build 16 QA).
2. Create named master and export layers.
3. Inspect actual size and shape previews, independently critique, fix and retest.
4. Persist reviewed package, integration instructions and exact publication evidence on an isolated GitHub branch.

## Acceptance checks

- A1: Exact HAVENLINE spelling in named color icon; no unintended text.
- A2: Polished warm hearth, blue stone and snow; distinct from the muted current product render.
- A3: Full-bleed opaque square master without baked rounded corners.
- A4: Whole name legible at normal 64/96px launcher sizes; inspect 48px readability and 32px hearth recognition honestly.
- A5: Circle and squircle masks retain essential hearth/flame/name; adaptive critical art stays in the documented safe circle.
- A6: Explicit transparent foreground, opaque background and optional monochrome export; verify size/alpha, source bindings and exact bytes.
- A7: Independent critic inspects actual pixels and source-bound evidence; preserve rejects and retests. Every mandatory scoped requirement passes, scores strictly above 9.0; stronger applicable reference requirements remain unchanged.
- A8: Preserve active gameplay branch, existing historical art and QA presets. No game build, physical device install, playtest or release approval claimed.
- A9: Published assets are full PNG Git blobs with verified remote identities. No generated art remains only in scratch.

## Platform evidence

- Godot 4.7 Android export docs: https://docs.godotengine.org/en/4.7/tutorials/export/exporting_for_android.html
- Android adaptive icon design: https://developer.android.com/develop/ui/compose/system/icon_design_adaptive

Checked 2026-11-27. Godot documents separate foreground/background and a centered 264px safe-circle diameter on a 432px canvas. Platform export resizing is mechanical; all creative artwork/edits use the built-in image generator.
