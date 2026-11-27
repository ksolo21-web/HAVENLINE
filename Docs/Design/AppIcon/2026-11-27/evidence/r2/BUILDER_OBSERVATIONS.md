# Named R2 mechanical preview observations

Builder: `/root/icon_source_audit`. This record is **not independent approval**.
The independent reviewer is `/root/icon_critic`.

## Evidence produced and inspected

- `native-sizes-dark.png` and `native-sizes-light.png` show the previous and R2 source artwork at actual 96, 64, 48 and 32 pixels, with square, circle and squircle shapes.
- `named-r2-mask-detail.png` shows R2 at 256 pixels in the three shapes.
- `preview-identity.json` records exact source and output SHA-256 identities and image properties. Source identities were checked before and after generation and are unchanged.
- `commands.txt` records actual ImageMagick commands. `make_previews.py` reproduces the evidence through mechanical resizing, launcher masking, composition and labels; it does not create or alter creative source artwork.

All three sheets were visually inspected using the image-viewing tool.
Representative masks use superellipse powers 2 (circle) and 4 (squircle).
These are mask simulations, not a device or Android launcher run.

## Observations

The new warm flame and blue furnace remain more readily distinguishable than
the muted previous furnace at all inspected sizes. The exact HAVENLINE word
is visible on the unmasked source. The square and squircle previews retain
the wordmark at the inspected 64 and 96 pixel sizes. Text is small at 48px;
the 32px row should be judged for hearth recognition, not promised full text
legibility.

**The circle clips the outer portions of the first H and last E.** This is
clear in the 256px detail and remains visible in the 64/96px rows. R2 does not
satisfy acceptance A5 as a circle-safe named icon. This needs a creative
layout correction by the image generator and fresh mechanical evidence.

No final export configuration, gameplay source, historical QA preset or
public repository was modified by this preview builder.
