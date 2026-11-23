# Isolated native buy marker reference
Godot 4.7.2, gl_compatibility project. Instantiate `buy_pad.tscn` and call `show_offer` after `_ready`. The display is a consumer of trusted, authoritative gameplay state, not an interaction zone, ledger, payment animation, placement decision, resource table, asset integration, or visual approval. Labels are injected from the caller and all supplied fixture text is synthetic. The scene only uses original native geometry; it has no dependency on source screenshots or concept pixels, and no change to the V3 storage candidate.

Directional cues: Havenline art ref 8f46b67568a9ae3bc2df0d9dade8714039a1cc99, purchase activation plate blob 58ccf2d22537c89c6c597ceecadd6265fda23a82; locked Primary B frames 5.2 / 5.5 / 5.8 / 6.1 / 6.4 / 6.7 sec. Use a low muted deck with separate pale corner brackets and readable action/cost. Tint only corners during partial payment; tint deck and corners during final pending confirmation; preserve the label and never hide a paying/pending instance. Hide only after acceptance for one-time, or return repeatable to the neutral offer if another tier is available. Unavailable offers are hidden; cancellation can restore the available snapshot. No copied amounts, timed ordering or fence timing. As a local candidate dimensions, materials and text proxies are unapproved and intentionally tunable. No sink animation or fade: reuse only on explicit trusted notification of a successful commit and after visual review.

Test from this directory:
```sh
tmp=$(mktemp -d)
XDG_DATA_HOME="$tmp/data" XDG_CONFIG_HOME="$tmp/config" XDG_CACHE_HOME="$tmp/cache" \
  godot --headless --path . --script res://verify_buy_pad.gd
```
Verify next on exact playable Level 1 with its normal gameplay camera and cold save: take matched frames next to passive wood/meat markers, before / partial / final pending / accepted, and confirm action symbol/text, price legibility, local tint and pose, actual typed resource transfer and install timing, and repeatable tier state. An independent critic must cover each applicable visual gate at 9.5+; headless checks only prove isolated inferred state behavior.
