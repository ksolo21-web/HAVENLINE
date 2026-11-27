# Integrate the reviewed Havenline icon

## Source binding

Audited game branch: `trial/world-one-expansion-2026-11-26`, commit `429cb7ea56d98f7d023d7d6eeb18c89feb711fbc` (Build 16 QA). Its `HavenlineLevel1/project.godot` already has:

```ini
[application]
config/icon="res://assets/field/field_icon.png"
```

The existing icon is 432×432 RGB, 211239 bytes, Git blob `262121a3f337f795aa05c29c166f3ba1ff88ba86`. Resolve the actual current trial head before integration; preserve unrelated changes and historical QA files.

## Files to copy into the active project

Paths on the left are relative to this package. Destinations are relative to `HavenlineLevel1/`.

| Selected package file | Destination |
|---|---|
| `assets/havenline-icon-1024.png` | `assets/field/field_icon.png` |
| `assets/havenline-adaptive-foreground-432.png` | `export-artwork/havenline-icon-foreground.png` |
| `assets/havenline-adaptive-background-432.png` | `export-artwork/havenline-icon-background.png` |
| `assets/havenline-monochrome-432.png` | `export-artwork/havenline-icon-monochrome.png` |

## Android preset fields

Apply these values to the current build's Android export preset; do not modify the captured historical `Docs/QA/Truck-Access-2026-11-27/Source/export_presets.cfg`.

```ini
launcher_icons/main_192x192="res://assets/field/field_icon.png"
launcher_icons/adaptive_foreground_432x432="res://export-artwork/havenline-icon-foreground.png"
launcher_icons/adaptive_background_432x432="res://export-artwork/havenline-icon-background.png"
launcher_icons/adaptive_monochrome_432x432="res://export-artwork/havenline-icon-monochrome.png"
```

The monochrome asset is selected after independent inspection of actual dark and warm themed composites. Replace the old monochrome binding as shown so the name and new hearth remain consistent. Its substantive alpha is entirely within the safe circle; four alpha=1 edge pixels beyond that circle are retained and documented in the review. Device QA should check the launcher's actual themed rendering.

Godot's 4.7 exporter accepts a larger main PNG and generates its smaller density variants. The two 432px adaptive layers are supplied separately, with essential foreground art inside the centered 264px safe circle. The explicit background prevents a fallback Godot background. Verify actual imported images and installed icon in the next build; these source instructions and simulated masks are not installed-device evidence.

## Official specification sources

- https://docs.godotengine.org/en/4.7/tutorials/export/exporting_for_android.html
- https://developer.android.com/develop/ui/compose/system/icon_design_adaptive

Checked 2026-11-27. No game name change, package identifier, version number, signing setting, workflow or gameplay behavior is part of this icon update.
