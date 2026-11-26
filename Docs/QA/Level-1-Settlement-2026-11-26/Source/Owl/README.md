# Expedition owl source

The source artwork is the selected eight-view Havenline expedition owl board at Git commit `b80c61f13ba31bb0940792dd47976a8e2878dbf5`. Its Git blob is `db465610eb61d155a7ae0876b624fa625361a19f`. [Selected owl turnaround](https://github.com/ksolo21-web/HAVENLINE/blob/b80c61f13ba31bb0940792dd47976a8e2878dbf5/Docs/Design/RenderArchive/2026-11-23/selected/animal-companions/pet_owl_01.png)

The builder reconstructs the body's volume from the board silhouettes and maps the painted plumage, face, leather harness and bedroll onto it. The folded-wing board supplies the feather patterns for the newly authored extended wings. The GLB has articulated shoulders, elbows and wrists on both sides and a talon morph for flight and striking. The runtime controls their timing and verifies talon contact against the wolf mesh.

To reproduce the GLB, use Python with NumPy, SciPy, Pillow and scikit-image 0.25.2. Run this with the source board and a separate output file.

```sh
python build_owl.py pet_owl_01.png expedition_owl.glb
```

The owl purchase and damage receipts belong to the game’s settlement save. The actor is instantiated once per scene. The independent runtime test is `qa_field_owl.gd`.
