# Rebuild the reviewed World One scene

Use Godot 4.7.2 and a checkout of Havenline containing the gameplay commit listed in Reviewed-files.json. From this directory, run the following commands. The extraction helper verifies each file against the frozen manifest before making the project available.

    python3 prepare.py /path/to/HAVENLINE /new/path/WorldOne
    godot --headless --editor --import --path /new/path/WorldOne
    XDG_DATA_HOME="$(mktemp -d)" godot --path /new/path/WorldOne

The final command runs the ordinary opening in a fresh Linux user-data directory. The entry scene is `res://field_opening.tscn`.

The preparation helper extracts the axe’s three original material maps from the verified Meshy donor before the first Godot import. This allows a fresh checkout to load the fitted axe regardless of the importer’s file order. [Texture provenance](../Play/Tool-texture-custody.json)
