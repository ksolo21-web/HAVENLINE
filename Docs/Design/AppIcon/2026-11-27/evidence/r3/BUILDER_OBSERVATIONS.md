# Named R3 mechanical preview observations

Builder: `/root/icon_source_audit`. This record is **not independent approval**.
The independent reviewer is `/root/icon_critic`.

## Actual evidence

The builder inspected `native-sizes-dark.png`, `native-sizes-light.png` and
`named-r3-mask-detail.png` using the image-viewing tool. The sheets contain
actual 96/64/48/32 pixel samples and a 256px shape detail. Source art remains
unchanged and exact identities are in `preview-identity.json`.

Compared with R2, the outer H and final E no longer clip under the circle
mask. The full word is retained in the square, circle and squircle at 256px
and at the inspected normal 64/96px sizes. The 64px title is small but its
letters remain distinguishable. The 48px title is very small. The 32px
sample retains the warm hearth identity; no promise of comfortable full
name reading is made for that size.

These are representative launcher-shape simulations, not an Android
installation or device run. Independent acceptance belongs to the critic.

## Mechanical delivery sizes

`assets/havenline-icon-1024.png` and `assets/havenline-icon-512.png` are
lossless PNG encodings of direct ImageMagick Lanczos resizes of the exact
R3 source. `export-derivation.json` records the source/output identities,
pixel properties and actual commands. No color, composition or lettering
was edited for these exports. The original source and all R2 evidence were
preserved unchanged.
